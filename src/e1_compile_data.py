from src.constants import PathData, COL
from src.data_prep import prep_911, prep_crime


def df_categories(df):
    return df[COL.category].unique()


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
                '\t- {y_setting}\n'
                ''.format(y_setting=self.data_y)
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
            raise ValueError(
                'Name=%s cannot be loaded, it hasnt been implemented. Supported data: %s' % (
                    dname, ', '.join(LOAD_FUNCS.keys())
                )
            )
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

    def set_x(self, dnames, by_catogory=True):
        pass

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
    compile_data = CompileData()
    compile_data.set_y('crime')
    compile_data.set_y('crime/burglary')
    compile_data.set_y('crime/burglary+robbery')
