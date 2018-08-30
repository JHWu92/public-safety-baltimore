from sklearn.metrics import mean_absolute_error, r2_score


def mse_wrap(y_true, y_pred, spu=None):
    return mean_absolute_error(y_true, y_pred)


def r2_wrap(y_true, y_pred, spu=None):
    return r2_score(y_true, y_pred)
