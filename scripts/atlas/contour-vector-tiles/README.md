# Source-aware Riffelhorn contour MVT feasibility

Offline, bounded visual prototype using existing Swiss masters, not new contour extraction. See the [feasibility record](../../../docs/atlas/contour-vector-tile-feasibility.md). The application is untouched.

The prepared demo is **http://127.0.0.1:5180/**. Use the wheel/+/− to explore scale bands; **Regional scale** hides contours, **Study area** restores z14. Select a product and manual 100/50/20/10 m interval for same-camera comparison; click a visible line for LN02 metres/source identity. The previous offline viewer link opens the accepted 45 MB artefact separately. No live map provider, DEM read, glyphs, sprite, account or key is involved. Outside the retained study footprint there is only a neutral background, not claimed elevation coverage.

## Existing tools

Installed public-repository dependencies: MapLibre GL JS 6.11.2 (BSD-3-Clause), geojson-vt 6.1.1 (ISC), vt-pbf 4.3.2 (MIT), vector-tile 3.0.0 / pbf 5.1.2 (BSD-3-Clause), Vite 8.0.16 (MIT). Installed scientific venv: PyProj 3.7.2 / PROJ 9.5.1, NumPy, Rasterio and Pillow. Existing packages are reused without installation or package/lockfile edits. Retain their licence notices; the data remain ©swisstopo / Swiss OGD with source-specific qualifications.

## Start or stop the prepared demonstration

From the public repository:

```powershell
$env:MERIDIAN_TILE_ROOT = 'C:\Users\gbsam\Documents\Projects\meridian-data\experiments\atlas\contour-vector-tiles-v1'
node scripts/atlas/contour-vector-tiles/serve.mjs $env:MERIDIAN_TILE_ROOT 5180
```

The server binds **127.0.0.1 only** and serves an explicit resource whitelist, not the repository or arbitrary data workspace. Stop that terminal with **Ctrl+C**. Missing expected product files return an error; legitimate outside-product tile requests return a valid empty MVT. No caching/offline manager or production host is created. `/stats` is local, aggregate request/response-body accounting, not external telemetry.

## Reproduction commands — fresh output only

The experiment has already run; do not overwrite it. For an explicitly intended repeat, set a **fresh external** output directory. These commands transform existing XY records and horizontally warp the retained intensity/alpha PNG; they do not derive contours or recompute hillshade from a DEM.

```powershell
$dataRoot = 'C:\Users\gbsam\Documents\Projects\meridian-data'
$env:MERIDIAN_TILE_ROOT = "$dataRoot\experiments\atlas\contour-vector-tiles-new"
& "$dataRoot\earth-lab\.venv\Scripts\python.exe" -B scripts/atlas/contour-vector-tiles/prepare.py --data-root $dataRoot --output $env:MERIDIAN_TILE_ROOT
node --expose-gc --max-old-space-size=512 scripts/atlas/contour-vector-tiles/package.mjs $env:MERIDIAN_TILE_ROOT
node node_modules/vite/bin/vite.js build --config scripts/atlas/contour-vector-tiles/vite.config.mjs
```

`prepare.py` verifies seven input pins and the historical inventory, transforms EPSG:2056 XY to WGS84 using the recorded offline non-ballpark operation, and leaves LN02 elevations untouched. Preparation checks 120 seconds, 64 MB per GeoJSON, 100 MB total prepared storage and a 20-million-pixel visual warp ceiling. These are cooperative checks, not a new resource-supervision framework. It reads the previous hillshade PNG, never the source DEM.

`package.mjs` builds one spatially filtered GeoJSONVT index per output tile and retires it with explicit GC. Public library APIs only. It writes MVT v2, XYZ z10–17, extent8192, buffer64, tolerance0; ordinary overzoom supplies closer display. It reserves count/bytes before writing and checks 2500 tiles, 120 MB tile bodies, 120 seconds and 1 GiB RSS; Node heap cap512 MiB. No background worker or distributed processing. Its bounds are intentionally one 2 km study area, not a general pipeline. Use `tile-receipt.json` for settings, versions, hashes, exact counts and representative seam evidence.

## Validation

With the prepared product/server:

```powershell
$env:MERIDIAN_TILE_ROOT = 'C:\Users\gbsam\Documents\Projects\meridian-data\experiments\atlas\contour-vector-tiles-v1'
node --test scripts/atlas/contour-vector-tiles/test_tiles.mjs
node node_modules/eslint/bin/eslint.js --config scripts/atlas/contour-vector-tiles/eslint.config.mjs scripts/atlas/contour-vector-tiles/*.mjs scripts/atlas/contour-vector-tiles/demo.js
# Optional repeat of the installed headless Chromium test, into a fresh external directory:
$env:MERIDIAN_BROWSER_OUTPUT = "$env:MERIDIAN_TILE_ROOT\browser-review-repeat"
node scripts/atlas/contour-vector-tiles/test_browser.mjs
```

The browser test blocks non-loopback HTTP requests. Chromium/SwiftShader timing is a desktop test condition, not Android or hardware-GPU performance. The owner accepts the visual and technical prototype, including refined index opacity. Android touch/pinch and mobile performance remain untested. Test output, screenshots, transformed GeoJSON, tiles, imagery and all partial attempts belong outside Git. Original input/source/output data must never be included in a research utility commit.

## Focused index prominence

Automatic100 m indices now fade from zero at z11 through opacity0.08/0.22/0.60 at z11.5/12/13, peak at1.00 at z14, then decrease to0.60/0.40/0.30 at z16/18/21. These provisional linear stops do not change ordinary-contour interval rules or manual comparison opacity. Source fades are unchanged; independent reconstructed fields can still briefly show doubled lines. See the report for the limitation and future options.

The fractional-zoom browser comparison reuses the existing server and requires a **fresh external directory**:

```powershell
$env:MERIDIAN_OPACITY_OUTPUT = "$env:MERIDIAN_TILE_ROOT\opacity-review-new"
node scripts/atlas/contour-vector-tiles/test_opacity.mjs
```

The accepted-data geometry test compares an existing `geometry-validation.json` read-only, creating it only when absent. No tile, terrain or metadata regeneration is part of an opacity review.
