import geopandas as gp
from shapely.geometry import Point

def y_cnt_event(spatial_units, coords):
    """

    :param spatial_units: gp.GeoDataFrame
    :param coords: pd.Series of coords, the coords should be in the same crs of spatial units
    :return:
    """
    events = gp.GeoDataFrame(coords.apply(lambda x: Point(*x))).rename(columns={'coords': 'geometry'}).reset_index()
    while events.crs is None and spatial_units.crs is not None:
        events.crs = spatial_units.crs
    joined = gp.sjoin(events, spatial_units)
    y_cnt = spatial_units.join(joined.groupby('index_right').size().rename('counts'), how='left').fillna(0)
    return y_cnt['counts']