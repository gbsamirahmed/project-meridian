# Preserve contour R&D and review existing Swiss contours

**12 October 2026. Offline visual experiment prepared; owner review pending.** Genuine [Riffelhorn pilot](source-aware-contour-pilot.md) remains **Outcome C**. No genuine processing was resumed, and no new scientific conclusion, map integration or preservation commit is claimed.

## Preservation and proposed commit inventory

Starting public `main`/locally recorded `origin/main`: `c952b8050c1259fe6d3f674e6f84195a3491d95a`, 0/0; no fetch. Before/after checks verify all seven original input sizes/hashes, **867 retained files / 64,250,005 bytes**, 113 protected production hashes and 42 canonical research statuses. The three Swiss masters and all historical receipts remain unchanged. Existing authorised processing, accounting, supervision and topology work is preserved. No private repository was accessed or modified.

Proposed research-preservation commit scope, subject to owner approval:

| Group | Contents |
|---|---|
| Existing contour pilot utility | All 36 files in `scripts/atlas/contour-pilot/`: original/memory-bounded methods, tests, sealed receipts/pins, accounting, supervision, conservative topology investigation, staged adapter and explicitly unapproved profile |
| Existing R&D records | Pilot, memory recovery, pipeline recovery, precomputed terrain proposal and staged adapter — historical outcomes retained |
| Offline visual experiment | Small packaging/viewer/figure utilities, focused tests, scoped lint config, README and lightweight validation receipt in `scripts/atlas/contour-visual-review/` |
| Documentation | This record and append-only development log; a current visual-review reference in the pilot record |

No application source, original DEM, generated contour payload, HTML data bundle, tile archive or PNG belongs in this commit. Full file inventory/hashes are retained in the external preservation receipt. Review found no unrelated tracked modification; the only tracked diff is the append-only development log. Commit and push remain **unapproved**.

## Actual products used

Master files are `${MERIDIAN_DATA_ROOT}/experiments/atlas/source-aware-contours-v1/execution-3/processing/run-1/{product}/{level}.ndjson`, with adjacent `manifest.json`. Each record contains two-dimensional LV95 **EPSG:2056** coordinates, `level` in **metres LN02 / EPSG:5728**, index and 20 m-subset flags, and a line identifier scoped to its level. Lines can be open or closed. They are neither GeoJSON longitude/latitude nor vector tiles.

| Product | 10 m lines / vertices | 20 m subset lines / vertices |
|---|---:|---:|
| `swiss-native`, native 0.5 m | 1,596 / 662,196 | 762 / 332,486 |
| `swiss-2m`, strict 4 × 4 means | 356 / 150,389 | 176 / 75,518 |
| `swiss-smoothed`, sigma 2 m / radius 6 m | 203 / 140,562 | 101 / 70,484 |

All 121 level-file hashes per product are checked, including empty files. Declared levels are 2000–3200 m every 10 m; non-empty levels are 2190–2970 m. Source is swissALTI3D **2024/2 DTM**, ©swisstopo / Swiss OGD. Original source/method pins, source support and epoch/accuracy limitations remain linked through the manifests and receipts. Coarse/smoothed fields are explicit reconstructions, not geometric simplification or improved accuracy claims. No Copernicus or incomplete transformed geometry enters the demonstration.

## Open the demonstration

In Chrome, press **Ctrl+O** and select:

```text
${MERIDIAN_DATA_ROOT}\experiments\atlas\contour-visual-review-v1\viewer\contours.html
```

The single **30,140,131-byte HTML file** contains the three master sets and all UI code. There is no server, provider, dependency acquisition or external resource. Disconnect internet if desired. Select each source and 10/20 m interval at the same camera; drag, wheel/+ /− zoom, and click a contour to inspect its retained elevation. **Fit study area** resets the view. Arrow keys and +/− also work when the canvas has focus. Changes between sources/intervals preserve the view.

The prepared static `figures-final/whole-study.png` and `figures-final/centre-detail.png` show six equal-weight panels each. The latter crops only the display to a 600 × 600 m central area; it does not alter the scientific extent or masters. All generated files are in the fresh external `contour-visual-review-v1` workspace, separate from the immutable genuine directory. Earlier draft figures remain as disposable new evidence.

