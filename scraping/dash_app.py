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

    app.layout = html.Div(className="container", children=[
        head(),
        general_information(orders),
        plots(orders)
    ], style={'fontSize': 18})

    app.run_server(debug=True)


def head():
    return html.Header(children=[
        html.H1(children='Amazon Order History - Evaluation'),
        'A web application to analyze different aspects of your amazon orders'
    ])


def general_information(orders: List[Order]) -> html.Div:
    # ToDo
    return html.Div(children=[
        html.H3(children="General Statistics"),
        html.Div(children=[
            f"Amazon: {eval.get_total(orders)}€",
            html.Br(),
            f"Audible: {eval.get_audible_total(orders)}€",
            html.Br(),
            f"Prime Instant Video: {eval.get_instant_video_total(orders)}€"
        ])
    ])


def plots(orders: List[Order]) -> html.Div:
    return html.Div(children=[
        html.H3(children="Plots"),
        gen_stacked_totals_graph(orders)
    ])


def gen_bar(data: Dict, name: str) -> go.Bar:
    return go.Bar(x=list(data.keys()), y=list(data.values()), name=name)


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
        gen_bar(eval.get_prime_member_fee_by_year(orders), 'amazon prime member fee'),
        gen_bar(eval.get_uncategorized_totals(orders), 'uncategorized'),
    ],
    )

    fig.update_layout(barmode='stack',
                      title_text='Amazon totals by year, split by categories',
                      yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
                      xaxis=dict(title='Year', titlefont_size=18, tickfont_size=16),
                      legend=dict(
                          x=0, y=1.0, font_size=16,
                          bgcolor='rgba(255, 255, 255, 0)',
                      )
                      )

    fig.update_xaxes(dtick=1.0)

    return dcc.Graph(id='stacked-graph', figure=fig)


if __name__ == '__main__':
    main()
