# coding=utf-8
import pandas as pd
from manual.category_mapping import CatMapping
import sys


def main():
    sys.path.append("../../src")
    from constants import COL

    crimes = pd.read_csv('raw/BPD_Part_1_Victim_Based_Crime_Data.csv')
    crimes = crimes[~((crimes.Longitude.isnull()) | (crimes.Latitude.isnull()))].copy()
    # parse datetime
    crimes[COL.date] = pd.to_datetime(crimes['CrimeDate'], format='%m/%d/%Y')
    crimes.sort_values(COL.date, inplace=True)

    # There are some full-line duplicates
    crimes = crimes[~crimes.duplicated()].copy()

    print('map categories')
    cmap = CatMapping('manual/crime_categories.csv')
    crimes[cmap.to_col] = cmap.apply_mapping(crimes)

    # clean noise
    crimes['In/Outside'] = crimes['Inside/Outside'].apply(
        lambda x: 'O' if x == 'Outside' else 'I' if x == 'Inside' else x)

    # drop unused columns
    crimes.drop(['Location 1', 'Total Incidents', 'Inside/Outside', 'CrimeDate'], axis=1, inplace=True)
    crimes.rename(columns={'CrimeTime': COL.time}, inplace=True)

    print('split dev/test set')
    crimes[crimes.Date < pd.datetime.strptime('2017-01-01', '%Y-%m-%d')].to_csv('clean/crimes-dev-set.csv')
    crimes[crimes.Date >= pd.datetime.strptime('2017-01-01', '%Y-%m-%d')].to_csv('clean/crimes-test-set.csv')

    return


if __name__ == '__main__':
    main()