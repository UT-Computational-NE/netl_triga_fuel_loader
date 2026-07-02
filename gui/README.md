# gui

The Dash application (a thin layer over the `netl_triga_fuel_loader` engine):
an interactive radial hex map of the TRIGA core for placing fuel materials, a
material-definition form, and a **Generate Input File** button that writes a
`specs.py`.

Built in [#5](https://github.com/UT-Computational-NE/netl_triga_fuel_loader/issues/5)
(hex map) and [#6](https://github.com/UT-Computational-NE/netl_triga_fuel_loader/issues/6)
(forms + generate).

Install the GUI extras and run locally (from the repo root):

```bash
pip install -e ".[gui]"
python -m gui.app
```

## What it does

- **Problem** — pick a target problem from the dropdown (discovered from the
  problems available under `netl_triga_dt`).
- **Materials** — every fuel location starts assigned to a default material
  (`Fuel Material 1`, 600 K). Define additional materials (name, density,
  temperature, fraction type, an editable composition grid, and S(a,b) laws),
  click **Update Material** to add/update one, then select it in the Materials
  list and click fuel locations on the hex map to paint it there. Each material
  in the list shows a color swatch matching its cells on the map.
- **Save pattern / Load pattern** — serialize the current materials +
  assignments to JSON, or restore a previously saved one.
- **Generate Input File** — downloads a runnable, self-contained `specs.py` for
  the selected problem, with every fuel location assigned an explicit material.

## Notes

- The composition grid (`dash-ag-grid`) infers nuclide vs. element from the
  species format (a mass number, e.g. `U235`, is a nuclide; a bare symbol,
  e.g. `Cr`, is an element) -- no separate kind selector needed.
- Material selection uses a custom clickable list rather than `dcc.RadioItems`,
  since per-option colored labels are not reliably supported; see
  `gui/app.py` for the click-handling design (and why the material list only
  regenerates when the material set changes, not on every paint).
