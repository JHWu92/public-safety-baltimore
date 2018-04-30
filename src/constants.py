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
    # spatial related
    lat = 'Latitude'
    lon = 'Longitude'
    coords = 'Coords'
    center = 'Cen_coords'
    area = 'Area'


class PathRaw:
    crime = 'data/open-baltimore/raw/BPD_Part_1_Victim_Based_Crime_Data.csv'


class PathDev:
    """
    path names of clean dev set data

    Attributes
    ----------
    p911: 911 data
    """
    p911 = 'data/open-baltimore/clean/911-dev-set.csv'
    crime = 'data/open-baltimore/clean/crimes-dev-set.csv'


class PathTest:
    """
    path names of clean dev set data

    Attributes
    ----------
    p911: 911 data
    """
    p911 = 'data/open-baltimore/clean/911-test-set.csv'
    crime = 'data/open-baltimore/clean/crimes-test-set.csv'


class PathShape:
    """
    path names of shapefiles/geojson

    Attributes
    ----------
    cityline: the cityline of Baltimore
    """
    cityline = 'data/open-baltimore/raw/Baltcity_Line/baltcity_line.shp'
