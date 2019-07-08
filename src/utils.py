import datetime

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November',
          'Dezember']


def save_file(file_path: str, data: str):
    with open(file_path, 'w') as fh:
        fh.write(data)


def str_to_datetime(date_str: str) -> datetime.datetime:
    """ expects a date str formated in german date format as 'day. month year' e.g. '4. September 2018' """
    day_str, month_str, year_str = date_str.split(' ')

    day = int(day_str.replace('.', ''))
    month = MONTHS.index(month_str) + 1
    year = int(year_str)

    return datetime.datetime(day=day, month=month, year=year)


def serialize_date(obj) -> str:
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))