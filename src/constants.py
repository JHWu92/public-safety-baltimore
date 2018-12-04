class COL:
    """column names

        Attributes:
        ----------

        other:

        - ori_index: name for the original index of the raw data file
        - category: category column

        Datetime related:

        - date: Date column for timestamped dataframe
        - date_format: the string format of Date column
        - time: Time column for timestamped dataframe
        - time_format: the string format of Time column

        Spatial related:

        - lat: Latitude
        - lon: Longitude
        - coords: coordinate of points, (lon, lat) or (X, Y) in other CRS
        - center: the coordinate of the center of a geometry object
        - area: the area of the unit, in m^2
    """
    # other
    ori_index = 'ori_index'
    category = 'Category'
    risk = 'Risk'
    num_events = '#events'
    # datetime related
    date = 'Date'
    date_format = '%Y-%m-%d'
    time = 'Time'
    time_format = '%H:%M:%S'
    datetime = 'DateTime'
    datetime_format = date_format + ' ' + time_format
    dt_from = 'From'
    dt_to = 'To'
    # spatial related
    lat = 'Latitude'
    lon = 'Longitude'
    coords = 'Coords'
    center = 'Cen_coords'
    area = 'Area'
    spu = 'SPU'


class PathData:
    """
    path names of data

    Attributes (prefix: [raw/train/dev/test]_)
    ----------
    crime: part 1 victim based crime
    911: 911 data
    """
    # crime
    raw_crime = 'data/open-baltimore/raw/BPD_Part_1_Victim_Based_Crime_Data.csv'
    tr_crime = 'data/open-baltimore/clean/train-crime-victim-based-part1.csv'
    de_crime = 'data/open-baltimore/clean/dev-crime-victim-based-part1.csv'
    te_crime = 'data/open-baltimore/clean/test-crimes-victim-based-part1.csv'
    # 911
    raw_911 = 'data/open-baltimore/raw/911_Police_Calls_for_Service.csv'
    tr_911 = 'data/open-baltimore/clean/train-911.csv'
    de_911 = 'data/open-baltimore/clean/dev-911.csv'
    te_911 = 'data/open-baltimore/clean/test-911.csv'

    as_dict = {
        'train': {
            'crime': tr_crime,
            '911': tr_911,
        },
        'dev': {
            'crime': de_crime,
            '911': de_911,
        },
        'test': {
            'crime': te_crime,
            '911': te_911,
        }
    }


class PathShape:
    """
    path names of shapefiles/geojson

    Attributes
    ----------
    cityline: the cityline of Baltimore
    """
    cityline = 'data/open-baltimore/raw/Baltcity_Line/baltcity_line.shp'
    spu_dir = 'data/spu/'


class DateTimeRelated:
    """ Datetime related constants

        Attributes:
        ----------
        time_format: string
            the string format of Time column
        date_format: string
            the string format of Date column
        train_sd: datetime.datetime
            train set start date
        train_ed: datetime.datetime
            train set end date
        dev_sd: datetime.datetime
            dev set start date
        dev_ed: datetime.datetime
            dev set end date
        test_sd: datetime.datetime
            test set start date
        test_ed: datetime.datetime
            test set end date
    """
    from datetime import datetime as dt
    time_format = '%H:%M:%S'
    date_format = '%Y-%m-%d'
    datetime_format = '%s %s' % (date_format, time_format)

    train_sd = dt.strptime('2012-07-01', date_format)
    train_ed = dt.strptime('2016-07-01', date_format)
    dev_sd = train_ed
    dev_ed = dt.strptime('2017-07-01', date_format)
    test_sd = dev_ed
    test_ed = dt.strptime('2018-07-01', date_format)


