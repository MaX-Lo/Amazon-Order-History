"""
data classes for orders and items
"""

import datetime
from dataclasses import dataclass
from typing import List, Dict

import dateutil.parser

from . import utils


@dataclass
class Item:
    """ a dataclass for items """
    price: float
    link: str
    title: str
    seller: str
    # category depth as key and name as value, e.g. [0: Bekleidung, 1: Herren, 2: Tops,T-Shirts & Hemden, 3: T-Shirts]
    category: Dict[int, str]

    def to_dict(self) -> Dict:
        """ convert item to a dictionary """
        return self.__dict__

    @staticmethod
    def from_dict(item_dict: Dict) -> 'Item':
        """ returns an item object for a given order as dict """
        category = {int(cat[0]): cat[1] for cat in item_dict['category'].items()}
        return Item(item_dict['price'], item_dict['link'], item_dict['title'], item_dict['seller'], category)


@dataclass
class Order:
    """ a dataclass for orders, where one order usually contains at least one item """
    order_id: str
    price: float  # overall costs
    # shipment: float  # total shipment cost
    date: datetime.date
    items: List[Item]

    def is_equal(self, order) -> bool:
        """ compares to orders for equality by comparing their ids"""
        return order.order_id == self.order_id

    def to_dict(self) -> Dict:
        """ returns a serializable representation of this order as dict """
        attr_dict = self.__dict__
        attr_dict['items'] = [item.to_dict() for item in self.items]
        attr_dict['date'] = utils.serialize_date(self.date)
        return attr_dict

    @staticmethod
    def from_dict(order_dict: Dict) -> 'Order':
        """ returns an order object for a given order as dict """
        order_id = order_dict['order_id']
        price = float(order_dict['price'])
        date: datetime.date = dateutil.parser.parse(order_dict['date']).date()
        items = [Item.from_dict(item) for item in order_dict['items']]
        return Order(order_id, price, date, items)
