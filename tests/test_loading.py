import pytest

from netl_triga_fuel_loader.loading import CoreLoadingPattern
from netl_triga_fuel_loader.materials import FuelMaterialSpec


def _pattern():
    hot = FuelMaterialSpec(name="Fuel_Hot", temperature=700.0)
    std = FuelMaterialSpec(name="Fuel_Std")
    return CoreLoadingPattern(
        groups={"Fuel_Hot": hot, "Fuel_Std": std},
        assignments={"B-01": "Fuel_Hot", "B-02": "Fuel_Hot", "C-02": "Fuel_Std"},
    )


def test_valid_pattern_and_specs_by_location():
    pattern = _pattern()
    by_loc = pattern.fuel_specs_by_location()
    assert by_loc["B-01"].name == "Fuel_Hot"
    assert by_loc["C-02"].name == "Fuel_Std"
    assert set(by_loc) == {"B-01", "B-02", "C-02"}


@pytest.mark.parametrize("bad_location", ["A-01", "C-01", "D-03", "G-32", "Z-99"])
def test_rejects_non_fuel_or_unknown_locations(bad_location):
    spec = FuelMaterialSpec(name="Fuel_Std")
    with pytest.raises(ValueError):
        CoreLoadingPattern(groups={"Fuel_Std": spec}, assignments={bad_location: "Fuel_Std"})


def test_rejects_unknown_group():
    spec = FuelMaterialSpec(name="Fuel_Std")
    with pytest.raises(ValueError):
        CoreLoadingPattern(groups={"Fuel_Std": spec}, assignments={"B-01": "Missing"})


def test_rejects_group_key_name_mismatch():
    spec = FuelMaterialSpec(name="Fuel_Std")
    with pytest.raises(ValueError):
        CoreLoadingPattern(groups={"WrongKey": spec})


def test_assign_and_unassign():
    pattern = _pattern()
    pattern.assign("B-03", "Fuel_Std")
    assert pattern.assignments["B-03"] == "Fuel_Std"
    pattern.unassign("B-03")
    assert "B-03" not in pattern.assignments
    with pytest.raises(ValueError):
        pattern.assign("A-01", "Fuel_Std")  # reserved location


def test_json_roundtrip():
    pattern = _pattern()
    restored = CoreLoadingPattern.from_json(pattern.to_json())
    assert restored.assignments == pattern.assignments
    assert restored.groups == pattern.groups


def test_from_dict_rejects_unexpected_keys():
    data = _pattern().to_dict()
    data["assignmnets"] = {}  # typo -> should not be silently ignored
    with pytest.raises(ValueError):
        CoreLoadingPattern.from_dict(data)
