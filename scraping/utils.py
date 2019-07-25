import datetime
import json
import os
from collections import OrderedDict

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November',
          'Dezember']


def str_to_datetime(date_str: str) -> datetime.datetime:
    """ expects a date str formatted in german date format as 'day. month year' e.g. '4. September 2018' """
    day_str, month_str, year_str = date_str.split(' ')

    day = int(day_str.replace('.', ''))
    month = MONTHS.index(month_str) + 1
    year = int(year_str)

    return datetime.datetime(day=day, month=month, year=year)


def serialize_date(obj) -> str:
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def wait_for_element_by_class_name(browser: WebDriver, class_name: str, timeout: float = 5) -> bool:
    """ wait the specified timout for a element to load
        :returns true if element was found
    """
    try:
        WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.CLASS_NAME, class_name)))
        return True
    except TimeoutException:
        print(f'Skipping, loading took too much time! (>{timeout}sec)')
        return False


def wait_for_element_by_id(browser: WebDriver, order_id: object, timeout: object = 5) -> object:
    """ wait the specified timout for a element to load """
    try:
        WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.ID, order_id)))
        return True
    except TimeoutException:
        print(f'Skipping, loading took too much time! (>{timeout}sec)')
        return False


def sort_dict_by_key(dic: dict) -> OrderedDict:
    return_dict = OrderedDict()

    keys = list(dic.keys())
    keys.sort()

    for key in keys:
        return_dict[key] = dic[key]

    return return_dict
