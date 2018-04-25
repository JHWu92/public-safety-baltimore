# coding=utf-8
import datetime

import numpy as np
import pandas as pd

from .bsln_kde import KDE


def rtm_score(l):
    """

    :param l: array-like numeric data
    :return: array scores digitized by [mean, mean+std, mean+std*2]
    """
    mean = np.mean(l)
    std = np.std(l, ddof=1)
    return np.digitize(l, [mean, mean + std, mean + std * 2])


class RTM:
    """Risk Terrain Modeling

    Original paper:
    ---------------
    \cite{Caplan2011-pd}: Caplan, J.M. et al. 2011.
    Risk Terrain Modeling: Brokering Criminological Theory and GIS Methods for Crime Forecasting.
    Justice quarterly: JQ / Academy of Criminal Justice Sciences. 28, 2 (Apr. 2011), 360–381.

    About hyper-parameters in paper:
    -----------------
    The specific parameters for density calculations used in this study were
    a bandwith of 1,000 feet and
    a cellsize of 100 feet
    Data were divided into three six-month time period

    Parameters
    ----------
    grid_size: float in meter, default 30.48 m(100 feet)
    bw: bandwidth, float in meter, dafault 304.8 m (1000 feet)
    tw: time window, int in day, default 60 days

    Attributes
    ----------
    estimators: {name_of_coords: kde}
    """

    def __str__(self):
        return 'RTM with bandwidth={} meters, grid size={} meters, time window={} days'.format(
            self.bw, self.grid_size, self.tw)

    def __repr__(self):
        return '<RTM bw={}, grid_size={}, tw={}>'.format(
            self.bw, self.grid_size, self.tw)

    def __init__(self, grid_size=30.48, bw=304.8, tw=60, verbose=0):
        self.grid_size = grid_size
        self.bw = bw
        self.tw = tw
        self.verbose = verbose
        # attributes after fit
        self.estimators = {}

    def get_last_date(self, dict_coords, last_date):
        """
        if last_date is not None, return last date;
        else, find the latest date in all coords

        Parameters
        ----------
        :param dict_coords: {name_of_coords: pd.Series([coord], index=Date)}
        :param last_date: string (format='%Y-%m-%d') or DateTime, default None
            the last date of the time window. If None, the last date of coords is used
        :return: Datetime of last date
        """
        # TODO: some dataset may not be Datetime indexed
        if last_date is None:
            last_date = datetime.datetime.strptime('1970-01-01', '%Y-%m-%d')
            for coords in dict_coords.values():
                cur_ld = coords.index.max()
                if cur_ld > last_date:
                    last_date = cur_ld
            if self.verbose > 0:
                print('last_date is None, using largest coords.index.max()=%s as last_date' % (
                    last_date.strftime('%Y-%m-%d')))

        elif isinstance(last_date, str):
            last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d')

        return last_date

    def fit(self, named_x_coords, y_coords=None, last_date=None):
        """

        :param named_x_coords: {name_of_coords: pd.Series([coord], index=Date)}
        :param y_coords: not used in RTM, for compatibility purpose
        :param last_date: string (format='%Y-%m-%d') or DateTime, default None
            the last date of the time window. If None, the last date of coords is used
        :return:
        """
        last_date = self.get_last_date(named_x_coords, last_date=last_date)

        # for each type of coords, fit a KDE
        for name, coords in named_x_coords.items():
            kde = KDE(bw=self.bw, tw=self.tw, verbose=self.verbose)
            kde.fit(coords, last_date=last_date)
            self.estimators[name] = kde

    def pred(self, spatial_units, now_date=None):
        """

        :param spatial_units: assuming coords of the centers. pd.Series([coord], index=Date)
        :param now_date: Not used in KDE
        :return:
        """
        # TODO spatial_units can be shapes other than grids

        # not dict_coords, just coords of grids
        # ==============================
        # check if names are matched
        # not_in_estimators = dict_coords.keys() - self.estimators.keys()
        # not_in_data = self.estimators.keys() - dict_coords.keys()
        # if len(not_in_data) != 0 or len(not_in_estimators) != 0:
        #     msg = "keys of dict_coords and estimators do not match."
        #     if self.verbose > 0:
        #         msg += 'keys not in estimators: {}, not in data: {}'.format(','.join(not_in_estimators),
        #                                                                     ','.join(not_in_data))
        #     warnings.warn(msg)

        # in_both = dict_coords.keys() & self.estimators.keys()
        # if self.verbose >0:
        #     print('computing PDF for: %s' % ','.join(in_both))
        # ================================

        # compute PDF for names in both data and estimators
        if self.verbose > 0:
            print('using KDE of [%s] to compute risk scores' % ','.join(self.estimators.keys()))
        scores = {}
        for name, kde in self.estimators.items():
            pdf = kde.pred(spatial_units)
            scores[name] = pd.Series(rtm_score(pdf), index=pdf.index)

        scores = pd.DataFrame(scores)
        return scores.sum(axis=1)

    def tune(self, bw=None):
        """
        the paper doesn't have bw tuning, this method is for API consistency
        """
        if bw is not None:
            self.bw = bw


def main():
    return


if __name__ == '__main__':
    main()
