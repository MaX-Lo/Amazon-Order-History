"""
contains file handling related methods
"""

import json
import os
from typing import List

from .data import Order


def remove_file(file_name: str) -> bool:
    """ removes a file with file_name """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)

    if not os.path.isfile(path):
        return False

    os.remove(path)
    print(f"{file_name} removed")
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


def load_password(file_name: str = 'pw.txt'):
    """ reads the password files content """
    path = to_file_path(file_name)
    if not os.path.exists(path):
        print(f"Password file not found")
        return ""

    with open(path) as file:
        return file.read()


def save_file(file_name: str, data: str):
    """ writes a file, if a file with file_name already exists its content gets overwritten """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    with open(path, 'w') as file:
        file.write(data)


def read_json_file(file_name):
    """ returns a json object based on the file content under file_name"""
    path = to_file_path(file_name)
    if not os.path.exists(path):
        print(f"{file_name} not found")
        return ""

    with open(path) as file:
        return json.load(file)


def to_file_path(file_name):
    """ :returns an existing absolute file path based on the project root directory + file_name"""
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    return path
