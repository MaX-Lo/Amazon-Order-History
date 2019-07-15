import json
import os
from typing import List

from scraping.Data import Order


def load_orders(file_name: str = 'orders.json') -> List[Order]:
    if os.path.exists(f'../{file_name}'):
        with open(f'../{file_name}') as file:
            data = json.load(file)
    else:
        print(f"{file_name} not found")
        return []

    if not data:
        return []

    orders = []
    for order_dict in data:
        orders.append(Order.from_dict(order_dict))

    return orders
