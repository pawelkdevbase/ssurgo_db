import pandas as pd
import geopandas as gpd

from .csr2_dcts import DCT_SFAC, DCT_MFAC, DCT_EJ_ADD, DCT_EJ_SUBST
from . import utils

dct_sfac = DCT_SFAC
dct_mfac = DCT_MFAC
dct_ej_add = DCT_EJ_ADD
dct_ej_subst = DCT_EJ_SUBST


def calc_mfactor(val):
    out = 0
    if val is None:
        val = ''
    if val in dct_mfac:
        out += dct_mfac[val]
    elif val is None:
        out += 5
    elif 'skeletal' in val:
        return 12
    if 'calcareous' in val:
        out += 5
    return out


def calc_wfactor(val):
    try:
        float(val)
    except Exception:
        return 99
    if val < 3.01:
        return 24
    if val < 6.00:
        return 12
    if val < 9.0:
        return 8
    return 0


def calc_dfactor(row):
    if 'Histosols' in row.compname:
        return 0
    try:
        int(row.tfact)
    except Exception:
        return 0

    if int(row.tfact) == 5:
        return 0
    if int(row.tfact) == 4:
        return 10
    if int(row.tfact) == 3:
        return 20
    if int(row.tfact) == 2:
        return 30
    if int(row.tfact) == 1:
        return 40


def calc_fpond(val):
    if val.ponddurcl in ['Brief (2 to 7 days)',
                         'Very Brief']:
        if val.pondfreqcl in ['Frequent', 'Occasional']:
            return 20
    if val.ponddurcl in ['Long (7 to 30 days)',
                         'Very long (more than 30 days)']:
        if val.pondfreqcl in ['Frequent', 'Occasional']:
            return 44
    return 0


def calc_fflood(val):
    if val.flodfreqcl == 'Frequent':
        if val.floddurcl == 'Brief (2 to 7 days)':
            return 20
        if val.floddurcl == 'Very brief (4 to 48 hours)':
            return 10
        if val.floddurcl == 'Extremely brief (0.1 to 4 hours)':
            return 5
    if val.flodfreqcl == 'Occasional':
        if val.floddurcl == 'Brief (2 to 7 days)':
            return 6
        if val.floddurcl == 'Very brief (4 to 48 hours)':
            return 4
        if val.floddurcl == 'Long (7 to 30 days)':
            return 10
        if val.floddurcl == 'Very long (more than 30 days)':
            return 34
        if val.floddurcl == 'Extremely brief (0.1 to 4 hours)':
            return 2
    return 0


def calc_slope(val):
    try:
        float(val)
    except Exception:
        return 0

    if val < 2:
        return 0
    if val < 5:
        return 5
    if val < 9:
        return 15
    return 3 * val


def calc_conditions(row):
    out = 0
    if 'channeled' in str(row.localphase):
        out += 40
    if 'Class 2' in str(row.erocl):
        out += 3
    return out


def calc_ej(row):
    out = 0
    if row.compname in dct_ej_subst:
        out += dct_ej_subst[row.compname]
    if row.compname in dct_ej_add:
        out -= dct_ej_add[row.compname]

    if row.mukey in dct_ej_add:
        out -= dct_ej_add[row.mukey]
    return out


