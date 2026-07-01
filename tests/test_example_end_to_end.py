"""Example artifacts + an end-to-end guard for the full generate -> build pipeline."""

import importlib.util
from pathlib import Path

import pytest

from netl_triga_fuel_loader.generator import render_specs
from netl_triga_fuel_loader.loading import CoreLoadingPattern

_EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "example"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_example():
    return _load_module("build_example", _EXAMPLE_DIR / "build_example.py")


# --- Light checks: the checked-in artifacts stay in sync with the pattern -------


def test_example_json_matches_pattern():
    build_example = _build_example()
    on_disk = CoreLoadingPattern.from_json((_EXAMPLE_DIR / "example_loading.json").read_text())
    assert on_disk == build_example.example_pattern()


def test_example_specs_is_current():
    build_example = _build_example()
    expected = render_specs(build_example.example_pattern(), build_example.example_config())
    assert (_EXAMPLE_DIR / "specs.py").read_text() == expected


# --- Heavy check: generate -> import -> build MPACT input ------------------------


def test_example_end_to_end_mpact(tmp_path):
    pytest.importorskip("openmc")
    pytest.importorskip("coreforge")
    pytest.importorskip("progression_problems")

    from coreforge import materials, mpact_builder
    from coreforge.mpact_builder.builder_specs import DEFAULT_MPACT_MATERIAL_SPECS
    from progression_problems.TRIGA.NETL.problem_5_utils import write_mpact_input
    from progression_problems.TRIGA.NETL.utils import default_mpact_material_specs

    # Import the checked-in generated specs.py to get its reactor.
    specs = _load_module("example_specs", _EXAMPLE_DIR / "specs.py")
    assert specs.problem_ID == "N_5_B_example"

    loading = specs.reactor.core.loading
    assert loading["B-01"].fuel_meat.material.name == "Fuel_Hot"
    assert loading["C-02"].fuel_meat.material.name == "Fuel_Warm"
    assert loading["D-01"].fuel_meat.material.name == "Fuel"  # unassigned -> default fuel

    # The per-location fuels get the U-ZrH MPACT spec.
    material_by_name = {m.name: m for m in specs.reactor.get_materials()}
    mpact_specs = default_mpact_material_specs(list(material_by_name.values()))
    uzrh_specs = DEFAULT_MPACT_MATERIAL_SPECS[materials.UZrH]
    assert mpact_specs[material_by_name["Fuel_Hot"]] is uzrh_specs
    assert mpact_specs[material_by_name["Fuel_Warm"]] is uzrh_specs

    # The full MPACT input builds and is written.
    build_specs = mpact_builder.triga.netl.Reactor.Specs(exclude_excore=True, num_procs=1)
    mpact_input = tmp_path / "mpact.inp"
    write_mpact_input(specs.reactor, reactor_build_specs=build_specs, filename=str(mpact_input))
    assert mpact_input.exists() and mpact_input.stat().st_size > 0
