# Riffelhorn — multiscale contours over offline hillshade

**Prepared 12 October 2026; visually reviewed and accepted by the owner on 13 October 2026 as a successful demonstration. Preservation commit remains unapproved.** This is a bounded cartographic experiment. The [scientific pilot](source-aware-contour-pilot.md) remains Outcome C; no genuine contour processing, missing-product derivation or repeatability run has resumed. Existing [visual review](contour-visual-demonstration.md) and [precomputed product architecture](precomputed-terrain-products.md) retain their qualifications.

## Open and compare

In Chrome, **Ctrl+O** and select:

```text
C:\Users\gbsam\Documents\Projects\meridian-data\experiments\atlas\multiscale-contours-hillshade-v1\viewer-final\contours-hillshade.html
```

Use **Automatic scale**, zoom slowly from the overview, then choose **Manual comparison** to switch any of the three representations and 10/20 m intervals at the same camera. Drag/arrow keys pan, wheel/+/−/pinch zoom, and clicking a contour reports its unchanged LN02 height. **Fit study area** resets the camera. Toggle Hillshade for a neutral comparison. The legend reports the active representation, interval, metre/CSS-pixel scale and whole-study line/vertex counts. Darker/thicker lines are 100 m index contours. Source notices and experimental limits are embedded.

The single **45,211,680-byte** HTML includes its PNG, source geometry and executable script. CSP denies network connections and external resources, permits only embedded images and the sealed executable script. No server is involved. The adjacent `bundle-receipt.json` seals the final HTML (`8a75d588bf7cbe7848682221e713838ead8d51a48a02635c071f0132842f476c`). The earlier `viewer/` directory is an encoding-error draft; use **viewer-final**, not that draft.

## Background and alignment

No suitable retained georeferenced north-up hillshade was established. The explicitly permitted small background render used only the **four pinned swissALTI3D 2024/2 0.5 m EPSG:2056 / EPSG:5728 DTM tiles**, ©swisstopo / Swiss OGD. Native 3 × 3 Horn gradients illuminate a flat image from **grid azimuth 315°, altitude 45°, z factor 1**. Neutral greys are composited at 50% opacity. This is a visual derivative, not numerical elevation evidence or a new contour source; epoch/accuracy limitations are unchanged.

The 4000 × 4000 PNG covers exactly `[2624000,1091000,2626000,1093000]`. Pixel centres are `E=2624000+(column+0.5)*0.5`, `N=1093000-(row+0.5)*0.5`. A common LV95 translation, uniform scale and north-up Y inversion places raster pixel edges and unchanged contour coordinates in the same 2000 × 2000 metre display footprint. **No reprojection, height transformation or coordinate rounding** occurs. Grid north is not asserted to be true north.

256-row strips share true neighbours across both the strip and 1 km source joins; no independent tile-edge shading is used. Any invalid neighbour makes shading transparent, including the outer one-pixel rim: **15,984,004 valid pixels**, exactly the 3998 × 3998 interior. Outside support remains neutral. The subset is not a national source boundary. PNG: **11,300,581 bytes**, SHA-256 `ff455800a74872e4529ebf25d03580df486a1b7f2683a31dcc4de8159f89f08c`. Background render: **2.8 s**, measured actual-process lifetime peak **203,534,336 bytes (194.1 MiB)**, one numerical thread, no children. The [utility README](../../scripts/atlas/contour-multiscale-review/README.md) documents guards and their limitations.

The four original input filenames are listed below; exact immutable SHA-256 pins and external paths are in [input-pins.json](../../scripts/atlas/contour-pilot/input-pins.json). No replacement or additional data was used.

| Swiss input | Native grid / height reference |
|---|---|
| `swissalti3d_2024_2624-1091_0.5_2056_5728.tif` | 0.5 m LV95 / LN02 |
| `swissalti3d_2024_2624-1092_0.5_2056_5728.tif` | 0.5 m LV95 / LN02 |
| `swissalti3d_2024_2625-1091_0.5_2056_5728.tif` | 0.5 m LV95 / LN02 |
| `swissalti3d_2024_2625-1092_0.5_2056_5728.tif` | 0.5 m LV95 / LN02 |

The existing contour masters are `swiss-native`, `swiss-2m` and `swiss-smoothed`, retained under external `source-aware-contours-v1/execution-3/processing/run-1/{product}/`. Their level-specific NDJSON records and manifests preserve source revision, EPSG:2056 coordinates, LN02 metre elevations and processing history. The background does not replace their provenance.

This **Swiss-native background differs from the heterogeneous Mapterhorn field in the application**. Its visual compatibility cannot establish that these contours match Mapterhorn everywhere. See [global evaluation](global-terrain-foundation-evaluation.md) and [source-product architecture](terrain-source-product-architecture.md).

## Provisional scale rules

| Nominal metres per CSS pixel | Active representation | Interval |
|---|---|---|
| ≥2 | Smoothed 2 m field | 20 m |
| 0.75–<2 | Strict 2 m field | 20 m |
| 0.25–<0.75 | Strict 2 m field | 10 m |
| <0.25 | Native 0.5 m field | 10 m |

Thresholds are small adjustable constants in `viewer.js`, **not map zoom levels, source accuracy or production policy**. A 12% hysteresis holds the active band near boundaries; source/interval changes wait 180 ms after interaction, and cannot occur while pointers remain down. The camera is preserved. 20 m is the retained even-level subset; no new levels are interpolated. Source switches are deliberately discrete: no invented morphing or elevation fusion. Genuine line-position changes remain possible because aggregation/smoothing reconstruct different fields. Close-scale magnification adds no source resolution.

