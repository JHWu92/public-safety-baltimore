# coding=utf-8
from src import constants as C

import pandas as pd

from pyproj import Proj, transform


def prep_data(raw, cached_path=None, col_date='Date', date_format='%m/%d/%Y', from_epsg=4326, to_epsg=None,
              col_type=None, keep_types=None, col_lon=None, col_lat=None, col_coords=None, verbose=0):
    """from raw data to ready-to-use data format

    1. sort data by date
    2. keep targeted types of data if col_type is specified
    3. remove rows without coordinates and get coords Series indexed by Date
    4. change to target CRS if specified

    Return

    Parameters
    ----------
    raw: string, or pd.DataFrame instance, or gp.GeoDataFrame instance
        Raw data to be processed. The parameter can be:

        - string, a path to the data set.
          '.geojson' or '.shp' will be loaded as gp.GeoDataFrame, assuming no missing geometry information
          '.csv' will be loaded as pd.DataFrame
          other types are not supported

        - pd.DataFrame or gp.GeoDataFrame, loaded data

    col_date: string, the name of the date column, default='Date'
    date_format: string, the format to parse col_date, default='%m/%d/%Y'

    col_type: string, default=None
    keep_types: string of list/tuple of strings, default None
        if col_type is not None, keep rows with types in keep_types

    col_lon, col_lat, col_coords: strings, default None
        indicating which column(s) has coordinates information

        - if 'geometry' is in columns, these 3 parameters are ignored

        - elif both col_lon and col_lat is not None, build list of (lon,lat)

        - elif col_coords is not None, use this column. Note that coords should be (lon, lat)

    from_epsg, to_epsg: int, from_epsg default 4326, to_epsg default None
        if to_epsg is not None, the coords would be transformed from from_epsg to to_epsg

    """

    # Loading raw
    if isinstance(raw, str):
        if raw.endswith('.geojson') or raw.endswith('.shp'):
            raw = gp.read_file(raw)
        elif raw.endswith('.csv'):
            raw = pd.read_csv(raw)
        else:
            raise ValueError('raw_path=%s, this type of file is not supported' % raw)

    # make sure data has column of date
    if col_date not in raw.columns: raise ValueError('date column %s is not in columns' % col_date)

    # keep row with coords
    if verbose > 0: print('remove rows w/o coords')
    if 'geometry' in raw.columns:
        # assuming each row has a valid geometry
        if verbose > 0: print('geometry is in columns')
        clean = raw.copy()
    elif col_lon is not None and col_lat is not None:
        clean = raw[~raw[col_lon].isnull()].copy()
    elif col_coords is not None:
        clean = raw[~raw[col_coords].isnull()].copy()
    else:
        raise ValueError('No coordinate column(s) is provided')

    # get coords Series
    if verbose > 0: print('get coords Series')
    if 'geometry' in clean.columns:
        clean[C.COL.coords] = clean.geometry.apply(lambda x: x.coords[0])
    elif col_lon is not None and col_lat is not None:
        clean[C.COL.coords] = clean.apply(lambda x: (x[col_lon], x[col_lat]), axis=1)
    elif col_coords is not None:
        pass

    # convert to to_epsg
    if verbose > 0:
        print('project to the to_epsg if specified', to_epsg)
    if to_epsg is not None:
        from_proj = Proj(init='epsg:%d' % from_epsg)
        to_proj = Proj(init='epsg:%d' % to_epsg)
        lons = clean[C.COL.coords].apply(lambda x: x[0]).tolist()
        lats = clean[C.COL.coords].apply(lambda x: x[1]).tolist()
        lons, lats = transform(from_proj, to_proj, lons, lats)
        clean[C.COL.coords] = list(zip(lons, lats))

    # clean date column
    if verbose > 0:
        print('sort data by date, set col_date from "%s" to "Date"' % col_date)
    clean.rename(columns={col_date: 'Date'}, inplace=True)
    clean['Date'] = pd.to_datetime(clean['Date'], format=date_format)
    clean = clean.reset_index().set_index('Date').sort_index()

    # clean types of data
    if verbose > 0:
        print('keep targeted types of data if col_type is specified', col_type)
    if col_type is not None:
        if keep_types is None:
            raise ValueError('please specify keep_types')
        if isinstance(keep_types, str):
            keep_types = (keep_types,)
        clean = clean[clean[col_type].isin(keep_types)]

    return clean


def prep_911_by_category(path=None, from_epsg=4326, to_epsg=3559, verbose=0, coords_only=True):
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
    d911[C.COL.date] = pd.to_datetime(d911[C.COL.date], format=C.COL.date_format)
    d911 = d911.reset_index().set_index(C.COL.date)

    d911_by_cat = dict(tuple(d911.groupby(C.COL.category)))
    if coords_only:
        d911_by_cat = {name: data[C.COL.coords] for name, data in d911_by_cat.items()}
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