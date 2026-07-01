"""Build the example core loading pattern and (re)generate the example artifacts.

Run this to refresh the checked-in ``example_loading.json`` and ``specs.py``:

    python example/build_example.py

The example places a hotter fuel in the innermost ring and a warm fuel in part of
the next ring, leaving every other fuel location on the default fuel -- a small,
concrete demonstration of per-location fuel loading.
"""

from pathlib import Path

from netl_triga_fuel_loader import CoreLoadingPattern, FuelMaterialSpec, SpecsConfig, write_specs

_HERE = Path(__file__).resolve().parent

PATTERN_PATH = _HERE / "example_loading.json"
SPECS_PATH = _HERE / "specs.py"

_HOT_LOCATIONS = ["B-01", "B-02", "B-03", "B-04", "B-05", "B-06"]
_WARM_LOCATIONS = ["C-02", "C-03", "C-04", "C-05", "C-06"]


def example_pattern() -> CoreLoadingPattern:
    """The example loading pattern: hot inner ring, warm partial next ring."""
    hot = FuelMaterialSpec(name="Fuel_Hot", temperature=800.0)
    warm = FuelMaterialSpec(name="Fuel_Warm", temperature=700.0)
    assignments = {location: "Fuel_Hot" for location in _HOT_LOCATIONS}
    assignments.update({location: "Fuel_Warm" for location in _WARM_LOCATIONS})
    return CoreLoadingPattern(groups={"Fuel_Hot": hot, "Fuel_Warm": warm}, assignments=assignments)


def example_config() -> SpecsConfig:
    """The reactor/problem parameters used for the example ``specs.py``."""
    return SpecsConfig(problem_id="N_5_B_example")


def main() -> None:
    """Regenerate example_loading.json and specs.py from the example pattern/config."""
    pattern = example_pattern()
    PATTERN_PATH.write_text(pattern.to_json() + "\n")
    write_specs(pattern, example_config(), SPECS_PATH, overwrite=True, backup=False)
    print(f"Wrote {PATTERN_PATH.name} and {SPECS_PATH.name}")


if __name__ == "__main__":
    main()
