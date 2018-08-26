from itertools import chain

from src.constants import COL
from src.e0_load_tr_de_spu import LOAD_FUNCS, get_spu
from src.utils import df_categories, subdf_by_categories
from src.tr_de_container import Data


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
                '\t- Spatial Unit: {spu_name}\n'
                ''.format(x_setting=self.data_x, y_setting=self.data_y,
                          spu_name=self.spu_name)
                )

    def __init__(self, spu_name=None, verbose=0):
        self.verbose = verbose
        self.spu_name = spu_name
        self.spu = get_spu(spu_name)
        # init Data container
        self.data_context = Data('context', verbose=verbose)
        self._data_loaded = Data('Loaded', verbose=verbose)
        self.data_y = Data('y', verbose=verbose)
        self.data_x = Data('X', verbose=verbose)

    def load_data(self, dname):
        """select data loading function by name"""

        if dname not in LOAD_FUNCS:
            raise ValueError('Name=%s cannot be loaded, it hasnt been implemented. Supported data: %s' % (
                dname, ', '.join(LOAD_FUNCS.keys()))
                             )

        if self.verbose:
            print('loading data ' + dname)

        func = LOAD_FUNCS[dname]
        train, dev = func(self.spu_name, self.verbose)
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

    if os.getcwd().endswith('src'):
        os.chdir('..')
    print('current working directory' + os.getcwd())

    # different y loading
    # compile_data.set_y('crime')
    cdata.set_y('crime/burglary')
    cdata.set_y('crime/burglary+robbery')

    # different x loading
    # compile_data.set_x(['crime', '911'], by_category=[True, False],
    #                    category_groups={'crime': [['burglary', 'theft_larceny']]})
    # compile_data.set_x(['crime', '911'], by_category=[True, False])
    # compile_data.set_x(['crime', '911'], category_groups={'crime': [['burglary', 'theft_larceny']]})
    # compile_data.set_x(['crime', '911'], by_category=False,
    #                    category_groups={'crime': [['burglary', 'theft_larceny']]})

    # test roll_de_to_tr
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
    compile_data = CompileData(verbose=1, spu_name='grid_1000')
    main(compile_data)