class BniaIndicators:
    population = ('Total Population',)

    age = (
        'Percent of Population  Under 5 years old', 'Percent of Population 5-17 years old',
        'Percent of Population 18-24 years old', 'Percent of Population 25-64 years old',
        'Percent of Population 65 years and over'
    )

    gender = ('Total Male Population', 'Total Female Population',)

    racial = (
        'Percent of Residents - Black/African-American', 'Percent of Residents - White/Caucasian',
        'Percent of Residents - Asian', 'Percent of Residents - Two or More Races',
        'Percent of Residents - All Other Races (Hawaiian/ Pacific Islander, Alaskan/ Native American Other Race)',
        'Percent of Residents - Hispanic', 'Racial Diversity Index',
    )
    household_size = ('Total Number of Households', 'Percent of Female-Headed Households with Children under 18',
                      'Percent of Households with Children Under 18', 'Average Household Size')
    household_income = ('Median Household Income', 'Percent of Households Earning Less than $25,000',
                        'Percent of Households Earning $25,000 to $40,000',
                        'Percent of Households Earning $40,000 to $60,000',
                        'Percent of Households Earning $60,000 to $75,000',
                        'Percent of Households Earning More than $75,000',
                        'Percent of Family Households Living Below the Poverty Line',
                        'Percent of Children Living Below the Poverty Line',)
    housing = ('Median Price of Homes Sold', 'Median Number of Days on the Market', 'Number of Homes Sold',
               'Percentage of Housing Units that are Owner-Occupied',
               'Percentage of Properties Under Mortgage Foreclosure',
               'Percentage of Residential Properties that are Vacant and Abandoned',
               'Percentage of Residential Properties with Housing Violations (Excluding Vacants)',
               'Percentage of Properties with Rehabilitation Permits Exceeding $5,000',
               'Total Number of Residential Properties', 'Percentage of Residential Sales for Cash',
               'Percentage of Residential Sales in Foreclosure (REO)', 'Percentage of Residential Tax Lien Sales',
               'Number of Demolition Permits per 1,000 Residential Properties',
               'Number of New Construction Permits per 1,000 Residential Properties',
               'Percentage of Vacant Properties Owned by Baltimore City', 'Affordability Index - Mortgage',
               'Affordability Index - Rent', 'Number of Historic Tax Credits per 1,000 Residential Units',
               'Number of Homestead Tax Credits per 1,000 Residential Units',
               'Number of Homeowner\'s Tax Credits per 1,000 Residential Units',
               'Percent Residential Properties that do Not Receive Mail',)

    education = ('Number of Students Ever Attended 1st - 5th Grade', 'Number of Students Ever Attended 6th - 8th Grade',
                 'Number of Students Ever Attended 9th - 12th Grade',
                 'Percent of Students that are African American',
                 'Percent of Students that are White (non-Hispanic)', 'Percent of Students that are Hispanic',
                 'Percent of 1st-5th Grade Students that are Chronically Absent (Missing at least 20 days)',
                 'Percent of 6th-8th Grade Students that are Chronically Absent (Missing at least 20 days)',
                 'Percent of 9th-12th Grade Students that are Chronically Absent (Missing at least 20 days)',
                 'Percentage of Students Suspended or Expelled During School Year',
                 'Percentage of Students Receiving Free or Reduced Meals',
                 'Percentage of Students Enrolled in Special Education Programs', 'Kindergarten School Readiness',
                 'Percentage of 3rd Grade Students Passing MSA Math',
                 'Percentage of 3rd Grade Students Passing MSA Reading',
                 'Percentage of 5th Grade Students Passing MSA Math',
                 'Percentage of 5th Grade Students Passing MSA Reading',
                 'Percentage of 8th Grade Students Passing MSA Math',
                 'Percentage of 8th Grade Students Passing MSA Reading',
                 'Percentage of Students Passing H.S.A. English ', 'Percentage of Students Passing H.S.A. Biology',
                 'Percentage of Students Passing H.S.A. Government', 'Percentage of Students Passing H.S.A. Algebra',

                 'High School Dropout/Withdrawal Rate', 'High School Completion Rate',
                 'Percent of Students Switching Schools within School Year',
                 'Percentage of Population aged 16-19 in School and/or Employed')


if __name__ == '__main__':
    print(DateTimeRelated.train_sd, type(DateTimeRelated.train_sd))
