import datetime
from typing import List, Dict
import dateutil.parser

from . import utils


class Item:
    def __init__(self, price, link, title, seller: str):
        self.price = price
        self.link = link
        self.title = title
        self.seller = seller

    def to_dict(self) -> Dict:
        return self.__dict__

    @staticmethod
    def from_dict(item_dict: Dict) -> 'Item':
        """ returns an item object for a given order as dict """
        return Item(item_dict['price'], item_dict['link'], item_dict['title'])


class Order:
    def __init__(self, order_id: str, price: float, date: datetime.datetime, items: List[Item]):
        self.order_id = order_id
        self.price = price
        self.date = date
        self.items = items

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
        date = dateutil.parser.parse(order_dict['date']) # datetime.datetime.strptime(order_dict['date'], '%Y-%m-%d')
        items = [Item.from_dict(item) for item in order_dict['items']]
        return Order(id, price, date, items)
