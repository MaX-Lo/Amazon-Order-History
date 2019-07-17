import datetime
from typing import Optional

import click

from . import evaluation, dash_app, scraping


@click.group()
def main():
    pass


@main.command()
def dash():
    dash_app.main()


@main.command()
def eval():
    evaluation.main()


@main.command()
@click.option("--email", required=True, help="The users email address")
@click.option("--password", required=False, default=None)
@click.option("--headless", required=False, default=False)
@click.option("--start", default=2010)
@click.option("--end", default=datetime.datetime.now().year)
def scrape(email: str, password: Optional[str], headless: bool, start: int, end: int):
    scraping.main(email, password, headless, start, end)


if __name__ == '__main__':
    main()
