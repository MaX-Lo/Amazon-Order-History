import datetime
import json
from typing import List, Tuple, Optional, Dict
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from . import utils, file_handler
from .Data import Order, Item
from .utils import wait_for_element_by_class_name, wait_for_element_by_id


def main(email: str, password: Optional[str], headless: bool, start: int, end: int, extensive: bool):
    if password is None:
        password = file_handler.load_password()
        if password == "":
            print("Password not given nor pw.txt found")
            exit(1)

    browser = setup_scraping(headless, email, password)
    orders: List = get_orders(browser, start, end, extensive)

    file_handler.save_file('orders.json', json.dumps([order.to_dict() for order in orders]))

    browser.quit()


def setup_scraping(headless, email, password):
    fp = FirefoxProfile()
    fp.set_preference("browser.tabs.remote.autostart", False)
    fp.set_preference("browser.tabs.remote.autostart.1", False)
    fp.set_preference("browser.tabs.remote.autostart.2", False)
    opts = Options()
    opts.headless = headless
    if opts.headless:
        print("Run in headless mode.")
    browser = Firefox(options=opts, firefox_profile=fp)
    navigate_to_orders_page(browser)
    complete_sign_in_form(browser, email, password)
    if not signed_in_successful(browser):
        print("Couldn't sign in. Maybe your credentials are incorrect?")
        browser.quit()
        exit()
    skip_adding_phone_number(browser)
    return browser


def get_orders(browser: WebDriver, start_year: int, end_year: int, extensive: bool) -> List[Order]:
    """
        get a list of all orders in the given range (start and end year inclusive)
        to save network capacities it is checked if some orders got already fetched earlier in 'orders.json'

        :param browser is a WebDriver pointing to the orders page and having the user logged in already
        :param start_year the year to start with (included)
        :param end_year the year to end with (included)
        :param extensive - if set each items page is opened to scrape its categorization
        """
    orders: List[Order] = []
    last_date: datetime.datetime = datetime.datetime(year=start_year, month=1, day=1)
    end_date: datetime.datetime = datetime.datetime.now() if end_year == datetime.datetime.now().year else \
        datetime.datetime(year=end_year, month=12, day=31)

    if (start_year != 2010 or end_year != datetime.datetime.now().year) and file_handler.file_exists("orders.json"):
        file_handler.remove_file("orders.json")
    else:
        data = file_handler.read_json_file("orders.json")

    if data:
        for order_dict in data:
            orders.append(Order.from_dict(order_dict))
        orders = sorted(orders, key=lambda order: order.date)
        last_date = orders[-1].date

        scraped_orders: List[Order] = scrape_orders(browser, last_date, end_date, extensive)

        # check for intersection of fetched orders
        existing_order_ids = list(map(lambda order: order.order_id, orders))
        new_orders: List[Order] = list(filter(lambda order: order.order_id not in existing_order_ids, scraped_orders))
        orders.extend(new_orders)

    else:
        orders = scrape_orders(browser, last_date, end_date, extensive)

    orders = sorted(orders, key=lambda order: order.date)
    return orders


def scrape_orders(browser: WebDriver, start_date: datetime.datetime, end_date: datetime.datetime, extensive: bool) -> List[Order]:
    """ returns list of all orders in between given start year (inclusive) and end year (inclusive) """
    start_year: int = start_date.year
    end_year: int = end_date.year
    assert start_year <= end_year, "start year must be before end year"
    assert start_year >= 2010, "Amazon order history works only for years after 2009"
    assert end_year <= datetime.datetime.now().year, "End year can not be in the future"
    orders = []

    start_time = time.time()
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

            orders_on_page: List[Order] = scrape_page_for_orders(browser, extensive)
            orders.extend(orders_on_page)

            if len(orders_on_page) > 0 and start_date > orders_on_page[-1].date:
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
        current_year = datetime.datetime.now().year + 2 - order_filter_index
        print_progress(start_year,end_year, current_year, len(orders), start_time)

    return orders


def print_progress(start_year: int, end_year: int, current_year: int, orders_len: int, scraping_start_time):
    already_scraped_years = end_year - current_year + 1
    years_ahead = current_year - start_year

    average_orders_per_year = orders_len / already_scraped_years
    orders_to_do = years_ahead * average_orders_per_year
    orders_percentage = orders_len / (orders_len + orders_to_do) * 100

    time_passed = time.time() - scraping_start_time
    average_time_per_year = time_passed / already_scraped_years
    end_time = time.time() + average_time_per_year * years_ahead
    approximated_time_to_end = end_time - scraping_start_time
    print_time = str(datetime.timedelta(seconds=approximated_time_to_end))

    print(f'Finished {current_year} / {orders_percentage}%. Approximately finished in {print_time}')


