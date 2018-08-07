# coding=utf-8
import pandas as pd
from manual.category_mapping import CatMapping
import sys


def extract_coords(x):
    x = x.strip()
    if x is None:
        return None
    try:
        coords = eval(x.split('\n')[-1])
    except (NameError, SyntaxError):
        return None
    if isinstance(coords, tuple):
        return coords
    return None


def main():
    sys.path.append("../../src")
    from constants import COL, DateTimeRelated as dtc, PathData
    print('loading data')
    path_prefix = 'data/open-baltimore/'
    df911 = pd.read_csv(PathData.raw_911.replace(path_prefix, ''))
    # print(df911.head())

    print('preprocessing location and time')
    df911.location.fillna('NaN', inplace=True)
    print('extract location')
    df911[COL.coords] = df911.location.apply(extract_coords)
    df911[COL.lat] = df911[COL.coords].apply(lambda x: x[0] if x is not None else None)
    df911[COL.lon] = df911[COL.coords].apply(lambda x: x[1] if x is not None else None)
    print('parse datetime')
    df911[COL.datetime] = pd.to_datetime(df911['callDateTime'], format='%m/%d/%Y %I:%M:%S %p')
    df911[COL.date] = df911.DateTime.apply(lambda x: x.date())
    df911[COL.time] = df911.DateTime.apply(lambda x: x.time())

    print('map categories')
    cmap = CatMapping('manual/911_categories.csv')
    df911[cmap.to_col] = cmap.apply_mapping(df911)
    c = df911[~(df911.Longitude.isnull()) & (df911.Category != 'undefined')] \
        [['recordId', COL.datetime, COL.date, COL.time, COL.lat, COL.lon, 'description', 'Category', 'priority']] \
        .sort_values(COL.datetime)

    # print('split dev/test set')
    # df911_clean[df911_clean[COL.datetime] < pd.datetime.strptime('2017-01-01', '%Y-%m-%d')]\
    #     .drop(COL.datetime, axis=1).to_csv('clean/911-dev-set.csv')
    # df911_clean[df911_clean[COL.datetime] >= pd.datetime.strptime('2017-01-01', '%Y-%m-%d')]\
    #     .drop(COL.datetime, axis=1).to_csv('clean/911-test-set.csv')

    print('split train/dev/test set')
    c[(c[COL.datetime] >= dtc.train_sd) & (c[COL.datetime] < dtc.train_ed)].to_csv(
        PathData.train_911.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.dev_sd) & (c[COL.datetime] < dtc.dev_ed)].to_csv(
        PathData.dev_911.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.test_sd) & (c[COL.datetime] < dtc.test_ed)].to_csv(
        PathData.test_911.replace(path_prefix, ''))


if __name__ == '__main__':
    main()
