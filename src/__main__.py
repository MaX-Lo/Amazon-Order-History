import datetime
import json
import os
from typing import List, Tuple
import argparse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from . import utils, evaluation
from .Data import Order, Item
from .utils import wait_for_element_by_class_name, wait_for_element_by_id


def main():
    email, password, headless, start, end, eval = parse_cli_arguments()

    browser = setup_scraping(headless, email, password)
    orders: List = get_orders(browser, start, end)

    utils.save_file('orders.json', json.dumps([order.to_dict() for order in orders]))

    if eval:
        evaluation.main()
        return

    close(browser)


def parse_cli_arguments() -> Tuple[str, str, bool, int, int, bool]:
    arg_parser = argparse.ArgumentParser(description='Scrapes your Amazon.de order history')
    arg_parser.add_argument('--email', type=str, help='the users email address')
    arg_parser.add_argument('--password', type=str, default="", help='the users password')
    arg_parser.add_argument('--headless', action='store_true',
                            help='run the browser in headless mode (browser is invisible)')
    arg_parser.add_argument('--start', type=int, default=2010, help='the year to start with. If not set 2010 is used.')
    arg_parser.add_argument('--end', type=int, default=datetime.datetime.now().year,
                            help='the year to end with. If not set the current year is used.')
    arg_parser.add_argument('--eval', action='store_true',
                            help='Perform evaluation right after fetching the order history.')

    password = getattr(arg_parser.parse_args(), 'password')
    if len(getattr(arg_parser.parse_args(), 'password')) == 0:
        if os.path.exists('pw.txt'):
            file = open('pw.txt')
            password = file.read()

    return (getattr(arg_parser.parse_args(), 'email'),
            password,
            getattr(arg_parser.parse_args(), 'headless'),
            getattr(arg_parser.parse_args(), 'start'),
            getattr(arg_parser.parse_args(), 'end'),
            getattr(arg_parser.parse_args(), 'eval'))


def setup_scraping(headless, email, password):
    opts = Options()
    opts.headless = headless
    if opts.headless:
        print("Run in headless mode.")
    browser = Firefox(options=opts)
    navigate_to_orders_page(browser)
    complete_sign_in_form(browser, email, password)
    if not signed_in_successful(browser):
        print("Couldn't sign in. Maybe your credentials are incorrect?")
        close(browser)
        exit()
    skip_adding_phone_number(browser)
    return browser


def get_orders(browser, start_year: int, end_year: int) -> List[Order]:
    orders: List[Order] = []
    last_date: datetime.datetime = datetime.datetime(year=start_year, month=1, day=1)
    end_date: datetime.datetime = datetime.datetime.now() if end_year == datetime.datetime.now().year else datetime.datetime(
        year=end_year, month=12, day=31)

    data = utils.read_json_file("orders.json")
    if data:
        for order_dict in data:
            orders.append(Order.from_dict(order_dict))
        orders = sorted(orders, key=lambda order: order.date)
        last_date = orders[-1].date

        scraped_orders: List[Order] = scrape_orders(browser, last_date, end_date)

        # check for intersection of fetched orders
        new_orders: List[Order] = list(
            filter(lambda order: order.order_id not in list(map(lambda order: order.order_id, orders)), scraped_orders))
        orders.extend(new_orders)

    else:
        orders = scrape_orders(browser, last_date, end_date)

    orders = sorted(orders, key=lambda order: order.date)
    return orders


def scrape_orders(browser: WebDriver, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Order]:
    """ returns list of all orders in between given start year (inclusive) and end year (inclusive) """
    start_year: int = start_date.year
    end_year: int = end_date.year
    assert start_year <= end_year, "start year must be before end year"
    assert start_year >= 2010, "Amazon order history works only for years after 2009"
    assert end_year <= datetime.datetime.now().year, "End year can not be in the future"

    orders = []

    # order filter option 0 and 1 are already contained in option 2 [3months, 6months, currYear, lastYear, ...]
    start_index = 2 + (datetime.datetime.now().year - end_year)
    end_index = 2 + (datetime.datetime.now().year - start_year) + 1

    for order_filter_index in range(start_index, end_index):
        # open the dropdown
        wait_for_element_by_id(browser, 'a-autoid-1-announce')
        browser.find_element_by_id('a-autoid-1-announce').click()

        # select and click on a order filter
        id_order_filter = f'orderFilter_{order_filter_index}'
        wait_for_element_by_id(browser, id_order_filter)
        dropdown_element = browser.find_element_by_id(id_order_filter)
        dropdown_element.click()

        pages_remaining = are_orders_for_year_available(browser)
        while pages_remaining:

            orders_on_page: List[Order] = scrape_page_for_orders(browser)
            orders.extend(orders_on_page)

            if start_date > orders_on_page[-1].date:
                break
            if is_paging_menu_available(browser):
                pagination_element = browser.find_element_by_class_name('a-pagination')
            else:
                break

            pages_remaining = is_next_page_available(browser)
            if pages_remaining:
                next_page_link = pagination_element.find_element_by_class_name('a-last') \
                    .find_element_by_css_selector('a').get_attribute('href')
                browser.get(next_page_link)
        year = datetime.datetime.now().year + 2 - order_filter_index
        progress = round((order_filter_index - 1) / (end_index - 2.0) * 100)
        print(f'finished year {year}, ({progress}%)')

    return orders


