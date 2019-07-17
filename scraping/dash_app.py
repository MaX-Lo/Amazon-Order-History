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

    add_total_plots(app, orders)

    app.run_server(debug=True)


def add_total_plots(app: dash.Dash, orders: List[Order]):
    total_by_year_amazon = eval.get_total_by_year(orders)
    total_by_year_audible = eval.get_audible_total_by_year(orders)
    total_by_year_instant_video = eval.get_instant_video_per_year(orders)

    data_amazon = [go.Bar(
        x=list(total_by_year_amazon.keys()),
        y=list(total_by_year_amazon.values()),
        name='amazon total'
    )]

    data_audible = [go.Bar(
        x=list(total_by_year_audible.keys()),
        y=list(total_by_year_audible.values()),
        name='amazon total'
    )]

    data_instant_video = [go.Bar(
        x=list(total_by_year_instant_video.keys()),
        y=list(total_by_year_instant_video.values()),
        name='amazon total'
    )]

    app.layout = html.Div(children=[
        html.H1(children='Amazon Order History - Evaluation'),

        html.Div(children='''
                A web application to analyze different aspects of your amazon orders
            '''),

        dcc.Graph(
            id='amazon-graph',
            figure={
                'data': data_amazon,
                'layout': {
                    'title': 'Amazon totals by year'
                }
            }
        ),

        dcc.Graph(
            id='audible-graph',
            figure={
                'data': data_audible,
                'layout': {
                    'title': 'Audible totals by year'
                }
            }
        ),

        dcc.Graph(
            id='instant-video-graph',
            figure={
                'data': data_instant_video,
                'layout': {
                    'title': 'Instant Video totals by year'
                }
            }
        )

    ])


def add_instant_video_total_plot(app: dash.Dash, orders: List[Order]):
    total_by_year = eval.get_instant_video_per_year(orders)

    data = [go.Bar(
        x=list(total_by_year.keys()),
        y=list(total_by_year.values()),
        name='amazon total'
    )]
    add_total_by_year_plot(app, data)


def add_audible_total_plot(app: dash.Dash, orders: List[Order]):
    total_by_year = eval.get_audible_total_by_year(orders)

    data = [go.Bar(
        x=list(total_by_year.keys()),
        y=list(total_by_year.values()),
        name='amazon total'
    )]
    add_total_by_year_plot(app, data)


def add_total_by_year_plot(app: dash.Dash, data: List):
    app.layout = html.Div(children=[
        html.H1(children='Amazon Order History - Evaluation'),

        html.Div(children='''
                        A web application to analyze different aspects of your amazon orders
                    '''),

        dcc.Graph(
            id='my-graph',
            figure={
                'data': data,
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }
        )
    ])


if __name__ == '__main__':
    main()
