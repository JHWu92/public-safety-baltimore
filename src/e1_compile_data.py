import datetime
from itertools import chain

import pandas as pd

from src.constants import COL
from src.utils import parse_date_str
from src.utils import df_categories, subdf_by_categories
from src.e0_load_data_spu import LOAD_FUNCS


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
            return df_categories(data[dname])
        return {name: df_categories(data[name]) for name in data.keys()}

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


class CompileData:
    """module for compiling data for next step

    Attributes:
    ----------

    data_x: Data object.
        train and dev set for X

    data_y: Data object.
        train and dev set for Y

    data_context: Data object?
        atemporal context data (e.g., POI, landuse)

    verbose: int.
        level of verbosity.

    y_dev: dict (key=dname, value=GDF)
        dev set for y

    y_train: dict (key=dname, value=GDF)
        train set for y

    x_dev: dict (key=dname, value=GDF)
        dev set for x

    x_train: dict (key=dname, value=GDF)
        train set for x
    """

    def __str__(self):
        return ('Compile Data Module:\n'
                '\t- {x_setting}\n'
                '\t- {y_setting}\n'
                ''.format(x_setting=self.data_x, y_setting=self.data_y)
                )

    def __init__(self, verbose=0):
        self.data_context = Data('context', verbose=verbose)
        self._data_loaded = Data('Loaded', verbose=verbose)
        self.data_y = Data('y', verbose=verbose)
        self.data_x = Data('X', verbose=verbose)
        self.verbose = verbose

    def load_data(self, dname):
        """select data loading function by name"""

        if dname not in LOAD_FUNCS:
            raise ValueError('Name=%s cannot be loaded, it hasnt been implemented. Supported data: %s' % (
                dname, ', '.join(LOAD_FUNCS.keys()))
                             )

        if self.verbose:
            print('loading data ' + dname)

        func = LOAD_FUNCS[dname]
        train, dev = func()
        self._data_loaded.set_tr_de(dname, train, dev)

    def is_loaded(self, dname):
        """assert data sets are loaded in both train and dev set; if the data is not loaded, load the data

        Parameters:
        ----------
        :param dname: str
            the name of data to be loaded
        """

        if dname not in self._data_loaded.tr:
            self.load_data(dname)

    def set_y(self, dname):
        """set data for y
        :param dname: str
            the name of the data (e.g., crime)
            or name/category (e.g., crime/shooting)
            or name/categories (e.g., crime/shooting+homicide)
            for y
        """
        categories = None
        dname_cat = dname

        if '/' in dname:
            dname, categories = dname_cat.split('/')
            categories = categories.split('+')

        self.is_loaded(dname)
        tr = self._data_loaded.tr[dname]
        de = self._data_loaded.de[dname]

        if categories:
            tr_cat = df_categories(tr)
            de_cat = df_categories(de)
            for c in categories:
                assert c in tr_cat, 'category: %s is not in Train set (%s)' % (c, tr_cat)
                assert c in de_cat, 'category: %s is not in Train set (%s)' % (c, de_cat)
            tr = tr[tr[COL.category].isin(categories)]
            de = de[de[COL.category].isin(categories)]

        self.data_y.set_tr_de(dname_cat, tr, de)
        if self.verbose >= 1:
            print('set data for y, dname/categories=%s' % dname_cat)

    def set_x(self, dnames, by_category=True, category_groups=None):
        """Set data for X.

        :param dnames: list.
            List of dnames to be used to generate feature X.
        :param by_category: bool or list of Boolean, default True.
            whether or not to divide the data by categories.
            Specify list for multiple datasets.
            If this is a list of bools, must match the length of the dnames.
        :param category_groups: dict
            key: dname;
            value: list of groups of categories.
            define categories that should be treated as groups for each dname.

        Examples:
        ----------

        >>> compile_data.set_x(['crime', '911'], by_category=[True, False],
        ...               category_groups={'crime': [['burglary', 'theft_larceny']]})

        """
        if not isinstance(by_category, (tuple, list)):
            by_category = [by_category] * len(dnames)
        assert len(by_category) == len(dnames), 'Len of by_category != dnames'

        for dname, byc in zip(dnames, by_category):
            self.is_loaded(dname)
            has_group = category_groups is not None and dname in category_groups
            groups = category_groups[dname] if has_group else []
            cat_in_g = set(chain(*groups))

            # categories in groups are treated as homogeneous
            if has_group:
                if self.verbose:
                    print('set_x: adding groups for data ' + dname)
                for g in groups:
                    dname_cat = '%s/%s' % (dname, '+'.join(g))
                    self.data_x.set_tr_de(dname_cat,
                                          subdf_by_categories(self._data_loaded.tr[dname], g),
                                          subdf_by_categories(self._data_loaded.de[dname], g))

            # each category not in groups is treated as a set of independent point
            if byc:
                categories = set(df_categories(self._data_loaded.tr[dname])) | set(
                    df_categories(self._data_loaded.de[dname]))

                if self.verbose:
                    print('set_x: adding individual category of data ' + dname)
                    print('all categories in data: {} are: {}.'.format(dname, categories))
                    if has_group:
                        print('individual categories are: {}'.format(categories - cat_in_g))

                for c in categories - cat_in_g:
                    dname_cat = '%s/%s' % (dname, c)
                    self.data_x.set_tr_de(dname_cat,
                                          subdf_by_categories(self._data_loaded.tr[dname], c),
                                          subdf_by_categories(self._data_loaded.de[dname], c))

            # treated as one set of homogeneous points
            if not has_group and not byc:
                if self.verbose:
                    print('set_x: adding whole set of data ' + dname)
                self.data_x.set_tr_de(dname, self._data_loaded.tr[dname], self._data_loaded.de[dname])

    @property
    def y_train(self):
        return self.data_y.tr

    @property
    def y_dev(self):
        return self.data_y.de

    @property
    def x_train(self):
        return self.data_x.tr

    @property
    def x_dev(self):
        return self.data_x.de


