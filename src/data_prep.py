# coding=utf-8
from src import constants as C

import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from pyproj import Proj, transform


def prep_data_from_raw(raw, cached_path=None, col_date='Date', date_format='%m/%d/%Y', from_epsg=4326, to_epsg=None,
                       col_type=None, keep_types=None, col_lon=None, col_lat=None, col_coords=None, verbose=0):
    """from raw data to ready-to-use data format

    1. sort data by date
    2. keep targeted types of data if col_type is specified
    3. remove rows without coordinates and get coords Series indexed by Date
    4. change to target CRS if specified

    Parameters
    ----------

    raw: string, or pd.DataFrame instance, or gp.GeoDataFrame instance
        Raw data to be processed. The parameter can be:

        - string, a path to the data set.
          '.geojson' or '.shp' will be loaded as gp.GeoDataFrame, assuming no missing geometry information
          '.csv' will be loaded as pd.DataFrame
          other types are not supported

        - pd.DataFrame or gp.GeoDataFrame, loaded data

    col_date: string, default='Date'
        the name of the date column,
    date_format: string, default='%m/%d/%Y'
        the format to parse col_date,

    col_type: string, default=None
    keep_types: string of list/tuple of strings, default None
        if col_type is not None, keep rows with types in keep_types

    col_lon: see col_coords

    col_lat: see col_coords

    col_coords : strings, default None
        indicating which column(s) has coordinates information

        - if 'geometry' is in columns, these 3 parameters are ignored

        - elif both col_lon and col_lat is not None, build list of (lon,lat)

        - elif col_coords is not None, use this column. Note that coords should be (lon, lat)

    from_epsg: int,default 4326
    to_epsg: int, default None
        if to_epsg is not None, the coords would be transformed from from_epsg to to_epsg


    Examples
    ----------
    >>> crimes = prep_data_from_raw('data/open-baltimore/raw/BPD_Part_1_Victim_Based_Crime_Data.csv',
    ...             col_lon='Longitude', col_lat='Latitude', col_date='CrimeDate', to_epsg=3559)

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


def prep_911(path=None, from_epsg=4326, to_epsg=3559, col_lat=True, col_lon=True, col_coords=True,
             by_category=True, gpdf=False, coords_series=True, verbose=0):
    """load clean 911 data
    :param path the 911 data which should be cleaned by clean_911.py. default src.constants.PathDev.p911
    Other parameters see prep_clean_point_data()
    """
    if path is None:
        path = C.PathDev.p911
    return prep_clean_point_data(path, from_epsg=from_epsg, to_epsg=to_epsg,
                                 col_lat=col_lat, col_lon=col_lon, col_coords=col_coords,
                                 by_category=by_category, gpdf=gpdf, coords_series=coords_series, verbose=verbose)


def prep_crime(path=None, from_epsg=4326, to_epsg=3559, col_lat=True, col_lon=True, col_coords=True,
               by_category=True, gpdf=False, coords_series=True, verbose=0):
    """load clean 911 data
     :param path the 911 data which should be cleaned by clean_911.py. default src.constants.PathDev.p911
     Other parameters see prep_clean_point_data()
     """
    if path is None:
        path = C.PathDev.crime
    return prep_clean_point_data(path, from_epsg=from_epsg, to_epsg=to_epsg,
                                 col_lat=col_lat, col_lon=col_lon, col_coords=col_coords,
                                 by_category=by_category, gpdf=gpdf, coords_series=coords_series, verbose=verbose)


def prep_clean_point_data(path, from_epsg=4326, to_epsg=3559, col_lat=True, col_lon=True, col_coords=True,
                          by_category=True, gpdf=False, coords_series=True, verbose=0):
    """load clean point data

    Parameters
    ----------

    :param path: cleaned point data, the column names are renamed as those in src.constants.COL

    CRS related

    :param from_epsg: int, epsg of raw data, default 4326
    :param to_epsg: int, epsg of desired crs, e.g. equal distance. default 3559

    what columns to keep, default all true

    :param col_lat: if False, drop Latitude
    :param col_lon: if False, drop Longitude
    :param col_coords: if False and gpdf is True and coords_series not True, drop coords

    types of return data

    :param gpdf: defautl False, if True and coords_series not True, add geometry column and transform pd.DF into gp.GDF
    :param by_category: default True, divide 911 data into dictionary with key=category and value=data in that category
    :param coords_series: default True, return only series of coords.

    other parameters

    :param verbose: verbosity
    """
    if verbose > 0: print('loading data from:', path)
    data = pd.read_csv(path, index_col=0)
    data.index.name = C.COL.ori_index

    # get coords Series
    lons = data[C.COL.lon].tolist()
    lats = data[C.COL.lat].tolist()
    # convert to to_epsg
    if verbose > 0:
        print('project to the to_epsg if specified', to_epsg)
    if to_epsg is not None:
        from_proj = Proj(init='epsg:%d' % from_epsg)
        to_proj = Proj(init='epsg:%d' % to_epsg)
        lons, lats = transform(from_proj, to_proj, lons, lats)
    data[C.COL.coords] = list(zip(lons, lats))

    # set Date as index
    data[C.COL.date] = pd.to_datetime(data[C.COL.date], format=C.COL.date_format)
    data = data.reset_index().set_index(C.COL.date)

    # drop redundant columns
    if not col_lat:
        data.drop(C.COL.lat, inplace=True)
    if not col_lon:
        data.drop(C.COL.lon, inplace=True)
    if not col_coords and gpdf and not coords_series:
        data.drop(C.COL.coords, inplace=True)

    # transform to geopandas.GeoDataFrame
    if gpdf and not coords_series:
        data['geometry'] = data[C.COL.coords].apply(lambda x: Point(x[0], x[1]))
        data = gp.GeoDataFrame(data)
        data.crs = {'init': 'epsg:%d' % (to_epsg if to_epsg is not None else from_epsg), 'no_defs': True}
        if verbose > 0: print('transformed to gpdf, crs=', data.crs)

    # divide 911 by category
    if by_category:
        if verbose > 0: print('divide dataframe by category')
        data = dict(tuple(data.groupby(C.COL.category)))

    # key coords series only
    if coords_series:
        if verbose > 0: print('keep coords series only')
        data = {name: data[C.COL.coords] for name, data in data.items()} if by_category else data[C.COL.coords]

    return data


def main():
    d911 = prep_911(path='../' + C.PathTest.p911, verbose=1, by_category=True, coords_series=False, gpdf=True)
    if isinstance(d911, dict):
        for key, df in d911.items():
            print('=======================')
            print(key, type(df))
            print('=======================')
            print(df.head())
    else:
        print(type(d911))
        print(d911.head())
    return


if __name__ == '__main__':
    main()
