import pandas as pd
import numpy as np
import pymongo
import sklearn as sk
from matplotlib import pyplot as plt
import plotly as pl
from tqdm.auto import tqdm
from xml.etree import ElementTree
import plotly.graph_objects as go
import urllib
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output

from .layout import html_layout

def init_callbacks(app,df_ebal,df_unfcc,palette):

# Dropdowns - World map
    @app.callback(
        Output("WORLD_MAP", 'figure'),
        Input("TRANSACTION_DPDN", 'value'),
        Input("COMMODITY_DPDN", 'value'),
    )
    def plot_world_map(trans, comm):

        plot_df = df_ebal.query("(TRANSACTION == @trans) and (COMMODITY == @comm)")
        if plot_df.shape[0] == 0:
            return
        plot_df = plot_df.groupby(["REF_AREA"])['value'].mean()
        fig = go.Figure()
        fig.add_trace(
            go.Choropleth(
                locations=plot_df.index,
                z=plot_df.values,
                colorscale="Viridis",
                marker_line_color='white',
                marker_line_width=0.5,
            )
        )
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            dragmode=False,
        #     range=[-90, 50],
            geo={
                'showocean': True,
                'oceancolor': palette['ocean'],
                'showlakes': True,
                'lakecolor': palette['lake'],
                'showcoastlines': False,
                'landcolor': palette['background'],
            },
            plot_bgcolor=palette['background'],
            paper_bgcolor=palette['background'],
            font_color=palette['text'],
        )
        return fig


# Frances' plots here: World map + Dropdowns - Summary
#@app.callback(
#    Output("COUNTRY_SUMMARY", 'figure'),
#    Input("TRANSACTION_DPDN", 'value'),
#    Input("COMMODITY_DPDN", 'value'),
#    Input("WORLD_MAP", 'clickData'),
#)
    def plot_country_summary(trans, comm, country):
        """
        :param trans: The transaction currently selected
        :param comm: The commodity currently selected
        :param country: The country that was just clicked on
            has format like:
            {'points': [{'curveNumber': 0, 'pointNumber': 36, 'pointIndex': 36, 'location': 'CHN', 'z': 271769.93042857136}]}
        """

        # Change code below
        fig = go.Figure()
        fig.add_trace(go.Choropleth(
            locations=[country['points'][0]['location']],
            z=[1]
        ))
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            dragmode=False,
        #     range=[-90, 50],
            geo={
                'showocean': True,
                'oceancolor': palette['ocean'],
                'showlakes': True,
                'lakecolor': palette['lake'],
                'showcoastlines': False,
                'landcolor': palette['background'],
            },
            plot_bgcolor=palette['background'],
            paper_bgcolor=palette['background'],
            font_color=palette['text'],
        )

        return fig

    @app.callback(
        Output("PIE_CHART", 'figure'),
        Output("BAR_CHART", 'figure'),
        Input("TRANSACTION_DPDN", 'value'),
        Input("COMMODITY_DPDN", 'value'),
        Input("WORLD_MAP", 'clickData'),
    )
    def plot_pie_bar(trans, comm, country):
        """
        :param trans: The transaction currently selected
        :param comm: The commodity currently selected
        :param country: The country that was just clicked on
            has format like:
            {'points': [{'curveNumber': 0, 'pointNumber': 36, 'pointIndex': 36, 'location': 'CHN', 'z': 271769.93042857136}]}
        """
        if country is None:
            return go.Figure(), go.Figure()
        country = country['points'][0]['location']
        
        plot_df_pie = df_ebal.query("(TRANSACTION == @transactions) and (COMMODITY == @comm)").reset_index(drop=True)
        plot_df_pie = plot_df_pie.query("(TIME_PERIOD in '1990') and (REF_AREA in '{}')".format(country))
        plot_df_bar = df_ebal.query("(TRANSACTION == @trans) and (COMMODITY == @commodities)").reset_index(drop=True)
        plot_df_bar = plot_df_bar.query("(TIME_PERIOD in '1990') and (REF_AREA in '{}')".format(country))
        

        bar_fig = go.Figure()
        for transaction, group in plot_df_bar.groupby("TRANSACTION"):
            bar_fig.add_trace(go.Bar(x=group["COMMODITY"], y=group["value"],name=transaction))
        
        bar_fig.update_layout(legend_title_text = "{} Distribution among Commodities in {}".format(trans,country))
        bar_fig.update_xaxes(title_text="Commodity")
        bar_fig.update_yaxes(title_text="Energy (in TJ)")
        bar_fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            dragmode=False,
            plot_bgcolor=palette['background'],
            paper_bgcolor=palette['background'],
            font_color=palette['text'],
        )
    
    
    
        pie_fig = go.Figure()
        pie_fig.add_trace(go.Pie(labels=plot_df_pie['TRANSACTION'].unique(), values=plot_df_pie['value'],
                             name=comm,showlegend=False))
        pie_fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            dragmode=False,
            plot_bgcolor=palette['background'],
            paper_bgcolor=palette['background'],
            font_color=palette['text'],
        )
        pie_fig.update_traces(hole=.6, hoverinfo="label+percent+name")
        
        return pie_fig, bar_fig
