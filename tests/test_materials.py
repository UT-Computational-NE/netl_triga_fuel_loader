import pytest

from netl_triga_fuel_loader.materials import (
    DEFAULT_FUEL_DENSITY,
    FuelMaterialSpec,
    make_fuel,
    require_unique_names,
)


def test_default_spec_matches_netl_fresh_fuel():
    spec = FuelMaterialSpec(name="Fuel")
    assert spec.density == DEFAULT_FUEL_DENSITY
    assert spec.percent_type == "wo"
    assert spec.nuclides["U235"] == 0.0152
    assert "c_H_in_ZrH" in spec.s_alpha_beta


def test_spec_validation():
    with pytest.raises(ValueError):
        FuelMaterialSpec(name="")
    with pytest.raises(ValueError):
        FuelMaterialSpec(name="X", density=0.0)
    with pytest.raises(ValueError):
        FuelMaterialSpec(name="X", temperature=-1.0)
    with pytest.raises(ValueError):
        FuelMaterialSpec(name="X", percent_type="mo")
    with pytest.raises(ValueError):
        FuelMaterialSpec(name="X", nuclides={}, elements={})


def test_to_from_dict_roundtrip():
    spec = FuelMaterialSpec(name="Fuel_Hot", density=6.0, temperature=700.0)
    restored = FuelMaterialSpec.from_dict(spec.to_dict())
    assert restored == spec


def test_from_dict_rejects_unexpected_keys():
    data = FuelMaterialSpec(name="Fuel").to_dict()
    data["densty"] = 6.0  # typo -> should not be silently ignored
    with pytest.raises(ValueError):
        FuelMaterialSpec.from_dict(data)


def test_require_unique_names():
    a = FuelMaterialSpec(name="Fuel_A")
    a_again = FuelMaterialSpec(name="Fuel_A")  # identical -> allowed duplicate
    b = FuelMaterialSpec(name="Fuel_A", density=6.0)  # same name, different comp -> error

    assert require_unique_names([a, a_again]) == [a]
    with pytest.raises(ValueError):
        require_unique_names([a, b])


def test_make_fuel_builds_openmc_material():
    pytest.importorskip("openmc")
    spec = FuelMaterialSpec(name="Fuel_Ring_B", density=5.9, temperature=650.0)
    material = make_fuel(spec)
    assert material.name == "Fuel_Ring_B"
    assert material.temperature == 650.0
    assert material.get_mass_density() == pytest.approx(5.9)
    nuclide_names = {nuclide[0] for nuclide in material.nuclides}
    assert "U235" in nuclide_names