def scrape_page_for_orders(browser: WebDriver, extensive: bool) -> List[Order]:
    """ get a list of all orders found on the currently open page """
    orders = []
    for order_element in browser.find_elements_by_class_name('order'):

        wait_for_element_by_class_name(order_element, 'order-info', timeout=3)
        order_info_element = order_element.find_element_by_class_name('order-info')
        order_id, order_price, date = get_order_info(order_info_element)

        items = []
        # looking in an order there is a 'a-box' for order_info and and 'a-box' for each seller containing detailed
        # items info
        for items_by_seller in order_element.find_elements_by_class_name('a-box')[1:]:
            for item_element in items_by_seller.find_elements_by_class_name('a-fixed-left-grid'):
                seller = get_item_seller(item_element)
                title, link = get_item_title(item_element)
                item_price = order_price if is_digital_order(order_id) else \
                    get_item_price(item_element, order_element, browser)
                categories = get_item_categories(link, browser) if extensive else dict()

                items.append(Item(item_price, link, title, seller, categories))

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


def get_item_seller(item_element) -> str:
    try:
        seller = item_element.text.split('durch: ')[1]
        seller = seller.split('\n')[0]
        return seller
    except IndexError:
        return 'not available'


def get_item_title(item_element) -> (str, str):
    item_elements = item_element.find_element_by_class_name('a-col-right') \
        .find_elements_by_class_name('a-row')
    item_title_element = item_elements[0]
    title = item_title_element.text
    try:
        link = item_title_element.find_element_by_class_name('a-link-normal').get_attribute('href')
    except NoSuchElementException:
        link = 'not available'

    return title, link


def get_item_price(item_element: WebElement, order_element: WebElement, browser: WebDriver) -> float:
    try:
        item_price_str = item_element.find_element_by_class_name('a-color-price').text
        item_price = price_str_to_float(item_price_str)
    except (NoSuchElementException, ValueError) as e:
        item_price = get_item_price_through_details_page(order_element, browser)

    return item_price


def get_item_price_through_details_page(order_element: WebElement, browser: WebDriver) -> float:
    item_price = 0
    try:
        order_details_link = order_element.find_element_by_class_name('a-link-normal').get_attribute('href')

        browser.execute_script(f'''window.open("{order_details_link}","_blank");''')
        browser.switch_to.window(browser.window_handles[1])
        wait_for_element_by_id(browser, 'od-subtotals')

        order_price_details = browser.find_element_by_id('od-subtotals')
        order_price_details = order_price_details.text.split("Summe:")[1]
        order_price_details = order_price_details.split(" ")[1]

        item_price = order_price_details.split("\n")[0]

        browser.close()
        browser.switch_to.window(browser.window_handles[0])

    except (NoSuchElementException, ValueError) as e:
        item_price = 0
        browser.close()
        browser.switch_to.window(browser.window_handles[0])
        print(f'Could not parse price for order:\n{order_element.text}')

    finally:
        return item_price


def get_item_categories(item_link: str, browser: WebDriver) -> Dict[int, str]:
    categories = dict()

    browser.execute_script(f'''window.open("{item_link}","_blank");''')
    browser.switch_to.window(browser.window_handles[1])

    if not utils.wait_for_element_by_id(browser, 'wayfinding-breadcrumbs_container'):
        browser.close()
        browser.switch_to.window(browser.window_handles[0])
        return categories

    categories_element = browser.find_element_by_id('wayfinding-breadcrumbs_container')
    for index, category_element in enumerate(categories_element.find_elements_by_class_name("a-list-item")):
        element_is_separator = index % 2 == 1
        if element_is_separator:
            continue
        depth = index // 2 + 1
        categories[depth] = category_element.text

    browser.close()
    browser.switch_to.window(browser.window_handles[0])

    return categories


def navigate_to_orders_page(browser: WebDriver):
    browser.get('https://www.amazon.de/gp/css/order-history?ref_=nav_orders_first')


def complete_sign_in_form(browser: WebDriver, email: str, password: str):
    try:
        email_input = browser.find_element_by_id('ap_email')
        email_input.send_keys(email)

        password_input = browser.find_element_by_id('ap_password')
        password_input.send_keys(password)

        browser.find_element_by_name('rememberMe').click()

        sign_in_input = browser.find_element_by_id('signInSubmit')
        sign_in_input.click()
    except NoSuchElementException:
        print("Error while trying to sign in, couldn't find all needed form elements")


def signed_in_successful(browser: WebDriver) -> bool:
    """ simple check if we are still on the login page """
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


def is_digital_order(order_id):
    return order_id[:3] == 'D01'


def price_str_to_float(price_str) -> float:
    return float((price_str[4:]).replace(',', '.'))
