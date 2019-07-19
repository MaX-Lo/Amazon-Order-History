import datetime
from typing import Optional

import click

from . import dash_app, scraping


@click.group()
def main():
    pass


@main.command()
def dash():
    dash_app.main()


@main.command()
@click.option("--email", required=True, help="The users email address")
@click.option("--password", required=False, default=None, help="the users password")
@click.option("--headless", required=False, default=False,
              help="run the browser in headless mode (browser is invisible")
@click.option("--start", default=2010, help="the year to start with. If not set 2010 is used.")
@click.option("--end", default=datetime.datetime.now().year,
              help="the year to end with. If not set the current year is used.")
def scrape(email: str, password: Optional[str], headless: bool, start: int, end: int):
    scraping.main(email, password, headless, start, end)


if __name__ == '__main__':
    main()
