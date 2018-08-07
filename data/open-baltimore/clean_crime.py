# coding=utf-8
import pandas as pd
from manual.category_mapping import CatMapping
import sys


def main():
    sys.path.append("../../src")
    from constants import COL, DateTimeRelated as dtc, PathData
    from utils import reg_check_time_format, reg_check_date_format
    path_prefix = 'data/open-baltimore/'

    c = pd.read_csv(PathData.raw_crime.replace(path_prefix, ''))
    print('begin cleaning, now # rows = %d'%len(c))

    # remove rows with incomplete Lat/Lon
    cond = ~((c.Longitude.isnull()) | (c.Latitude.isnull()))
    c[~cond].to_csv('remove_from_clean/crime_no_latlon.csv')
    c = c[cond].copy()
    print('dropped rows with incomplete, now # rows = %d ' % (len(c)))

    # There are some full-line duplicates
    c[c.duplicated()].to_csv('remove_from_clean/crime_duplicates.csv')
    c = c[~c.duplicated()].copy()
    print('dropped duplicates rows, now # rows = %d ' % (len(c)))

    # parse datetime
    c['match_time_format'] = c['CrimeTime'].apply(reg_check_time_format)
    c[~c['match_time_format']].to_csv('remove_from_clean/time_format_issue.csv')
    c = c[c['match_time_format']].copy()
    print('dropped rows with wrong time format, now # rows = %d ' % (len(c)))
    c[COL.datetime] = c['CrimeDate'] + ' ' +c['CrimeTime']
    c[COL.datetime] = pd.to_datetime(c[COL.datetime], format='%m/%d/%Y %H:%M:%S')
    c[COL.date] = pd.to_datetime(c['CrimeDate'], format='%m/%d/%Y')
    c[COL.date] = c.DateTime.apply(lambda x: x.date())
    c[COL.time] = c.DateTime.apply(lambda x: x.time())
    c.sort_values(COL.datetime, inplace=True)

    print('map categories')
    cmap = CatMapping('manual/crime_categories.csv')
    c[cmap.to_col] = cmap.apply_mapping(c)

    # clean noise
    c['In/Outside'] = c['Inside/Outside'].apply(
        lambda x: 'O' if x == 'Outside' else 'I' if x == 'Inside' else x)

    # drop unused columns
    c.drop(
        ['Location 1', 'Total Incidents', 'Inside/Outside', 'CrimeDate', 'CrimeTime', 'match_time_format'],
        axis=1, inplace=True)

    print('split train/dev/test set')
    c[(c[COL.datetime] >= dtc.train_sd) & (c[COL.datetime] < dtc.train_ed)].to_csv(PathData.train_crime.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.dev_sd) & (c[COL.datetime] < dtc.dev_ed)].to_csv(PathData.dev_crime.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.test_sd) & (c[COL.datetime] < dtc.test_ed)].to_csv(PathData.test_crime.replace(path_prefix, ''))

    return


if __name__ == '__main__':
    main()