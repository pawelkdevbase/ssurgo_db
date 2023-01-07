import os
import geopandas as gpd
import pandas as pd

from . import utils

# dict to translate county names to Surveyareas
counties_dct = {
    "Lyon": "IA119",
    "Osceola": "IA143",
    "Dickinson": "IA059",
    "Emmet": "IA063",
    "Kossuth": "IA109",
    "Winnebago": "IA189",
    "Worth": "IA195",
    "Mitchell": "IA131",
    "Howard": "IA089",
    "Winneshiek": "IA191",
    "Allamakee": "IA005",
    "Sioux": "IA167",
    "O'Brien": "IA141",
    "Clay": "IA041",
    "Palo Alto": "IA147",
    "Hancock": "IA081",
    "Cerro Gordo": "IA033",
    "Floyd": "IA067",
    "Chickasaw": "IA037",
    "Fayette": "IA065",
    "Clayton": "IA043",
    "Plymouth": "IA149",
    "Cherokee": "IA035",
    "Buena Vista": "IA021",
    "Pocahontas": "IA151",
    "Humboldt": "IA091",
    "Wright": "IA197",
    "Franklin": "IA069",
    "Butler": "IA023",
    "Bremer": "IA017",
    "Dubuque": "IA061",
    "Woodbury": "IA193",
    "Ida": "IA093",
    "Sac": "IA161",
    "Calhoun": "IA025",
    "Webster": "IA187",
    "Hamilton": "IA079",
    "Hardin": "IA083",
    "Grundy": "IA075",
    "Black Hawk": "IA013",
    "Buchanan": "IA019",
    "Delaware": "IA055",
    "Jackson": "IA097",
    "Tama": "IA171",
    "Benton": "IA011",
    "Linn": "IA113",
    "Jones": "IA105",
    "Monona": "IA133",
    "Crawford": "IA047",
    "Carroll": "IA027",
    "Greene": "IA073",
    "Boone": "IA015",
    "Story": "IA169",
    "Marshall": "IA127",
    "Clinton": "IA045",
    "Harrison": "IA085",
    "Shelby": "IA165",
    "Audubon": "IA009",
    "Guthrie": "IA077",
    "Dallas": "IA049",
    "Polk": "IA153",
    "Jasper": "IA099",
    "Poweshiek": "IA157",
    "Iowa": "IA095",
    "Johnson": "IA103",
    "Cedar": "IA031",
    "Scott": "IA163",
    "Muscatine": "IA139",
    "Pottawattamie": "IA155",
    "Cass": "IA029",
    "Adair": "IA001",
    "Madison": "IA121",
    "Warren": "IA181",
    "Marion": "IA125",
    "Mahaska": "IA123",
    "Keokuk": "IA107",
    "Washington": "IA183",
    "Louisa": "IA115",
    "Mills": "IA129",
    "Montgomery": "IA137",
    "Adams": "IA003",
    "Union": "IA175",
    "Clarke": "IA039",
    "Lucas": "IA117",
    "Monroe": "IA135",
    "Wapello": "IA179",
    "Jefferson": "IA101",
    "Henry": "IA087",
    "Des Moines": "IA057",
    "Fremont": "IA071",
    "Page": "IA145",
    "Taylor": "IA173",
    "Ringgold": "IA159",
    "Decatur": "IA053",
    "Wayne": "IA185",
    "Appanoose": "IA007",
    "Davis": "IA051",
    "Van Buren": "IA177",
    "Lee": "IA111",
}


def process_csr2(pth: str) -> pd.DataFrame:
    pth_fl = os.path.dirname(__file__)
    pth_csr2 = os.path.join(pth_fl, '..', 'data', 'CSR2_ratings.csv')
    dc = pd.read_csv(pth_csr2, sep='\t')
    dc['NAME'] = dc.County.str.replace(' County', '')
    dc.rename(columns={'Soil Code': 'MUSYM',
                       'Soil Description.1': 'csr2'},
              inplace=True)
    del dc['Soil Description']

    # get all mukes per county
    allmu = pd.DataFrame()
    ii = 0
    while True:
        mu = gpd.read_file(
            pth,
            layer='MUPOLYGON',
            ignore_geometry=True,
            rows=slice(ii, ii+10000)
        )
        if mu.shape[0] == 0:
            break
        allmu = pd.concat([allmu, mu], ignore_index=True)
        # drop duplicate to preserve memory
        allmu = allmu.drop_duplicates(subset=['MUKEY', 'AREASYMBOL'])
        ii += 10000

    del allmu['Shape_Area']
    del allmu['Shape_Length']
    del allmu['SPATIALVER']

    # attach county names
    dsl = pd.DataFrame(
        [{'NAME': key, 'AREASYMBOL': val} for key, val in counties_dct.items()]
    )
    allmus = allmu.merge(dsl, on='AREASYMBOL')
    # atach csr2 values
    df = allmus.merge(dc, on=['NAME', 'MUSYM'], how='left')[['MUKEY', 'csr2']]
    df.rename(columns={'MUKEY': 'mukey'}, inplace=True)
    return df
