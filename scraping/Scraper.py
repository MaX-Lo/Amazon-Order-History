"""
downloads and parses the data from amazon.de to store it in a orders.json file
"""
# pylint: disable=R0913
import datetime
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from . import file_handler
from .data import Order, Item
from . import utils as ut

FILE_NAME: str = "orders.json"


@dataclass
class Scraper:
    """
    Scrapping instance, scrapes all Orders in the given year range and outputs it into FILE_NAME
    """
    email: str
    password: Optional[str]
    headless: bool
    start_year: int
    end_year: int
    extensive: bool

    def __post_init__(self) -> None:
        assert self.email, "no email provided"
        assert '@' in self.email and '.' in self.email, "no correct email layout"
        assert self.start_year <= self.end_year, "start year must be before end year"
        assert self.start_year >= 2010, "Amazon order history works only for years after 2009"
        assert self.end_year <= datetime.datetime.now().year, "End year can not be in the future"

        self.orders: List[Order] = []
        self.browser: WebDriver
        self.start_date: datetime.date = datetime.date(year=self.start_year, month=1, day=1)
        self.end_date: datetime.date = datetime.datetime.now().date() if self.end_year == datetime.datetime.now().year \
            else datetime.date(year=self.end_year, month=12, day=31)

        self._get_password()
        self._setup_scraping()
        self._get_orders()

        file_handler.save_file(FILE_NAME, json.dumps([order.to_dict() for order in self.orders]))
        self.browser.quit()

    def _get_password(self) -> None:
        """
        checks if the password was given or if the pw.txt file exists and contains a password
        Exit(1) if none of these cases appear
        :return:
        """
        if not self.password:
            self.password = file_handler.load_password()
            if not self.password:
                print("Password not given nor pw.txt found")
                exit(1)

    def _setup_scraping(self) -> None:
        """
        prepares the WebDriver for scraping the data by:
            - setting up the WebDrive
            - log in the user with the given credentials
            - skipping the adding phone number dialog (should it appear)
         """
        firefox_profile = FirefoxProfile()
        firefox_profile.set_preference("browser.tabs.remote.autostart", False)
        firefox_profile.set_preference("browser.tabs.remote.autostart.1", False)
        firefox_profile.set_preference("browser.tabs.remote.autostart.2", False)
        opts = Options()
        opts.headless = self.headless
        if opts.headless:
            print("Run in headless mode.")
        self.browser = Firefox(options=opts, firefox_profile=firefox_profile)
        self._navigate_to_orders_page()
        self._complete_sign_in_form()
        if not self._signed_in_successful():
            print("Couldn't sign in. Maybe your credentials are incorrect?")
            self.browser.quit()
            exit(1)
        self._skip_adding_phone_number()

    def _navigate_to_orders_page(self) -> None:
        """
        navigates to the orders page
        """
        self.browser.get('https://www.amazon.de/gp/css/order-history?ref_=nav_orders_first')

    def _complete_sign_in_form(self) -> None:
        """ searches for the sign in form enters the credentials and confirms
            if successful amazon redirects the browser to the previous site """
        try:
            email_input = self.browser.find_element_by_id('ap_email')
            email_input.send_keys(self.email)

            password_input = self.browser.find_element_by_id('ap_password')
            password_input.send_keys(self.password)

            self.browser.find_element_by_name('rememberMe').click()

            sign_in_input = self.browser.find_element_by_id('signInSubmit')
            sign_in_input.click()
        except NoSuchElementException:
            print("Error while trying to sign in, couldn't find all needed form elements")

    def _signed_in_successful(self) -> bool:
        """ simple check if we are still on the login page """
        return self.browser.current_url != 'https://www.amazon.de/ap/signin'

    def _skip_adding_phone_number(self) -> None:
        """ find and click the 'skip adding phone number' button if found on the current page """
        try:
            skip_adding_phone_link = self.browser.find_element_by_id('ap-account-fixup-phone-skip-link')
            skip_adding_phone_link.click()
            print('skipped adding phone number')
        except NoSuchElementException:
            print('no need to skip adding phone number')

    def _is_custom_date_range(self) -> bool:
        """
        :param start: start date
        :param end: end date
        :return: whether the maximum date range is used or a custom user set range
        """
        return self.start_year != 2010 or self.end_year != datetime.datetime.now().year

    def _are_orders_for_year_available(self) -> bool:
        """
        checks if there are any orders in the current selected year
        :return: True if there were orders, False if not
        """
        return self.browser.page_source.find('keine Bestellungen aufgegeben') == -1 # No error!

    def _is_next_page_available(self) -> bool:
        """
        as long as the next page button exists there is a next page
        :return: True if there is a next page, False if not"""
        pagination_element = self.browser.find_element_by_class_name('a-pagination')
        try:
            return 'Weiter' not in pagination_element.find_element_by_class_name('a-disabled').text
        except NoSuchElementException:
            return True

    @staticmethod
    def _is_digital_order(order_id: str) -> bool:
        """
        checks if the order is digital (e.g. Amazon Video or Audio Book)
        :param order_id: the id of the order to check
        :return: True if order is digital, False if not
        """
        return order_id[:3] == 'D01'

    def _is_paging_menu_available(self) -> bool:
        """
        :returns: whether there are multiple pages for the current year by searching for a paging menu
        """
        try:
            return self.browser.find_element_by_class_name('a-pagination') is not None
        except NoSuchElementException:
            return False

    def _get_orders(self):
        """
        get a list of all orders in the given range (start and end year inclusive)
        to save network capacities it is checked if some orders got already fetched earlier in 'orders.json'

        :returns: List of all Orders
        """
        if self._is_custom_date_range():
            file_handler.remove_file(FILE_NAME)
            data = None
        else:
            data = file_handler.read_json_file(FILE_NAME)

        if data:
            for order_dict in data:
                self.orders.append(Order.from_dict(order_dict))
            self._scrape_partial()
        else:
            self._scrape_complete()
        self.orders = sorted(self.orders, key=lambda order: order.date)

    def _get_order_info(self, order_info_element: WebElement) -> Tuple[str, float, datetime.date]:
        """
        :param order_info_element:
        :returns: the OrderID, price and date
        """
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
        order_price_str = order_info_list[1]
        if order_price_str.find('EUR') != -1:
            order_price = self._price_str_to_float(order_price_str)
        else:
            order_price = 0

        date_str = order_info_list[0]
        date = ut.str_to_date(date_str)
        return order_id, order_price, date

    def _scrape_complete(self) -> None:
        """
        scrapes all the data without checking for duplicates (when some orders already exist)
        """
        self.orders = self._scrape_orders(self.start_date)

    def _scrape_partial(self) -> None:
        """ scrape data until finding duplicates, at which point the scraping can be canceled since the rest
         is already there """
        self.orders = sorted(self.orders, key=lambda order: order.date)
        last_date = self.orders[-1].date

        scraped_orders: List[Order] = self._scrape_orders(last_date)

        # check for intersection of fetched orders
        existing_order_ids = list(map(lambda order: order.order_id, self.orders))
        new_orders: List[Order] = list(filter(lambda order: order.order_id not in existing_order_ids, scraped_orders))
        self.orders.extend(new_orders)

    def _scrape_orders(self, start_date: datetime.date) -> List[Order]:
        """
        :returns: a list of all orders in between given start year (inclusive) and end year (inclusive)
        """
        start_time = time.time()
        orders: List[Order] = []
        # order filter option 0 and 1 are already contained in option 2 [3months, 6months, currYear, lastYear, ...]
        start_index = 2 + (datetime.datetime.now().year - self.end_year)
        end_index = 2 + (datetime.datetime.now().year - start_date.year) + 1

        for order_filter_index in range(start_index, end_index):
            # open the dropdown
            ut.wait_for_element_by_id(self.browser, 'a-autoid-1-announce')
            self.browser.find_element_by_id('a-autoid-1-announce').click()

            # select and click on a order filter
            id_order_filter = f'orderFilter_{order_filter_index}'
            ut.wait_for_element_by_id(self.browser, id_order_filter)
            dropdown_element = self.browser.find_element_by_id(id_order_filter)
            dropdown_element.click()

            pages_remaining = self._are_orders_for_year_available()
            while pages_remaining:

                orders_on_page: List[Order] = self._scrape_page_for_orders()
                orders.extend(orders_on_page)

                if orders_on_page and start_date > orders_on_page[-1].date:
                    break
                if self._is_paging_menu_available():
                    pagination_element = self.browser.find_element_by_class_name('a-pagination')
                else:
                    break

                pages_remaining = self._is_next_page_available()
                if pages_remaining:
                    next_page_link = pagination_element.find_element_by_class_name('a-last') \
                        .find_element_by_css_selector('a').get_attribute('href')
                    self.browser.get(next_page_link)
            current_year = datetime.datetime.now().year + 2 - order_filter_index
            self._print_progress(orders=orders, start_year=start_date.year, current_year=current_year,
                                 scraping_start_time=start_time)
        return orders

    def _scrape_page_for_orders(self) -> List[Order]:
        """ :returns a list of all orders found on the currently open page """
        orders = []
        for order_element in self.browser.find_elements_by_class_name('order'):

            ut.wait_for_element_by_class_name(order_element, 'order-info', timeout=3)
            order_info_element = order_element.find_element_by_class_name('order-info')
            order_id, order_price, date = self._get_order_info(order_info_element)

            items = []
            # looking in an order there is a 'a-box' for order_info and and 'a-box' for each seller containing detailed
            # items info
            for items_by_seller in order_element.find_elements_by_class_name('a-box')[1:]:

                for index, item_element in enumerate(items_by_seller.find_elements_by_class_name('a-fixed-left-grid')):
                    seller = self._get_item_seller(item_element)
                    title, link = self._get_item_title(item_element)
                    item_price = order_price if self._is_digital_order(order_id) else \
                        self._get_item_price(item_element, index, order_element)
                    categories = self._get_item_categories(link) if self.extensive else dict()

                    items.append(Item(item_price, link, title, seller, categories))

            orders.append(Order(order_id, order_price, date, items))

        return orders

    @staticmethod
    def _get_item_seller(item_element: WebElement) -> str:
        """
        :param item_element: the item div
        :return: returns the seller
        """
        try:
            seller_raw: str = item_element.text.split('durch: ')[1]
            seller: str = seller_raw.split('\n')[0]
            return seller
        except IndexError:
            return 'not available'

    @staticmethod
    def _get_item_title(item_element: WebElement) -> Tuple[str, str]:
        """
        :param item_element: the item div
        :return: returns the title and link of an item
        """
        item_elements = item_element.find_element_by_class_name('a-col-right') \
            .find_elements_by_class_name('a-row')
        item_title_element = item_elements[0]
        title = item_title_element.text
        try:
            link = item_title_element.find_element_by_class_name('a-link-normal').get_attribute('href')
        except NoSuchElementException:
            link = 'not available'

        return title, link

    def _get_item_price(self, item_element: WebElement, item_index: int, order_element: WebElement) -> float:
        """
        :param item_element: the item div
        :param item_index: the index of the item in the order
        :param order_element: the order div
        :return: returns the price of an item
        """
        try:
            item_price_str = item_element.find_element_by_class_name('a-color-price').text
            item_price = self._price_str_to_float(item_price_str)
        except (NoSuchElementException, ValueError):
            item_price = self._get_item_price_through_details_page(order_element, item_index)

        return item_price

    def _get_item_price_through_details_page(self, order_element: WebElement, item_index: int) -> float:
        """
        :param order_element: the order div
        :param item_index: the index of the item in the order
        :returns: the item price found on the order details page
        """
        item_price: float = 0

        try:
            order_details_link = order_element.find_element_by_class_name('a-link-normal').get_attribute('href')

            self.browser.execute_script(f'''window.open("{order_details_link}","_blank");''')
            self.browser.switch_to.window(self.browser.window_handles[1])
            if not ut.wait_for_element_by_class_name(self.browser, 'od-shipments'):
                return item_price

            od_shipments_element = self.browser.find_element_by_class_name('od-shipments')
            price_fields: List[WebElement] = od_shipments_element.find_elements_by_class_name('a-color-price')
            print([self._price_str_to_float(price.text) for price in price_fields])
            item_price = self._price_str_to_float(price_fields[item_index].text)

        except (NoSuchElementException, ValueError):
            item_price = 0
            print(f'Could not parse price for order:\n{order_element.text}')

        finally:
            self.browser.close()
            self.browser.switch_to.window(self.browser.window_handles[0])
        return item_price

    def _get_item_categories(self, item_link: str) -> Dict[int, str]:
        """
        :param item_link: the link to the item itself
        :returns: a dict with the categories and the importance as key
        """
        categories: Dict[int, str] = dict()

        self.browser.execute_script(f'''window.open("{item_link}","_blank");''')
        self.browser.switch_to.window(self.browser.window_handles[1])

        if ut.wait_for_element_by_id(self.browser, 'wayfinding-breadcrumbs_container'):
            categories = self._get_item_categories_from_normal()
            self.browser.close()
            self.browser.switch_to.window(self.browser.window_handles[0])
            return categories

        if ut.wait_for_element_by_class_name(self.browser, 'dv-dp-node-meta-info'):
            categories = self._get_item_categories_from_video()
            self.browser.close()
            self.browser.switch_to.window(self.browser.window_handles[0])
            return categories

        self.browser.close()
        self.browser.switch_to.window(self.browser.window_handles[0])

        return categories

    def _get_item_categories_from_normal(self) -> Dict[int, str]:
        """
        :return: the categories for a normal ordered item
        """
        categories = dict()
        categories_element = self.browser.find_element_by_id('wayfinding-breadcrumbs_container')
        for index, category_element in enumerate(categories_element.find_elements_by_class_name("a-list-item")):
            element_is_separator = index % 2 == 1
            if element_is_separator:
                continue
            depth = int(index // 2 + 1)
            categories[depth] = category_element.text
        return categories

    def _get_item_categories_from_video(self) -> Dict[int, str]:
        """
        :return: the genre of a movie as categories
        """
        categories = dict()
        text: str = self.browser.find_element_by_class_name('dv-dp-node-meta-info').text
        genre = text.split("\n")[0]
        genre_list: List[str] = genre.split(", ")
        genre_list[0] = genre_list[0].split(" ")[1]
        for index, genre in enumerate(genre_list):
            categories[index] = genre

        categories[len(genre_list)] = 'movie'
        return categories

    @staticmethod
    def _price_str_to_float(price_str: str) -> float:
        """
        converts the price str to a float value
        :param price_str: the price in string format as it is scraped
        :return: the price as float
        """
        return float((price_str[4:]).replace(',', '.'))

    def _print_progress(self, orders: List[Order], start_year: int, current_year: int,
                        scraping_start_time: float) -> None:
        """ prints the progress to console and the approximated time to finish """
        already_scraped_years = self.end_year - current_year + 1
        years_ahead = current_year - start_year

        average_orders_per_year = len(orders) / already_scraped_years
        orders_to_do = years_ahead * average_orders_per_year
        orders_percentage = len(orders) / (len(orders) + orders_to_do) * 100

        time_passed = time.time() - scraping_start_time
        average_time_per_year = time_passed / already_scraped_years
        end_time = time.time() + average_time_per_year * years_ahead
        approximated_time_to_end = end_time - scraping_start_time
        print_time = str(datetime.timedelta(seconds=approximated_time_to_end))

        print(f'Finished {current_year} / {orders_percentage}%. Approximately finished in {print_time}')
