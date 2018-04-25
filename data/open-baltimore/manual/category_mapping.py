# coding=utf-8
import pandas as pd


class CatMapping:
    def __init__(self, path, verbose=0):
        if verbose > 0:
            print('=======================\n'
                  'initializing CatMapping\n'
                  '=======================\n')
        self.path = path
        self.verbose = verbose

        if verbose > 0:
            print('loading data from: %s' % path)
        mapping = pd.read_csv(path)
        if mapping.shape[1] != 2:
            raise ValueError('mapping file should have and only have 2 columns')

        mapping.fillna(method='ffill', inplace=True)
        self.to_col = mapping.columns[0]
        self.from_col = mapping.columns[1]
        self.mapping = mapping
        self.mapping_dict = {x[1]: x[0] for _, x in mapping.iterrows()}

        if verbose > 0:
            print('mapping raw types in column %s to categories in column %s' % (self.from_col, self.to_col))

    def get_categories(self):
        return self.mapping.iloc[:, 0].unique()

    def get_mapping(self):
        return self.mapping

    def get_mapping_dict(self):
        return self.mapping_dict

    def apply_mapping(self, obj):
        if isinstance(obj, pd.Series):
            if self.verbose > 0:
                print('obj is pd.Series')
            return obj.apply(self.apply_mapping)

        if isinstance(obj, pd.DataFrame):
            if self.verbose > 0:
                print('obj is pd.DataFrame')
            return obj[self.from_col].apply(self.apply_mapping)

        if self.verbose > 1:
            print('obj is %s' % type(obj))
        return self.mapping_dict.get(obj, 'undefined')


def main():
    path = 'crime_categories.csv'
    cmap = CatMapping(path, verbose=1)
    # print(cmap.get_categories())
    # print(cmap.get_mapping())
    # print(cmap.get_mapping_dict())
    df = cmap.get_mapping()
    print(df[cmap.from_col].apply(cmap.apply_mapping))
    print(cmap.apply_mapping(df[cmap.from_col]))
    print(cmap.apply_mapping(df))
    return


if __name__ == '__main__':
    main()
