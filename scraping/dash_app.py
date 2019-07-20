# -*- coding: utf-8 -*-
import copy
from typing import List, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from . import evaluation as eval
from . import file_handler as fh
from .Data import Order

layout = dict(
    autosize=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)


def main():
    app = dash.Dash(__name__)

    orders = fh.load_orders()

    app.layout = html.Div(
        children=[
            head(),
            html.Div(
                [
                    general_information(orders),
                    gen_stacked_totals_graph(orders)
                ],
                className="row flex-display"
            ),
            html.Div(
                gen_scatter_by_month_graph(orders),
                className="row flex-display"
            )
        ],
        id="mainContainer"
    )

    app.run_server(debug=True)


def head():
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


def general_information(orders: List[Order]) -> html.Div:
    return html.Div([
        html.Div(
            [f" {eval.get_total(orders)}€", html.H6("Amazon (all)")],
            className='mini_container'
        ),
        html.Div(
            [f"{eval.get_audible_total(orders)}€", html.H6("Audible")],
            className='mini_container'
        ),
        html.Div(
            [f"{eval.get_instant_video_total(orders)}€", html.H6("Prime Instant Video")],
            className='mini_container'
        ),
        html.Div(
            [f"{eval.get_most_expensive_order(orders)[0].price}€", html.H6("max order price")],
            className='mini_container'
        ),
        html.Div(
            [f"{len(eval.get_orders_with_most_items(orders)[0].items)} items", html.H6("largest order")],
            className='mini_container'
        ),
        html.Div(
            [f"{eval.get_order_count(orders)}", html.H6("Orders")],
            className='mini_container'
        ),
        html.Div(
            [f"{eval.get_item_count(orders)}", html.H6("Items")],
            className='mini_container'
        ),

    ],
        className="two columns",
    )


def gen_bar(data: Dict, name: str) -> go.Bar:
    return go.Bar(x=list(data.keys()), y=list(data.values()), name=name)


def gen_scatter(data: Dict, name: str) -> dcc.Graph:
    return go.Scatter(x=list(data.keys()), y=list(data.values()), name=name)


def gen_stacked_totals_graph(orders: List[Order]) -> html.Div:
    """ generates a graph with each bar subdivided into different categories
        - ToDo (prime music unlimited)
        - ToDo (prime membership fee)
    """
    fig = go.Figure(data=[
        gen_bar(eval.audible_total_by_year(orders), 'audible'),
        gen_bar(eval.instant_video_total_per_year(orders), 'prime instant video'),
        gen_bar(eval.prime_member_fee_by_year(orders), 'amazon prime member fee'),
        gen_bar(eval.added_balance_per_year(orders), 'balance added'),
        gen_bar(eval.uncategorized_totals_per_year(orders), 'uncategorized'),
    ], layout=copy.deepcopy(layout))

    fig.update_layout(
        barmode='stack',
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(title='Year', titlefont_size=18, tickfont_size=16),
        legend=dict(x=1.0, y=1.0, font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
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


def gen_scatter_by_month_graph(orders: List[Order]) -> html.Div:
    """ generates a line graph with spend amount for each month """
    totals_by_month = eval.totals_by_month(orders)

    fig = go.Figure(data=[
        gen_scatter(totals_by_month, 'total'),
        gen_scatter(eval.trend_by_month(totals_by_month), 'trend')
    ], layout=copy.deepcopy(layout))

    fig.update_layout(
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(titlefont_size=18, tickfont_size=16),
        legend=dict(x=1.0, y=1.0, font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
        title="Amazon totals by month",
        titlefont={"size": 20}
    )

    return html.Div(
        dcc.Graph(id='scatter-graph', figure=fig),
        className="pretty_container twelve columns"
    )


if __name__ == '__main__':
    main()
