import re
from src.constants import DateTimeRelated as dtr
import datetime

def reg_check_time_format(time_str):
    """ fast reg check if a time string possibly matched format %H:%M:%S
    if False, it doesn't match
    But if True, it could still doesn't match
    """
    return bool(re.match('\d{1,2}:\d{1,2}:\d{1,2}', time_str))


def reg_check_date_format(date_str):
    return bool(re.match('\d{4}-\d{1,2}-\d{1,2}', date_str))


def parse_date_str(text):
    for fmt in (dtr.datetime_format, dtr.date_format):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')


if __name__ == "__main__":
    print(reg_check_time_format('242'))
    print(reg_check_time_format('12:00:22'))
    print(reg_check_date_format('120-01-11'))
    print(reg_check_date_format('1200-01-11'))
    print(parse_date_str('2018-01-01'))
    print(parse_date_str('2018-01-10 12:23:45'))
