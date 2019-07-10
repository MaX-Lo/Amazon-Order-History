from functools import reduce

import json
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt

from .Data import Order


def main():
    with open("orders.json", 'r') as file:
        data = json.load(file)

    if not data:
        return

    orders = []
    for order_dict in data:
        orders.append(Order.from_dict(order_dict))

    print(f'counted {get_order_count(data)} orders with a total price of {get_total(data)} Euro')
    print(f'most expensive order was: {get_most_expensive_order(data)}')

    plot_expenses_by_year(orders)


def plot_expenses_by_year(orders: List[Order]):
    totals_by_year = get_total_by_year(orders)
    objects = tuple(totals_by_year.keys())
    y_pos = np.arange(len(objects))
    performance = list(totals_by_year.values())

    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Amount in Euro')
    plt.title('Year')

    plt.show()


def get_total_by_year(orders: List[Order]) -> Dict[int, float]:
    totals_by_year = dict()
    for order in orders:
        if order.date.year not in totals_by_year:
            totals_by_year[order.date.year] = 0
        totals_by_year[order.date.year] += order.price
    return totals_by_year


def get_total(data):
    return reduce((lambda total, order: total + order['price']), data, 0)


def get_most_expensive_order(data):
    max_order_price = max(map(lambda order: order['price'], data))
    return list(filter(lambda order: order['price'] == max_order_price, data))


def get_order_count(data):
    return len(data)


if __name__ == '__main__':
    main()
