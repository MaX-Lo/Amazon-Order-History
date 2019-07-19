import datetime
from dataclasses import dataclass
from typing import List, Dict

import dateutil.parser

from . import utils


@dataclass
class Item:
    price: float
    link: str
    title: str
    seller: str

    def to_dict(self) -> Dict:
        return self.__dict__

    @staticmethod
    def from_dict(item_dict: Dict) -> 'Item':
        """ returns an item object for a given order as dict """
        return Item(item_dict['price'], item_dict['link'], item_dict['title'], item_dict['seller'])


@dataclass
class Order:
    order_id: str
    price: float
    date: datetime.datetime
    items: List[Item]

    def is_equal(self, order) -> bool:
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
        id = order_dict['order_id']
        price = float(order_dict['price'])
        date = dateutil.parser.parse(order_dict['date'])  # datetime.datetime.strptime(order_dict['date'], '%Y-%m-%d')
        items = [Item.from_dict(item) for item in order_dict['items']]
        return Order(id, price, date, items)
