import re


def reg_check_time_format(time_str):
    """ fast reg check if a time string possibly matched format %H:%M:%S
    if False, it doesn't match
    But if True, it could still doesn't match
    """
    return bool(re.match('\d{1,2}:\d{1,2}:\d{1,2}', time_str))


def reg_check_date_format(date_str):
    return bool(re.match('\d{4}-\d{1,2}-\d{1,2}', date_str))


if __name__ == "__main__":
    print(reg_check_time_format('242'))
    print(reg_check_time_format('12:00:22'))
    print(reg_check_date_format('120-01-11'))
    print(reg_check_date_format('1200-01-11'))