def main(cdata):
    import os

    os.chdir('..')
    print('current working directory' + os.getcwd())

    # compile_data.set_y('crime')
    cdata.set_y('crime/burglary')
    cdata.set_y('crime/burglary+robbery')
    # compile_data.set_x(['crime', '911'], by_category=[True, False],
    #                    category_groups={'crime': [['burglary', 'theft_larceny']]})
    # compile_data.set_x(['crime', '911'], by_category=[True, False])
    # compile_data.set_x(['crime', '911'], category_groups={'crime': [['burglary', 'theft_larceny']]})
    # compile_data.set_x(['crime', '911'], by_category=False,
    #                    category_groups={'crime': [['burglary', 'theft_larceny']]})

    sd_right = '2016-07-01'
    be = '2016-07-10'
    sd_too_early = '2016-06-30'
    sd_too_late = '2016-07-01 22:00:00'
    sd_not_earlier_than_be = '2016-07-10'
    print(cdata.data_y.time_range)
    try:
        cdata.data_y.roll_de_to_tr(sd_too_early, be)  # failed
        raise ValueError('This check fail')
    except ValueError:
        print('Raise error sd<max(tr.To) works')

    try:
        cdata.data_y.roll_de_to_tr(sd_too_late, be)  # failed
        raise ValueError('This check fail')
    except ValueError:
        print('Raise error sd>=min(de.From) works')

    try:
        cdata.data_y.roll_de_to_tr(sd_not_earlier_than_be, be)  # failed
        raise ValueError('This check fail')
    except ValueError:
        print('Raise error sd<=before works')
    cdata.data_y.roll_de_to_tr(sd_right, be)


if __name__ == "__main__":
    compile_data = CompileData(verbose=1)
    main(compile_data)
