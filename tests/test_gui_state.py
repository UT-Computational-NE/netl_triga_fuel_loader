import base64

import pytest

from gui import state
from netl_triga_fuel_loader.materials import FuelMaterialSpec


def _group(name, **kwargs):
    return FuelMaterialSpec(name=name, **kwargs).to_dict()


def test_default_group_name_and_temperature():
    group = state.default_group()
    assert group["name"] == state.DEFAULT_GROUP_NAME
    assert group["temperature"] == 600.0


def test_group_color_map_is_deterministic_and_distinct():
    colors = state.group_color_map(["B", "A", "C"])
    assert set(colors) == {"A", "B", "C"}
    assert len({colors["A"], colors["B"], colors["C"]}) == 3
    assert state.group_color_map(["A", "B", "C"]) == colors  # stable


def test_upsert_group_adds_and_replaces_by_name():
    groups = state.upsert_group([], "Fuel_Hot", 5.85, 700.0)
    assert [g["name"] for g in groups] == ["Fuel_Hot"]
    groups = state.upsert_group(groups, "Fuel_Hot", 6.0, 800.0)  # replace, not duplicate
    assert [g["name"] for g in groups] == ["Fuel_Hot"]
    assert groups[0]["density"] == 6.0


def test_upsert_group_rejects_invalid():
    with pytest.raises(ValueError):
        state.upsert_group([], "  ", 5.85, 700.0)


def test_composition_rows_infer_nuclide_vs_element_by_format():
    nuclides, elements = state.composition_from_rows(
        [
            {"species": "U235", "fraction": 0.2},  # has mass number -> nuclide
            {"species": "Cr", "fraction": 0.05},  # bare symbol -> element
            {"species": " ", "fraction": 1.0},  # blank -> skipped
            {"species": "Fe", "fraction": None},
        ]  # no fraction -> skipped
    )
    assert nuclides == {"U235": 0.2} and elements == {"Cr": 0.05}


def test_rows_from_spec_roundtrips():
    group = _group("Fuel_X")
    parsed_n, parsed_e = state.composition_from_rows(state.rows_from_spec(group))
    assert parsed_n == group["nuclides"] and parsed_e == group["elements"]


def test_sab_text_roundtrip():
    laws = ["c_H_in_ZrH", "c_Zr_in_ZrH"]
    assert state.sab_from_text(state.sab_to_text(laws)) == laws
    assert state.sab_from_text("a\n\n  b  \n") == ["a", "b"]


def test_upsert_group_with_custom_composition():
    groups = state.upsert_group(
        [],
        "Fuel_Enriched",
        5.9,
        700.0,
        nuclides={"U235": 0.2, "U238": 0.8},
        elements={},
        percent_type="ao",
        s_alpha_beta=["c_H_in_ZrH"],
    )
    group = groups[0]
    assert group["nuclides"] == {"U235": 0.2, "U238": 0.8}
    assert group["elements"] == {}
    assert group["percent_type"] == "ao"
    assert group["s_alpha_beta"] == ["c_H_in_ZrH"]


def test_paint_sets_fuel_locations_only():
    assignments = state.paint({}, "B-01", "Fuel_Hot")
    assert assignments == {"B-01": "Fuel_Hot"}
    assert state.paint(assignments, "A-01", "Fuel_Hot") == assignments  # reserved -> ignored
    assert state.paint(assignments, "D-03", "Fuel_Hot") == assignments  # non-fuel -> ignored
    assert state.paint(assignments, "B-01", "Fuel_Cold")["B-01"] == "Fuel_Cold"  # override


def test_initial_assignments_cover_all_fuel_locations():
    from netl_triga_fuel_loader import core_map

    assignments = state.initial_assignments()
    assert set(assignments) == set(core_map.FUEL_LOCATIONS)
    assert set(assignments.values()) == {state.DEFAULT_GROUP_NAME}


def test_most_common_group_and_suggested_name():
    assert state.most_common_group({"B-01": "A", "B-02": "A", "C-02": "B"}) == "A"
    assert state.most_common_group({}) == state.DEFAULT_GROUP_NAME
    assert state.suggested_name([state.default_group()]) == "Fuel Material 2"


def test_build_pattern_drops_orphan_assignments():
    groups = [_group("Fuel_Hot")]
    pattern = state.build_pattern(groups, {"B-01": "Fuel_Hot", "B-02": "Gone"})
    assert pattern.assignments == {"B-01": "Fuel_Hot"}


def test_generate_specs_text_is_valid_and_placed():
    groups = [_group("Fuel_Hot", temperature=700.0)]
    text = state.generate_specs_text(groups, {"B-01": "Fuel_Hot"}, "N_5_B")
    compile(text, "<specs>", "exec")
    assert "problem_ID = 'N_5_B'" in text
    assert "'B-01': FuelSpec(material=" in text


def test_pattern_json_load_roundtrip():
    groups = [_group("Fuel_Hot", temperature=700.0), _group("Fuel_Warm", temperature=650.0)]
    assignments = {"B-01": "Fuel_Hot", "C-02": "Fuel_Warm"}
    json_text = state.pattern_json(groups, assignments)

    upload = "data:application/json;base64," + base64.b64encode(json_text.encode()).decode()
    loaded_groups, loaded_assignments = state.load_pattern(upload)
    assert loaded_assignments == assignments
    assert {g["name"] for g in loaded_groups} == {"Fuel_Hot", "Fuel_Warm"}
