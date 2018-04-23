# coding=utf-8
from src import constants as C

import pandas as pd

from pyproj import Proj, transform


def prep_911_by_category(path=None, from_epsg=4326, to_epsg=3559, verbose=0):
    """
    the 911 data is cleaned, see clean_911.py for details
    """
    if path is None:
        path = C.PATH_DEV.p911
    d911 = pd.read_csv(path, index_col=0)
    d911.index.name = C.COL.ori_index

    # get coords Series
    lons = d911[C.COL.lon].tolist()
    lats = d911[C.COL.lat].tolist()
    # convert to to_epsg
    if verbose > 0:
        print('project to the to_epsg if specified', to_epsg)
    if to_epsg is not None:
        from_proj = Proj(init='epsg:%d' % from_epsg)
        to_proj = Proj(init='epsg:%d' % to_epsg)
        lons, lats = transform(from_proj, to_proj, lons, lats)
    d911[C.COL.coords] = list(zip(lons, lats))

    # set Date as index
    d911 = d911.reset_index().set_index(C.COL.date)

    d911_by_cat = dict(tuple(d911.groupby(C.COL.category)))
    return d911_by_cat


def main():
    d911_by_cat = prep_911_by_category(path='../'+C.PATH_DEV.p911, verbose=1)
    for key, df in d911_by_cat.items():
        print('=======================')
        print(key)
        print('=======================')
        print(df.head())
    return


if __name__ == '__main__':
    main()