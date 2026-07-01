# gui

The Dash application (a thin layer over the `netl_triga_fuel_loader` engine):
an interactive radial hex map of the TRIGA core for placing fuel materials, a
material-definition form, and a **Generate Input File** button that writes a
`specs.py`.

Built in [#5](https://github.com/UT-Computational-NE/netl_triga_fuel_loader/issues/5)
(hex map) and [#6](https://github.com/UT-Computational-NE/netl_triga_fuel_loader/issues/6)
(forms + generate).

Install the GUI extras and run locally:

```bash
pip install -e ".[gui]"
python gui/app.py
```
