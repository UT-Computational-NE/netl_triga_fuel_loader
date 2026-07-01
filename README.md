# netl_triga_fuel_loader

A utility for defining **per-location fuel loading** of the NETL TRIGA reactor and
generating a ready-to-run `specs.py` input for the neutronics models
(MPACT / OpenMC) built on top of
[`progression_problems`](https://github.com/UT-Computational-NE/progression_problems)
and [`CoreForge`](https://github.com/UT-Computational-NE/CoreForge).

## What it does

1. Lets a user define one or more **fuel materials** (composition, density, temperature).
2. Lets the user **place** those materials at specific core locations via an
   interactive radial hex map of the TRIGA core.
3. **Generates an input file** (`specs.py`) that propagates the chosen fuel
   materials into the reactor model, so the standard `setup.py` scripts produce
   an MPACT/OpenMC model with the per-location fuel.

## Design

The project is split into a pure-Python **engine** and a thin **GUI**, so the
generator is testable without a UI and the frontend stays swappable:

```
netl_triga_fuel_loader/      # pure-Python engine (no GUI imports)
  core_map.py                # TRIGA hex rings + valid fuel locations
  materials.py               # fuel-group / material data model + make_fuel()
  loading.py                 # a "core loading pattern" object
  generator.py               # renders specs.py from a loading pattern
example/                     # example specs.py-style file the tool can regenerate
gui/                         # Dash app (thin layer over the engine)
tests/
```

## Status

Early scaffolding. The roadmap is tracked in
[Issues](https://github.com/UT-Computational-NE/netl_triga_fuel_loader/issues).
