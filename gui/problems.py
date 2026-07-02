"""Discover the available progression problems to target.

The generated ``specs.py`` is a drop-in for a problem under ``netl_triga_dt``'s
``progression_problems`` tree; this lists the problem IDs (leaf directory names
containing a ``specs.py``) for the GUI's problem dropdown. Returns an empty list
if ``netl_triga_dt`` is not installed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import List


def available_problems() -> List[str]:
    """Sorted problem IDs discovered under netl_triga_dt (e.g. ``["N_1_A", ..., "N_5_B"]``)."""
    spec = importlib.util.find_spec("netl_triga_dt")
    if spec is None or not spec.submodule_search_locations:
        return []
    root = Path(list(spec.submodule_search_locations)[0]) / "progression_problems"
    if not root.is_dir():
        return []
    return sorted({path.parent.name for path in root.rglob("specs.py")})
