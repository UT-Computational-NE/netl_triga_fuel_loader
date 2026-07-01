import importlib.util

import pytest

from netl_triga_fuel_loader.generator import SpecsConfig, render_specs, write_specs
from netl_triga_fuel_loader.loading import CoreLoadingPattern
from netl_triga_fuel_loader.materials import FuelMaterialSpec


def _pattern():
    hot = FuelMaterialSpec(name="Fuel_Hot", temperature=700.0)
    std = FuelMaterialSpec(name="Fuel Ring-B")  # awkward name -> exercises identifier sanitizing
    unused = FuelMaterialSpec(name="Fuel_Unused")
    return CoreLoadingPattern(
        groups={"Fuel_Hot": hot, "Fuel Ring-B": std, "Fuel_Unused": unused},
        assignments={"B-01": "Fuel_Hot", "B-02": "Fuel_Hot", "C-02": "Fuel Ring-B"},
    )


def _config():
    return SpecsConfig(problem_id="N_5_B_test", fuel_temp=600.0, non_fuel_temp=293.15)


def test_render_is_deterministic():
    pattern, config = _pattern(), _config()
    assert render_specs(pattern, config) == render_specs(pattern, config)


def test_render_compiles_and_has_expected_content():
    text = render_specs(_pattern(), _config())
    compile(text, "<generated specs.py>", "exec")  # valid Python

    assert "problem_ID = 'N_5_B_test'" in text
    assert "fuel_materials = {" in text
    assert "'B-01': FuelSpec(material=" in text
    assert "fuel_materials=fuel_materials," in text
    # Rod positions default to the fully-inserted constants.
    assert "transient_rod_position=NETLDefaultGeometries.TRANSIENT_ROD_FULLY_INSERTED_POSITION" in text
    # Only assigned groups are emitted (the unused group is dropped).
    assert "Fuel_Unused" not in text
    assert "name='Fuel_Hot'" in text


def test_rod_position_override_emitted_as_float():
    config = SpecsConfig(problem_id="P", transient_rod_position=-70.0)
    text = render_specs(_pattern(), config)
    assert "transient_rod_position=-70.0" in text


def test_specsconfig_requires_problem_id():
    with pytest.raises(ValueError):
        SpecsConfig(problem_id="  ")


def test_write_specs_clobber_guard(tmp_path):
    pattern, config = _pattern(), _config()
    target = tmp_path / "specs.py"

    written = write_specs(pattern, config, target)
    assert written == target and target.exists()

    # Second write without overwrite is refused.
    with pytest.raises(FileExistsError):
        write_specs(pattern, config, target)

    # Overwrite backs up the previous file.
    write_specs(pattern, config, target, overwrite=True)
    assert target.with_suffix(".py.bak").exists()


def test_generated_specs_builds_reactor(tmp_path):
    pytest.importorskip("openmc")
    pytest.importorskip("coreforge")
    pytest.importorskip("progression_problems")

    pattern, config = _pattern(), _config()
    target = tmp_path / "generated_specs.py"
    write_specs(pattern, config, target)

    spec = importlib.util.spec_from_file_location("generated_specs", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.problem_ID == "N_5_B_test"
    loading = module.reactor.core.loading
    assert loading["B-01"].fuel_meat.material.name == "Fuel_Hot"
    assert loading["C-02"].fuel_meat.material.name == "Fuel Ring-B"
    assert loading["D-01"].fuel_meat.material.name == "Fuel"  # unassigned -> default fuel
