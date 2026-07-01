"""Fuel-material data model for the fuel loader.

``FuelMaterialSpec`` is a plain, serializable description of a U-ZrH fuel
composition (no OpenMC dependency), so the data model and the loading logic stay
dependency-light. ``make_fuel`` is the single bridge that turns a spec into an
``openmc.Material``; it is the only part of this module that imports OpenMC.

The defaults reproduce the ``progression_problems`` NETL fresh-fuel composition
(U-ZrH, 5.85 g/cc), so a spec created with just a name matches the standard fuel
and can then be tweaked (enrichment, density, temperature, ...).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple

# NETL default fresh-fuel composition (weight fractions), from progression_problems
# TRIGA DefaultMaterials.fresh_fuel (Redhouse et al. NETL-FF-BP1/5-128-cca).
_DEFAULT_FUEL_NUCLIDES: Dict[str, float] = {
    "H1": 0.014355,
    "Mn55": 0.0014287,
    "U235": 0.0152,
    "U238": 0.061568,
    "Zr90": 0.43706,
    "Zr91": 0.0942,
    "Zr92": 0.14253,
    "Zr94": 0.14136,
    "Zr96": 0.02228,
}
_DEFAULT_FUEL_ELEMENTS: Dict[str, float] = {
    "Cr": 0.013573,
    "Fe": 0.049647,
    "Ni": 0.0067863,
}
_DEFAULT_S_ALPHA_BETA: Tuple[str, ...] = ("c_H_in_ZrH", "c_Zr_in_ZrH")

DEFAULT_FUEL_DENSITY: float = 5.85
DEFAULT_FUEL_TEMPERATURE: float = 293.6

# Keys accepted by FuelMaterialSpec.from_dict; anything else is rejected so that a
# hand-edited/typo'd key (e.g. "densty") fails loudly instead of silently defaulting.
_SPEC_KEYS: frozenset = frozenset(
    {"name", "density", "density_units", "temperature", "nuclides", "elements", "percent_type", "s_alpha_beta"}
)


@dataclass(frozen=True)
class FuelMaterialSpec:
    """A serializable U-ZrH fuel definition.

    Attributes
    ----------
    name : str
        Unique material name. Distinct compositions must use distinct names so
        that CoreForge does not merge or reject them downstream.
    density : float
        Material density (default 5.85).
    density_units : str
        Density units understood by ``openmc.Material.set_density`` (default 'g/cm3').
    temperature : float
        Temperature in Kelvin (default 293.6).
    nuclides : Mapping[str, float]
        Nuclide -> fraction (see ``percent_type``). Defaults to the NETL fresh fuel.
    elements : Mapping[str, float]
        Element -> fraction (see ``percent_type``). Defaults to the NETL fresh fuel.
    percent_type : str
        'wo' (weight) or 'ao' (atom). Default 'wo'.
    s_alpha_beta : tuple[str, ...]
        Thermal scattering laws to add (default the ZrH laws).
    """

    name: str
    density: float = DEFAULT_FUEL_DENSITY
    density_units: str = "g/cm3"
    temperature: float = DEFAULT_FUEL_TEMPERATURE
    nuclides: Mapping[str, float] = field(default_factory=lambda: dict(_DEFAULT_FUEL_NUCLIDES))
    elements: Mapping[str, float] = field(default_factory=lambda: dict(_DEFAULT_FUEL_ELEMENTS))
    percent_type: str = "wo"
    s_alpha_beta: Tuple[str, ...] = _DEFAULT_S_ALPHA_BETA

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("FuelMaterialSpec.name must be a non-empty string.")
        if self.density <= 0.0:
            raise ValueError(f"FuelMaterialSpec.density must be positive; got {self.density}.")
        if self.temperature < 0.0:
            raise ValueError(f"FuelMaterialSpec.temperature must be >= 0 K; got {self.temperature}.")
        if self.percent_type not in ("wo", "ao"):
            raise ValueError(f"FuelMaterialSpec.percent_type must be 'wo' or 'ao'; got {self.percent_type!r}.")
        if not self.nuclides and not self.elements:
            raise ValueError("FuelMaterialSpec must define at least one nuclide or element.")

    def to_dict(self) -> Dict[str, Any]:
        """A JSON-serializable dict representation."""
        return {
            "name": self.name,
            "density": self.density,
            "density_units": self.density_units,
            "temperature": self.temperature,
            "nuclides": dict(self.nuclides),
            "elements": dict(self.elements),
            "percent_type": self.percent_type,
            "s_alpha_beta": list(self.s_alpha_beta),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FuelMaterialSpec":
        """Build a spec from a dict produced by :meth:`to_dict`.

        Unexpected keys are rejected (rather than silently ignored) so that a typo
        or stale field surfaces as an error instead of a wrong default.
        """
        unexpected = set(data) - _SPEC_KEYS
        if unexpected:
            raise ValueError(f"Unexpected key(s) in fuel material spec: {sorted(unexpected)}")
        return cls(
            name=data["name"],
            density=data.get("density", DEFAULT_FUEL_DENSITY),
            density_units=data.get("density_units", "g/cm3"),
            temperature=data.get("temperature", DEFAULT_FUEL_TEMPERATURE),
            nuclides=dict(data.get("nuclides", _DEFAULT_FUEL_NUCLIDES)),
            elements=dict(data.get("elements", _DEFAULT_FUEL_ELEMENTS)),
            percent_type=data.get("percent_type", "wo"),
            s_alpha_beta=tuple(data.get("s_alpha_beta", _DEFAULT_S_ALPHA_BETA)),
        )


def make_fuel(spec: FuelMaterialSpec) -> "openmc.Material":
    """Build an ``openmc.Material`` from a :class:`FuelMaterialSpec`."""
    # Imported here (not at module top) so the data model stays usable without the
    # OpenMC stack; openmc is present wherever a material is actually built.
    import openmc  # pylint: disable=import-error,import-outside-toplevel

    material = openmc.Material(name=spec.name)
    material.temperature = spec.temperature
    material.set_density(spec.density_units, spec.density)
    for nuclide, fraction in spec.nuclides.items():
        material.add_nuclide(nuclide, fraction, percent_type=spec.percent_type)
    for element, fraction in spec.elements.items():
        material.add_element(element, fraction, percent_type=spec.percent_type)
    for law in spec.s_alpha_beta:
        material.add_s_alpha_beta(law)
    return material


def require_unique_names(specs: Iterable[FuelMaterialSpec]) -> List[FuelMaterialSpec]:
    """Return the specs, raising ``ValueError`` if two share a name but differ.

    Mirrors CoreForge's same-name/same-composition rule: identical specs may share
    a name, but two distinct compositions under one name are rejected.
    """
    seen: Dict[str, FuelMaterialSpec] = {}
    result: List[FuelMaterialSpec] = []
    for spec in specs:
        existing = seen.get(spec.name)
        if existing is None:
            seen[spec.name] = spec
            result.append(spec)
        elif existing != spec:
            raise ValueError(
                f"Two different fuel materials share the name {spec.name!r}; " f"give each distinct composition a unique name."
            )
    return result