def scrape_page_for_orders(browser: WebDriver) -> List[Order]:
    """ get a list of all orders found on the currently open page """
    orders = []
    for order_element in browser.find_elements_by_class_name('order'):

        wait_for_element_by_class_name(order_element, 'order-info', timeout=3)
        order_info_element = order_element.find_element_by_class_name('order-info')
        order_id, order_price, date = get_order_info(order_info_element)

        items = []
        for items_by_seller in order_element.find_elements_by_class_name('shipment'):
            for item_element in items_by_seller.find_elements_by_class_name('a-fixed-left-grid'):
                try:
                    item_elements = item_element.find_element_by_class_name('a-col-right') \
                        .find_elements_by_class_name('a-row')
                    item_title_element = item_elements[0]
                    link = item_title_element.find_element_by_class_name('a-link-normal').get_attribute('href')
                    title = item_title_element.text

                    item_seller_element = item_elements[1].find_element_by_class_name('a-color-secondary')
                    seller = item_seller_element.text.split(': ')[1]
                    print(f'DEBUG seller: {seller}')

                except NoSuchElementException:
                    link = 'not available'
                    title = 'not available'
                    seller = 'not available'
                    print(f'DEBUG seller failed: {date}')

                    item_elements = item_element.find_element_by_class_name('a-col-right') \

                    print("------------------------")
                    print(item_elements[0].text)
                    print("------------------------")
                    break

                try:
                    item_price_str = item_element.find_element_by_class_name('a-color-price').text
                    item_price = price_str_to_float(item_price_str)
                except (NoSuchElementException, ValueError) as e:
                    print(f'Could not parse price for order {link}')
                    item_price = 0.0

                items.append(Item(item_price, link, title, seller))
        orders.append(Order(order_id, order_price, date, items))

    return orders


def get_order_info(order_info_element: WebElement) -> Tuple[str, float, datetime.datetime]:
    order_info_list: List[str] = [info_field.text for info_field in
                                  order_info_element.find_elements_by_class_name('value')]

    # value tags have only generic class names so a constant order in form of:
    # [date, price, recipient_address, order_id] or if no recipient_address is available
    # [date, recipient_address, order_id]
    # is assumed
    if len(order_info_list) < 4:
        order_id = order_info_list[2]
    else:
        order_id = order_info_list[3]

    # price is usually formatted as 'EUR x,xx' but special cases as 'Audible Guthaben' are possible as well
    order_price = order_info_list[1]
    if order_price.find('EUR') != -1:
        order_price = price_str_to_float(order_price)
    else:
        order_price = 0

    date_str = order_info_list[0]
    date = utils.str_to_datetime(date_str)
    return order_id, order_price, date


def navigate_to_orders_page(browser: WebDriver):
    browser.get('https://www.amazon.de/gp/css/order-history?ref_=nav_orders_first')


def complete_sign_in_form(browser: WebDriver, email: str, password: str):
    try:
        email_input = browser.find_element_by_id('ap_email')
        email_input.send_keys(email)

        password_input = browser.find_element_by_id('ap_password')
        password_input.send_keys(password)

        sign_in_input = browser.find_element_by_id('signInSubmit')
        sign_in_input.click()
    except NoSuchElementException:
        print("Error while trying to sign in, couldn't find all needed form elements")


def signed_in_successful(browser: WebDriver) -> bool:
    """ simple check if we are still on the login page
        ToDo probably can be replaced by some better method """
    return browser.current_url != 'https://www.amazon.de/ap/signin'


def skip_adding_phone_number(browser: WebDriver):
    """ find and click the 'skip adding phone number' button if found on the current page """
    try:
        skip_adding_phone_link = browser.find_element_by_id('ap-account-fixup-phone-skip-link')
        skip_adding_phone_link.click()
        print('skipped adding phone number')
    except NoSuchElementException:
        print('no need to skip adding phone number')


def is_next_page_available(browser: WebDriver) -> bool:
    """ as long as the next page button exists there is a next page """
    pagination_element = browser.find_element_by_class_name('a-pagination')
    try:
        return 'Weiter' not in pagination_element.find_element_by_class_name('a-disabled').text
    except NoSuchElementException:
        return True


def is_paging_menu_available(browser: WebDriver):
    """ returns whether there are multiple pages for the current year by searching for a paging menu """
    try:
        return browser.find_element_by_class_name('a-pagination') is not None
    except NoSuchElementException:
        return False


def are_orders_for_year_available(browser: WebDriver):
    return browser.page_source.find('keine Bestellungen aufgegeben') == -1


def price_str_to_float(price_str) -> float:
    return float((price_str[4:]).replace(',', '.'))


def close(browser):
    browser.close()
    quit()


if __name__ == '__main__':
    main()
