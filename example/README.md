# example

A worked example of per-location fuel loading and the input it generates.

| File | What it is |
|------|-----------|
| `build_example.py` | Defines the example loading pattern/config and regenerates the two files below. |
| `example_loading.json` | The example `CoreLoadingPattern` (fuel groups + location assignments), serialized. |
| `specs.py` | The runnable input generated from that pattern — drop-in for a problem's `setup.py`. |

The example places a hotter fuel (`Fuel_Hot`, 800 K) in the innermost ring
(B-01…B-06) and a warm fuel (`Fuel_Warm`, 700 K) in part of the next ring
(C-02…C-06); every other fuel location keeps the default fuel.

Regenerate the artifacts after changing `build_example.py`:

```bash
python example/build_example.py
```

`tests/test_example_end_to_end.py` checks that `specs.py` stays in sync with the
pattern and (when the OpenMC/CoreForge stack is available) that generating and
importing it yields a reactor with the per-location fuels and correct MPACT specs.
