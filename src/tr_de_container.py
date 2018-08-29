import datetime

import pandas as pd

from src.constants import COL
from src.utils import get_df_categories, parse_date_str


class Data:
    """Data object for storing train and dev set

    Attributes:
    ----------

    tr: dict
        training set.
        key: dname (name, or name/category, or name/c1+c2...);
        value: GeoDataFrame

    de: dict
        dev set.
        key: dname (name, or name/category, or name/c1+c2...);
        value: GeoDataFrame

    tr_de_paired: bool.
        if the keys of train and dev set is the same.
    """

    def __str__(self):
        if self.tr_de_paired:
            keys = 'train/dev: %s' % list(self.tr.keys())
        else:
            keys = 'train: %s, dev: %s' % (list(self.tr.keys()), list(self.de.keys()))
        return "Data {name}, dname of {keys}".format(name=self.name, keys=keys)

    def __init__(self, name, atemporal=False, verbose=0):
        self.tr = {}
        self.de = {}
        self.name = name
        self.rolled = False
        self.atemporal = atemporal
        self.verbose = verbose

    def slice_data(self, tr_or_de, sd, ed):
        self.assert_paired('slice_data(tr_or_de=%s' % tr_or_de)
        data = getattr(self, tr_or_de)
        slice = {dname: d[sd:ed] for dname, d in data.items()}
        return slice

    def get_tr_de(self, dname):
        self.assert_paired('get_tr_de(dname=%s' % dname)
        if dname not in self.tr:
            raise ValueError('get_tr_de: Data %s has not been loaded')
        return self.tr[dname], self.de[dname]

    def set_tr_de(self, dname, tr, de):
        self.assert_paired('set_tr_de(dname=%s)' % dname)
        self.tr[dname] = tr
        self.de[dname] = de

    def loaded(self):
        self.assert_paired('loaded()')
        return bool(self.tr)

    @property
    def tr_de_paired(self):
        return self.tr.keys() == self.de.keys()

    def assert_paired(self, msg=''):
        assert self.tr_de_paired, '{msg} / Data {name}: train and dev are not paired'.format(msg=msg, name=self.name)

    def categories(self, dname=None, tr_or_de='tr'):
        assert tr_or_de in ['tr', 'de']
        data = self.tr if tr_or_de == 'tr' else self.de
        if dname:
            return get_df_categories(data[dname])
        return {name: get_df_categories(data[name]) for name in data.keys()}

    @property
    def time_range(self):
        """
        :return: time_range of each dset of each dname, pd.DF
            columns = ['dset', 'dname', COL.dt_from, COL.dt_to]
        """
        if self.atemporal:
            raise AttributeError('Atemporal data has no time range')
        trange = []
        for dname in self.tr.keys():
            tr, de = self.get_tr_de(dname)
            trfrom, trto = min(tr.index), max(tr.index)
            trange.append(['tr', dname, trfrom, trto])
            defrom, deto = min(de.index), max(de.index)
            trange.append(['de', dname, defrom, deto])
        return pd.DataFrame(trange, columns=['dset', 'dname', COL.dt_from, COL.dt_to])

    def roll_de_to_tr(self, start_from, before=None, tw=None):
        """Roll data from dev set to train set during rolling experiment.
        If atemporal=True, raise AttributeError

        The datetime range of the data to be rolled is:
            - If before is not None: [start_from, before); (1 second before the 'before' datetime will be rolled)
            - elif before is None and tw is not None: [start_from, start_from+tw days);
            - else: raise ValueError

        After moving, sort train's index again to make sure the index is sorted.

        :param start_from: datetime.datetime
            the start datetime of the rolling.
            <= the From datetime of all the dev set (<=min(de.From))
            > the To datetime of all the train set (: >max(tr.To))
        :param before: datetime.datetime
            the before datetime of the rolling.
        :param tw: int
            the number of days from start_from of the rolling.
        :return:
        """
        if self.atemporal:
            raise AttributeError('Atemporal data cannot be rolled')

        # # handle start_from and before datetime
        # TODO: 1. allow start_from, before to be string
        if isinstance(start_from, str):
            start_from = parse_date_str(start_from)
        if not isinstance(start_from, datetime.datetime):
            raise TypeError('start_from cannot be parsed as datetime.datetime')
        if isinstance(before, str):
            before = parse_date_str(before)
        # 2. check start_from date
        trange = self.time_range
        min_defrom = trange[trange.dset == 'de'][COL.dt_from].min()
        max_trto = trange[trange.dset == 'tr'][COL.dt_to].max()
        if not start_from <= min_defrom:
            raise ValueError('The start_from (%s) should be <= min(de.From) (%s)' % (start_from, min_defrom))
        if not start_from > max_trto:
            raise ValueError('The start_from (%s) should be > max(tr.To) (%s)' % (start_from, max_trto))
        # 3. get before from the tw parameter
        if before is None:
            if tw is None:
                raise ValueError('either before or tw has to be specified')
            if not isinstance(tw, int):
                raise ValueError('tw must be int, now tw is %s' % type(tw))
            before = start_from + datetime.timedelta(days=tw)
        if not isinstance(before, datetime.datetime):
            raise ValueError('before cannot be parsed as datetime.datetime')
        # 4. subtract 1 second from before, to make sure the time range to roll is [start_from, before).
        before = before - datetime.timedelta(seconds=1)
        # 5. start_from <= before (after it being subtracted)
        if not start_from <= before:
            raise ValueError('start_from (%s) > before (%s)' % (start_from, before))

        # # begin rolling
        self.rolled = True
        # roll data for each dname
        for dname in self.tr.keys():
            tr, de = self.get_tr_de(dname)
            to_roll = de.loc[start_from: before]  # this index slice include before, hence the before is subtracted 1s
            len_tr_before_roll = len(tr)
            len_de_before_roll = len(de)
            len_to_move = len(to_roll)

            tr = tr.append(to_roll).sort_index()
            de = de.loc[before:]
            self.set_tr_de(dname, tr, de)
            len_tr_after_roll = len(tr)
            len_de_after_roll = len(de)
            if self.verbose:
                print('Data {name} '
                      'rolling data from {sf} to {bf}, dname={dname}, # rows: {mv} '
                      'train size: {trbf} -> {traf} '
                      'dev size: {debf} -> {deaf}'.format(
                    name=self.name, dname=dname, sf=start_from, bf=before, mv=len_to_move,
                    trbf=len_tr_before_roll, traf=len_tr_after_roll,
                    debf=len_de_before_roll, deaf=len_de_after_roll
                ))
