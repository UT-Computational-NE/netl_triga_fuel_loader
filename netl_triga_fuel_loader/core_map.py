"""TRIGA NETL core map: ring layout, reserved / fuel locations, and hex coordinates.

This module is a dependency-light (pure-Python) mirror of two upstream sources:

* the ring layout and reserved locations mirror CoreForge's
  ``coreforge.geometry_elements.triga.netl.core.Core`` (``RING_MAP`` /
  ``RESERVED_LOCATIONS``); and
* the fuel locations mirror the ``progression_problems`` NETL default core
  loading (the positions that build a ``FuelElement``) -- which is exactly the
  set that ``reactor(fuel_materials=...)`` accepts.

Keeping this a pure-Python mirror lets the engine be imported, linted, and unit
tested without the OpenMC / CoreForge stack. The mirror is guaranteed to match
its sources by ``tests/test_core_map_sources.py``, which imports them directly
and fails on any drift.

Location labels are ``"<ring>-<nn>"`` (1-indexed, zero-padded), e.g. ``"B-01"``.
Rings run A (center) through G (outermost); ring ``k`` holds ``6*k`` locations
(A is the single central location).
"""

from __future__ import annotations

from math import sqrt
from typing import Dict, List, Tuple

# Ring letters from center outward and their location counts.
RING_LETTERS: Tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G")
_RING_INDEX: Dict[str, int] = {letter: index for index, letter in enumerate(RING_LETTERS)}


def _ring_locations(letter: str) -> List[str]:
    """Ordered location labels for a ring (``["A-01"]`` for the center)."""
    index = _RING_INDEX[letter]
    count = 1 if index == 0 else 6 * index
    return [f"{letter}-{position:02d}" for position in range(1, count + 1)]


# Ordered rings, center (A) -> outermost (G). Mirrors CoreForge Core.RING_MAP
# (which lists them outermost -> center); verified in the source-of-truth test.
RINGS: Dict[str, List[str]] = {letter: _ring_locations(letter) for letter in RING_LETTERS}

# All core locations, center -> outward, in ring/position order.
ALL_LOCATIONS: Tuple[str, ...] = tuple(loc for letter in RING_LETTERS for loc in RINGS[letter])

# Reserved (non-loadable) locations: central thimble, the four control rods, and
# the six water holes. Mirrors CoreForge Core.RESERVED_LOCATIONS.
RESERVED_LOCATIONS: frozenset = frozenset(
    {"A-01", "C-01", "C-07", "D-06", "D-14", "G-01", "G-07", "G-13", "G-19", "G-25", "G-31"}
)

# Non-reserved positions that do not hold fuel in the NETL default loading: the
# D-03 graphite element, the G-32 source holder, and the E-11 / F-13 / F-14 /
# G-34 empty water holes.
NON_FUEL_LOCATIONS: frozenset = frozenset({"D-03", "G-32", "E-11", "F-13", "F-14", "G-34"})

# Locations that hold a fuel element in the NETL default loading -- i.e. the
# positions where a per-location fuel material may be placed. Mirrors the
# FuelElement positions of progression_problems' NETLDefaultGeometries.core().
FUEL_LOCATIONS: frozenset = frozenset(
    loc for loc in ALL_LOCATIONS if loc not in RESERVED_LOCATIONS and loc not in NON_FUEL_LOCATIONS
)


def ring_of(location: str) -> str:
    """Return the ring letter for a location label (e.g. ``"B-01" -> "B"``)."""
    if location not in _LOCATION_SET:
        raise KeyError(f"Unknown core location: {location!r}")
    return location.split("-", 1)[0]


def is_reserved(location: str) -> bool:
    """True if ``location`` is a reserved (non-loadable) position."""
    return location in RESERVED_LOCATIONS


def is_fuel_location(location: str) -> bool:
    """True if ``location`` may hold a per-location fuel material."""
    return location in FUEL_LOCATIONS


# --- hex geometry ----------------------------------------------------------

# Axial-coordinate step directions used to walk a hexagonal ring, in order
# (red-blob "Hexagonal Grids" ring algorithm).
_AXIAL_DIRECTIONS: Tuple[Tuple[int, int], ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)

# The ring walk begins at this corner, scaled by the ring radius, before stepping
# through _AXIAL_DIRECTIONS in order. (Per the red-blob algorithm, the start corner
# is the direction opposite the first step direction.)
_RING_START_DIRECTION: Tuple[int, int] = (-1, 1)


def _ring_axial_cells(k: int) -> List[Tuple[int, int]]:
    """Axial (q, r) coordinates of the ``6*k`` cells of hex ring ``k`` (``[(0,0)]`` for k=0)."""
    if k == 0:
        return [(0, 0)]
    cells: List[Tuple[int, int]] = []
    q, r = _RING_START_DIRECTION[0] * k, _RING_START_DIRECTION[1] * k
    for step in _AXIAL_DIRECTIONS:
        step_q, step_r = step
        for _ in range(k):
            cells.append((q, r))
            q, r = q + step_q, r + step_r
    return cells


def _axial_to_xy(q: int, r: int) -> Tuple[float, float]:
    """Pointy-top axial (q, r) -> Cartesian (x, y) with unit hex size."""
    x = sqrt(3.0) * (q + r / 2.0)
    y = 1.5 * r
    return (x, y)


def hex_coordinates() -> Dict[str, Tuple[float, float]]:
    """Map every core location to a Cartesian ``(x, y)`` for hex rendering.

    Locations are laid out as concentric hexagonal rings (ring ``k`` at hex-ring
    ``k``), center at the origin, position order following the label numbering.
    The absolute orientation is a rendering detail; it can be rotated/flipped by
    the GUI to match a reference core drawing.
    """
    coordinates: Dict[str, Tuple[float, float]] = {}
    for letter in RING_LETTERS:
        k = _RING_INDEX[letter]
        cells = _ring_axial_cells(k)
        locations = RINGS[letter]
        for location, (q, r) in zip(locations, cells):
            coordinates[location] = _axial_to_xy(q, r)
    return coordinates


_LOCATION_SET: frozenset = frozenset(ALL_LOCATIONS)
