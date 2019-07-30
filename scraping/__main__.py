"""
Projects entry point providing command parsing
"""
import datetime
import logging
import sys
from typing import Optional

import click

from . import dash_app, scraping


@click.group()
def main():
    setup_logger()


@main.command()
def dash():
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
def scrape(email: str, password: Optional[str], headless: bool, start: int, end: int, extensive: bool):
    scraping.main(email, password, bool(headless), start, end, extensive)


def setup_logger() -> None:
    """ Setup the logging configuration """
    logging.basicConfig(level=logging.INFO)
    # ToDo replace hardcoded package name, __name__ doesn't work since it contains __main__ if executed as such
    root_logger = logging.getLogger("scraping")
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("[%(asctime)s - %(levelname)s - %(name)s] %(message)s")
    handler.setFormatter(formatter)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


if __name__ == '__main__':
    main()
