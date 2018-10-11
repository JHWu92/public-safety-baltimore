import geopandas as gp
import pandas as pd
from shapely.geometry import Point

from src import constants as C
from src.utils import str_is_float


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


def prepare_temporal_data_for_model(data, setting, spu=None):
    if setting == 'event_cnt':
        return event_cnt(data, spu=spu)
    elif setting == 'time_indexed_points':
        return time_indexed_points(data)
    elif setting.startswith('hot_spot'):
        if '/' not in setting:
            raise ValueError('please specify the kind of hot spots with a /')
        kind = setting.split('/')[1]
        return hot_spot_cls(data, kind, spu=spu)
    else:
        raise NotImplementedError('No such setting:' + setting)


def event_cnt(data, spu=None):
    """

    :param data: dict
        key: dname, value: dataframe with spu_assignment
    :param spu: Dataframe, default None
        spatial unit used to reindex event_cnt if not None
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

    if spu is not None:
        cnts = cnts.reindex(spu.index).fillna(0)
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


def hot_spot_cls(data, kind='mean', spu=None):
    cnts = event_cnt(data, spu=spu)

    if str_is_float(kind):
        kind = float(kind)
        if kind > 1 or kind <= 0:
            raise ValueError('kind should be >0 or <1')
        thres = cnts.max() - kind * (cnts.max() - cnts.min())
        hot_spot = (cnts > thres).astype(int)
    else:
        if kind == 'mean':
            hot_spot = cnts.apply(lambda c: c > c.mean()).astype(int)
        elif kind == 'mean+std':
            hot_spot = cnts.apply(lambda c: c > (c.mean() + c.std())).astype(int)
        elif kind == 'median':
            hot_spot = cnts.apply(lambda c: c > (c.median())).astype(int)
        else:
            raise ValueError('hotspot cls: kind=%s is not supported' % kind)
    return hot_spot


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
    data_y_past = D.data_y.slice_data('2015-01-01', '2015-01-03')
    x = prepare_temporal_data_for_model(data_x_past, setting='time_indexed_points')
    y = prepare_temporal_data_for_model(data_y_past, setting='hot_spot/mean')
    y2 = prepare_temporal_data_for_model(data_y_past, setting='event_cnt', spu=D.spu)
    y4 = prepare_temporal_data_for_model(data_y_past, setting='hot_spot/mean', spu=D.spu)
    y3 = prepare_temporal_data_for_model(data_y_past, setting='event_cnt')
