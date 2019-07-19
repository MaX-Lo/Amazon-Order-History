import datetime
from functools import reduce

from typing import List, Dict

from .Data import Order


def get_most_expensive_order(orders: List[Order]):
    max_order_price = max(map(lambda order: order.price, orders))
    return list(filter(lambda order: order.price == max_order_price, orders))


def get_order_count(orders: List[Order]):
    return len(orders)


def get_total(orders: List[Order]):
    total = reduce((lambda total, order: total + order.price), orders, 0)
    return round(total, 2)


def get_audible_total(orders: List[Order]) -> float:
    total = sum(audible_total_by_year(orders).values())
    return round(total, 2)


def get_instant_video_total(orders: List[Order]) -> float:
    total = sum(instant_video_total_per_year(orders).values())
    return round(total, 2)


def order_contains_audible_items(order: Order) -> bool:
    for item in order.items:
        if item.seller == 'Audible GmbH':
            return True
    return False


def order_contains_instant_video_items(order: Order) -> bool:
    for item in order.items:
        if item.seller == 'Amazon Instant Video Germany GmbH':
            return True
    return False


def total_by_year(orders: List[Order]) -> Dict[int, float]:
    totals_by_year = dict()
    for order in orders:
        if order.date.year not in totals_by_year:
            totals_by_year[order.date.year] = 0
        totals_by_year[order.date.year] += order.price
    totals_by_year = {year: round(total, 2) for year, total in totals_by_year.items()}
    return totals_by_year


def audible_total_by_year(orders: List[Order]) -> Dict[int, float]:
    audible_orders = [order for order in orders if order_contains_audible_items(order)]
    total_by_year = {}
    for order in audible_orders:
        if order.date.year not in total_by_year.keys():
            total_by_year[order.date.year] = 0
        total_by_year[order.date.year] += order.price
    total_by_year = {year: round(total, 2) for year, total in total_by_year.items()}

    return total_by_year


def instant_video_total_per_year(orders: List[Order]) -> Dict[int, float]:
    instant_video_orders = [order for order in orders if order_contains_instant_video_items(order)]
    total_by_year = {}
    for order in instant_video_orders:
        if order.date.year not in total_by_year.keys():
            total_by_year[order.date.year] = 0
        total_by_year[order.date.year] += order.price
    total_by_year = {year: round(total, 2) for year, total in total_by_year.items()}

    return total_by_year


def uncategorized_totals_per_year(orders: List[Order]) -> Dict[int, float]:
    amazon = total_by_year(orders)
    audible = audible_total_by_year(orders)
    prime_vid = instant_video_total_per_year(orders)
    prime = prime_member_fee_by_year(orders)

    remaining_totals = {}
    for year in amazon.keys():
        remaining = amazon[year]
        remaining = remaining - audible[year] if year in audible.keys() else remaining
        remaining = remaining - prime_vid[year] if year in prime_vid.keys() else remaining
        remaining = remaining - prime[year] if year in prime.keys() else remaining

        remaining_totals[year] = remaining
    return remaining_totals


def prime_member_fee_by_year(orders: List[Order]) -> Dict[int, float]:
    # ToDo
    return {}


def totals_by_month(orders: List[Order]) -> Dict[int, float]:
    totals = dict()
    for order in orders:
        key = datetime.datetime(year=order.date.year, month=order.date.month, day=1)
        if key not in totals:
            totals[key] = 0
        totals[key] += order.price
    totals = {year: round(total, 2) for year, total in totals.items()}
    return totals
