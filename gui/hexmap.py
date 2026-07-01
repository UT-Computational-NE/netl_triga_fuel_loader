"""Plotly rendering of the TRIGA core as a radial hex map, plus pure click helpers.

``build_core_figure`` draws every core location as a hexagon, colored by category
(reserved / non-fuel / fuel) or by the fuel group assigned to it, with an optional
highlighted selection. The click helpers are pure functions so the Dash callbacks
in ``gui.app`` stay thin and testable.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go

from netl_triga_fuel_loader import core_map

# Pointy-top hexagon vertex angles (points at top/bottom, flat vertical sides).
_HEX_VERTEX_ANGLES = [math.radians(30 + 60 * i) for i in range(6)]

# Circumradius that makes cells tile contiguously given core_map's ring spacing
# (centers of adjacent cells are sqrt(3) apart, i.e. the flat-to-flat width).
_HEX_SIZE = 1.0

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


def _fill_color(location: str, assignments: Dict[str, str], group_colors: Dict[str, str]) -> str:
    """Fill color for a cell: its assigned group's color, else its category color."""
    group = assignments.get(location)
    if group is not None:
        return group_colors.get(group, CATEGORY_COLORS["fuel"])
    return CATEGORY_COLORS[cell_category(location)]


def _hexagon_vertices(center: Tuple[float, float]) -> Tuple[List[float], List[float]]:
    """Closed (x, y) vertex lists for a pointy-top hexagon centered at ``center``."""
    cx, cy = center
    xs = [cx + _HEX_SIZE * math.cos(angle) for angle in _HEX_VERTEX_ANGLES]
    ys = [cy + _HEX_SIZE * math.sin(angle) for angle in _HEX_VERTEX_ANGLES]
    return xs + [xs[0]], ys + [ys[0]]


def _hexagon_trace(location: str, center: Tuple[float, float], fill: str, selected: bool) -> go.Scatter:
    """A single filled, hoverable/clickable hexagon for one core location."""
    xs, ys = _hexagon_vertices(center)
    line = _SELECTED_LINE if selected else _DEFAULT_LINE
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        fill="toself",
        fillcolor=fill,
        line={"color": line["color"], "width": line["width"]},
        hoveron="fills",
        hoverinfo="text",
        text=location,
        customdata=[location] * len(xs),
        showlegend=False,
    )


def build_core_figure(
    assignments: Optional[Dict[str, str]] = None,
    group_colors: Optional[Dict[str, str]] = None,
    selected: Optional[str] = None,
) -> go.Figure:
    """Build the core hex-map figure as a contiguous honeycomb of filled hexagons.

    Each core location is a filled hexagon; the location name appears only on hover.

    Parameters
    ----------
    assignments : dict[str, str], optional
        Location -> fuel-group name; assigned cells are colored via ``group_colors``.
    group_colors : dict[str, str], optional
        Fuel-group name -> fill color.
    selected : str, optional
        Location to highlight with a bold outline (drawn last so it sits on top).
    """
    assignments = assignments or {}
    group_colors = group_colors or {}
    coordinates = core_map.hex_coordinates()

    traces = [
        _hexagon_trace(
            location,
            coordinates[location],
            _fill_color(location, assignments, group_colors),
            selected=(location == selected),
        )
        for location in core_map.ALL_LOCATIONS
    ]
    # Draw the selected cell last so its bold outline is not overdrawn by neighbors.
    traces.sort(key=lambda trace: trace.customdata[0] == selected)

    figure = go.Figure(traces)
    figure.update_layout(
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        plot_bgcolor="white",
        height=700,
        hovermode="closest",
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return figure
