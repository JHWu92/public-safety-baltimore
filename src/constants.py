class COL:
    """column names

        Attributes:
        ----------

        other:

        - ori_index: name for the original index of the raw data file

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
        - category: category column
    """
    # other
    ori_index = 'ori_index'
    # datetime related
    date = 'Date'
    date_format = '%Y-%m-%d'
    time = 'Time'
    time_format = '%H:%M:%S'
    # spatial related
    lat = 'Latitude'
    lon = 'Longitude'
    coords = 'Coords'
    center = 'Cen_coords'
    category = 'Category'


class PATH_DEV:
    """
    path names of clean dev set data

    Attributes
    ----------
    p911: 911 data
    """
    p911 = 'data/open-baltimore/clean/911-dev-set.csv'
