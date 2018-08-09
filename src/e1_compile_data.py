from src.constants import PathData, COL
from itertools import chain
from src.data_prep import prep_911, prep_crime


def df_categories(df):
    return df[COL.category].unique()


def subdf_by_categories(df, categories):
    """

    :param df:
    :param categories: str, or list
    :return:
    """
    if isinstance(categories, str):
        return df[df[COL.category] == categories]
    return df[df[COL.category].isin(categories)]


def load_911():
    train = prep_911(PathData.tr_911, by_category=False, coords_series=False, gpdf=True)
    dev = prep_911(PathData.de_911, by_category=False, coords_series=False, gpdf=True)
    return train, dev


def load_crime():
    train = prep_crime(PathData.tr_crime, by_category=False, coords_series=False, gpdf=True)
    dev = prep_crime(PathData.de_crime, by_category=False, coords_series=False, gpdf=True)
    return train, dev


LOAD_FUNCS = {'crime': load_crime, '911': load_911}


class Data:
    """
    Attributes

    tr: dict
        training set.
        key: dname (name, or name/category, or name/c1+c2...);
        value: GeoDataFrame

    de: dict
        dev set.
        key: dname (name, or name/category, or name/c1+c2...);
        value: GeoDataFrame
    """

    def __str__(self):
        if self.tr_de_paired:
            keys = 'train/dev: %s' % list(self.tr.keys())
        else:
            keys = 'train: %s, dev: %s' % (list(self.tr.keys()), list(self.de.keys()))
        return "Data {name}, dname of {keys}".format(name=self.name, keys=keys)

    def __init__(self, name):
        self.tr = {}
        self.de = {}
        self.name = name

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


class CompileData:
    def __str__(self):
        return ('Compile Data Module:\n'
                '\t- {x_setting}\n'
                '\t- {y_setting}\n'
                ''.format(x_setting=self.data_x, y_setting=self.data_y)
                )

    def __init__(self, verbose=0):
        self.data_context = Data('context')
        self._data_loaded = Data('Loaded')
        self.data_y = Data('y')
        self.data_x = Data('X')
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


if __name__ == "__main__":
    import os

    os.chdir('..')
    print('current working directory' + os.getcwd())
    compile_data = CompileData(verbose=1)
    compile_data.set_y('crime')
    compile_data.set_y('crime/burglary')
    compile_data.set_y('crime/burglary+robbery')
    compile_data.set_x(['crime', '911'], by_category=[True, False]
                       # , category_groups={'crime': [['burglary', 'theft_larceny']]}
                       )
