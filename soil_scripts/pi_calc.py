import os
import pandas as pd
import geopandas as gpd


# only favorable soils are used (first 3 values) - no
# table provided to separete one from another, but there is column in csv where
# this can be specified (1=unfavorable) and values from columns 4-6 will be
# taken in calculation also.
letters = {
    'A': [1, 0.96, 0.89, 1., 0.94, 0.79],  # 0-2%
    'B': [0.99, 0.95, 0.88, .99, .93, .78],  # 2-4
    'C': [0.97, 0.93, 0.86, .96, .90, .74],  # 4-7
    'D': [0.93, 0.89, 0.81, .91, .83, .69],  # 7-12
    'E': [0.87, 0.82, 0.75, .85, .78, .63],  # 12-18
    'F': [0.71, 0.66, 0.59, .68, .62, .47],  # 18-35
    'G': [0.52, 0.48, 0.40, .49, .43, .28],  # 35-43
    'H': [0.48, 0.44, 0.36, .45, .39, .24],  # >43
}
pth_fl = os.path.dirname(__file__)
pth_sr = os.path.join(pth_fl, '..', 'data', 'soil_ratings.csv')

# this file contains 2 columns with values, one returns values equal to this
# from book, others from written example on coda.io
# all soils are marked as favorable as no source was specified to get proper
# values
# originating from this site:
# https://www.nrcs.usda.gov/publications/University%20of%20Illinois%20Base%20Yield%20Indices%20%28for%20use%20in%20IL%20only%29%20-Query%20By%20Soil%20Survey%20Area.html#reportref  # noqa
dv = pd.read_csv(pth_sr)


def calculate_pi_val(code: str) -> int:
    if code not in dv.musym.values:
        return None
    slope_code = ''
    soil_code = ''
    letter = ''
    for li in letters.keys():
        if li in code:
            soil_code = code.split(li)[0]
            slope_code = code.split(li)[-1]
            slope_code = slope_code if slope_code in ['3', '2'] else ''
            letter = li

    if soil_code == '':
        slope_code = ''
        letter = 'A'
        # there are some other caps letters in soil names
        # like L but script will treat it as A

    val = dv[dv.musym == code].loc[:, 'value'].values[0]
    fav = dv[dv.musym == code].loc[:, 'unfavorable'].values[0]
    # this will use unfavorable columns [3:6] from letters
    fav = fav if fav == 0 else 3
    ind = 0
    if slope_code == '2':
        ind = 1
    elif slope_code == '3':
        ind = 2

    return round(val * letters[letter][int(ind+fav)])


def process_pi(pth: str) -> pd.DataFrame:
    df = gpd.read_file(pth, layer='mapunit', ignore_geometry=True)

    df.loc[:, 'pi'] = df.apply(lambda xx: calculate_pi_val(xx.musym), axis=1)
    return df[['mukey', 'pi']]


if __name__ == '__main__':
    process_pi('/Users/pawel/freelance/ssurgo/gSSURGO_IL.gdb')
