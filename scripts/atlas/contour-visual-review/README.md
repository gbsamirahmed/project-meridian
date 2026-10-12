# Offline Riffelhorn contour review

This is a disposable experimental viewer of **existing** unsimplified Swiss contour masters, not a Meridian feature. [Research/visual review](../../../docs/atlas/contour-visual-demonstration.md) records qualifications and owner decisions. No DEM decoding, contour generation, provider, development server or application dependency is involved.

The prepared file is `${MERIDIAN_DATA_ROOT}/experiments/atlas/contour-visual-review-v1/viewer/contours.html`. Open it directly with Chrome: **Ctrl+O**, select that file. It needs no server or internet. Choose a source and 10/20 m interval; drag to pan, use the wheel or +/− to zoom, click a line for its unchanged metre LN02 elevation. Source/interval changes preserve the camera. **Fit study area** returns to the 2 × 2 km footprint. Grid north is up. The 500 m grid and scale are LV95 planar metres, not a geodesic distance service.

All source records are copied verbatim; the screen uses an explicit local EPSG:2056 origin, uniform scale and Y inversion. No reprojection, vertical conversion, rounding or geometric simplification is performed. 20 m is a selection of retained even levels, not new contour derivation. Source notices/qualifications are embedded. The neutral background avoids unverified alignment with retained perspective screenshots.

Content Security Policy denies connections and all external resources; the executable script is SHA-256 authorised. There is no fetch, external font, map provider, worker or image request. Ordinary browser/app background traffic is outside this file's control. Self-contained HTML embeds about 30 MB of geometry for review; this is **not** a proposed mobile delivery format. Browser rendering and controls require owner confirmation; the available automated browser blocks `file:` URLs.

Use installed tools only. These commands read existing masters, never scientific DEMs, and require a fresh output child:

```powershell
& $terrainControllerPython -B scripts/atlas/contour-visual-review/build.py `
  --data-root $terrainData --output "$terrainData/experiments/atlas/contour-visual-review-v1/new-viewer"
& $terrainControllerPython -B -m unittest discover -s scripts/atlas/contour-visual-review -p test_bundle.py
$env:MERIDIAN_CONTOUR_HTML = "$terrainData/experiments/atlas/contour-visual-review-v1/viewer/contours.html"
node --test scripts/atlas/contour-visual-review/test_viewer.mjs
node node_modules/eslint/bin/eslint.js --no-config-lookup `
  --config scripts/atlas/contour-visual-review/eslint.config.mjs `
  scripts/atlas/contour-visual-review/viewer.js scripts/atlas/contour-visual-review/test_viewer.mjs
& $terrainPython -B scripts/atlas/contour-visual-review/render_comparison.py `
  --html $env:MERIDIAN_CONTOUR_HTML --output "$terrainData/experiments/atlas/contour-visual-review-v1/new-figures"
```

Only the figure exporter uses already installed Pillow 12.3.0. Python packaging is standard-library-only; Node tests use built-ins and lint reuses existing ESLint. No installation or new dependency is needed. Generated HTML, PNGs and bulky contour copies stay outside Git. All historical inputs/products/receipts remain immutable; no commit or push is authorised by these instructions.
