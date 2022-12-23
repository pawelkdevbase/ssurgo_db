
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

from soil_scripts import config, db, utils
from soil_scripts.downloader import download_ssurgo
from soil_scripts.csr2 import process_csr2

from zipfile import ZipFile
import shutil


def load_mupolygon(dbf: str, state: str) -> None:
    """
    Loads polygons to db by geopandas, its a slower but with more control over
    the process than using ogr2ogr
    """
    sl = 0  # slice
    utils.log_event(f'uploading mupolygon layer for state - {state}, [START]')
    while True:
        try:
            gdf = gpd.read_file(
                dbf, layer='mupolygon', rows=slice(sl, sl+1000)
            )
        except Exception:
            utils.log_event(
                f'Failed to load mupolygon features slice [{sl} - {sl+1000}] '
                f'for state: {state}',
                ltype='ERROR'
            )
            continue
        if gdf.shape[0] == 0:
            break
        gdf = gdf.to_crs(epsg='4326')
        # delete columns by ArcGIS
        del gdf['Shape_Area']
        del gdf['Shape_Length']
        # turn columns names to lower to match db headers
        gdf.rename(columns={xx: xx.lower() for xx in gdf.columns},
                   inplace=True)
        # promote all geometries to multi
        gdf["geometry"] = [
            MultiPolygon([feature]) if isinstance(feature, Polygon)
            else feature for feature in gdf["geometry"]
        ]
        gdf['state'] = state  # add state name to column
        # checking geometry is omitting here, check out ssurgo_stat, there is
        # procedure to check geoemtry duplicates for state database,
        # NOTE: data from october 2022 have no overlapping and duplicates
        # problems

        try:
            with db.sync_session() as session:
                eng = session.get_bind()
                gdf.to_postgis(
                    name='mupolygon', con=eng,
                    schema='ssurgo', if_exists='append', chunksize=500
                )
        except Exception:
            utils.log_event(
                f'Failed to load mupolygon features slice [{sl} - {sl+1000}] '
                f'for state: {state}',
                ltype='ERROR'
            )
        sl += 1000
    utils.log_event(f'uploaded mupolygon layer for state - {state}, [END]')


def load_aggreg(dbf: str, state: str) -> None:
    """
    Function downloads all mukeys values from database to avoid duplicates (
    some states have same mukey records - no need to import them again,
    they have the same values).
    inputs:
    dbf: path to esri gdb folder
    state: state shortcut ('AI')
    """
    # check if file with PI and DI exists, if so load it or create dummy df
    mpth = os.path.dirname(__file__)
    if os.path.isfile(
        os.path.join(mpth, 'data', 'Max_Components_DI_PI_LUT_2020.csv')
    ):
        pidi = pd.read_csv(
            os.path.join(mpth, 'data', 'Max_Components_DI_PI_LUT_2020.csv'),
            converters={'mukey': str, 'Final_PI': int, 'Final_DI': int}
        )
        pidi = pidi.loc[:, ['mukey', 'Final_PI', 'Final_DI']]
    else:  # no file - create dummy empty dataset
        pidi = pd.DataFrame(index=['mukey', 'Final_DI', 'Final_PI', ])
    pidi.rename(columns={'Final_PI': 'pi', 'Final_DI': 'di'}, inplace=True)

    with db.sync_session() as session:
        eng = session.get_bind()
        ukey = pd.read_sql_query('select mukey from ssurgo.aggreg', con=eng)

    df = gpd.read_file(
        dbf,
        layer='mapunit',
        ignore_geometry=True,
    )
    df.rename(columns={xx: xx.lower() for xx in df.columns}, inplace=True)
    df = df.loc[:, ["mukey", "muname", "iacornsr"]]
    df.rename(columns={'iacornsr': 'csr'}, inplace=True)
    df = df[~df['mukey'].isin(ukey.mukey.values)]
    df = df.merge(pidi, on='mukey', how='left')
    del pidi

    dfv = gpd.read_file(
        dbf,
        layer='valu1',
        ignore_geometry=True,
    )
    dfv.rename(columns={xx: xx.lower() for xx in dfv.columns}, inplace=True)
    dfv = dfv.loc[:, ['mukey', 'nccpi3corn', 'nccpi3soy', 'nccpi3cot',
                      'nccpi3sg', 'nccpi3all', ]]

    df = df.merge(dfv, on='mukey', how='left')

    with db.sync_session() as session:
        eng = session.get_bind()
        df.to_sql(
            name='aggreg', con=eng,
            schema='ssurgo', if_exists='append', chunksize=400,
            index=False
        )
    utils.log_event(f'uploaded aggreg table for state - {state}')


