from typing import List
import argparse

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.Order import Order


def main():

    email, password = parse_cli_arguments()

    opts = Options()
    # opts.headless = True
    # assert opts.headless
    browser = Firefox(options=opts)

    navigate_to_orders_page(browser)

    complete_sign_in_form(browser, email, password)

    if not signed_in_successfull(browser):
        print("Couldn't sign in. Maybe your credentials are incorrect?")
        close(browser)

    skip_adding_phone_number(browser)

    orders = []

    # order filter option 2 contains allready all order of option 0 and 1
    for index_order_filter in range(2, 5):
        # open the dropdown

        wait_for_element_by_id(browser, 'a-autoid-1-announce')
        browser.find_element_by_id('a-autoid-1-announce').click()

        # select and click on a order filter
        id_order_filter = f'orderFilter_{index_order_filter}'
        dropdown_element = browser.find_element_by_id(id_order_filter)
        dropdown_element.click()

        pages_remaining = True
        while pages_remaining:

            orders.append(scrape_page_for_orders(browser))

            pagination_element = browser.find_element_by_class_name('a-pagination')

            pages_remaining = is_next_page_available(browser)
            if pages_remaining:
                next_page_link = pagination_element.find_element_by_class_name('a-last')\
                    .find_element_by_css_selector('a').get_attribute('href')
                browser.get(next_page_link)

    print(orders)

    close(browser)


def parse_cli_arguments():
    arg_parser = argparse.ArgumentParser(description='Scrapes your Amazon.de order history')
    arg_parser.add_argument('--email', type=str, help='the users email adress')
    arg_parser.add_argument('--password', type=str, help='the users password')

    return getattr(arg_parser.parse_args(), 'email'), getattr(arg_parser.parse_args(), 'password')


def navigate_to_orders_page(browser):
    browser.get('https://www.amazon.de/gp/css/order-history?ref_=nav_orders_first')


def complete_sign_in_form(browser, email, password):
    try:
        email_input = browser.find_element_by_id('ap_email')
        email_input.send_keys(email)

        passwort_input = browser.find_element_by_id('ap_password')
        passwort_input.send_keys(password)

        sign_in_input = browser.find_element_by_id('signInSubmit')
        sign_in_input.click()
    except NoSuchElementException:
        print("Error while trying to sign in, couldn't find all needed form elements")

def signed_in_successfull(browser):
    """ simple check if we are still on the login page
        ToDo propably can be replaced by some better method """
    return browser.current_url != 'https://www.amazon.de/ap/signin'

def skip_adding_phone_number(browser):
    """ find and click the 'skip adding phone number' button if found on the current page """
    try:
        skip_adding_phone_link = browser.find_element_by_id('ap-account-fixup-phone-skip-link')
        skip_adding_phone_link.click()
        print('skipped adding phone number')
    except NoSuchElementException:
        print('no need to skip adding phone number')


def scrape_page_for_orders(browser) -> List[Order]:
    """ get a list of all orders found on the currently open page """
    orders = []
    for order_element in browser.find_elements_by_class_name('order'):

        wait_for_element_by_class_name(order_element, 'order-info', timeout=3)
        order_info_element = order_element.find_element_by_class_name('order-info')
        order_info_list = [info_field.text for info_field in order_info_element.find_elements_by_class_name('value')]

        # value tags have only generic class names so a constant order is assumed...
        # [date, price, recipient_address, order_id] or if no recipient_address is available
        # [date, recipient_address, order_id]
        if len(order_info_list) < 4:
            id = order_info_list[2]
        else:
            id = order_info_list[3]

        # price is usually formated as 'EUR x,xx' but special cases as 'Audible Guthaben' are possible as well
        price = order_info_list[1]
        if price.find('EUR'):
            price = price[4:]
        else:
            price = 0
            title = price

        date = order_info_list[0]

        try:
            order_shipment_element = order_element.find_element_by_class_name('shipment')
            order_title_element = order_shipment_element.find_element_by_class_name('a-link-normal')

            title = order_title_element.get_attribute('href')
        except NoSuchElementException:
            print(f'no title for "{id}" available')
            title = 'not available'

        orders.append(Order(id, price, date, title))
    return orders


def is_next_page_available(browser):
    """ as long as the next page button exists there is a next page """
    pagination_element = browser.find_element_by_class_name('a-pagination')
    try:
        print(pagination_element.find_element_by_class_name('a-disabled').text)
        return 'Weiter' not in pagination_element.find_element_by_class_name('a-disabled').text
    except NoSuchElementException:
        return True


def wait_for_element_by_id(browser, id: str, timeout: float = 5) -> bool:
    """ wait the specified timout for a element to load """
    try:
        WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.ID, id)))
        return True
    except TimeoutException:
        print(f'Loading took too much time! (>{timeout}sec)')
        return False


def wait_for_element_by_class_name(browser, class_name: str, timeout: float = 5) -> bool:
    """ wait the specified timout for a element to load """
    try:
        WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        return True
    except TimeoutException:
        print("Loading took too much time!")
        return False

def close(browser):
    browser.close()
    quit()

if __name__ == '__main__':
    main()