def calc_csr2(mukey: str = '409089', **kwargs) -> int:
    component = kwargs['component']
    comnth = kwargs['comnth']
    cho = kwargs['cho']

    sin = component[component.mukey == mukey]

    # initial checking
    if 'Gullied Land' in sin.compname.values:
        return 5
    if 'Urban Land' in sin.compname.values:
        return 5
    if sin[(sin.nirrcapscl == 'w') & (sin.nirrcapcl == 5)].shape[0] > 0:
        return 25
    if 'Miscellaneous Area' in sin.compkind:
        return 0

    sin = sin[[
        'mukey',
        'cokey',
        'majcompflag',
        'comppct_r',
        'compname',
        'localphase',
        'taxsubgrp',
        'taxpartsize',
        'tfact',
        'slope_r',
        'erocl',
    ]]

    sin['s_fact'] = sin.apply(
        lambda xx: dct_sfac[xx.taxsubgrp]
        if xx.taxsubgrp in dct_sfac else -999, axis=1)

    sin = sin[sin.s_fact > -100]
    if sin.shape[0] == 0:
        return 5

    cokey = sin.cokey.values
    coms = comnth[(comnth.cokey.isin(cokey))]

    if 'Very frequent' in coms.flodfreqcl:
        return 5
    if 'Frequent' in coms.flodfreqcl and \
            'Very long (more than 30 days)' in coms.floddurcl:
        return 5
    if 'Frequent' in coms.flodfreqcl and \
            'Long (7 to 30 days)' in coms.floddurcl:
        return 5
    coms = comnth[(comnth.cokey.isin(cokey)) & (comnth.month == 'May')]
    coms = coms[[
        'flodfreqcl', 'floddurcl', 'pondfreqcl', 'ponddurcl', 'cokey'
    ]]

    # select chorizons from this component
    chos = cho[cho.cokey.isin(cokey)]
    # calc m factor
    sin['m_fact'] = sin.apply(lambda xx: calc_mfactor(xx.taxpartsize), axis=1)

    chos.loc[:, 'cwhc'] = (chos.hzdepb_r - chos.hzdept_r) * chos.awc_r
    chos.loc[:, 'dpth'] = chos.hzdepb_r - chos.hzdept_r
    chocalc = chos.groupby('cokey').agg({'dpth': 'sum', 'cwhc': 'sum'})
    sin = sin.merge(chocalc, on='cokey', how='left')
    sin = sin.dropna(subset=['cwhc'])  # drop components without water

    # wfactor
    sin['w_fact'] = sin.apply(lambda xx: calc_wfactor(xx.cwhc), axis=1)

    # d factor
    sin['d_fact'] = sin.apply(lambda row: calc_dfactor(row), axis=1)

    sin = sin.merge(coms, on='cokey', how='left')
    sin['f_flood'] = sin.apply(lambda xx: calc_fflood(xx), axis=1)
    sin['f_pond'] = sin.apply(lambda xx: calc_fpond(xx), axis=1)

    sin['slope'] = sin.apply(lambda row: calc_slope(row.slope_r), axis=1)
    sin['erosion'] = sin.apply(lambda row: calc_conditions(row), axis=1)
    sin['f_fact'] = sin.f_flood+sin.f_pond+sin.slope+sin.erosion

    sin['ej_fact'] = sin.apply(lambda xx: calc_ej(xx), axis=1)

    sin['csr2'] = \
        sin.s_fact-sin.m_fact-sin.w_fact-sin.f_fact-sin.d_fact-sin.ej_fact

    sin['csr2'] = sin.apply(
        lambda xx: 5 if xx['csr2'] < 5 else xx.csr2, axis=1
    )

    # csr2 needs to weighted by area of component in map unit
    sin['csr2_weight'] = (sin.comppct_r/100)*sin.csr2
    sum_csr2 = sin.csr2_weight.sum()

    # for debug purposes, return sin df so You can see selected mukey
    # calculations for each factor
    return round(5 if sum_csr2 < 5 else sum_csr2)


def process_csr2(pth: str) -> pd.DataFrame:
    # load all needed tables
    mapunit = gpd.read_file(pth, layer='mapunit', ignore_geometry=True)
    component = gpd.read_file(pth, layer='component', ignore_geometry=True)
    agg = gpd.read_file(pth, layer='muaggatt', ignore_geometry=True)
    comnth = gpd.read_file(pth, layer='comonth', ignore_geometry=True)
    cho = gpd.read_file(pth, layer='chorizon', ignore_geometry=True)

    # dict needs to be updated from agg table
    dct_ej_add.update(
        {xx: 10 for xx in agg[agg['musym'] == '221B'].mukey.values}
    )

    df = pd.DataFrame(columns=['mukey', 'csr2'])
    for ii, mukey in enumerate(mapunit.mukey.values):
        try:
            val = calc_csr2(mukey, component=component, comnth=comnth, cho=cho)
            df = pd.concat([
                df, pd.DataFrame({'mukey': mukey, 'csr2': val}, index=[0])
            ], ignore_index=True)
        except Exception:
            print(mukey, 'duzy zonk')
            utils.log_event(
                f'Error calculating CSR2 for mukey: {mukey}', ltype='ERROR'
            )

        if ii % 500 == 0 and ii > 0:
            print(f'processed {ii}')

    return df


if __name__ == '__main__':
    process_csr2('/Users/pawel/freelance/ssurgo/gSSURGO_IA.gdb')
