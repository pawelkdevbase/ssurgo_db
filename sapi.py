from flask import Flask
from flask import jsonify
import pandas as pd
import geopandas as gpd
import json
from shapely.wkt import loads
from urllib.parse import unquote

from soil_scripts import db


EMPTY = '{"type": "FeatureCollection", "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3857" } }, "features": []}'


def get_features_bbox(bounds: list = []):
    sql = 'select * from ssurgo.poly_aggreg where ' + \
        'ST_Intersects(geometry, ST_MakeEnvelope(' + \
        ', '.join(map(str, bounds)) + ', 4326));'

    with db.sync_session() as session:
        eng = session.get_bind()
        try:
            gdf = gpd.read_postgis(sql, con=eng, crs=4326, geom_col='geometry')
        except Exception:
            gdf = gpd.GeoDataFrame()
    del gdf['id']
    return gdf


app = Flask(__name__)


@app.route("/get-features-bbox/<xmin>,<ymin>,<xmax>,<ymax>")
def get_bbox(xmin, ymin, xmax, ymax):
    gdf = get_features_bbox([xmin, ymin, xmax, ymax])
    if gdf.shape[0] == 0:
        return jsonify(json.loads(EMPTY))

    js = gdf.to_json()
    js = json.loads(js)
    return jsonify(js)


@app.route("/get-features-poly/<poly>")
def get_poly(poly):
    un = unquote(poly)
    try:
        poly = loads(un)
    except Exception:
        return jsonify(json.loads(EMPTY))

    gdf = get_features_bbox(poly.bounds)
    gdf = gdf.to_crs(5070)
    gdf['total_area'] = gdf.area
    gdf = gdf.to_crs(4326)
    gdf = gdf.clip(poly)
    if gdf.shape[0] == 0:
        return jsonify(json.loads(EMPTY))
    gdf = gdf.to_crs(5070)
    gdf['area_AOI'] = gdf.area
    gdf['area_perc'] = (gdf.area_AOI/gdf.area.sum()) * 100
    gdf = gdf.to_crs(4326)

    js = gdf.to_json()
    js = json.loads(js)
    return jsonify(js)


@app.route("/get-components-by-mukey/<muks>")
def get_components(muks):
    """
    returns components descriptions as json for max 500 mukeys codes
    """

    mukeys = "'"
    mukeys += "','".join(
        [xx for xx in muks.split(',') if xx.isdigit()][:500]
    )
    mukeys += "'"
    sql = '''
    select
        mukey,
        cokey,
        comppct_r,
        compname,
        slope_r,
        cropprodindex
    from
        ssurgo.component
    where mukey in
   ''' + f"({mukeys});"

    with db.sync_session() as session:
        eng = session.get_bind()
        try:
            df = pd.read_sql_query(sql, con=eng)
        except Exception:
            df = pd.DataFrame()

    js = df.to_json()
    js = json.loads(js)
    return jsonify(js)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
