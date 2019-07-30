# -*- coding: utf-8 -*-
# pylint: disable=C0111
# pylint: disable=C0330

import copy
from typing import Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from scraping.CustomExceptions import OrdersNotFound
from scraping.evaluation import Evaluation
from . import evaluation
from . import file_handler as fh

LAYOUT = dict(
    autosize=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)


def main() -> None:
    app = dash.Dash(__name__)

    orders = fh.load_orders()
    if not orders:
        raise OrdersNotFound
    evaluated = evaluation.Evaluation(orders)

    app.layout = html.Div(
        children=[
            head(),
            html.Div(
                [
                    general_information(evaluated),
                    gen_stacked_totals_graph(evaluated)
                ],
                className="row flex-display"
            ),
            html.Div(
                gen_scatter_by_month_graph(evaluated),
                className="row flex-display"
            ),
            html.Div(
                gen_one_bar_graph(evaluated),
                className="row flex-display"
            )
        ],
        id="mainContainer"
    )

    app.run_server(debug=True)


def head() -> html.Div:
    return html.Div(
        [
            html.H3(
                "Amazon Order History",
                style={"margin-bottom": "0px"},
            ),
            html.H5(
                "Evaluation", style={"margin-top": "0px"}
            ),
        ],
        className="column",
        id="title",
    )


def general_information(evaluated: Evaluation) -> html.Div:
    return html.Div([
        html.Div(
            [f" {evaluated.get_total()}€", html.H6("Amazon (all)")],
            className='mini_container'
        ),
        html.Div(
            [f"{evaluated.get_audible_total()}€", html.H6("Audible")],
            className='mini_container'
        ),
        html.Div(
            [f"{evaluated.get_instant_video_total()}€", html.H6("Prime Instant Video")],
            className='mini_container'
        ),
        html.Div(
            [f"{evaluated.get_most_expensive_order()[0].price}€", html.H6("max order price")],
            className='mini_container'
        ),
        html.Div(
            [f"{len(evaluated.get_orders_with_most_items()[0].items)} items", html.H6("largest order")],
            className='mini_container'
        ),
        html.Div(
            [f"{evaluated.get_order_count()}", html.H6("Orders")],
            className='mini_container'
        ),
        html.Div(
            [f"{evaluated.get_item_count()}", html.H6("Items")],
            className='mini_container'
        ),

    ],
        className="two columns",
    )


def gen_bar(data: Dict, name: str) -> go.Bar:
    return go.Bar(x=list(data.keys()), y=list(data.values()), name=name)


def gen_scatter(data: Dict, name: str) -> dcc.Graph:
    return go.Scatter(x=list(data.keys()), y=list(data.values()), name=name)


def gen_stacked_totals_graph(evaluated: Evaluation) -> html.Div:
    """ generates a graph with each bar subdivided into different categories
        - ToDo (prime music unlimited)
        - ToDo (prime membership fee)
    """
    fig = go.Figure(data=[
        gen_bar(evaluated.audible_total_by_year(), 'audible'),
        gen_bar(evaluated.instant_video_total_per_year(), 'prime instant video'),
        gen_bar(evaluated.prime_member_fee_by_year(), 'amazon prime member fee'),
        gen_bar(evaluated.added_balance_per_year(), 'balance added'),
        gen_bar(evaluated.uncategorized_totals_per_year(), 'uncategorized'),
    ], layout=copy.deepcopy(LAYOUT))

    fig.update_layout(
        barmode='stack',
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(title='Year', titlefont_size=18, tickfont_size=16),
        legend=dict(font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
        height=600,
        title="Amazon totals by year, split by categories",
        titlefont={"size": 20}
    )

    fig.update_xaxes(dtick=1.0)

    return html.Div(
        dcc.Graph(id='count_graph', figure=fig),
        id="right-column",
        className="pretty_container ten columns"
    )


def gen_scatter_by_month_graph(evaluated: Evaluation) -> html.Div:
    """ generates a line graph with spend amount for each month """

    fig = go.Figure(data=[
        gen_scatter(evaluated.totals_by_month(), 'total'),
        gen_scatter(evaluated.trend_by_month(), 'trend')
    ], layout=copy.deepcopy(LAYOUT))

    fig.update_layout(
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(titlefont_size=18, tickfont_size=16),
        legend=dict(font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
        title="Amazon totals by month",
        titlefont={"size": 20}
    )

    return html.Div(
        dcc.Graph(id='scatter-graph', figure=fig),
        className="pretty_container twelve columns"
    )


def gen_one_bar_graph(evaluated: Evaluation) -> html.Div:

    category_sums = evaluated.total_by_level_1_category()
    total = sum(category_sums.values())
    percentages = {category[0]: category[1] / total * 100 for category in category_sums.items()}

    data = [go.Bar(name=category[0], x=[category[1]], y=[1], orientation='h') for category in percentages.items()]

    fig = go.Figure(
        data=data,
        layout=copy.deepcopy(LAYOUT)
    )

    fig.update_layout(
        barmode='stack',
        yaxis=dict(tickfont_size=16, showticklabels=False),
        xaxis=dict(tickfont_size=16, ticksuffix="%"),
        legend=dict(font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
        # height=600,
        title="Totals split by level 1 categories",
        titlefont={"size": 20,},
    )

    return html.Div(
        dcc.Graph(id='bar-graph', figure=fig),
        className="pretty_container twelve columns"
    )


if __name__ == '__main__':
    main()
