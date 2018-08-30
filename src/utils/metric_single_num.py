from sklearn.metrics import mean_absolute_error, r2_score, auc
from .metric_roc_like import (search_efficient_rate_upct_wrap, prediction_accuracy_index_upct_wrap,
                              area_to_perimeter_ratio_upct_wrap, hit_rate_upct_wrap)

from . import p2f


def mse_wrap(y_true, y_pred, spu=None):
    return mean_absolute_error(y_true, y_pred)


def r2_wrap(y_true, y_pred, spu=None):
    return r2_score(y_true, y_pred)


def curve2auc(curve):
    x = curve.reset_index()['index'].apply(p2f)
    y = curve.values
    return auc(x, y)


def search_efficient_rate_upct_auc(y_true, y_pred, spu):
    return curve2auc(search_efficient_rate_upct_wrap(y_true, y_pred, spu))


def prediction_accuracy_index_upct_auc(y_true, y_pred, spu):
    return curve2auc(prediction_accuracy_index_upct_wrap(y_true, y_pred, spu))


def area_to_perimeter_ratio_upct_auc(y_true, y_pred, spu):
    return curve2auc(area_to_perimeter_ratio_upct_wrap(y_true, y_pred, spu))


def hit_rate_upct_auc(y_true, y_pred, spu):
    return curve2auc(hit_rate_upct_wrap(y_true, y_pred, spu))
