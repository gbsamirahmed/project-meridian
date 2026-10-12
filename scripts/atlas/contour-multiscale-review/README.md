# Offline multiscale contours over hillshade

Small cartographic experiment, separate from the application and genuine contour processing. See the [review record](../../../docs/atlas/multiscale-contours-hillshade.md). No service, package acquisition or production policy.

Open the prepared external `experiments/atlas/multiscale-contours-hillshade-v1/viewer-final/contours-hillshade.html` in Chrome with **Ctrl+O**. It contains all three unchanged Swiss contour masters and the hillshade PNG. No server or internet is needed. Use Automatic scale, wheel/+/−/pinch and drag; switch to Manual comparison to select any source/interval at the same camera. Click a contour for its retained LN02 height. The background checkbox allows a neutral comparison. Fit study area returns to the overview.

`viewer.js` defines four provisional bands in metres per CSS pixel, independent of screen density: 2, 0.75 and 0.25 m/CSS px boundaries, 12% hysteresis and 180 ms settling. Editing these requires rebuilding the HTML; this is not a delivery-zoom specification. 100 m indices are darker/thicker. No contour labelling engine is implemented.

## Reproduce locally

From the public repository in PowerShell, use the already installed runtimes; output arguments must be **fresh directories outside Git**. These commands render a small visual background and package existing lines, never extract contours. The first command intentionally reads the four pinned DTM rasters and must not be confused with permission to run a scientific continuation.

```powershell
$dataRoot = 'C:\Users\gbsam\Documents\Projects\meridian-data'
$reviewRoot = "$dataRoot\experiments\atlas\multiscale-contours-hillshade-v1"
$python = "$dataRoot\earth-lab\.venv\Scripts\python.exe"
# Use fresh output names for a repeat; the prepared directories already exist.
& $python -B scripts/atlas/contour-multiscale-review/background.py --data-root $dataRoot --output "$reviewRoot\background-new"
& $python -B scripts/atlas/contour-multiscale-review/build.py --data-root $dataRoot --background "$reviewRoot\background-new" --output "$reviewRoot\viewer-new"
& $python -B scripts/atlas/contour-multiscale-review/render_comparison.py --html "$reviewRoot\viewer-new\contours-hillshade.html" --background "$reviewRoot\background-new\hillshade.png" --output "$reviewRoot\figures-new"
```

`background.py` uses native 0.5 m samples, 256-row strips with neighbour overlap, a 32 MiB GDAL cache and one numerical thread. It applies the existing Windows self-process memory guard (512 MiB resident maximum, 384 MiB private commit), checks a cooperative 60-second deadline, and limits its PNG to 64 MB. No children are launched. The deadline is checked between bounded strips and after PNG writing; it is not a new hard-time supervisor. Output is transparent when any slope-neighbour sample is invalid, including the outer rim. Read-only source hashes are checked before/after. GeoTIFF sidecar creation and PROJ networking are disabled.

Packaging reuses the existing verified, verbatim NDJSON packager; it verifies all historical membership/hashes before/after and rejects an HTML exceeding 64 MB. Receipts describe affine registration and source meaning. A failed new partial file is not historical evidence and is not silently accepted as a viewer. Keep each repeat explicit rather than accumulating archives.

## Focused checks

```powershell
Push-Location scripts/atlas/contour-multiscale-review
& $python -B -m unittest test_background -v
Pop-Location
$env:MERIDIAN_MULTISCALE_HTML = "$reviewRoot\viewer-final\contours-hillshade.html"
node --test scripts/atlas/contour-multiscale-review/test_viewer.mjs
node node_modules/eslint/bin/eslint.js --config scripts/atlas/contour-multiscale-review/eslint.config.mjs scripts/atlas/contour-multiscale-review/viewer.js scripts/atlas/contour-multiscale-review/test_viewer.mjs
```

The Node tests include a mock canvas/control environment, not a browser rendering or touch-performance test. Browser layout, genuine gestures, perceived threshold shifts and disconnected operation require owner review. The 45 MB whole-study HTML is intentionally an experimental desktop artefact; no mobile delivery suitability is inferred.
