import pytest

pytest.importorskip("plotly")

# pylint: disable=wrong-import-position
from netl_triga_fuel_loader import core_map
from gui import hexmap


def _trace_by_location(figure):
    """Map each location to its hexagon trace (one filled hexagon per location)."""
    return {trace.customdata[0]: trace for trace in figure.data}


def test_figure_has_one_hexagon_per_location():
    figure = hexmap.build_core_figure()
    assert len(figure.data) == len(core_map.ALL_LOCATIONS)
    assert set(_trace_by_location(figure)) == set(core_map.ALL_LOCATIONS)
    # Each hexagon is a closed filled polygon (7 points, fill='toself').
    a01 = _trace_by_location(figure)["A-01"]
    assert a01.fill == "toself"
    assert len(a01.x) == 7 and a01.x[0] == a01.x[-1]


def test_category_colors_applied():
    trace_of = _trace_by_location(hexmap.build_core_figure())
    assert trace_of["A-01"].fillcolor == hexmap.CATEGORY_COLORS["reserved"]  # central thimble
    assert trace_of["D-03"].fillcolor == hexmap.CATEGORY_COLORS["non_fuel"]  # graphite
    assert trace_of["B-01"].fillcolor == hexmap.CATEGORY_COLORS["fuel"]  # unassigned fuel


def test_assignment_colors_override_category():
    figure = hexmap.build_core_figure(assignments={"B-01": "Fuel_Hot"}, group_colors={"Fuel_Hot": "#ff0000"})
    assert _trace_by_location(figure)["B-01"].fillcolor == "#ff0000"


def test_selected_cell_is_highlighted():
    trace_of = _trace_by_location(hexmap.build_core_figure(selected="B-01"))
    assert trace_of["B-01"].line.width == 3.0
    assert trace_of["B-02"].line.width == 1.0


def test_cell_category():
    assert hexmap.cell_category("A-01") == "reserved"
    assert hexmap.cell_category("D-03") == "non_fuel"
    assert hexmap.cell_category("B-01") == "fuel"


def test_selected_location_from_click():
    assert hexmap.selected_location_from_click(None) is None
    assert hexmap.selected_location_from_click({"points": []}) is None
    assert hexmap.selected_location_from_click({"points": [{"customdata": "B-01"}]}) == "B-01"


def test_next_selection_reducer():
    assert hexmap.next_selection(None, "B-01") == "B-01"  # select a fuel cell
    assert hexmap.next_selection("B-01", "A-01") == "B-01"  # reserved click ignored
    assert hexmap.next_selection("B-01", "D-03") == "B-01"  # non-fuel click ignored
    assert hexmap.next_selection("B-01", None) == "B-01"  # empty-space click ignored


def test_is_selectable():
    assert hexmap.is_selectable("B-01")
    assert not hexmap.is_selectable("A-01")
    assert not hexmap.is_selectable(None)
