#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 13:27:47 2022

@author: laasyapothuganti
"""

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
from plotly.subplots import make_subplots
import dash 
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

def clean_data(df):
    
    # turn all column names to lowercase
    cols = [col.lower() for col in df.columns]
    crime_data = df.rename(dict(zip(df.columns, cols)), axis=1)
    
    # drop nan values from "important" columns
    crime_data = crime_data.dropna(subset=['street', 'lat', 'long'])
    
    # change offense_code_group, street to title case
    crime_data["offense_code_group"] = crime_data["offense_code_group"].str.title()
    crime_data["street"] = crime_data["street"].str.title()

    # remove incorrect location data
    crime_data = crime_data[(crime_data.lat > 42) & (crime_data.long != 0)]
    
    # assign offense code group to NaN values in offense code group column
    crime_data = assign_offcode_group(crime_data)
    
    return crime_data

def main():
    # read in csv files for all Boston crime data
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
    
    # clean DataFrame
    crime_data = clean_data(crime_data)
    
    # group dataframe by year and offense
    crime_year_offense = crime_data.groupby(['year', 'offense_code_group']).count()
    
    # obtain list of offenses, street names (for dropdown elements)
    # order lists in alphabetical order
    # add all option to lists
    offense = crime_data['offense_code_group'].unique().tolist()
    offense = sorted(offense)
    offense.insert(0, "All Offense Code Groups")
    street = crime_data['street'].unique().tolist()
    street = sorted(street)
    street.insert(0, "All Streets")
    

    app = Dash(__name__)
    
    app.layout = html.Div(
        children=[
            html.H1(children="Boston Crime Analytics",
                    style = {"color": "black", "fontSize": "48px", "fontWeight": "bold", "textAlign": "center", "margin": "auto"}
            ),
            html.P(
                children="Analyze the types of crimes and the number of crimes committed in Boston from August 2015 to April 2022 on a yearly, monthly, daily, and hourly basis and at a street level",
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
                value="All Offense Code Groups",
                multi = True,
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
                    id="line-chart", config={"displayModeBar": False}
                ),
                className="card",
            ),
            html.Br(),
            html.Div(children="Street", className="menu-title"),
            dcc.Dropdown(
                id="street-filter",
                options=street,
                value="All Streets",
                multi = True,
                clearable=False,
                style = dict(width='50%'),
                ),
            html.Div(children="Crime", className="menu-title"),
            dcc.Dropdown(
                id="crime-filter",
                options=offense,
                value="All Offense Code Groups",
                multi = True,
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
            dcc.Slider(0, 100, 5, value=15, id='count-slider'
            ),
        ],
    )
    
    @app.callback(
        Output("graph-chart", "figure"),
        Output("bar-chart", "figure"),
        Output("line-chart", "figure"),
        Output("street_chart", "figure"),
        Input("year-slider", "value"),
        Input("offense-filter", "value"),
        Input("street-filter", "value"),
        Input("crime-filter", "value"),
        Input("count-slider", "value")
        )
    
    def update_charts(year, offense, street, crime, count):
        
        # Initial Data Clean/Data Prep
        # convert year to integer
        # filter DataFrame to year selected
        year = int(year)
        year_bool = crime_data['year'] == year
        crime_ybool = crime_data.loc[year_bool,:]
        
        # convert offense code groups to list for all filter in map plot
        offenses = crime_ybool['offense_code_group'].unique().tolist()
       
        # filter grouped year/offense DataFrame by year selected
        crime_obool = crime_year_offense.loc[year]
        
        
        
        # Street to Crime Sankey Diagram
        # return non-updated dashboard when nothing is selected in filter
        if len(street) == 0:
            return dash.no_update
        
        elif isinstance(street, str):
            # keep all streets in DataFrame if all filter is selected
            if street == "All Streets":
                crime_sankey = crime_ybool
            # keep only relevant street in DataFrame if single street is selected
            else:
                crime_sankey = crime_ybool[crime_ybool["street"] == street]
        
        elif isinstance(street, list):
            # keep all streets in DataFrame if all filter is selected
            if "All Streets" in street:
                crime_sankey = crime_ybool
            # keep only relevant streets in DataFrame if multiple streets are selected
            else:
                crime_sankey = crime_ybool[crime_ybool["street"].isin(street)]
        
        # return non-updated dashboard when nothing is selected in filter
        if len(crime) == 0:
            return dash.no_update
        
        elif isinstance(crime, str):
            # keep all offense code groups in DataFrame if all filter is selected
            if crime == "All Offense Code Groups":
                crime_sankey = crime_sankey
            # keep only relevant offense code group in DataFrame if single offense code group is selected
            else:
                crime_sankey = crime_sankey[crime_sankey["offense_code_group"] == crime]
        
        elif isinstance(crime, list):
            # keep all offense code groups in DataFrame if all filter is selected
            if "All Offense Code Groups" in crime:
                crime_sankey = crime_sankey
             # keep only relevant offense code groups in DataFrame if multiple offense code groups are selected
            else:
                crime_sankey = crime_sankey[crime_sankey["offense_code_group"].isin(crime)]

        
        # group DataFrame by street and offense code group
        # sort values in descending order
        # filter DataFrame by count
        # create Sankey diagram
        crime_sankey = crime_sankey.groupby(['street', 'offense_code_group']).size().reset_index(name='count')
        crime_sankey = crime_sankey.sort_values('count', ascending=False)
        crime_sankey = crime_sankey[crime_sankey["count"] >= count]
        street_chart = ms.make_sankey(crime_sankey, 'street', 'offense_code_group', 'count')
        
        
        
        # Map Plot/Bar Chart/Line Chart Subplots
        # return non-updated dashboard when nothing is selected in filter
        if len(offense) == 0:
            return dash.no_update
        
        elif isinstance(offense, str):
            # plot all offenses when all filter is selected
            # keep all offense code groups in DataFrame when all filter is selected
            if offense == "All Offense Code Groups":
                graph_chart = px.scatter_mapbox(crime_ybool[crime_ybool["offense_code_group"].isin(offenses)], lat="lat", lon="long", hover_name="incident_number", hover_data=["location", "year", "offense_code_group", "offense_description", "district", "reporting_area", "street", "occurred_on_date"],
                        color_discrete_sequence=["fuchsia"], zoom=10, height=600)
                crime = crime_ybool
            
            # plot selected single offense
            # keep selected single offense code group in DataFrame
            else:
                graph_chart = px.scatter_mapbox(crime_ybool[crime_ybool["offense_code_group"]==offense], lat="lat", lon="long", hover_name="incident_number", hover_data=["location", "year", "offense_code_group", "offense_description", "district", "reporting_area", "street", "occurred_on_date"],
                                    color_discrete_sequence=["fuchsia"], zoom=10, height=600)
                crime = crime_ybool[crime_ybool["offense_code_group"] == offense]
       
        elif isinstance(offense, list):
            # plot all offenses when all filter is selected
            # keep all offense code groups in DataFrame when all filter is selected
            if "All Offense Code Groups" in offense:
                graph_chart = px.scatter_mapbox(crime_ybool[crime_ybool["offense_code_group"].isin(offenses)], lat="lat", lon="long", hover_name="incident_number", hover_data=["location", "year", "offense_code_group", "offense_description", "district", "reporting_area", "street", "occurred_on_date"],
                        color_discrete_sequence=["fuchsia"], zoom=10, height=600)
                crime = crime_ybool
            
            # plot selected multiple offenses
            # keep selected multiple offense code groups in DataFrame
            else:
                graph_chart = px.scatter_mapbox(crime_ybool[crime_ybool["offense_code_group"].isin(offense)], lat="lat", lon="long", hover_name="incident_number", hover_data=["location", "year", "offense_code_group", "offense_description", "district", "reporting_area", "street", "occurred_on_date"],
                        color_discrete_sequence=["fuchsia"], zoom=10, height=600)
                crime = crime_ybool[crime_ybool["offense_code_group"].isin(offense)]
        
        # update map plot layout style and margins
        graph_chart.update_layout(mapbox_style="open-street-map")
        graph_chart.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        # create grouped DataFrames by month, hour, and day
        crime_month = crime.groupby("month").count()
        cats = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        crime_day = crime.groupby(["day_of_week"]).count().reindex(cats) 
        crime_hour = crime.groupby("hour").count()
        
        # plot bar chart of offense code groups and number of incidents for selected year
        # add title, x-axis label, y-axis label
        bar_chart = px.bar(crime_obool, x=crime_obool.index, y=crime_obool["incident_number"])
        bar_chart.update_layout(height = 600, title_text="Yearly Number of Incidents by Offense Code Group")
        bar_chart.update_xaxes(title_text="Offense Code Group")
        bar_chart.update_yaxes(title_text='Number of Incidents')
        
        # produce 3 subplots for month, day, and hour DataFrame data
        # add subtitles
        line_chart = make_subplots(rows=1, cols=3, subplot_titles=('Number of Incidents by Month',  'Number of Incidents by Day','Number of Incidents by Hour'))
        
        # plot month with number of incidents 
        line_chart.add_trace(
            go.Scatter(x=crime_month.index, y=crime_month['incident_number']),
            row=1, col=1
        )
        # plot day wit number of incidents
        line_chart.add_trace(
            go.Scatter(x=crime_day.index, y=crime_day['incident_number']),
            row=1, col=2
        )
        # plot hour with number of incidents
        line_chart.add_trace(
            go.Scatter(x=crime_hour.index, y=crime_hour['incident_number']),
            row=1, col=3
        )
        
        # add title, x-axis labels, y-axis label
        line_chart.update_layout(title_text="Number of Incidents for Selected Offense Code Group(s) by Month, Day, and Hour", showlegend=False)
        line_chart.update_yaxes(title_text='Number of Incidents', row=1, col=1)
        line_chart.update_xaxes(title_text='Month', row=1, col=1)
        line_chart.update_xaxes(title_text='Day', row=1, col=2)
        line_chart.update_xaxes(title_text='Hour', row=1, col=3)
        
        
        return graph_chart, bar_chart, line_chart, street_chart
    
    app.run_server(debug=True)
    
if __name__ == '__main__':
    main()

