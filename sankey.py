# noinspection SpellCheckingInspection
"""
sankey.py
Sankey visualization tools
J. Rachlin
"""

import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "browser" # also, close opera!


def _code_mapping(df, src, targ):
    """ Map labels in src and targ columns to integers """

    # Get distinct labels
    labels = list(df[src]) + list(df[targ])
    labels = sorted(list(set(labels)))

    # Get integer codes
    codes = list(range(len(labels)))

    # Create label to code mapping
    lc_map = dict(zip(labels, codes))

    # Substitute names for codes in dataframe
    df = df.replace({src: lc_map, targ: lc_map})
    return df, labels


def make_sankey(df, src, targ, vals=None, **kwargs):
    """Create sankey diagram from source and target columns
       using vals column for edge weights """
    df, labels = _code_mapping(df, src, targ)

    if vals:
        value = df[vals]
    else:
        value = [1] * len(df[src])

    link = {'source': df[src], 'target': df[targ], 'value': value}

    pad = kwargs.get('pad', 100)
    thickness = kwargs.get('thickness', 10)
    line_color = kwargs.get('line_color', 'black')
    line_width = kwargs.get('line_width', 1)

    node = {'pad': pad,
            'thickness': thickness,
            'line': {'color': line_color, 'width': line_width}, 'label': labels}

    sk = go.Sankey(link=link, node=node)

    fig = go.Figure(sk)

    return fig
