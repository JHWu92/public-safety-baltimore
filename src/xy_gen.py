import geopandas as gp

def y_cnt_event(spatial_units, events):
    """

    :param spatial_units: gp.GeoDataFrame
    :param events: gp.GeoDataFrame
    :return:
    """

    joined = gp.sjoin(events.reset_index(), spatial_units)
    y_cnt =spatial_units.join(joined.groupby('index_right').agg({'index':'count'}), how='left')\
                    .rename(columns={'index':'count'}).fillna(0)
    return y_cnt[['count']]