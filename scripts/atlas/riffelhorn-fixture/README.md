# Offline Riffelhorn preparation

Run from `project-meridian`, using the existing public-data GIS environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-fixture/prepare.py prepare --output ../meridian-data/derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-fixture/prepare.py verify --output ../meridian-data/derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-fixture/test_prepare.py
```

The frozen plan and specification define the only target. Exact inputs, native
headers, fields and original-ZIP selection are verified offline. Canonical output
contains full native geometries plus source-scoped semantic declarations and
raster bindings. A hash-sealed preparation manifest distinguishes complete output
from staging. The verifier reconstructs the source-qualified output; it is not
merely a check of a self-asserted manifest.

`--interrupt early` or `--interrupt pre-completion` leaves deliberately incomplete
isolated staging. There is no current/publication pointer. Immutable retry
validates old output and retains its staging metadata without overwriting history.
Temporary tests never alter retained inputs. Payloads and full geometries stay
outside Git. No registration, query, derivation, tiles, acquisition or serving.

`measure.py` repeats empty preparation and fresh processes; `validate.py` records
focused and established regression coverage. It does not rerun closed receipt
optimisation benchmarks. See the durable report for custody/scientific limitations.
