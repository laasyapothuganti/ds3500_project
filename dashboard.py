#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 13:27:47 2022

@author: laasyapothuganti
"""

#import make_sankey_copy as ms
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
import imageio
import pathlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import sankey as ms

def assign_offcode_group(crime_data):
    '''
    Purpose:
        for all nan values, assign the appropriate offense group based on offense code of crime
        
    Args:
        
        
    Return:
        dataframe with no nan values in offense code group
    '''
    
    # create dict w keys as offense code groups and values as list of corresponding codes
    off_codes = {off: list(crime_data[crime_data.offense_code_group == off].offense_code.unique()) 
                 for off in crime_data['offense_code_group'].unique()}
    
    # reverse the dictionary so that keys are the codes and values are its corresponding offense code group 
    pairs = {code: off for off in off_codes.keys() for code in off_codes[off]}
    
    # remove any offense code without offense code group
    crime_data = crime_data[crime_data.offense_code.isin(pairs.keys())]
    
    # mend dataframe
    crime_data['offense_code_group'] = crime_data.apply(lambda row: pairs[row.offense_code], axis=1)
    
    return crime_data

def main():
    # read csv file for all boston crime data
    crime_2022 = pd.read_csv('crime_2022.csv')
    crime_2021 = pd.read_csv('crime_2021.csv')
    crime_2020 = pd.read_csv('crime_2020.csv')
    crime_2019 = pd.read_csv('crime_2019.csv')
    crime_2018 = pd.read_csv('crime_2018.csv')
    crime_2017 = pd.read_csv('crime_2017.csv')
    crime_2016 = pd.read_csv('crime_2016.csv')
    crime_2015 = pd.read_csv('crime_2015.csv')
    
    # join all datasets together by column
    crime_data = pd.concat([crime_2022, crime_2021, crime_2020, crime_2019, crime_2018, 
                            crime_2017, crime_2016, crime_2015], axis=0)
    
    # turn all column names to lowercase
    cols = [col.lower() for col in crime_data.columns]
    crime_data = crime_data.rename(dict(zip(crime_data.columns, cols)), axis=1)
    
    # drop nan values from "important" columns
    crime_data = crime_data.dropna(subset=['street', 'lat', 'long', 'district'])
    
    # change offense_code_group to title case
    crime_data["offense_code_group"] = crime_data["offense_code_group"].str.title()
    
    # change street to title case
    crime_data["street"] = crime_data["street"].str.title()

    # remove incorrect location data
    crime_data = crime_data[(crime_data.lat > 42) & (crime_data.long != 0)]
    
    # remove any data without offense group code
    crime_data = assign_offcode_group(crime_data)
    
    # group dataframe by year and offense
    # reset index
    crime_year_offense = crime_data.groupby(['year', 'offense_code_group']).count()
    #crime_year_offense = crime_year_offense.reset_index()
    
    # group dataframe by year
    # reset index
    crime_year = crime_data.groupby(['year']).count()
    #crime_year = crime_year.reset_index()
    
    # group dataframe by offense
    # reset index
    crime_offense = crime_data.groupby(['offense_code_group']).count()
    #crime_offense = crime_offense.reset_index()
    
    # obtain list of years,offenses,street names
    year = crime_data['year'].unique().tolist()
    offense = crime_data['offense_code_group'].unique().tolist()
    street = crime_data['street'].unique().tolist()
    

    app = Dash(__name__)
    
    app.layout = html.Div(
        children=[
            #html.Header(
                    #style = {"color": "black", "height": "256px", "display": "flex", "flexDirection": "column", "justifyContent": "center"}
            #),
            html.H1(children="Boston Crime Analytics",
                    style = {"color": "black", "fontSize": "48px", "fontWeight": "bold", "textAlign": "center", "margin": "auto"}
            ),
            html.P(
                children="Analyze the types of crimes and the number of crimes committed in Boston from August 2015 to December 2018 on a yearly, monthly, daily, and hourly basis and at a street level",
                style = {"color": "black", "textAlign": "center", "margin": "4px auto", 'maxWidth': '384px'}
            ),
            html.Div(children="Year", className="menu-title"),
            dcc.Slider(
                id='year-slider', 
                value=2015, 
                min=2015, 
                max=2022, 
                step=1,
                marks={'2015': '2015',
                       '2016': '2016',
                       '2017': '2017',
                       '2018': '2018',
                       '2019': '2019',
                       '2020': '2020',
                       '2021': '2021',
                       '2022': '2022'},
            ),
            html.Br(),
            html.Div(children="Offense Code Group", className="menu-title"),
            dcc.Dropdown(
                id="offense-filter",
                options=offense,
                value="Aggravated Assault",
                clearable=False,
                style = dict(width='50%'),
                ),
            html.Br(),
            html.Div(
                children=dcc.Graph(
                    id="graph-chart", config={"displayModeBar": False},
                ),
                className="card",
            ),
            html.Div(
                children=dcc.Graph(
                    id="bar-chart", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Div(
                children=dcc.Graph(
                    id="line-chart1", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Div(
                children=dcc.Graph(
                    id="line-chart2", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Div(
                children=dcc.Graph(
                    id="line-chart3", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Br(),
            html.Div(children="Street", className="menu-title"),
            dcc.Dropdown(
                id="street-filter",
                options=street,
                value="Gibson St",
                clearable=False,
                style = dict(width='50%'),
                ),
            html.Div(
                children=dcc.Graph(
                    id="street_chart", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Div(children="Minimum Crimes", className="menu-title"),
            dcc.Slider(0, 50, 5, value=10, id='count-slider'
            ),
        ],
    )
    
    @app.callback(
        Output("graph-chart", "figure"),
        Output("bar-chart", "figure"),
        Output("line-chart1", "figure"),
        Output("line-chart2", "figure"),
        Output("line-chart3", "figure"),
        Output("street_chart", "figure"),
        Input("year-slider", "value"),
        Input("offense-filter", "value"),
        Input("street-filter", "value"),
        Input("count-slider", "value")
        )
    
    def update_charts(year, offense, street, count):
        
        year = int(year)
        year_bool = crime_data['year'] == year
        crime_ybool = crime_data.loc[year_bool,:]
        
        crime_obool = crime_year_offense.loc[year]
        
        #crime_street = crime_ybool.groupby(['offense_code_group', 'street']).size().reset_index(name='count')
        #crime_street = crime_street.sort_values('count', ascending=False)
        #crime_street = crime_street[crime_street["count"] >= 50]
        
        crime = crime_ybool[crime_ybool.offense_code_group.str.contains(offense)]
        crime_month = crime.groupby("month").count()
        cats = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        crime_day = crime.groupby(["day_of_week"]).count().reindex(cats) 
        crime_hour = crime.groupby("hour").count()
        
        #crime_street = crime.groupby(['offense_code_group', 'street']).size().reset_index(name='count')
        #crime_street = crime_street.sort_values('count', ascending=False)
        #crime_street = crime_street[crime_street["count"] >= 5]
        
        crime_street = crime_ybool[crime_ybool.street.str.contains(street)]
        crime_street_offense = crime_street.groupby(['street', 'offense_code_group']).size().reset_index(name='count')
        crime_street_offense = crime_street_offense.sort_values('count', ascending=False)
        crime_street_offense = crime_street_offense[crime_street_offense["count"] >= count]
        
        graph_chart = px.scatter_mapbox(crime_ybool[crime_ybool["offense_code_group"]==offense], lat="lat", lon="long", hover_name="incident_number", hover_data=["year", "offense_code_group", "district", "reporting_area", "occurred_on_date", "street"],
                            color_discrete_sequence=["fuchsia"], zoom=10, height=600)
        graph_chart.update_layout(mapbox_style="open-street-map")
        graph_chart.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        
        street_chart = ms.make_sankey(crime_street_offense, 'street', 'offense_code_group', 'count')
        
        
        bar_chart = {
            "data": [
                {
                    "x": crime_obool.index,
                    "y": crime_obool["incident_number"],
                    "type": "bar",
                },
            ],
            "layout": {
                "title": {
                    "text": "Yearly Number of Incidents by Offense Code Group",
                    "x": 0.05,
                    "xanchor": "left"
                },
            },
        }
        
        line_chart1 = {
            "data": [
                {
                    "x": crime_month.index,
                    "y": crime_month["incident_number"],
                    "type": "lines",
                },
            ],
            "layout": {
                "title": {
                    "text": "Monthly Number of Incidents for Given Offense Code Group",
                    "x": 0.05,
                    "xanchor": "left"
                },
            },
        }
    
        line_chart2 = {
            "data": [
                {
                    "x": crime_day.index,
                    "y": crime_day["incident_number"],
                    "type": "lines",
                },
            ],
            "layout": {
                "title": {
                    "text": "Daily Number of Incidents for Given Offense Code Group",
                    "x": 0.05,
                    "xanchor": "left"
                },
            },
        }
        
        line_chart3 = {
            "data": [
                {
                    "x": crime_hour.index,
                    "y": crime_hour["incident_number"],
                    "type": "lines",
                },
            ],
            "layout": {
                "title": {
                    "text": "Hourly Number of Incidents for Given Offense Code Group",
                    "x": 0.05,
                    "xanchor": "left"
                },
            },
        }
        
        return graph_chart, bar_chart, line_chart1, line_chart2, line_chart3, street_chart
    
    app.run_server(debug=True)
    
if __name__ == '__main__':
    main()

