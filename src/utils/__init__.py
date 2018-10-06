import datetime
import re
from copy import copy

import numpy as np

from src.constants import DateTimeRelated as dtr, COL


def loubar_thres(arr, is_sorted=False):
    if not is_sorted:
        arr = copy(arr)
        arr = sorted(arr)

    lonrenz_y = arr.cumsum() / arr.sum()
    lonrenz_y = np.insert(lonrenz_y, 0, 0)
    x_axis = np.arange(lonrenz_y.size)/(lonrenz_y.size-1)
    slope = (lonrenz_y[-1] - lonrenz_y[-2]) / (x_axis[-1] - x_axis[-2])
    loubar = (slope - 1) / slope
    arr_thres = arr[int(np.ceil((lonrenz_y.size - 1) * loubar) - 1)]

    return loubar, arr_thres


def p2f(x):
    return float(x.strip('%')) / 100


# ==========================
# clean data related
# ==========================
def reg_check_time_format(time_str):
    """ fast reg check if a time string possibly matched format %H:%M:%S
    if False, it doesn't match
    But if True, it could still doesn't match
    """
    return bool(re.match('\d{1,2}:\d{1,2}:\d{1,2}', time_str))


def reg_check_date_format(date_str):
    return bool(re.match('\d{4}-\d{1,2}-\d{1,2}', date_str))


def can_be_parsed_time(time_str):
    try:
        datetime.datetime.strptime(time_str, '%H:%M:%S')
        return True
    except ValueError:
        return False


# ==========================
# Datetime related
# ==========================
def parse_date_str(text):
    if isinstance(text, datetime.datetime):
        return text
    for fmt in (dtr.datetime_format, dtr.date_format):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found for "%s" (type=%s)' % (text, type(text)))


# ==========================
# DataFrame related
# ==========================
def get_df_categories(df):
    return df[COL.category].unique()


def subdf_by_categories(df, categories):
    """

    :param df:
    :param categories: str, or list
    :return:
    """
    if isinstance(categories, str):
        return df[df[COL.category] == categories]
    return df[df[COL.category].isin(categories)]


if __name__ == "__main__":
    print(reg_check_time_format('242'))
    print(reg_check_time_format('12:00:22'))
    print(reg_check_date_format('120-01-11'))
    print(reg_check_date_format('1200-01-11'))
    print(parse_date_str('2018-01-01'))
    print(parse_date_str('2018-01-10 12:23:45'))
