import geopandas as gp
import pandas as pd
from shapely.geometry import Point

from src import constants as C


def y_cnt_event(spatial_units, coords):
    """

    :param spatial_units: gp.GeoDataFrame
    :param coords: pd.Series of coords, the coords should be in the same crs of spatial units
    :return:
    """
    events = gp.GeoDataFrame(coords.apply(lambda x: Point(*x))).rename(columns={C.COL.coords: 'geometry'}).reset_index()
    while events.crs is None and spatial_units.crs is not None:
        events.crs = spatial_units.crs
    joined = gp.sjoin(events, spatial_units)
    y_cnt = spatial_units.join(joined.groupby('index_right').size().rename(C.COL.num_events), how='left').fillna(0)
    return y_cnt[C.COL.num_events]


def prepare_temporal_data_for_model(data, setting, index_order=None):
    if setting == 'event_cnt':
        prepared = event_cnt(data)
        if index_order is not None:
            prepared = prepared.reindex(index_order).fillna(0)
        return prepared
    elif setting == 'time_indexed_points':
        return time_indexed_points(data)
    else:
        raise NotImplementedError('No such setting:' + setting)


def event_cnt(data):
    """

    :param data: dict
        key: dname, value: dataframe with spu_assignment
    :return: pd.DataFrame
        index.name = constants.COL.spu
        columns = dnames
    """
    cnts = []
    # get a column per dname
    for dname, df in data.items():
        cnt = df.groupby(C.COL.spu).size()
        cnt.name = dname
        cnts.append(cnt)
    cnts = pd.concat(cnts, axis=1)
    if isinstance(cnts, pd.Series):
        cnts = cnts.to_frame()
    return cnts


def time_indexed_points(data):
    """

    :param data: dict
        key: dname, value: dataframe with spu_assignment
    :return: dict
        key: dname, value: pd.Series of coords of points
    """
    points = {dname: df[C.COL.coords] for dname, df in data.items()}
    return points


if __name__ == '__main__':
    from src.exp_helper import CompileData
    import os

    if os.getcwd().endswith('src'):
        os.chdir('..')
    print(os.getcwd())

    D = CompileData(spu_name='grid_1000')
    D.set_x(['crime'], by_category=True)
    D.set_y('crime/burglary')

    data_x_past = D.data_x.slice_data('2015-01-01', '2015-01-03')
    x = prepare_temporal_data_for_model(data_x_past, setting='time_indexed_points')
