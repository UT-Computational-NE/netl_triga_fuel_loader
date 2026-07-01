"""Guards that core_map's hardcoded mirror matches its upstream sources.

Skipped automatically when CoreForge / progression_problems (and the OpenMC
stack they need) are not installed, so it runs in the heavy integration CI job
but not in the lightweight lint/smoke job.
"""

import pytest

from netl_triga_fuel_loader import core_map

pytest.importorskip("coreforge")
pytest.importorskip("progression_problems")

# pylint: disable=wrong-import-position
from coreforge.geometry_elements.triga import FuelElement
from coreforge.geometry_elements.triga.netl.core import Core
import progression_problems.TRIGA.NETL as NETL


def test_all_locations_match_coreforge_ring_map():
    upstream = {location for ring in Core.RING_MAP for location in ring}
    assert set(core_map.ALL_LOCATIONS) == upstream


def test_reserved_locations_match_coreforge():
    assert core_map.RESERVED_LOCATIONS == frozenset(Core.RESERVED_LOCATIONS)


def test_fuel_locations_match_default_core_loading():
    core = NETL.DefaultGeometries.core()
    upstream_fuel = {location for location, element in core.loading.items() if isinstance(element, FuelElement)}
    assert core_map.FUEL_LOCATIONS == upstream_fuel
