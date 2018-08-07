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
    datetime_format = date_format + ' ' +time_format
    # spatial related
    lat = 'Latitude'
    lon = 'Longitude'
    coords = 'Coords'
    center = 'Cen_coords'
    area = 'Area'


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


class PathShape:
    """
    path names of shapefiles/geojson

    Attributes
    ----------
    cityline: the cityline of Baltimore
    """
    cityline = 'data/open-baltimore/raw/Baltcity_Line/baltcity_line.shp'


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
    datetime_format = '%s %s' %(date_format, time_format)

    train_sd = dt.strptime('2012-07-01', date_format)
    train_ed = dt.strptime('2016-07-01', date_format)
    dev_sd = train_ed
    dev_ed = dt.strptime('2017-07-01', date_format)
    test_sd = dev_ed
    test_ed = dt.strptime('2018-07-01', date_format)


if __name__ == '__main__':
    print(DateTimeRelated.train_sd, type(DateTimeRelated.train_sd))