"""Core loading pattern: which fuel group goes at which core location.

A :class:`CoreLoadingPattern` holds a set of named fuel groups (each a
:class:`~netl_triga_fuel_loader.materials.FuelMaterialSpec`) and an assignment of
core locations to those groups. It validates locations against
:mod:`~netl_triga_fuel_loader.core_map` (only fuel locations may be assigned) and
serializes to/from JSON so GUI sessions can be saved and resumed.

This module is dependency-light (no OpenMC); the specs are converted to
``openmc.Material`` only later, by the generator.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from netl_triga_fuel_loader.core_map import ALL_LOCATIONS, FUEL_LOCATIONS
from netl_triga_fuel_loader.materials import FuelMaterialSpec, require_unique_names

_ALL_LOCATION_SET = frozenset(ALL_LOCATIONS)


@dataclass
class CoreLoadingPattern:
    """A validated map of fuel groups to core locations.

    Attributes
    ----------
    groups : dict[str, FuelMaterialSpec]
        Named fuel groups, keyed by material name (``key == spec.name``).
    assignments : dict[str, str]
        Core location -> group name. Only fuel locations may be assigned; every
        assigned group name must exist in ``groups``.
    """

    groups: Dict[str, FuelMaterialSpec] = field(default_factory=dict)
    assignments: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise ``ValueError`` if the pattern is inconsistent."""
        for name, spec in self.groups.items():
            if spec.name != name:
                raise ValueError(f"Fuel group key {name!r} does not match its material name {spec.name!r}.")
        require_unique_names(self.groups.values())

        for location, group_name in self.assignments.items():
            if location not in _ALL_LOCATION_SET:
                raise ValueError(f"{location!r} is not a TRIGA core location.")
            if location not in FUEL_LOCATIONS:
                raise ValueError(
                    f"{location!r} is not a fuel location (it is reserved or holds a "
                    f"non-fuel element); fuel cannot be assigned there."
                )
            if group_name not in self.groups:
                raise ValueError(f"Location {location!r} is assigned to unknown fuel group {group_name!r}.")

    def add_group(self, spec: FuelMaterialSpec) -> None:
        """Add or replace a fuel group, then re-validate."""
        self.groups[spec.name] = spec
        self.validate()

    def assign(self, location: str, group_name: str) -> None:
        """Assign ``location`` to ``group_name``, then re-validate."""
        self.assignments[location] = group_name
        self.validate()

    def unassign(self, location: str) -> None:
        """Remove any assignment at ``location`` (no-op if unassigned)."""
        self.assignments.pop(location, None)

    def fuel_specs_by_location(self) -> Dict[str, FuelMaterialSpec]:
        """Return ``{location: FuelMaterialSpec}`` for every assigned location."""
        return {location: self.groups[group] for location, group in self.assignments.items()}

    def to_dict(self) -> Dict[str, Any]:
        """A JSON-serializable dict representation."""
        return {
            "groups": {name: spec.to_dict() for name, spec in self.groups.items()},
            "assignments": dict(self.assignments),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CoreLoadingPattern":
        """Build a pattern from a dict produced by :meth:`to_dict`."""
        groups = {name: FuelMaterialSpec.from_dict(spec_data) for name, spec_data in data.get("groups", {}).items()}
        assignments = dict(data.get("assignments", {}))
        return cls(groups=groups, assignments=assignments)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the pattern to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "CoreLoadingPattern":
        """Deserialize a pattern from a JSON string."""
        return cls.from_dict(json.loads(text))
