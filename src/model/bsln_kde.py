# Author: Jiahui Wu <jeffwu@terpmail.umd.edu>


import datetime

import geopandas as gp
import numpy as np
import pandas as pd
from pyproj import Proj, transform
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KernelDensity

from src import constants as C


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
            last_date = coords.index.max().normalize() + datetime.timedelta(days=1, seconds=-1)
        elif isinstance(last_date, str):
            last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d') + datetime.timedelta(seconds=-1)
        if self.verbose > 0:
            print('last_date = %s' % last_date)
        return last_date

    def fit(self, x_coords, y_coords=None, last_date=None):
        """
        :param x_coords: pd.Series
            Indexed and sorted by Date, with values = coords

            For compatibility with inputs containing names of coords, such as those for RTM,
            coords can be dict. In this case, only len(coords)=1 (1 key) is allowed.

        :param y_coords: not used in KDE, for compatibility purpose

        :param last_date: string (format='%Y-%m-%d') or DateTime, default None
            the last date of the time window. If None, the last date of coords is used
        """

        # for compatibility
        if isinstance(x_coords, dict):
            if len(x_coords) != 1: raise ValueError('input coords is dict, but len!=1')
            if self.verbose > 0: print('coords is a dictionary, len==1, keep its value only')
            x_coords = list(x_coords.values())[0]

        if self.tw is not None:
            last_date = self.get_last_date(x_coords, last_date)
            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            begin_date = last_date - datetime.timedelta(days=self.tw - 1)
            x_coords = x_coords.loc[begin_date:last_date]

        kde = KernelDensity(bandwidth=self.bw)
        kde.fit(x_coords.tolist())
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