All retained geometry remains unsimplified: native **662,196**, strict **150,389**, smoothed **140,562** master vertices. 20 m filtering displays **332,486 / 75,518 / 70,484** respectively. Elevation picking selects a retained line only, not an interpolated height at a position. The rejected whole-product simplification remains rejected.

## Validation and observed appearance

**25 focused tests passed:** five synthetic background tests; eight new Node viewer checks; six existing packaging tests; six existing viewer regressions. Focused ESLint passes. Python syntax, local document references, source/output seals and final preservation checks are recorded separately. Background tests cover flat/sloping illumination, height-offset invariance, north/south orientation, invalid neighbours, synthetic four-tile/strip equality and pixel-centre registration. Node checks cover threshold/hysteresis rules, affine zoom alignment, manual camera preservation, height picking, delayed source swaps, decoding failures, background toggle, embedded CSP and all **953,147** coordinate round trips (maximum observed difference **0 m** at tested double precision). Node current RSS was about **285 MB**, not measured browser peak or Android performance.

Two initial mock-control assertions exposed an explicit-UTF-8 copying error; it was corrected in new files and all eight checks rerun successfully. Installed Rasterio/NumPy/affine emit upstream deprecation warnings; none was suppressed or treated as a scientific failure. No new dependencies were acquired.

Static six-panel figures in external `figures/` were rendered and visually inspected at **2000 m overview**, **600 m ridge detail** and **100 m close detail**, keeping footprint, background and line hierarchy constant across variants. These are Pillow raster comparisons, **not browser screenshots**:

- Broad relief patterns and contour shape appear aligned; no obvious systematic displacement or source-tile shading seam was seen. That observation is not independent scientific accuracy evidence.
- 20 m spacing is clearer at overview scales; gentler slopes retain separation while cliff sectors remain crowded. 10 m adds substantial density, especially around the ridge.
- Strict/smoothed fields reduce fine waviness. At close scale the native lines reveal additional local undulation; the owner considers the current geometry and close-up detail satisfactory for now. This is visual acceptance, not an accuracy conclusion; further smoothing or reconstruction is not required at this checkpoint.
- Different reconstructed fields can place contours differently. Tests show camera-preserving, hysteretic, deferred swaps; the owner has accepted the demonstration after visual review. No separate quantified transition-distraction measurement was supplied.

The available browser tool previously rejected file URLs, so no server/browser workaround or automated Chrome pass is claimed. **Owner visual review is now accepted.** This does not establish separate measured passes for every gesture, keyboard path or disconnected-use check; no automated Chrome rendering or mobile-performance claim is made. No comprehensive contour-intersection validation or new genuine topology result follows from a raster picture. Steep-cliff congestion remains unresolved; no automatic labels or roads/basemap overlay were added.

## Preservation, costs and next decision

Seven input seals, **867 historical files / 64,250,005 bytes**, three canonical masters, **113 protected hashes**, original viewer and old processing/viewer utilities remain unchanged. No private application access/modification, external request, package installation, agent-run Android/Chrome map trial, commit or push; the owner separately reviewed the offline viewer. Only a new sibling utility directory, this report and an append-only development-log entry are proposed in Git. PNGs, HTML bundles, figures and full audit receipts remain external. The new experiment retains a corrected viewer plus its disposable first draft; final audit records whole-directory bytes. These display artefacts are not a new allowance for scientific continuation.

**Recommendation:** suitable candidates for a small, separately approved vector-tile packaging experiment **subject to separate scope approval**, with no production readiness claim. It must explicitly validate LV95-to-delivery XY conversion (unchanged LN02 values), clipping/buffers and shared-edge quantisation, line identity and coverage, source/field/vertical metadata, interval/detail bands, index/label placement, notices and source rights, generated tile/storage volume and measured mobile decoding/render cost. Unsimplified geometry is sufficient to begin a bounded packaging comparison; topology-safe simplification is not a prerequisite. This 45 MB whole-study bundle is not a mobile delivery design.

## Owner acceptance and next cartographic direction

The owner accepts the current experiment as a **successful visual demonstration**, including satisfactory current contour geometry and close-up detail. It is not a production-ready terrain product, proof of scientific accuracy, completed genuine repeatability or worldwide coverage. Preserve the accepted geometry; no further smoothing or reconstruction is required now.

The next cartographic direction is broader zoom-out behaviour: contours should eventually **disappear at sufficiently distant/regional scales**, then progress through broad intervals such as **100 m → 50 m → 20 m → 10 m** while geometric detail increases during zoom-in. Native high-resolution detail should remain available where justified. Interval selection and field reconstruction/generalisation are distinct choices; a broad interval is not permission to alter heights or merge sources.

This is a direction for a later bounded experiment, **not implemented here**. Precise thresholds, any later smoothing policy and global source coverage remain unresolved. No new contour extraction is implied: interval subsets could first be tested against existing retained levels, with source/support qualifications intact. This preservation review does not approve new processing, packaging or application integration.

The present four-band rules remain an accurate record of the accepted demonstration, not a permanent regional/global policy. The immediate owner decision is whether to approve the scoped preservation commit. No integration, global processing, offline manager or 3D work has begun.
