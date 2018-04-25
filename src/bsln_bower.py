# coding=utf-8
import datetime

import geopandas as gp
import numpy as np
from shapely.geometry import Point

from src import constants as C


# some helper function for Bower.pred()
def get_distance(row):
    a = np.array(row.geometry.coords[0])
    b = np.array(row.cen_coords)
    return np.linalg.norm(a - b)


def calc_risk(df, grid_size, now_date):
    distance = df.apply(get_distance, axis=1) // (grid_size / 2) + 1
    n_weeks = df.Date.apply(lambda x: (now_date - x).days // 7 + 1)
    return (1 / distance * 1 / n_weeks).sum()


class Bower:
    """developed in:
    Bowers, K.J. et al. 2004. Prospective Hot-SpottingThe Future of Crime Mapping?
    The British journal of criminology. 44, 5 (Sep. 2004), 641–658.

    Attributes
    ----------
    last_date: the last date of the events, set after self.fit(), used in self.has_fit()
    events
    """

    def __str__(self):
        return (
            'Bower method: weighted by distance and time, '
            'bandwidth={}, time window={}, verbose={}'
            ''.format(self.bw, self.tw, self.verbose))

    def __init__(self, grid_size, bw=400, tw=60, verbose=0):
        """
        :param grid_size: bower normalize distance by 1/2 of grid_size
        :param bw: bandwidth, int, default = 400
        :param tw: time window, int, default = 60, number of days in the past to be considered
        :param verbose: level of verbosity
        """
        self.bw = bw
        self.tw = tw
        self.verbose = verbose
        self.grid_size = grid_size
        # attributes set after self.fit
        self.last_date = None
        self.events = None

    def has_fit(self):
        return self.last_date is not None

    def fit(self, x_coords, y_coords=None, last_date=None):
        """
        :param x_coords: pd.Series
            Indexed and sorted by Date, with values = coords

            For compatibility with inputs containing names of coords, such as those for RTM,
            coords can be dict. In this case, only len(coords)=1 (1 key) is allowed.

        :param y_coords: not used in bower, for compatibility purpose

        :param last_date: string (format='%Y-%m-%d') or DateTime, default None
            the last date of the time window. If None, the last date of coords is used
        """

        # for compatibility
        if isinstance(x_coords, dict):
            if len(x_coords) != 1: raise ValueError('input coords is dict, but len!=1')
            if self.verbose > 0: print('coords is a dictionary, len==1, keep its value only')
            x_coords = list(x_coords.values())[0]

        if self.tw is not None:
            if last_date is None:
                last_date = x_coords.index.max()
                if self.verbose > 0:
                    print('last_date is None, using coords.index.max()=%s as last_date' % (
                        last_date.strftime('%Y-%m-%d')))
            elif isinstance(last_date, str):
                last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d')

            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            begin_date = last_date - datetime.timedelta(days=self.tw - 1)
            x_coords = x_coords.loc[begin_date:last_date]
            self.last_date = last_date

        events = gp.GeoDataFrame(x_coords.apply(lambda x: Point(*x))).rename(
            columns={C.COL.coords: 'geometry'}).reset_index()
        self.events = events

    def pred(self, spatial_units, now_date=None):
        """

        :param spatial_units: assuming coords of the centers. pd.Series([coord], index=Date)
        :param now_date: Datetime-like object, default None
            now_date for the prediction. If None, now_date=self.last_date+1day
        :return: pd.Series, index=data.index, value=risk score
        """
        # TODO spatial_units can be shapes other than grids

        if now_date is None:
            now_date = self.last_date + datetime.timedelta(days=1)
            if self.verbose > 0:
                print('now_date is None, using self.last_date+1day=%s as now_date' % now_date.strftime('%Y-%m-%d'))

        # grids_center has same index as coords
        grids = gp.GeoDataFrame(spatial_units)
        grids.columns = ['cen_coords']
        grids['geometry'] = grids.cen_coords.apply(lambda x: Point(*x))
        grids['geometry'] = grids.buffer(self.bw)
        joined = gp.sjoin(self.events, grids)
        pred = joined.groupby('index_right') \
            .apply(lambda df: calc_risk(df, self.grid_size, now_date)) \
            .reindex(grids.index).fillna(0)
        return pred

    def tune(self, bw=None):
        """
        Bowers' paper doesn't have bw tuning, this method is for consistency
        """
        if bw is not None:
            self.bw = bw


def main():
    return


if __name__ == '__main__':
    main()
