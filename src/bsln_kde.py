# Author: Jiahui Wu <jeffwu@terpmail.umd.edu>


import datetime

import geopandas as gp
import numpy as np
import pandas as pd
from pyproj import Proj, transform
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KernelDensity


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
        clean['coords'] = clean.geometry.apply(lambda x: x.coords[0])
    elif col_lon is not None and col_lat is not None:
        clean['coords'] = clean.apply(lambda x: (x[col_lon], x[col_lat]), axis=1)
    elif col_coords is not None:
        pass

    # convert to to_epsg
    if verbose > 0:
        print('project to the to_epsg if specified', to_epsg)
    if to_epsg is not None:
        from_proj = Proj(init='epsg:%d' % from_epsg)
        to_proj = Proj(init='epsg:%d' % to_epsg)
        lons = clean['coords'].apply(lambda x: x[0]).tolist()
        lats = clean['coords'].apply(lambda x: x[1]).tolist()
        lons, lats = transform(from_proj, to_proj, lons, lats)
        clean['coords'] = list(zip(lons, lats))

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


class KDE:
    def __str__(self):
        return 'KDE(bandwidth={}, timewindow={}, verbose={})'.format(self.bw, self.tw, self.verbose)

    def __init__(self, bw=1, tw=60, verbose=0):
        """

        :param tw: int, default=None
            time window of data to be considered in estimation
        :param bw:
        :param verbose:
        """
        self.verbose = verbose
        self.bw = bw
        self.tw = tw
        self.estimator = None

    def get_last_date(self, coords, last_date):
        if last_date is None:
            last_date = coords.index.max()
            if self.verbose > 0:
                print('last_date is None, using coords.index.max()=%s as last_date' % (
                    last_date.strftime('%Y-%m-%d')))
        elif isinstance(last_date, str):
            last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d')
        return last_date

    def fit(self, coords, last_date=None):
        """
        :param coords: pd.Series
            Indexed and sorted by Date, with values = coords

            For compatibility with inputs containing names of coords, such as those for RTM,
            coords can be dict. In this case, only len(coords)=1 (1 key) is allowed.

        :param last_date: string (format='%Y-%m-%d') or DateTime, default None
            the last date of the time window. If None, the last date of coords is used
        """

        # for compatibility
        if isinstance(coords, dict):
            if len(coords) != 1: raise ValueError('input coords is dict, but len!=1')
            if self.verbose > 0: print('coords is a dictionary, extracting the only one value')
            coords = list(coords.values())[0]

        if self.tw is not None:
            last_date = self.get_last_date(coords, last_date)
            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            begin_date = last_date - datetime.timedelta(days=self.tw - 1)
            coords = coords.loc[begin_date:last_date]

        kde = KernelDensity(bandwidth=self.bw)
        kde.fit(coords.tolist())
        self.estimator = kde

    def pred(self, data, now_date=None):
        """

        :param coords: pd.Series
        :param now_date: not used in KDE,
        :return:
        """
        # TODO: data could be other spatial unit
        # Now it is assumed as coords

        pdf = np.exp(self.estimator.score_samples(data.tolist()))
        pdf = pd.Series(pdf, index=data.index)
        return pdf

    def tune(self, coords, bw_choice=None, cv=20, n_jobs=1):
        """
        Bandwidth is estimated by gridsearchCV
        :param coords: coords for bw estimation
        :param bw_choice: list-like, default np.linspace(10, 1000, 30)
        :param cv: default 20
        """
        if isinstance(coords, pd.Series):
            if self.verbose > 0: print('converting pd.Series to list')
            coords = coords.tolist()

        if bw_choice is None:
            if self.verbose > 0: print('use default bw_choice')
            bw_choice = np.linspace(10, 1000, 30)
        if self.verbose > 0: print(str(bw_choice))

        if self.verbose > 0: print('gridsearching bw')
        search = GridSearchCV(KernelDensity(), {'bandwidth': bw_choice}, cv=cv, verbose=self.verbose, n_jobs=n_jobs)
        search.fit(coords)

        if self.verbose > 0: print('best parameters:', search.best_params_)
        self.bw = search.best_params_['bandwidth']
