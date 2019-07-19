from functools import reduce

from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt

from . import utils
from .Data import Order
from . import file_handler as fh


def main():
    orders = fh.load_orders()

    print(f'counted {get_order_count(orders)} orders with a total price of {get_total(orders)} Euro')
    print(f'most expensive order was: {get_most_expensive_order(orders)}')
    print(f'audible total: {get_audible_total(orders)}')

    #plot_expenses_by_year(orders)
    plot_audible_by_month(orders)
    plot_all(orders)


def plot_all(orders: List[Order]):
    amazon_totals_by_year = utils.sort_dict_by_key(get_total_by_year(orders))
    years = tuple(amazon_totals_by_year.keys())
    bar_amount = np.arange(len(years))

    instant_video_totals_by_year = get_instant_video_per_year(orders)
    audible_totals_by_year = get_audible_total_by_year(orders)
    for year in amazon_totals_by_year.keys():
        if year not in audible_totals_by_year.keys():
            audible_totals_by_year[year] = 0
        if year not in instant_video_totals_by_year.keys():
            instant_video_totals_by_year[year] = 0

    audible_totals_by_year = utils.sort_dict_by_key(audible_totals_by_year)
    instant_video_totals_by_year = utils.sort_dict_by_key(instant_video_totals_by_year)

    amazon_plot = plt.bar(bar_amount, list(amazon_totals_by_year.values()), align='center', alpha=0.5)
    audible_plot = plt.bar(bar_amount, list(audible_totals_by_year.values()), align='center', alpha=0.5)
    instant_video_plot = plt.bar(bar_amount, list(instant_video_totals_by_year.values()), align='center', alpha=0.5)

    plt.ylabel('Amount in Euro')
    plt.xlabel('Year')
    plt.xticks(bar_amount, years)
    plt.legend((amazon_plot[0], audible_plot[0], instant_video_plot[0]), ('Amazon Purchases', 'Audible Purchases', 'Instant Video Purchases'))

    plt.show()


def plot_expenses_by_year(orders: List[Order]):
    totals_by_year = get_total_by_year(orders)
    objects = tuple(totals_by_year.keys())
    y_pos = np.arange(len(objects))

    plt.bar(y_pos, list(totals_by_year.values()), align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Amount in Euro')
    plt.xlabel('Year')
    plt.title('Amazon Purchases')

    plt.show()


def plot_instant_video_by_month(orders: List[Order]):
    totals_by_year = get_instant_video_per_year(orders)
    objects = tuple(totals_by_year.keys())
    y_pos = np.arange(len(objects))

    plt.bar(y_pos, list(totals_by_year.values()), align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Amount in Euro')
    plt.xlabel('Year')
    plt.title('Instant Video Purchases')

    plt.show()


def plot_audible_by_month(orders: List[Order]):
    totals_by_year = get_audible_total_by_year(orders)
    objects = tuple(totals_by_year.keys())
    y_pos = np.arange(len(objects))

    plt.bar(y_pos, list(totals_by_year.values()), align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Amount in Euro')
    plt.xlabel('Year')
    plt.title('Audible Purchases')

    plt.show()


def get_total_by_year(orders: List[Order]) -> Dict[int, float]:
    totals_by_year = dict()
    for order in orders:
        if order.date.year not in totals_by_year:
            totals_by_year[order.date.year] = 0
        totals_by_year[order.date.year] += order.price
    totals_by_year = {year: round(total, 2) for year, total in totals_by_year.items()}
    return totals_by_year


def get_total(orders: List[Order]):
    return reduce((lambda total, order: total + order.price), orders, 0)


def get_most_expensive_order(orders: List[Order]):
    max_order_price = max(map(lambda order: order.price, orders))
    return list(filter(lambda order: order.price == max_order_price, orders))


def get_order_count(orders: List[Order]):
    return len(orders)


def get_audible_total(orders: List[Order]) -> float:
    audible_orders = filter(lambda order: order.order_id[:3] == 'D01', orders)
    total = sum(map(lambda order: order.price, audible_orders))
    return total


def order_contains_audible_items(order: Order) -> bool:
    for item in order.items:
        if item.seller == 'Audible GmbH':
            return True
    return False


def get_audible_total_by_year(orders: List[Order]) -> Dict[int, float]:
    audible_orders = [order for order in orders if order_contains_audible_items(order)]
    total_by_year = {}
    for order in audible_orders:
        if order.date.year not in total_by_year.keys():
            total_by_year[order.date.year] = 0
        total_by_year[order.date.year] += order.price
    total_by_year = {year: round(total, 2) for year, total in total_by_year.items()}

    return total_by_year


def order_contains_instant_video_items(order: Order) -> bool:
    for item in order.items:
        if item.seller == 'Amazon Instant Video Germany GmbH':
            return True
    return False


def get_instant_video_per_year(orders: List[Order]) -> Dict[int, float]:
    instant_video_orders = [order for order in orders if order_contains_instant_video_items(order)]
    total_by_year = {}
    for order in instant_video_orders:
        if order.date.year not in total_by_year.keys():
            total_by_year[order.date.year] = 0
        total_by_year[order.date.year] += order.price
    total_by_year = {year: round(total, 2) for year, total in total_by_year.items()}

    return total_by_year


def get_uncategorized_totals(orders: List[Order]) -> Dict[int, float]:
    amazon = get_total_by_year(orders)
    audible = get_audible_total_by_year(orders)
    prime_vid = get_instant_video_per_year(orders)
    prime = get_prime_member_fee_total_by_year(orders)

    remaining_totals = {}
    for year in amazon.keys():
        remaining = amazon[year]
        remaining = remaining - audible[year] if year in audible.keys() else remaining
        remaining = remaining - prime_vid[year] if year in prime_vid.keys() else remaining
        remaining = remaining - prime[year] if year in prime.keys() else remaining

        remaining_totals[year] = remaining
    return remaining_totals



def get_prime_member_fee_total_by_year(orders: List[Order]) -> Dict[int, float]:
    # ToDo
    return {}


if __name__ == '__main__':
    main()
