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
    from constants import COL
    print('loading data')
    df911 = pd.read_csv('raw/911_Police_Calls_for_Service.csv', sep=';')
    # print(df911.head())

    print('preprocessing location and time')
    df911.location.fillna('NaN', inplace=True)
    # extract location
    df911[COL.coords] = df911.location.apply(extract_coords)
    df911[COL.lat] = df911[COL.coords].apply(lambda x: x[0] if x is not None else None)
    df911[COL.lon] = df911[COL.coords].apply(lambda x: x[1] if x is not None else None)
    # parse datetime
    df911[COL.datetime] = pd.to_datetime(df911['callDateTime'], format='%m/%d/%Y %I:%M:%S %p')
    df911[COL.date] = df911.DateTime.apply(lambda x: x.date())
    df911[COL.time] = df911.DateTime.apply(lambda x: x.time())

    print('map categories')
    cmap = CatMapping('manual/911_categories.csv')
    df911[cmap.to_col] = cmap.apply_mapping(df911)
    df911_clean = df911[~(df911.Longitude.isnull()) & (df911.Category != 'undefined')] \
        [['recordId', COL.datetime, COL.date, COL.time, COL.lat, COL.lon, 'description', 'Category', 'priority']] \
        .sort_values(COL.datetime)

    print('split dev/test set')
    df911_clean[df911_clean[COL.datetime] < pd.datetime.strptime('2017-01-01', '%Y-%m-%d')]\
        .drop(COL.datetime, axis=1).to_csv('clean/911-dev-set.csv')
    df911_clean[df911_clean[COL.datetime] >= pd.datetime.strptime('2017-01-01', '%Y-%m-%d')]\
        .drop(COL.datetime, axis=1).to_csv('clean/911-test-set.csv')
    return


if __name__ == '__main__':
    main()
