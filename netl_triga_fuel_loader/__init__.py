"""netl_triga_fuel_loader.

Engine for defining per-location NETL TRIGA fuel loading and generating a
runnable ``specs.py`` input for the MPACT / OpenMC reactor models.

The public engine API is added in subsequent tickets:
  * ``core_map``  -- TRIGA hex map + valid fuel locations
  * ``materials`` -- fuel-group / material data model
  * ``loading``   -- a core loading pattern object
  * ``generator`` -- renders ``specs.py`` from a loading pattern
"""

# Single source of truth for the package version; pyproject reads this via
# [tool.setuptools.dynamic]. Bump here on release.
__version__ = "0.1.0"
