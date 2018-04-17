def hit_rate(grids_risk, grids_y):
    """

    :param grids_risk: Series(index=grid_index, value=risk_score)
    :param grids_y: Series(index=grid_index, value=y_value_
    :return:
    """
    num_grids = len(grids_risk)
    idx_for_auc = [int(num_grids * (i + 1) / 10) for i in range(9)] + [num_grids - 1]
    rank = grids_risk.sort_values(ascending=False).index
    hit = grids_y.loc[rank].cumsum()/grids_y.sum()
    return hit.iloc[idx_for_auc].values

