"""Plotly rendering of the TRIGA core as a radial hex map, plus pure click helpers.

``build_core_figure`` draws every core location as a hexagon, colored by category
(reserved / non-fuel / fuel) or by the fuel group assigned to it, with an optional
highlighted selection. The click helpers are pure functions so the Dash callbacks
in ``gui.app`` stay thin and testable.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import plotly.graph_objects as go

from netl_triga_fuel_loader import core_map

# Category fill colors for cells that are not assigned a fuel group.
CATEGORY_COLORS: Dict[str, str] = {
    "fuel": "#cfe8ff",  # selectable fuel location (unassigned)
    "reserved": "#555555",  # central thimble / control rods / water holes
    "non_fuel": "#b0b0b0",  # graphite element, source holder, empty holes
}

_SELECTED_LINE = {"color": "#111111", "width": 3.0}
_DEFAULT_LINE = {"color": "#666666", "width": 1.0}


def cell_category(location: str) -> str:
    """Return ``"reserved"``, ``"non_fuel"``, or ``"fuel"`` for a location."""
    if core_map.is_reserved(location):
        return "reserved"
    if location in core_map.NON_FUEL_LOCATIONS:
        return "non_fuel"
    return "fuel"


def is_selectable(location: Optional[str]) -> bool:
    """True if a location may hold a per-location fuel material."""
    return bool(location) and core_map.is_fuel_location(location)


def selected_location_from_click(click_data: Optional[dict]) -> Optional[str]:
    """Extract the clicked location from a Dash ``clickData`` payload (or ``None``)."""
    if not click_data:
        return None
    points = click_data.get("points") or []
    if not points:
        return None
    return points[0].get("customdata")


def next_selection(current: Optional[str], clicked: Optional[str]) -> Optional[str]:
    """Selection reducer: select a clicked fuel cell; ignore clicks on other cells."""
    if is_selectable(clicked):
        return clicked
    return current


def _fill_colors(
    locations: List[str],
    assignments: Dict[str, str],
    group_colors: Dict[str, str],
) -> List[str]:
    colors: List[str] = []
    for location in locations:
        group = assignments.get(location)
        if group is not None:
            colors.append(group_colors.get(group, CATEGORY_COLORS["fuel"]))
        else:
            colors.append(CATEGORY_COLORS[cell_category(location)])
    return colors


def build_core_figure(
    assignments: Optional[Dict[str, str]] = None,
    group_colors: Optional[Dict[str, str]] = None,
    selected: Optional[str] = None,
) -> go.Figure:
    """Build the core hex-map figure.

    Parameters
    ----------
    assignments : dict[str, str], optional
        Location -> fuel-group name; assigned cells are colored via ``group_colors``.
    group_colors : dict[str, str], optional
        Fuel-group name -> fill color.
    selected : str, optional
        Location to highlight with a bold outline.
    """
    assignments = assignments or {}
    group_colors = group_colors or {}

    coordinates = core_map.hex_coordinates()
    locations = list(core_map.ALL_LOCATIONS)
    xs = [coordinates[location][0] for location in locations]
    ys = [coordinates[location][1] for location in locations]

    fill_colors = _fill_colors(locations, assignments, group_colors)
    line_colors = [_SELECTED_LINE["color"] if loc == selected else _DEFAULT_LINE["color"] for loc in locations]
    line_widths = [_SELECTED_LINE["width"] if loc == selected else _DEFAULT_LINE["width"] for loc in locations]

    figure = go.Figure(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=locations,
            textposition="middle center",
            textfont={"size": 7, "color": "#222222"},
            customdata=locations,
            hovertext=locations,
            hoverinfo="text",
            marker={
                "symbol": "hexagon",
                "size": 22,
                "color": fill_colors,
                "line": {"color": line_colors, "width": line_widths},
            },
        )
    )
    figure.update_layout(
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        plot_bgcolor="white",
        height=700,
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return figure
