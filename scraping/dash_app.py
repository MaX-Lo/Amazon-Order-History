# -*- coding: utf-8 -*-
from typing import List, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from . import evaluation as eval
from . import file_handler as fh
from .Data import Order


def main():
    app = dash.Dash(__name__)

    orders = fh.load_orders()

    app.layout = html.Div(className="container", children=[
        head(),
        general_information(orders),
        gen_plots(orders)
    ], style={'fontSize': 18})

    app.run_server(debug=True)


def head():
    return html.Header(children=[
        html.H1(children='Amazon Order History - Evaluation'),
        'A web application to analyze different aspects of your amazon orders'
    ])


def general_information(orders: List[Order]) -> html.Div:
    return html.Div(children=[
        html.H2(children="General Statistics"),
        html.Div(children=[
            f"Amazon: {eval.get_total(orders)}€",
            html.Br(),
            f"Audible: {eval.get_audible_total(orders)}€",
            html.Br(),
            f"Prime Instant Video: {eval.get_instant_video_total(orders)}€"
        ])
    ])


def gen_plots(orders: List[Order]) -> html.Div:
    return html.Div(children=[
        html.H2(children="Plots"),

        html.H3(children='Amazon totals by year, split by categories'),
        gen_stacked_totals_graph(orders),

        html.H3(children='Amazon totals by month'),
        gen_scatter_by_month_graph(orders)
    ])


def gen_bar(data: Dict, name: str) -> go.Bar:
    return go.Bar(x=list(data.keys()), y=list(data.values()), name=name)


def gen_stacked_totals_graph(orders: List[Order]) -> dcc.Graph:
    """ generates a graph with each bar subdivided into different categories
        known categories:
            - audible
            - prime instant video
            - ToDo (prime music unlimited)
            - ToDo (prime membership fee)
            - remaining
    """
    fig = go.Figure(data=[
        gen_bar(eval.audible_total_by_year(orders), 'audible'),
        gen_bar(eval.instant_video_total_per_year(orders), 'prime instant video'),
        gen_bar(eval.prime_member_fee_by_year(orders), 'amazon prime member fee'),
        gen_bar(eval.uncategorized_totals_per_year(orders), 'uncategorized'),
    ])

    fig.update_layout(
        barmode='stack',
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(title='Year', titlefont_size=18, tickfont_size=16),
        legend=dict(x=0, y=1.0, font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
        height=750
    )

    fig.update_xaxes(dtick=1.0)

    return dcc.Graph(id='stacked-graph', figure=fig)


def gen_scatter(data: Dict, name: str) -> dcc.Graph:
    return go.Scatter(x=list(data.keys()), y=list(data.values()), name=name)


def gen_scatter_by_month_graph(orders: List[Order]) -> go.Figure:
    """ generates a line graph with spend amount for each month """
    fig = go.Figure(data=[
        gen_scatter(eval.totals_by_month(orders), 'uncategorized')
    ])

    fig.update_layout(
        yaxis=dict(title='Price in €', titlefont_size=18, tickfont_size=16),
        xaxis=dict(titlefont_size=18, tickfont_size=16),
        legend=dict(x=0, y=1.0, font_size=16, bgcolor='rgba(255, 255, 255, 0)'),
    )

    return dcc.Graph(id='scatter-graph', figure=fig)


if __name__ == '__main__':
    main()
