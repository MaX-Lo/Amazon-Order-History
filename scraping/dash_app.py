# -*- coding: utf-8 -*-
from typing import List, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from . import evaluation as eval
from . import file_handler as fh
from .Data import Order

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


def main():
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    orders = fh.load_orders()

    app.layout = html.Div(children=[
        html.H1(children='Amazon Order History - Evaluation'),
        html.Div(children='A web application to analyze different aspects of your amazon orders'),
        gen_amazon_totals_graph(orders),
        gen_stacked_totals_graph(orders)
    ], style={'fontSize': 22})

    app.run_server(debug=True)


def gen_amazon_totals_graph(orders: List[Order]):
    total_by_year_amazon = eval.get_total_by_year(orders)
    data_amazon = [gen_bar(total_by_year_amazon, 'amazon totals')]
    return gen_totals_graph(data_amazon, "Amazon totals by year", "amazon-graph")


def gen_bar(data: Dict, name: str) -> go.Bar:
    return go.Bar(x=list(data.keys()), y=list(data.values()), name=name)


def gen_totals_graph(data, title: str, id: str) -> dcc.Graph:
    fig: go.Figure = go.Figure(data=data)
    fig.update_layout(title_text=title)
    return dcc.Graph(id=id, figure=fig)


def gen_stacked_totals_graph(orders: List[Order]):
    """ generates a graph with each bar subdivided into different categories
        known categories:
            - audible
            - prime instant video
            - ToDo (prime music unlimited)
            - ToDo (prime membership fee)
            - remaining
    """
    fig = go.Figure(data=[
        gen_bar(eval.get_audible_total_by_year(orders), 'audible totals'),
        gen_bar(eval.get_instant_video_per_year(orders), 'prime instant video'),
        gen_bar(eval.get_prime_member_fee_total_by_year(orders), 'amazon prime member fee'),
        gen_bar(eval.get_uncategorized_totals(orders), 'uncategorized'),
    ])

    fig.update_layout(barmode='stack')
    fig.update_layout(title_text='Amazon totals by year, split by categories')
    return dcc.Graph(id='stacked-graph', figure=fig)


if __name__ == '__main__':
    main()
