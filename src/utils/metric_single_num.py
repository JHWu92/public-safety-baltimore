from sklearn.metrics import mean_absolute_error, r2_score, auc, mean_squared_error
from math import sqrt
from . import p2f
import numpy as np
from src.xy_gen import hot_spot_cls
from .metric_roc_like import (search_efficient_rate_upct_wrap, prediction_accuracy_index_upct_wrap,
                              area_to_perimeter_ratio_upct_wrap, hit_rate_upct_wrap)
from src.constants import COL


def hit_rate(y_true, y_pred, spu=None):
    """for 2-class classification only, y_pred is cast to a bool arr as mask for y_true"""
    mask = y_pred.astype(bool)
    y_true_in_pred = y_true[mask]
    return y_true_in_pred.sum()/y_true.sum()


def search_efficient_rate(y_true, y_pred, spu):
    mask = y_pred.astype(bool)
    y_true_in_pred = y_true[mask]
    area = spu.loc[mask][COL.area].sum() * 1e-6
    return y_true_in_pred.sum()/area


def prediction_accuracy_index(y_true, y_pred, spu):
    hit = hit_rate(y_true,y_pred,spu)
    mask = y_pred.astype(bool)
    area_pcnt = spu.loc[mask][COL.area].sum()/spu[COL.area].sum()
    return hit/area_pcnt


def rmse(y_true, y_pred, spu=None):
    return sqrt(mean_squared_error(y_true, y_pred))


def mae(y_true, y_pred, spu=None):
    return mean_absolute_error(y_true, y_pred)


def r2(y_true, y_pred, spu=None):
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


metrics = [rmse, mae, r2, search_efficient_rate_upct_auc, prediction_accuracy_index_upct_auc, hit_rate_upct_auc,
           area_to_perimeter_ratio_upct_auc]