## Display semantics, checks and limitations

The viewer copies each retained NDJSON geometry record **verbatim** into an embedded array. Only display coordinates are translated to a local LV95 origin, uniformly scaled and inverted in Y. Grid north is up; no true-bearing/geodesic claim is made. All 953,147 source coordinates pass round-trip checks at three scales, with recorded maximum difference **0 m at tested double precision**. Heights are never transformed, interpolated, rounded or inferred between lines. Screen rasterisation is not a new terrain product.

Content Security Policy uses the exact executable script hash and denies connections, images, fonts, workers and external resources. Static checks found no fetch/XHR/WebSocket or external resource references. This proves the viewer is self-contained; it does not monitor unrelated browser background traffic. All records, flags and counts are verified against the masters, including closed lines. No browser screenshot or actual pointer-interaction pass is claimed: Chrome automation was unavailable, and the available in-app browser **rejected local file URLs**. No server or alternative browser workaround was attempted. Owner review must confirm actual browser pan/zoom, source/interval switching, picking, layout and disconnected operation.

Validation passed: **74 existing synthetic research tests**, **six Python packaging tests**, **six Node viewer checks (zero skips)** and focused ESLint. Packaging took about **4 s**; the Node full-data check recorded **253,296,640 bytes current RSS**, not peak memory or Android performance. Two static figures were visually inspected; their layout spacing was corrected. No genuine DEM library/reader was invoked for packaging, and no contour derivation, network request, Android or Meridian launch occurred. The [lightweight receipt](../../scripts/atlas/contour-visual-review/visual-review-receipt.json) seals outputs/checks.

Relevant retained image folders contained perspective captures, rejected loading images and diagnostic plots; no suitable georeferenced north-up relief background was established. A neutral background is therefore used. Contour readability **over hillshade, roads and labels remains untested**. There are no automatic contour labels beyond picking, no comprehensive accessibility claim and no measured browser/mobile frame-rate baseline. Changing display scale/line weights can hide gaps or make neighbouring lines appear to intersect; raster appearance is not topology validation.

## Visual observations and minimum requirements

At the full study scale, native contours retain many small loops and fine waviness. The central 600 m comparison makes this more apparent. The strict 2 m reconstruction reduces much of this detail; the smoothed field reduces further small-scale waviness. Broad relief patterns remain recognisable in all panels. These are visual observations, not evidence that discarded details are false or smoothing is scientifically preferable.

20 m spacing approximately halves retained geometry and visibly eases crowding, but steep sectors still merge into dense bands at smaller display scales. Native geometry has about **4.4 times** the vertices of strict 2 m geometry. Geometric simplification is **not required to inspect** these retained lines in this offline experiment; its necessity/tolerance for efficient mobile delivery remains unresolved. The previously rejected whole-product simplification remains rejected. The rendered comparisons do not establish absence of every contour intersection or independent genuine repeatability.

A later product should preserve source/field identity, units/height reference and valid support; distinguish interval selection from smoothing/generalisation; maintain index hierarchy; and qualify unavailable data. These are supported semantic/readability requirements, not approval of these provisional colours, controls or a permanent contour UI.

## Packaging assessment and owner decisions

**The retained unsimplified masters are candidates for a subsequent bounded vector-tile packaging experiment**, not production-ready tiles. Their sealed levels, stable source-local line identities and completed single-run stitching/partition checks provide a useful starting point. A small experiment would still need explicit display/delivery XY conversion, clipping/buffers, quantisation and tile-edge tests, source/vertical metadata, label policy, lawful notices, multiscale density and measured client cost. The current 30 MB whole-study HTML is deliberately unsuitable as a proposed global/mobile delivery architecture. No packaging was begun.

Owner review now decides: whether the viewer works/readability is useful; which source/interval deserves further cartographic evaluation; and whether to authorise the **research-preservation commit**. A packaging experiment needs a separate bounded decision. Existing [staged continuation](staged-contour-continuation-adapter.md) workspace/member-cap blockers remain recorded but are not the immediate visual priority. No genuine rerun, new allowance, hillshade background, main-map integration or 3D work is authorised by this record.
