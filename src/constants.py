class COL:
    """column names
        Attributes:
        ----------
        Datetime related:

        date: Date column for timestamped dataframe
        date_format: the string format of Date column
        time: Time column for timestamped dataframe
        time_format: the string format of Time column

        Spatial related:

        lat: Latitude
        lon: Longitude
        coords: coordinate of points, (lat, lon) or (X, Y) in other CRS
        center: the coordinate of the center of a geometry object
        category: category column
    """
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
