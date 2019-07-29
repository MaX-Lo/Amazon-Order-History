"""
Projects entry point providing command parsing
"""

# pylint: disable=R0913
import datetime
from typing import Optional

import click

from . import dash_app, scraping
from .Scraper import Scraper


@click.group()
def main() -> None:
    """ main entry point of the application """
    pass


@main.command()
def dash() -> None:
    """ creates a dash app to visualize the evaluated scraping output """
    dash_app.main()

#@click.option("--password", required=False, default=None, hide_input=True, prompt=True, help="the users password")
@main.command()
@click.option("--email", required=True, help="The users email address")
@click.option("--password", required=False, default=None, help="the users password")
@click.option("--headless/--no-headless", required=False, default=False,
              help="run the browser in headless mode (browser is invisible")
@click.option("--start", default=2010, help="the year to start with. If not set 2010 is used.")
@click.option("--end", default=datetime.datetime.now().year,
              help="the year to end with. If not set the current year is used.")
@click.option("--extensive", default=True,
              help="if set to False categorization for items isn't available, but scraping itself should be faster")
def scrape(email: str, password: Optional[str], headless: bool, start: int, end: int, extensive: bool) -> None:
    """ starts the scraping process and collects all data """
    Scraper(email, password, bool(headless), start, end, extensive)


if __name__ == '__main__':
    main()
