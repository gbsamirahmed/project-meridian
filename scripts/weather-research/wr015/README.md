# WR015 — qualified model-ground / Atlas support experiment

[Scientific report](../../../docs/research/weather/model-ground-real-terrain-support-mismatch.md), [frozen pins](input-pins.json), [combined receipt](integrity-receipt.json).

One492,443-byte GFS HGT message from the same archived product as WR007; five unchanged native Swiss DTM cells. No acquisition client, terrain aggregation, production change or vertical conversion. Original profile and prospective metadata amendment are separately pinned. The actual quantity is WMO0/3/5 geopotential height: ecCodes `m` alias and NCEP/GDAL `gpm` labels preserved explicitly. Every real signed/absolute difference is null because the LN02 bridge is unresolved.

Use the existing primary Python3.12/ecCodes2.48.0/NumPy2.5.2/pyproj3.7.2/rasterio1.4.3 environment and a separate GDAL3.9.3/rasterio1.4.3 interpreter. No installation or fallback. The accepted NativeProj helper pins PROJ9.5.1, wheel3.7.2, DLL/database identity and disabled network; no height transformation. All dependencies are sealed in the pins. Paths below are caller-supplied placeholders, not downloads or committed personal paths.

```text
python -B scripts/weather-research/wr015/support_comparison.py --input <pinned-HGT.grib2> --forecast <WR007-t2m.grib2> --data-root <retained-meridian-data> --gdal-python <independent-python> --output <new-external-receipt.json>
```

Output must be new and outside the repository. Raw messages and terrain remain byte-identical; references are hashed before/after. One temporary GDAL array is removed after complete cell-aligned comparison. Scientific JSON is deterministic; separate resource JSON varies by process. Replaying without a reference interpreter fails, rather than passing/skipping independent evidence. No source files are moved and no full terrain raster array is read.

```text
python -B -m unittest discover -s scripts/weather-research/wr015 -p 'test_*.py' -v
```

For the **genuine** replay set `MERIDIAN_WR015_INPUT`, `MERIDIAN_WR007_INPUT`, `MERIDIAN_WR015_DATA` and `MERIDIAN_WR007_GDAL_PYTHON` to the pinned local inputs/existing interpreter. Optional `MERIDIAN_WR015_SCRATCH` specifies an owned temporary directory. Without these the genuine test is explicitly skipped, not validated. The final accepted run sets all variables and passes35 tests without skips:34 synthetic and one genuine full-grid/five-cell deterministic replay.

Nearest model sampling is angular-grid nearest, not universally geodesic nearest. Bilinear reuses WR008 geometry/arithmetic with explicit removal of Kelvin labels; native height numbers are not converted. Terrain sampling is one nearest centre with east/south tie, 0.5m half-open footprint. No model-cell terrain mean or exact three-dimensional Earth-reference equivalence is inferred.

Maintain **©swisstopo** attribution and the accepted source notices. Numerical integrity is distinct from height-datum equivalence and atmospheric accuracy. No temperature correction, skill, safety or commercial legal clearance. No next task begun.
