from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    price: float
    date: str
    link: str
    title: str
