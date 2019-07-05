from functools import reduce

import json


def main():
    with open("orders.json", 'r') as file:
        data = json.load(file)

    if not data:
        return

    print(f'counted {get_order_count(data)} orders with a total price of {get_total(data)} Euro')
    print(f'most expensive order was: {get_most_expensive_order(data)}')


def get_total(data):
    return reduce((lambda total, order: total + order['price']), data, 0)


def get_most_expensive_order(data):
    max_order_price = max(map(lambda order: order['price'], data))
    return list(filter(lambda order: order['price'] == max_order_price, data))


def get_order_count(data):
    return len(data)


if __name__ == '__main__':
    main()
