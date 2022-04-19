#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 14:21:00 2022

@author: laasyapothuganti
"""

import plotly.graph_objects as go
import pandas as pd
import code_mapping_copy as cm

def make_sankey(df, src, targ, vals, node=None):
    """Plot Sankey diagram"""
    
    # Map labels in DataFrame to integers
    df, labels = cm.code_mapping(df, src, targ)

    # Set link for Sankey diagram
    link = {'source':df[src], 'target':df[targ], 'value':df[vals]}
    
    # Initialize conditions for node if not given in parameters 
    if not node:
        node = {'pad':100, 'thickness':10,
            'line':{'color':'black', 'width':2},
            'label':labels}
    else:
        node = node
    
    # Create Sankey diagram object
    # Plot Sankey diagram
    sk = go.Sankey(link=link, node=node)
    fig = go.Figure(sk)
    fig.show()