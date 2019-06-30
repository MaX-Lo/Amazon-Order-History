from json import JSONEncoder
from typing import List, Any


class Item():
    def __init__(self, price, link, title):
        self.price = price
        self.link = link
        self.title = title

    def to_dict(self):
        return self.__dict__


class Order():
    def __init__(self, order_id: str, price: float, date: str, items: List[Item]):
        self.order_id = order_id
        self.price = price
        self.date = date
        self.items = items

    def to_dict(self):
        attr_dict = self.__dict__
        attr_dict['items'] = [item.to_dict() for item in self.items]
        return attr_dict


# pytype doesn't support dataclasses yet
# @dataclass
# class Order:
#     order_id: str
#     price: float
#     date: str
#     link: str
#     title: str
