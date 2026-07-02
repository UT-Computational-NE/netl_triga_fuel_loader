"""Pure state helpers for the fuel-loader GUI (no Dash).

Keeping the reducer logic here -- turning form inputs, map clicks, and uploads into
the ``groups``/``assignments`` state, and turning that state into a pattern, a
``specs.py``, or a JSON blob -- lets the Dash callbacks in ``gui.app`` stay thin and
lets this logic be unit-tested without a browser.

Model: every fuel location always carries a material. On startup all locations are
assigned a default fuel group; painting overrides individual locations.
"""

from __future__ import annotations

import base64
from collections import Counter
from typing import Dict, List, Optional, Tuple

from netl_triga_fuel_loader import core_map
from netl_triga_fuel_loader.generator import SpecsConfig, render_specs
from netl_triga_fuel_loader.loading import CoreLoadingPattern
from netl_triga_fuel_loader.materials import FuelMaterialSpec

# Name of the always-present default fuel group.
DEFAULT_GROUP_NAME = "Fuel Material 1"

# Distinct fill colors assigned to fuel groups (cycled if there are more groups).
_PALETTE = [
    "#4363d8",
    "#e6194B",
    "#3cb44b",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#469990",
    "#9A6324",
    "#800000",
    "#000075",
]


def group_color_map(group_names) -> Dict[str, str]:
    """Assign each group a stable color (sorted by name for determinism)."""
    return {name: _PALETTE[index % len(_PALETTE)] for index, name in enumerate(sorted(group_names))}


# --- composition (editable grid rows; nuclide vs element inferred by format) -----


def _is_nuclide(species: str) -> bool:
    """A nuclide has a mass number (a digit), e.g. ``U235``; an element does not, e.g. ``Cr``."""
    return any(char.isdigit() for char in species)


def composition_from_rows(rows) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Split grid rows (``{"species", "fraction"}``) into ``(nuclides, elements)``.

    Whether an entry is a nuclide or element is inferred from its format (a mass
    number implies a nuclide). Blank rows are skipped.
    """
    nuclides: Dict[str, float] = {}
    elements: Dict[str, float] = {}
    for row in rows or []:
        species = str(row.get("species") or "").strip()
        raw = row.get("fraction")
        if not species or raw in (None, ""):
            continue
        fraction = float(raw)
        (nuclides if _is_nuclide(species) else elements)[species] = fraction
    return nuclides, elements


def rows_from_spec(group: dict) -> List[dict]:
    """Composition grid rows for a group dict (nuclides first, then elements)."""
    rows = [{"species": name, "fraction": frac} for name, frac in group["nuclides"].items()]
    rows += [{"species": name, "fraction": frac} for name, frac in group["elements"].items()]
    return rows


def default_composition_rows() -> List[dict]:
    """The NETL default-fuel composition as grid rows (form starting point)."""
    return rows_from_spec(FuelMaterialSpec(name="_").to_dict())


def sab_to_text(laws) -> str:
    """S(a,b) laws as newline-separated text."""
    return "\n".join(laws)


def sab_from_text(text: str) -> List[str]:
    """Parse newline-separated S(a,b) laws (blank lines ignored)."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


# --- groups / assignments --------------------------------------------------------


def default_group() -> dict:
    """The default fuel group (NETL fresh fuel) placed at every location initially."""
    return FuelMaterialSpec(name=DEFAULT_GROUP_NAME, temperature=600.0).to_dict()


def initial_assignments() -> Dict[str, str]:
    """Assign every fuel location to the default group."""
    return {location: DEFAULT_GROUP_NAME for location in sorted(core_map.FUEL_LOCATIONS)}


def suggested_name(groups: List[dict]) -> str:
    """A suggested name for the next group, e.g. ``"Fuel Material 3"``."""
    return f"Fuel Material {len(groups) + 1}"


def most_common_group(assignments: Dict[str, str], fallback: str = DEFAULT_GROUP_NAME) -> str:
    """The most frequently assigned group (used as the default after a load)."""
    if not assignments:
        return fallback
    return Counter(assignments.values()).most_common(1)[0][0]


def upsert_group(
    groups: List[dict],
    name: str,
    density,
    temperature,
    nuclides: Optional[Dict[str, float]] = None,
    elements: Optional[Dict[str, float]] = None,
    percent_type: str = "wo",
    s_alpha_beta: Optional[List[str]] = None,
) -> List[dict]:
    """Add or replace (by name) a fuel group; returns the new list.

    Raises ``ValueError`` (via ``FuelMaterialSpec``) on invalid input.
    """
    extras: dict = {"percent_type": percent_type}
    if nuclides is not None or elements is not None:
        extras["nuclides"] = nuclides or {}
        extras["elements"] = elements or {}
    if s_alpha_beta is not None:
        extras["s_alpha_beta"] = tuple(s_alpha_beta)
    spec = FuelMaterialSpec(name=(name or "").strip(), density=float(density), temperature=float(temperature), **extras)
    data = spec.to_dict()
    result = [group for group in groups if group["name"] != data["name"]]
    result.append(data)
    return result


def paint(assignments: Dict[str, str], location: Optional[str], group: Optional[str]) -> Dict[str, str]:
    """Assign ``group`` to ``location`` (a fuel location); ignore other clicks."""
    if not location or not group or not core_map.is_fuel_location(location):
        return assignments
    updated = dict(assignments)
    updated[location] = group
    return updated


# --- outputs ---------------------------------------------------------------------


def build_pattern(groups: List[dict], assignments: Dict[str, str]) -> CoreLoadingPattern:
    """Build a validated ``CoreLoadingPattern`` from the GUI state.

    Assignments referencing a group that no longer exists are dropped.
    """
    group_objects = {group["name"]: FuelMaterialSpec.from_dict(group) for group in groups}
    valid = {loc: name for loc, name in assignments.items() if name in group_objects}
    return CoreLoadingPattern(groups=group_objects, assignments=valid)


def generate_specs_text(groups: List[dict], assignments: Dict[str, str], problem_id: str) -> str:
    """Render the ``specs.py`` text for the current state."""
    return render_specs(build_pattern(groups, assignments), SpecsConfig(problem_id=problem_id))


def pattern_json(groups: List[dict], assignments: Dict[str, str]) -> str:
    """Serialize the current state as a loading-pattern JSON blob."""
    return build_pattern(groups, assignments).to_json()


def load_pattern(upload_contents: str) -> Tuple[List[dict], Dict[str, str]]:
    """Parse a ``dcc.Upload`` payload into ``(groups, assignments)``."""
    _, _, encoded = upload_contents.partition(",")
    text = base64.b64decode(encoded).decode("utf-8")
    pattern = CoreLoadingPattern.from_json(text)
    groups = [spec.to_dict() for spec in pattern.groups.values()]
    return groups, dict(pattern.assignments)
