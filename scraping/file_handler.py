import json
import os
from typing import List

from .Data import Order


def file_exists(file_name: str) -> bool:
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    return os.path.isfile(path)


def remove_file(file_name: str) -> bool:
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    if os.path.isfile(path):
        os.remove(path)
        print(f"{file_name} removed")
        return True
    else:
        print(f"Failed to remove {file_name}")
        return False


def load_orders(file_name: str = 'orders.json') -> List[Order]:
    file = _read_file(file_name)
    if file:
       data = json.load(file)

    if not data:
        return []

    orders = []
    for order_dict in data:
        orders.append(Order.from_dict(order_dict))

    return orders


def load_password(file_name: str = 'pw.txt'):
    file = _read_file(file_name)
    if file:
        return file.read()
    else:
        return ""


def save_file(file_name: str, data: str):
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    with open(path, 'w') as fh:
        fh.write(data)


def read_json_file(file_name):
    file = _read_file(file_name)
    if file:
        return json.load(file)


def _read_file(file_name: str):
    package_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(package_directory, '..', file_name)
    if os.path.exists(path):
        file = open(path)
        return file
    else:
        print(f"{file_name} not found")
