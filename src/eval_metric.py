import pandas as pd

from src import constants as C


# TODO: metrics that compute on "hotspots" instead of top N% most risky grids


def auc_idx(len_obj, num_obs):
    """
    helper for creating AUC-like index
    :param len_obj: number of objects
    :param num_obs: number of observation points for plotting
    :return:
    """
    # print(len_obj, num_obs)
    idx_for_auc = [int(len_obj * (i + 1) / num_obs) for i in range(num_obs - 1)] + [len_obj - 1]
    readable_index = ['%.0f%%' % ((i + 1) / num_obs * 100) for i in range(num_obs)]
    return idx_for_auc, readable_index


def bin_idx(risk, num):
    mi, ma = risk.min(), risk.max()
    iloc_idx, readable_idx = [], []
    for i in range(num):
        thres = mi + (ma - mi) * (1 - (i + 1) / num)
        iloc_idx.append((risk >= thres).sum()-1)
        readable_idx.append('bin>=%d' % (i+1))
    # print(iloc_idx, readable_idx)
    return iloc_idx, readable_idx


def get_idx(spatial_unit_attr, num, auc_or_bin='auc'):
    if auc_or_bin == 'auc':
        len_obj = len(spatial_unit_attr)
        return auc_idx(len_obj, num)
    elif auc_or_bin == 'bin':
        risk = spatial_unit_attr[C.COL.risk]
        return bin_idx(risk, num)
    else:
        raise ValueError('auc_or_bin should be one of: auc, bin')


def hit_to_pai(spatial_unit_attr, event_normalized=False,
               area_normalized=False, event_by_area=False,
               auc_or_bin='auc'):
    """Aggregate hit rate, search efficient rate and PAI
    into a parameter-controlled process

    :param spatial_unit_attr: pd.DataFrame
        - index=unit_index
        - columns: at least risk, num_events and area

    :param event_normalized: if yes: hit rate; no, number of events
    :param area_normalized: if no: km^2 (search rate); if yes, area percentage(PAI)
    :param event_by_area: if no: hit rate; yes, search rate or PAI
    """

    # auc index
    # num_grids = len(spatial_unit_attr)
    # idx_for_auc = [int(num_grids * (i + 1) / 10) for i in range(9)] + [num_grids - 1]
    # iloc_idx, readable_idx = auc_idx(num_grids, 10)
    num = 5 if auc_or_bin == 'bin' else 10
    iloc_idx, readable_idx = get_idx(spatial_unit_attr, num, auc_or_bin)

    tmp = spatial_unit_attr.sort_values(C.COL.risk, ascending=False)
    tmp[C.COL.area] /= 1e6
    event_factor = tmp[C.COL.num_events].sum() if event_normalized else 1
    tmp['hit'] = tmp[C.COL.num_events].cumsum() / event_factor
    if not event_by_area:
        res = tmp['hit']
    else:
        area_factor = tmp[C.COL.area].sum() if area_normalized else 1
        tmp['cum_area'] = tmp[C.COL.area].cumsum() / area_factor
        res = tmp['hit'] / tmp['cum_area']

    res = res.iloc[iloc_idx]
    res.index = readable_idx
    return res


def hit_rate_auc(spatial_unit_attr):
    return hit_to_pai(spatial_unit_attr, event_normalized=True, event_by_area=False, auc_or_bin='auc')


def search_efficient_rate_auc(spatial_unit_attr):
    """Proposed by Bower et al 2004 (Bowers2004-gn):
    the number of crimes successfully predicted per kilometre-squared.
    Using a standardized index allows different procedures
    and different hot spots to be meaningfully compared.

    Critics by Chainey2008-ys:
    does not easily allow for comparisons between study areas of different sizes

    :param spatial_unit_attr: pd.DataFrame,
        index=unit_index,
        columns: at least risk, num_events, area
    :return:
    """
    return hit_to_pai(spatial_unit_attr, event_normalized=False, area_normalized=False, event_by_area=True,
                      auc_or_bin='auc')


def prediction_accuracy_index_auc(spatial_unit_attr):
    """PAI, Proposed by \cite{Chainey2008-ys}.

    the greater the number of future crime events in
    a hotspot area that is smaller in areal size to the whole study area,
    the higher the PAI value.

     We also believe it is a measure that is applicable to
     any study area, any crime point data,
     and to any analysis technique that aims to predict spatial patterns of crime
    """
    return hit_to_pai(spatial_unit_attr, event_normalized=True, area_normalized=True, event_by_area=True,
                      auc_or_bin='auc')


def area_to_perimeter_ratio_auc(spatial_unit_attr, auc_or_bin='auc'):
    """Proposed by bower-2004"""
    from shapely.ops import cascaded_union
    # auc index
    # num_grids = len(spatial_unit_attr)
    # idx_for_auc = [int(num_grids * (i + 1) / 10) for i in range(9)] + [num_grids - 1]
    # idx_for_auc, readable_idx = auc_idx(num_grids, 10)
    num = 5 if auc_or_bin == 'bin' else 10
    iloc_idx, readable_idx = get_idx(spatial_unit_attr, num, auc_or_bin)

    tmp = spatial_unit_attr.sort_values(C.COL.risk, ascending=False)
    tmp['cum_area'] = tmp[C.COL.area].cumsum()

    res = []
    for idx, name in zip(iloc_idx, readable_idx):
        sub_units = tmp.iloc[:idx + 1]['geometry']
        perimeter = cascaded_union(sub_units).length
        cum_area = tmp.iloc[idx]['cum_area']
        res.append(cum_area / perimeter)
        # print(idx, cum_area, perimeter)
        # print(cascaded_union(sub_units).wkt)

    return pd.Series(res, index=readable_idx)


def hit_rate_bin(spatial_unit_attr):
    return hit_to_pai(spatial_unit_attr, event_normalized=True, event_by_area=False, auc_or_bin='bin')


def search_efficient_rate_bin(spatial_unit_attr):
    return hit_to_pai(spatial_unit_attr, event_normalized=False, area_normalized=False, event_by_area=True,
                      auc_or_bin='bin')


def prediction_accuracy_index_bin(spatial_unit_attr):
    return hit_to_pai(spatial_unit_attr, event_normalized=True, area_normalized=True, event_by_area=True,
                      auc_or_bin='bin')


def area_to_perimeter_ratio_bin(spatial_unit_attr):
    return area_to_perimeter_ratio_auc(spatial_unit_attr, 'bin')


def main():
    import pandas as pd
    from shapely.geometry import box
    d = [
        (1, 2, 40000, box(0, 0, 200, 200)),
        (2, 3, 40000, box(200, 200, 400, 400)),
        (3, 1, 40000, box(0, 200, 400, 400)),
        (4, 4, 40000, box(600, 0, 800, 200)),
        (5, 2, 40000, box(800, 200, 1000, 400)),
        (6, 7, 40000, box(800, 0, 1000, 200))
    ]
    df = pd.DataFrame(d)
    df.columns = [C.COL.risk, C.COL.num_events, C.COL.area, 'geometry']
    # print(hit_rate(df))
    # print(search_efficient_rate(df))
    # print(prediction_accuracy_index(df))
    print(hit_rate_auc(df), hit_rate_auc.__name__)
    print(hit_rate_bin(df), hit_rate_bin.__name__)
    return


if __name__ == '__main__':
    main()
