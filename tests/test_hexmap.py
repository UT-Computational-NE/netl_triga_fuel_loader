import pytest

pytest.importorskip("plotly")

# pylint: disable=wrong-import-position
from netl_triga_fuel_loader import core_map
from gui import hexmap


def _marker(figure):
    return figure.data[0].marker


def test_figure_has_all_locations_with_customdata():
    figure = hexmap.build_core_figure()
    assert len(figure.data) == 1
    assert tuple(figure.data[0].customdata) == core_map.ALL_LOCATIONS
    assert len(_marker(figure).color) == len(core_map.ALL_LOCATIONS)


def test_category_colors_applied():
    figure = hexmap.build_core_figure()
    locations = list(core_map.ALL_LOCATIONS)
    colors = list(_marker(figure).color)
    color_of = dict(zip(locations, colors))
    assert color_of["A-01"] == hexmap.CATEGORY_COLORS["reserved"]  # central thimble
    assert color_of["D-03"] == hexmap.CATEGORY_COLORS["non_fuel"]  # graphite
    assert color_of["B-01"] == hexmap.CATEGORY_COLORS["fuel"]  # unassigned fuel


def test_assignment_colors_override_category():
    figure = hexmap.build_core_figure(assignments={"B-01": "Fuel_Hot"}, group_colors={"Fuel_Hot": "#ff0000"})
    locations = list(core_map.ALL_LOCATIONS)
    color_of = dict(zip(locations, _marker(figure).color))
    assert color_of["B-01"] == "#ff0000"


def test_selected_cell_is_highlighted():
    figure = hexmap.build_core_figure(selected="B-01")
    locations = list(core_map.ALL_LOCATIONS)
    width_of = dict(zip(locations, _marker(figure).line.width))
    assert width_of["B-01"] == 3.0
    assert width_of["B-02"] == 1.0


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
