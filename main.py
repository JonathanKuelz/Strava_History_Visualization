#!/usr/bin/env python3
# Author: Jonathan Külz
import matplotlib.pyplot as plt

from utils import load_data

import pydeck as pdk

def draw_pydeck(data):
    """Once the data is loaded, this function creates the pydeck map with the visualization of your GPS tracks."""
    layer = pdk.Layer(
        "PathLayer",
        data=data,
        auto_hightlight=True,
        pickable=True,
        get_color='color',
        get_path='path',
        width_scale=1,
        picking_radius=18,
        width_min_pixels=2,
        get_width=.8,
    )
    view_state = pdk.ViewState(latitude=48.137154, longitude=11.576124, zoom=10)  # Based in Munich
    r = pdk.Deck(layers=[layer], initial_view_state=view_state,
                 tooltip={
                     'html': '<b>{name}</b>, {date}',
                     'style': {
                         'color': 'white'
                     }
                 }
                 )
    return r

def main():
    data = load_data('data')
    viz = draw_pydeck(data)
    viz.to_html('map.html')


if __name__ == '__main__':
    main()
