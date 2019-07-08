import datetime
import json
from typing import List, Tuple
import argparse

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from src import utils
from src.Data import Order, Item


def main():
    email, password, headless, DEBUG = parse_cli_arguments()

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

    skip_adding_phone_number(browser)

    orders = []
    # order filter option 0 and 1 are already contained in option 2 [3months, 6months, currYear, lastYear, ...]
    # current year - first year + first index
    max_index = datetime.datetime.now().year - 2010 + 2
    if DEBUG: max_index = 3
    for order_filter_index in range(2, max_index):
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

            orders.extend(scrape_page_for_orders(browser))

            if is_paging_menu_available(browser):
                pagination_element = browser.find_element_by_class_name('a-pagination')
            else:
                break

            pages_remaining = is_next_page_available(browser)
            if pages_remaining:
                next_page_link = pagination_element.find_element_by_class_name('a-last') \
                    .find_element_by_css_selector('a').get_attribute('href')
                browser.get(next_page_link)
        print(f'finished year {datetime.datetime.now().year + 2 - order_filter_index}, ({round(
            (order_filter_index - 1.0) / (max_index - 1.0) * 100)}%)')

    utils.save_file('orders.json', json.dumps([order.to_dict() for order in orders]))

    close(browser)


def parse_cli_arguments() -> Tuple[str, str, bool, bool]:
    arg_parser = argparse.ArgumentParser(description='Scrapes your Amazon.de order history')
    arg_parser.add_argument('--email', type=str, help='the users email address')
    arg_parser.add_argument('--password', type=str, help='the users password')
    arg_parser.add_argument('--headless', action='store_true',
                            help='run the browser in headless mode (browser is invisible)')
    arg_parser.add_argument('--debug', action='store_true',
                            help='enables debug mode, only data for one year gets scraped')

    return getattr(arg_parser.parse_args(), 'email'), \
           getattr(arg_parser.parse_args(), 'password'), \
           getattr(arg_parser.parse_args(), 'headless'), \
           getattr(arg_parser.parse_args(), 'debug')


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
                    item_title_element = item_element.find_element_by_class_name('a-col-right') \
                        .find_element_by_class_name('a-row')
                    link = item_title_element.find_element_by_class_name('a-link-normal').get_attribute('href')
                    title = item_title_element.text
                except NoSuchElementException:
                    link = 'not available'
                    title = 'not available'

                try:
                    item_price_str = item_element.find_element_by_class_name('a-color-price').text
                    item_price = price_str_to_float(item_price_str)
                except (NoSuchElementException, ValueError) as e:
                    print(f'Could not parse price for order {link}')
                    item_price = 0.0

                items.append(Item(item_price, link, title))
        orders.append(Order(order_id, order_price, date, items))

    return orders


def get_order_info(order_info_element: WebElement) -> Tuple[str, float, datetime.datetime]:
    order_info_list: List[str] = [info_field.text for info_field in
                                  order_info_element.find_elements_by_class_name('value')]

    # value tags have only generic class names so a constant order is assumed...
    # [date, price, recipient_address, order_id] or if no recipient_address is available
    # [date, recipient_address, order_id]
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


def wait_for_element_by_id(browser: WebDriver, order_id: object, timeout: object = 5) -> object:
    """ wait the specified timout for a element to load """
    try:
        WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.ID, order_id)))
        return True
    except TimeoutException:
        print(f'Loading took too much time! (>{timeout}sec)')
        return False


def wait_for_element_by_class_name(browser: WebDriver, class_name: str, timeout: float = 5) -> bool:
    """ wait the specified timout for a element to load """
    try:
        WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.CLASS_NAME, class_name)))
        return True
    except TimeoutException:
        print(f'Loading took too much time! (>{timeout}sec)')
        return False


def price_str_to_float(price_str) -> float:
    return float((price_str[4:]).replace(',', '.'))


def close(browser):
    browser.close()
    quit()


if __name__ == '__main__':
    main()
