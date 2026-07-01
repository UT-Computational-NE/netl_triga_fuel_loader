"""Dash app shell: the interactive TRIGA core hex map with click-to-select.

Run with::

    python -m gui.app

Material-definition forms and the "Generate Input File" button are added in a
follow-up (#6); this shell provides the map and cell selection.
"""

from __future__ import annotations

import dash
from dash import Input, Output, State, dcc, html

from gui.hexmap import build_core_figure, next_selection, selected_location_from_click

_PROMPT = "Click a fuel location (light blue) to select it."


def create_app() -> dash.Dash:
    """Build the Dash application."""
    app = dash.Dash(__name__)
    app.title = "NETL TRIGA Fuel Loader"

    app.layout = html.Div(
        style={"maxWidth": "1000px", "margin": "0 auto", "fontFamily": "sans-serif"},
        children=[
            html.H2("NETL TRIGA Fuel Loader"),
            html.Div(id="selection-info", children=_PROMPT, style={"marginBottom": "8px"}),
            dcc.Graph(id="core-map", figure=build_core_figure(), config={"displayModeBar": False}),
            dcc.Store(id="selected-location", data=None),
        ],
    )

    @app.callback(
        Output("core-map", "figure"),
        Output("selection-info", "children"),
        Output("selected-location", "data"),
        Input("core-map", "clickData"),
        State("selected-location", "data"),
    )
    def _on_cell_click(click_data, current_selection):
        clicked = selected_location_from_click(click_data)
        selection = next_selection(current_selection, clicked)
        info = f"Selected: {selection}" if selection else _PROMPT
        return build_core_figure(selected=selection), info, selection

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
