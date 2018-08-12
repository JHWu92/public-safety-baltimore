# coding=utf-8
import pandas as pd
from manual.category_mapping import CatMapping
import sys




def main():
    sys.path.append("../../src")
    from constants import COL, DateTimeRelated as dtc, PathData
    from utils import reg_check_time_format, reg_check_date_format, can_be_parsed_time
    path_prefix = 'data/open-baltimore/'

    def pad_time_str(s):
        if reg_check_time_format(s):
            return s

        special_cases = {'1040`': '1040', '0149 01:49': '0149', '12:27': '1227', '1826h': '1826'}
        if s in special_cases:
            s = special_cases[s]
        if len(s) == 5 or len(s) == 6:
            raise ValueError('len of s=%d' % len(s))
        s += '00'
        s = '0' * (6 - len(s)) + s
        s = s[:2] + ':' + s[2:4] + ':' + s[4:6]
        return s

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

    # parse datetime, correct wrong time format
    c['wrong_time_format'] = c['CrimeTime'].apply(lambda x: not reg_check_time_format(x))
    c[c['wrong_time_format']].to_csv('remove_from_clean/time_format_issue_get_corrected.csv')
    c['CrimeTime'] = c['CrimeTime'].apply(pad_time_str)
    print('corrected %d rows with wrong time format ' % (c.wrong_time_format.sum()))
    # time format still unfixed
    c['can_be_parsed'] = c.CrimeTime.apply(can_be_parsed_time)
    c[~c['can_be_parsed']].to_csv('remove_from_clean/time_format_issue.csv')
    c = c[c['can_be_parsed']].copy()
    print('dropped rows with wrong time format, now # rows = %d ' % (len(c)))
    # get DataTime, Date and Time
    c[COL.datetime] = c['CrimeDate'] + ' ' +c['CrimeTime']
    c[COL.datetime] = pd.to_datetime(c[COL.datetime], format='%m/%d/%Y %H:%M:%S')
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
        ['Location 1', 'Total Incidents', 'Inside/Outside', 'CrimeDate', 'CrimeTime',
         'wrong_time_format', 'can_be_parsed'],
        axis=1, inplace=True)

    print('split train/dev/test set')
    c[(c[COL.datetime] >= dtc.train_sd) & (c[COL.datetime] < dtc.train_ed)].to_csv(PathData.tr_crime.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.dev_sd) & (c[COL.datetime] < dtc.dev_ed)].to_csv(PathData.de_crime.replace(path_prefix, ''))
    c[(c[COL.datetime] >= dtc.test_sd) & (c[COL.datetime] < dtc.test_ed)].to_csv(PathData.te_crime.replace(path_prefix, ''))

    return


if __name__ == '__main__':
    main()