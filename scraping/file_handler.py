"""
contains file handling related methods
"""
# pylint: disable=W1203
import json
import logging
import os
from typing import List, Iterable

from .data import Order

LOGGER = logging.getLogger(__name__)


def remove_file(file_name: str) -> bool:
    """ removes a file with :param file_name """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)

    if not os.path.isfile(path):
        return False

    os.remove(path)
    LOGGER.info(f"{file_name} removed")
    return True


def load_orders(file_name: str = 'orders.json') -> List[Order]:
    """ load all orders found in file_name """
    data = read_json_file(file_name)
    if not data:
        return []

    orders = []
    for order_dict in data:
        orders.append(Order.from_dict(order_dict))

    return orders


def load_password(file_name: str = 'pw.txt') -> str:
    """ reads the password files content """
    path = to_file_path(file_name)
    if not os.path.exists(path):
        LOGGER.warning(f"Password file not found")
        return ""

    with open(path) as file:
        return file.read()


def save_file(file_name: str, data: str) -> None:
    """ writes a file, if a file with file_name already exists its content gets overwritten """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    with open(path, 'w') as file:
        file.write(data)


def read_json_file(file_name: str) -> Iterable:
    """ :returns a json object based on the file content under file_name"""
    path = to_file_path(file_name)
    if not os.path.exists(path):
        LOGGER.warning(f"{file_name} not found")
        return []

    with open(path) as file:
        return iter(json.load(file))


def to_file_path(file_name: str) -> str:
    """ :returns an existing absolute file path based on the project root directory + file_name"""
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    return path