#app.run_server(debug=False)

def init_dashboard(server):

    MONGO_URI = 'mongodb+srv://sayan:infinity@infinity.9hew3.mongodb.net/<dbname>?retryWrites=true&w=majority'
    client = pymongo.MongoClient(MONGO_URI)

    db = client.UNSD
    col_ebal = db.ebal
    col_unfcc = db.unfcc

    global commodities
    global transactions

    commodities = [
        'Oil Products',
        'Electricity',
        'Natural Gas',
        'Memo: Renewables',
        'Biofuels and waste',
    ]

    transactions = [
        'Primary production',
        'Total energy supply',
        'Final consumption',
        'Final Energy Consumption',
        'Exports',
        'Imports',
        'Other Consumption',
        'Transformation',
        'Manufacturing, construction and non-fuel mining industries',
        'Electricity, Heat and CHP plants',
    ]

    df_unfcc = pd.DataFrame(col_unfcc.find()).drop("_id", axis=1)
    df_ebal = pd.DataFrame(col_ebal.find()).drop("_id", axis=1)
    df_ebal_small = df_ebal.query("(COMMODITY in @commodities) and (TRANSACTION in @transactions)").reset_index(drop=True)
    palette = {
        'background': '#fcfaf2',
        'text': '#787c7a',
        'ocean': '#519fd0',
        'lake': '#7bb2d4',
        'land': '#d4c981'
    }

    blank_fig = go.Figure()
    blank_fig.add_trace(go.Choropleth())
    blank_fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        dragmode=False,
        geo={
            'showocean': True,
            'oceancolor': palette['ocean'],
            'showlakes': True,
            'lakecolor': palette['lake'],
            'showcoastlines': False,
            'landcolor': palette['background'],
        },
    )
    blank_fig.update_layout(
        plot_bgcolor=palette['background'],
        paper_bgcolor=palette['background'],
        font_color=palette['text'],
    )


    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

#    app.index_string = html_layout

    app.layout = html.Div(children=[

        # Page title
        html.H1("World Map"),

        # Dropdowns
        html.Div([
            html.Div(
                children=[
                    dcc.Dropdown(
                        id='TRANSACTION_DPDN',
                        options=[{'label':trans, 'value': trans} for trans in transactions],
                        value=transactions[1],
                    )
                ],
                style={"width": '49%', 'display': 'inline-block'},
            ),
            html.Div(
                children=[
                    dcc.Dropdown(
                        id='COMMODITY_DPDN',
                        options=[{'label': comm, 'value': comm} for comm in commodities],
                        value=commodities[0],
                    ),
                ],
                style={"width": '49%', 'float': 'right', 'display': 'inline-block'},
            ),
        ],
            style={'display': 'inline-block', 'width': '80%', 'float': 'right', 'padding': '0px 120px'}
        ),

        # World map
        html.Div(
            children=[
                dcc.Graph(
                    id="WORLD_MAP",
                    figure=blank_fig,
                )
            ],
            style={'display': 'inline-block', 'width': '100%'}
        ),

        # Country Summary
        html.Div(
            children=[
                dcc.Graph(
                    id="COUNTRY_SUMMARY",
                    figure=blank_fig,
                )
            ],
            style={'display': 'inline-block', 'width': '100%'}
        ),

        # Bar and Pie charts
        html.Div(
            children=[
                html.Div([
                    dcc.Graph(
                        id="PIE_CHART",
                        figure=blank_fig,
                    )],
                    style={'width': '49%', 'display': 'inline-block'}
                ),
                html.Div([
                    dcc.Graph(
                        id="BAR_CHART",
                        figure=blank_fig,
                    )],
                    style={'width': '49%', 'display': 'inline-block'}
                )
            ],
            style={'display': 'inline-block', 'width': '100%'}
        ),

        # Predictor
        html.Div(
            children=[
                html.H1("Predictions")
            ],
            style={'display': 'inline-block', 'width': '100%'}
        ),],
        style={
            'backgroundColor': palette['background']
        }
    )
    init_callbacks(app,df_ebal,df_unfcc,palette)

    return app.server
    
