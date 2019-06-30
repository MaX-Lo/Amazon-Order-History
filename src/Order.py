
class Order:

    def __init__(self, order_id: str, price: float, date: str, link: str, title: str):
        self.order_id = order_id
        self.price = price
        self.date = date
        self.link = link
        self.title = title


# pytype doesn't support dataclasses yet
# @dataclass
# class Order:
#     order_id: str
#     price: float
#     date: str
#     link: str
#     title: str
