import datetime

from typing import List, Dict

from .Data import Order


class Evaluation:
    def __init__(self, orders: List[Order]):
        self.orders = orders

    def get_most_expensive_order(self) -> List[Order]:
        """ get a list with the most expensive order, contains usually only one element """
        max_order_price = max(map(lambda order: order.price, self.orders))
        return list(filter(lambda order: order.price == max_order_price, self.orders))

    def get_orders_with_most_items(self) -> List[Order]:
        max_item_count = max([len(order.items) for order in self.orders])
        return list(filter(lambda order: len(order.items) == max_item_count, self.orders))

    def get_order_count(self) -> int:
        return len(self.orders)

    def get_item_count(self) -> int:
        return sum([len(order.items) for order in self.orders])

    def get_total(self):
        total = sum([order.price for order in self.orders])
        return round(total, 2)

    def get_audible_total(self) -> float:
        total = sum(self.audible_total_by_year().values())
        return round(total, 2)

    def get_instant_video_total(self) -> float:
        total = sum(self.instant_video_total_per_year().values())
        return round(total, 2)

    @staticmethod
    def order_contains_audible_items(order: Order) -> bool:
        for item in order.items:
            if item.seller == 'Audible GmbH':
                return True
        return False

    @staticmethod
    def order_contains_instant_video_items(order: Order) -> bool:
        for item in order.items:
            if item.seller == 'Amazon Instant Video Germany GmbH':
                return True
        return False

    @staticmethod
    def order_contains_balance_item(order: Order) -> bool:
        for item in order.items:
            if item.title == "Amazon-Konto aufladen":
                return True
        return False

    def total_by_year(self) -> Dict[int, float]:
        totals = dict()
        for order in self.orders:
            if order.date.year not in totals:
                totals[order.date.year] = 0
            totals[order.date.year] += order.price
        totals = {year: round(total, 2) for year, total in totals.items()}
        return totals

    def audible_total_by_year(self) -> Dict[int, float]:
        audible_orders = [order for order in self.orders if self.order_contains_audible_items(order)]
        totals = {}
        for order in audible_orders:
            if order.date.year not in totals.keys():
                totals[order.date.year] = 0
            totals[order.date.year] += order.price
        totals = {year: round(total, 2) for year, total in totals.items()}

        return totals

    def instant_video_total_per_year(self) -> Dict[int, float]:
        instant_video_orders = [order for order in self.orders if self.order_contains_instant_video_items(order)]
        totals = {}
        for order in instant_video_orders:
            if order.date.year not in totals.keys():
                totals[order.date.year] = 0
            totals[order.date.year] += order.price
        totals = {year: round(total, 2) for year, total in totals.items()}

        return totals

    def added_balance_per_year(self) -> Dict[int, float]:
        balance_orders = [order for order in self.orders if self.order_contains_balance_item(order)]

        totals = {}
        for order in balance_orders:
            if order.date.year not in totals.keys():
                totals[order.date.year] = 0
            totals[order.date.year] += order.price
        totals = {year: round(total, 2) for year, total in totals.items()}

        return totals

    def uncategorized_totals_per_year(self) -> Dict[int, float]:
        amazon = self.total_by_year()
        audible = self.audible_total_by_year()
        prime_vid = self.instant_video_total_per_year()
        prime = self.prime_member_fee_by_year()
        balance = self.added_balance_per_year()

        remaining_totals = {}
        for year in amazon.keys():
            remaining = amazon[year]
            remaining = remaining - audible[year] if year in audible.keys() else remaining
            remaining = remaining - prime_vid[year] if year in prime_vid.keys() else remaining
            remaining = remaining - prime[year] if year in prime.keys() else remaining
            remaining = remaining - balance[year] if year in prime.keys() else remaining
            remaining_totals[year] = remaining
        return remaining_totals

    def prime_member_fee_by_year(self) -> Dict[int, float]:
        # ToDo
        return {}

    def totals_by_month(self) -> Dict[datetime.date, float]:
        totals = dict()
        for order in self.orders:
            key = datetime.datetime(year=order.date.year, month=order.date.month, day=1)
            if key not in totals:
                totals[key] = 0
            totals[key] += order.price
        totals = {date: round(total, 2) for date, total in totals.items()}
        return totals

    def trend_by_month(self) -> Dict[datetime.date, float]:
        """ return a trend value calculated through the expenses average over the last 6 month """
        totals = self.totals_by_month()

        trends = dict()
        last = [0.0] * 6

        for date, total in totals.items():
            last.pop(0)
            last.append(total)
            trend = sum(last) / len(last)
            trends[date] = trend

        return trends