def load_table(dbf: str, tab: str, ukey: list) -> bool:
    dfc = gpd.read_file(dbf, layer=tab, ignore_geometry=True)
    dfc.rename(columns={xx: xx.lower() for xx in dfc.columns}, inplace=True)
    if dfc.shape[0] == 0:  # if table is empty omit procedure
        utils.log_event(f"empty table {tab} omit - {dbf.split('_')[-1][:-4]}")
        return True
    dfc = dfc[~dfc['mukey'].isin(ukey)]  # omit values in db
    try:
        with db.sync_session() as session:
            eng = session.get_bind()
            dfc.to_sql(
                name=tab, con=eng, schema='ssurgo', if_exists='append',
                chunksize=500, index=False
            )
        return True
    except Exception:
        return False


def load_tables(dbf: str, state: str) -> None:
    for tab in config.IMPORT_TABLES:
        with db.sync_session() as session:
            eng = session.get_bind()
            ukey = pd.read_sql_query(f'select mukey from ssurgo.{tab}',
                                     con=eng)
        ukey = ukey.mukey.values

        if load_table(dbf, tab, ukey):
            utils.log_event(f'uploaded {tab} table for state - {state}')
        else:
            utils.log_event(f'ERROR uploading {tab} table for state - {state}',
                            ltype='ERROR')


def load_complete_ssurgo() -> None:
    if not os.path.isdir(config.DOWNLOAD_FOLDER):
        os.mkdir(config.DOWNLOAD_FOLDER)
    utils.log_event('Start downloading SSURGO databases')
    download_ssurgo()  # download all states at once
    for st in config.STATES:
        dbz = os.path.join(config.DOWNLOAD_FOLDER, f'gSSURGO_{st}.zip')
        dbf = os.path.join(config.DOWNLOAD_FOLDER, f'gSSURGO_{st}.gdb')
        if not os.path.isdir(dbf):
            if not os.path.isfile(dbz):
                utils.log_event(f'Didn\'t find zip SSURGO for state: {st}')
                continue
            with ZipFile(dbz, 'r') as zf:
                zf.extractall(config.DOWNLOAD_FOLDER)
        load_mupolygon(dbf, st)
        load_aggreg(dbf, st)
        load_tables(dbf, st)
        if st == 'IA':
            df = process_csr2(dbf)
            with db.sync_session() as session:
                eng = session.get_bind()
                df.to_sql(
                    name='aggreg_ia', con=eng,
                    schema='ssurgo', if_exists='append', chunksize=400,
                    index=False
                )
        shutil.rmtree(dbf)  # delete gdb
        os.remove(dbz)  # delete zip


if __name__ == '__main__':
    load_complete_ssurgo()

#     # this is example how to deploy only few states, if You need entire dataset
#     # simply run load_complete_ssurgo() - all USA will be processed
#     if not os.path.isdir(config.DOWNLOAD_FOLDER):
#         os.mkdir(config.DOWNLOAD_FOLDER)
#     states = [
#         # 'MO', 'MT', 'ID', 'WA',
#         # 'MH', 'AS',
#         # 'DC', 'MP', 'FM', 'PW', 'RI', 'DE', 'CT', 'NH', 'NJ', 'VT',
#         #'MA', 'MD', 'ME', #'WV', 'AZ', 'UT', 'SC', 'LA', 'AR', 'AK', 'NV',
#         # 'IA', 'DE'
#     ]
#     download_ssurgo(states)
#     for st in states:
#         dbz = os.path.join(config.DOWNLOAD_FOLDER, f'gSSURGO_{st}.zip')
#         dbf = os.path.join(config.DOWNLOAD_FOLDER, f'gSSURGO_{st}.gdb')
#         if not os.path.isdir(dbf):
#             with ZipFile(dbz, 'r') as zf:
#                 zf.extractall(config.DOWNLOAD_FOLDER)
#         load_mupolygon(dbf, st)
#         load_aggreg(dbf, st)
#         load_tables(dbf, st)
#         if st == 'IA':
#             df = process_csr2(dbf)
#             with db.sync_session() as session:
#                 eng = session.get_bind()
#                 df.to_sql(
#                     name='aggreg_ia', con=eng,
#                     schema='ssurgo', if_exists='append', chunksize=400,
#                     index=False
#                 )
#
#         shutil.rmtree(dbf)  # delete gdb
#         os.remove(dbz)  # delete zip
