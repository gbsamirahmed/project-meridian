# Bounded Copernicus + Swiss Atlas terrain hierarchy

Evaluation: 2026-10-04; verification/record finalized 2026-10-05. Baseline: `74ea75b1577fbdd7a85af3a1989ac8aee42c54f0`.
Status: **negative continuity result; useful scale/support evidence; no production adoption**.

**MERIDIAN EVIDENCE (M)** below means this bounded experiment, not global validation.
**EXTERNAL EVIDENCE (E)** identifies published source/implementation facts.
**RESEARCH HYPOTHESES / DIRECTIONS (H)** remain untested unless explicitly measured.

## Question, frozen inputs and success criteria

Can a common/coarse Copernicus representation supply broad context while preferred
Swiss children retain authoritative regional information, without false boundary
terrain or a broad arbitrary modification collar? The [plan](terrain-hierarchy-plan.json)
was recorded before implementation; the [policy](terrain-hierarchy-policy.json)
was frozen after common/H0 scale discovery, before the H1 navigation evaluation.

Both complete parent products and their canonical source inputs passed their existing
hash verifiers before use. No source was acquired, regenerated or edited.

| Role | Frozen product identity | Retained semantics |
| --- | --- | --- |
| Common/coarse | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2` | Six 2021 public GLO-30 COGs, exact sub-release unknown, edited DSM, one-arcsecond posts, EGM2008; complete two-root z8–13 mean pyramid |
| Preferred regional | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` | 100 official swissALTI3D 2024 inputs; 2021/22 LiDAR basis with 2023 updates, cell epoch unknown; DTM, 0.5 m distributed LV95 grid, LN02; complete supported delivery tiles z12–18 |

Input details and immutable manifests remain in the
[common product](copernicus-common-product.md) and
[Swiss support product](riffelhorn-swiss-support-product.md) records.
The protected interior remains a 1.5 km circle around LV95 [2625000,1092000].
Source support remains the surrounding 10 km square, not a validated seamline.

Success required useful regional detail, exact regional elevations when selected
inside the protected interior, unchanged common fallback signal, recoverable
contributors, understandable scale transitions and no unacceptable walls during
supported navigation. Numerical loading success alone was insufficient.

Production remains AWS visual terrain and independent AWS analytical z15 terrain.
All `src/`, normal Vite configuration and dependency files remain unchanged.
MapLibre 6.11.2, IGOR, its strengthened curve, 315° map anchoring, colors,
exaggeration 1.45, atmosphere, basemap, projection and camera behavior were held fixed.
Weather was unavailable through the existing evaluation-only 503 fixture; its
rendering/calculations and Traverse were not altered. No imagery work was performed.

## Representation, scale and spatial semantics

Common terrain provides lower-detail context. Regional terrain provides preferred
detail only where its actual **per-level complete delivery tile** exists.
Protected interior means preservation of the selected regional surface, not a
requirement that a coarse context representation reproduce Swiss point heights.
Regional source support, delivered coverage and validated transition support remain
different concepts. A heterogeneous selected stream is not labelled "Swiss terrain".

Two strategies and one common-only control were tested:

- **H0:** exact Swiss tile wherever the existing regional product supplies one at
  the requested DEM level; common otherwise. Swiss is absent below its z12 delivery
  floor. This is the hard spatial control, not an accepted product boundary.
- **H1:** common below requested DEM z14; exact supported Swiss tiles at z14–18;
  common otherwise. Scale eligibility and tile support are independent predicates.
- **Common-only:** original common tiles through z13; explicitly resampled common
  signal at higher delivery levels, under the same evaluation source ceilings.

There was no feather, correction field, seam fitting or weighted fusion. Optional
whole-view support gating was not implemented: the measured common-to-regional
height changes already show that switching an entire view could relocate the
continuity problem rather than establish a supported transition. That remains a hypothesis,
not an evaluated third strategy. No further variants were pursued to force success.

### Fixed camera discovery and actual requested scales (M)

Viewport 1440×900, DPR1, locale en-GB, Europe/London; Chromium version and actual
camera/bounds/DEM levels are in [renderer evidence](terrain-hierarchy-renderer.json).
Central camera: [7.76121329,45.97910794]. Purpose names describe these views,
not universal zoom categories.

| Purpose / camera | Geometry request levels seen | Relief request levels seen | Observation |
| --- | --- | --- | --- |
| Landscape 9.4, pitch45, bearing0 | 8–9 | 9–11 | Common supplies broad structure; no regional children |
| Wide planning 11.4, pitch45 | 8–11 | 11–13 | H0 changes little; H1/common stay common |
| Approach 12.4, pitch55 | 8–13 | 11–14 | Early finer relief requests; no sharp universal switch |
| Close 13.2, pitch55 | 8,10–14 | 12–15 | Regional channels/ledges visibly useful; H1 retains coarser geometry longer than H0 |
| Closer 14.2, pitch55 | 8,10–15 | 12–16 | Swiss cliff/ridge and channel structure clearly useful |
| Detail 16.2, pitch55 | 8–16 | 13–18 | Common remains smooth/oversampled; regional detail is substantial |

These are **requested/source-manager levels**, not a claim that every visible
mesh uses the finest level. The later capture tool additionally records actual
DEM parents used by renderable terrain meshes. During motion, loaded coarser
parents often remained active while requested children loaded.

At benchmark latitude, z13 postings are about 13.28 m; z14 about 6.64 m and z18
about 0.415 m. Copernicus source posts remain approximately 21.5 m east/west and
30.9 m north/south. Higher common delivery adds no observations. Swiss's 0.5 m
grid is not independent 0.5 m measurement resolution.

Actual settled H0 mesh DEM levels include8 at landscape,9–10 in planning,
10–13 at close, and9/11–15 in detail. Fine relief can therefore reveal more
source texture than the current mesh resolves. Neither source delivery ceilings
nor camera zoom imply a 0.5 m rendered geometry resolution.

The conservative H1 z14 tile gate admits detail at closer views and suppresses
premature regional coarse children. It is not an optimized threshold. Hillshade
and geometry request different levels, so fine regional hillshade can precede
regional mesh geometry. A single camera zoom cannot describe this selection.

Map bounds transformed approximately to LV95 span about 173 km horizontally in
the landscape view, 43 km in wide planning, 16 km in the close view, and 2 km
in the detail view. Bounds are conservative axis-aligned footprints, not uniform
screen resolution. The close view reaches outside the 10 km selection; the central
detail footprint fits inside it. Thus scale gating reduces normal central exposure
to the edge but does not protect lateral navigation or the pitched background.

## Height-reference decision (E, M)

**Native heights were preserved.** Copernicus cells remain EGM2008 and selected
Swiss cells remain LN02. The stream explicitly has heterogeneous height semantics.
It is not a common geodetic reference or accepted scientific harmonization.

The existing [global assessment](global-reference-assessment.md) retains the exact
PROJ diagnostic pipeline and grid hashes. It goes from LV95/Bessel through the
Swiss ETRS89/CHTRF95 LN02 geoid route and WGS84 ellipsoidal space to EGM2008 using
the NGA 2.5-minute grid. Horizontal frame assumptions, Swiss leveling semantics,
model error and the combined chain accuracy remain important limitations.

Primary sources checked 2026-10-04:

- [PROJ Swiss grid record](https://cdn.proj.org/ch_swisstopo_README.txt): official
  converted Swiss grids, CC0, distinct LN02/LHN95 routes to ETRS89 ellipsoidal height.
- [PROJ NGA grid record](https://cdn.proj.org/us_nga_README.txt): public-domain
  EGM2008 conversion grid and reproducible format-conversion route.
- [swisstopo geoid documentation](https://www.swisstopo.admin.ch/en/geoid-en):
  CHGeo2004 model accuracy stated as 1–3 cm; that is not the complete chain accuracy.
- [swisstopo REFRAME documentation](https://www.swisstopo.admin.ch/en/rest-api-geoservices-reframe-web):
  LN02/LHN95 leveling transformation has separate accuracy limitations.

The previous diagnostic correction was only +0.166 to +0.752 m, while present
ridge/glacier-region and level-change residuals reach tens to more than 100 m.
No accepted transformation error budget emerged here. A geoid correction could
not legitimately erase those terrain differences. No transformation, fitted
offset or horizontal registration correction was applied; original products stay
unchanged. A common vertical frame remains a prerequisite for a geodetically
harmonized product, but is not a remedy for all representation/epoch disagreement.

## One-source MapLibre evaluation delivery (M)

Installed `src/ui/map.ts:setTerrain` selects one terrain source. Its terrain tile
manager searches loaded parents (`getSourceTile(...,true)`); it does not combine
independent DEMs. DEM borders can use neighbor backfill, while absent terrain can
fall to the empty/flat texture. These installed implementation constraints were
inspected, not assumed from style-property names.

`scripts/atlas/terrain_hierarchy.py` provides one deterministic stream per strategy
on loopback port4183. The opt-in Vite plugin replaces only visual delivery config
in memory and adds minzoom8/common bounds to both existing geometry/relief sources.
Both evaluation source ceilings are 18. No normal Vite startup imports this plugin.

Common original tiles through z13 and selected Swiss tiles are copied byte-for-byte.
For common fallback above z13, the adapter bilinearly resamples the cell-centred
encoded z13 signal, with available neighboring cells backfilled, and independently
re-encodes Terrarium. This is explicit delivery overzoom, not detail synthesis or
a new reference. At the finite common outer perimeter, interpolation clamps the
available border; no tile outside common support is invented.

The shared source ceiling permits fine regional tiles and forces explicit common
delivery overzoom outside them. That increases request/mesh subdivision possibilities
relative to the original common-only max13 setup, without adding source information.
All controls here use the same max18 contract. Terrain mesh size stays128 and
presentation stays unchanged. This is not a production resolver or scalable global
generation policy.

## Disagreement stratified by spatial support (M)

The retained 400×400,25 m overlap arrays were hash-verified against the previous
assessment. Existing independently selected stable candidates were reused unchanged:
bare-cover support, glacier-buffer exclusion, source-edge guard and slope5–40°.
No residual-based filtering, refit or new registration was performed. Stable means
candidate comparison support, not proven invariant terrain or a valid seamline.

| Group | Stable samples | Median Swiss−common (m) | RMS (m) |
| --- | ---: | ---: | ---: |
| Protected radius≤1.5 km | 738 | −0.10 | 17.87 |
| Radius1.5–3 km | 4,117 | −0.64 | 4.61 |
| Radius3–4.5 km | 3,644 | −0.93 | 2.69 |
| Radius>4.5 km | 2,706 | +0.33 | 4.03 |

The northern/eastern stable sector has much more support than the southeastern
sector; stable counts are NW1960, NE6379, SW2567, SE299. Sector RMS ranges from
3.23 to12.20 m. Glacier-buffer cells, excluded from stable fitting, have median
−5.49 m and RMS27.07 m; they were retained visibly in the all-terrain diagnosis.
All protected-area cells have RMS39.80 m despite the small stable median.
Roughness/slope/boundary-distance strata and full ranges are retained in
[measurements](terrain-hierarchy-measurements.json). These support more careful
future transition study, not an automatic radial collar or accepted seam.

## Protected interior, boundaries and parent/child transitions (M)

All selected Swiss tile hashes equal their frozen parent hashes. On a deterministic
100 m sample of705 protected-interior points, H1 at z14,15,16,18 equals the H0
Swiss delivery field exactly: **0 m modification**. H1 z13 is common, explicitly
not claimed to be Swiss. No protected regional surface was smoothed to hide a join.

At the same705 points, level-to-level bilinear elevation changes were:

| Levels | RMS (m) | Range (m) | Interpretation |
| --- | ---: | --- | --- |
| 12→13 | 0.59 | −2.86…+2.71 | Common parent refinement |
| 13→14 | 39.82 | −102.57…+96.95 | Common→Swiss selection change, including source/epoch/reference/detail disagreement |
| 14→15 | 0.44 | −5.00…+2.05 | Swiss-only refinement |
| 15→16 | 0.26 | −3.78…+1.68 | Swiss-only refinement |
| 16→17 | 0.15 | −2.28…+1.14 | Swiss-only refinement |
| 17→18 | 0.07 | −1.16…+0.58 | Swiss-only refinement |

H0 makes its first common11→Swiss12 change earlier: RMS39.77 m, range
−101.07…+98.50 m on the same705 points. All705 are regional at12. Its finer
regional levels use the same Swiss delivery as H1. Gating relocates the large
source-change discontinuity; it does not make the products compatible.

These are delivered-field preparation/compatibility measurements, not Earth accuracy
or the exact elevation change of every rendered mesh. They identify a strong LOD
source-selection mismatch distinct from the geographic edge.

Twelve fixed strips per tested level cover four edges and their ends/corners,
chosen by inventory order, not visual success. Maximum adjacent-cell differences
were166.70 m at z14,44.43 m at z16 and45.75 m at z18. Common-only adjacent controls
at the same strips reached14.39,3.05 and0.58 m respectively; excess-over-common
statistics are recorded to distinguish ordinary slopes from the selected join.
Twelve z16 one-metre transects reached up to11.14 m between neighboring samples.
This is not directly comparable to the old2 km Swiss/AWS70.17 m maximum: source,
coverage, seam location and delivery differ. It is still unacceptable false terrain.

The fully supported Swiss tile frontier changes with zoom. Inset/staircase delivery
boundaries are not the native source rectangle and not scientific seamlines. Thus
the spatial artifact can move between levels; a fixed bbox alone cannot describe it.

## Renderer and navigation findings (M)

Both H0 and H1 show real regional structure in close/detail views. H1 provides
common landscape/planning context and useful fine relief, but holds some geometry
on common parents longer. No static central black/flat void was observed in the
normal supported views, unlike the earlier pure-regional-only product. Finite
common perimeter and z0–7 limitations remain; no globe/global coverage is claimed.

West/south edge views show obvious relief/height bands, with conspicuous southern
glacier-region walls. Northern views have smaller yet visible linear changes.
Corner views and 180° rotation do not remove the support problem. H0 and H1 often
match at high detail because both select the same supported Swiss children there.
The initial discovery/H1-static short credit was inherited from common-only
tooling; the retained harness now credits both sources, as subsequent H0 and
H1-moving captures confirm. Full modified-product notices remain a public-delivery
prerequisite, not satisfied by a short map credit.

Scale gating hides the hard join at coarse scales; it does not repair it at close
scale or while traversing the support edge.

Continuous sequences start at landscape9.4, approach planning11.4/close13.2/detail16.2,
rotate, move west toward [7.695,45.9793] then outside at [7.681,45.9793], and return
to central planning. Actual levels, moving samples, captures and requests were
recorded. Loaded parents persist while children arrive; relief and geometry refine
at different times. Screens/terrain can change patchwise rather than at one camera
threshold. This is a scale/loading effect as well as a source boundary effect.
No assertion of smooth silhouette animation follows from completed loading.

Satellite was not a separate comparison; production suppression remains unchanged.
Globe/Mercator code was not modified. This finite z8-floor stream cannot establish
meaningful globe terrain. Existing basemap missing-sprite/filter warnings remained
and were not repaired. QueryTerrainElevation values in capture records include
1.45 exaggeration and MapLibre mesh/parent behavior; they are not analytical elevations.

## Contributor metadata and delivery cost (M)

Each generated tile has a lossless uint8 contributor mask: label0 common EGM2008,
label1 Swiss LN02. There are no blended cells. Each receipt records strategy, XYZ,
native height reference, preparation method, config identity, tile/mask hashes and
bytes. Labels are identity, not confidence. Renderer interpolation across texels
or mesh triangles can span contributors; the mask describes delivery cells, not
an invented confidence/identity for every final shaded pixel.

The [Terrain Product record](terrain-hierarchy-product.json) fits the existing
metadata model without an extension. It preserves both immediate contributors,
heterogeneous vertical semantics, scoped sparse coverage, protected intent,
unresolved valid-transition support, fallback relationship, information ceilings,
source-specific rights and build identity. Renderer parameters are not source metadata.

The sparse evaluated inventory contains **4,206 terrain tiles**, totaling
**333.21 MB**, plus **1.27 MB** of label masks.
Independent reconstruction of every tile/mask matched the manifest identity
`1455456e250d5ae4333e3642028b63f0d4d820adab0a07a471efc2f59262d068`; rebuild time was
103.5 seconds on this machine. A later cached verification took4.9 seconds. These are bounded local costs.
Counts by strategy/level/contributor and full projected support area are recorded
in the product checks. Original Swiss complete-delivery counts are1,4,25,121,506,
2118,8654 at z12–18; H1 regional eligibility is zero below14. Projected support area
expands from95.73 million Mercator m² at12/13 to202.25 million at18. These are not
physical land-area measurements. No mixed product cells exist; masks do not claim
that MapLibre interpolation cannot span two contributors.

Across the five discovery/static/navigation runs, **4,190
completed local tile responses were200**, with zero page errors or recorded trial
failures. Logical returned bodies total 442.78 MB;
this is not measured network transfer or a throughput benchmark. The18 recorded
request failures are navigation cancellations (`ERR_ABORTED`), including vector
basemap requests. Cache reuse and loaded-parent behavior are retained in the
external traces. No missing response was observed within these tested views.


Original products stay immutable. The cache materializes only requested/numerically
tested tiles; it is not a full z8–18 pyramid. An independent sibling rebuild verifies
every evaluated tile, mask and manifest identity. Exact common bytes through13 and
exact Swiss bytes are checked; common delivery-overzoom quantization is≤1/512 m.
No original source or normal analytical route calculation changes.

The local service returns CORS-enabled PNGs, one-hour cache headers and contributor,
height and build headers. Fresh browser contexts isolate trials; unversioned local
URLs are not a production cache-revision policy. No CDN/throughput benchmark was run.

## Conclusion and smallest next step

**M:** H1 suppresses coarse spatial joins, but **neither strategy is accepted as
a continuous terrain hierarchy**. There is no preferred adoption strategy. The evaluation preserves detail
and identity, supplies usable coarse context and avoids broad arbitrary smoothing. It still
fails hard spatial support and parent/child compatibility. A datum shift below
one metre cannot explain or cure the measured mismatch.

There is evidence for requirements of a general contract, not yet a validated
general hierarchy algorithm: per-level spatial support and contributor identity;
separate geometry/relief/loading scales; parent/child compatibility; native versus
harmonized height semantics; explicit failure/fallback behavior. "Bounds + URL +
priority" and a zoom threshold are both insufficient.

**H:** The smallest next bounded investigation should evaluate a regional-preserving
parent policy on one protected-interior tile and neighboring support: derive
coarser parents from the explicitly contributed fine representation (including
support masks), compare their loading/height continuity with the present H0/H1 parents,
and determine whether the large LOD discontinuity can be avoided without modifying
fine Swiss terrain. This is a representation diagnostic, not a silent alteration
of the Copernicus reference. Geographic transition/seam support remains a separate
unresolved decision. Whole-view switching, a transformed composition and derived
transition surfaces have not been validated here. No generic resolver is justified.

No next experiment, acquisition, smoothing, imagery or production phase was started.

## Reproduction and validation

External products/captures remain under the documented `meridian-data` root:

- `derived/atlas/riffelhorn/riffelhorn-terrain-hierarchy-v1-discovery/`:
  immutable build config, tiles, contributor masks, receipts and manifest.
- Independent `-discovery-rebuild/` sibling: identical evaluated output hashes.
- `experiments/atlas/riffelhorn-terrain-hierarchy-v1/`: frozen-field diagnostics,
  twelve boundary profiles, figures, discovery/static/moving captures and request logs.

From repository root (existing scientific environment; no new dependency):

```powershell
$python = 'C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
& $python scripts/atlas/copernicus_common.py verify
& $python scripts/atlas/riffelhorn_support.py verify
& $python scripts/atlas/terrain_hierarchy.py serve --gate 14 --suffix=-discovery
# Separate terminal; loopback4183 running. Every capture creates a fresh browser.
node scripts/atlas/capture_terrain_hierarchy.mjs common '<DATA>/experiments/atlas/riffelhorn-terrain-hierarchy-v1/discovery' discovery
node scripts/atlas/capture_terrain_hierarchy.mjs H0 '<DATA>/experiments/atlas/riffelhorn-terrain-hierarchy-v1/discovery' discovery
node scripts/atlas/capture_terrain_hierarchy.mjs H1 '<DATA>/experiments/atlas/riffelhorn-terrain-hierarchy-v1/captures'
node scripts/atlas/capture_terrain_hierarchy.mjs H0 '<DATA>/experiments/atlas/riffelhorn-terrain-hierarchy-v1/captures'
node scripts/atlas/capture_terrain_hierarchy.mjs H1 '<DATA>/experiments/atlas/riffelhorn-terrain-hierarchy-v1/navigation' navigation
# Stop the local server before final inventory/rebuild to prevent concurrent growth.
& $python scripts/atlas/analyze_terrain_hierarchy.py --gate 14 --suffix=-discovery
& $python scripts/atlas/finish_terrain_hierarchy.py --suffix=-discovery --rebuild
```

The retained config fails closed if frozen parents or generation code change; use
an explicit named sibling for a revised experiment, never overwrite source products.
Record generation identity independently of capture hashes: live vector basemap
and UI/driver timing make screenshots a controlled record, not bitwise reproducible
rendering across machines. Capture reports record their production file hashes.

Validation passed: **33 synthetic Atlas Python tests;164 active Node application/
tool tests,1 existing optional skip; lint; TypeScript; application-only Vite build**.
One newly added assertion initially looked for a literal instead of the existing
exaggeration constant; it was corrected, then the full test set passed. No unrelated
test was changed and the clock-dependent workspace test did not fail in this run.
Existing rasterio/NumPy deprecation and large-JavaScript-chunk warnings remain.
All evaluated terrain/mask hashes match the independent rebuild; both parent source
and full delivery identities were verified. Metadata validation, source-policy tests,
documentation links and final production-diff inspection passed. Normal tests ran
with an empty external-root override and the local tile server stopped.


Normal validation uses an empty external-root override and no local service:

```powershell
$env:MERIDIAN_DATA_ROOT = '<absolute empty directory outside repository>'
& $python -m unittest discover -s scripts/atlas -p 'test_*.py'
$tests = Get-ChildItem scripts/atlas,scripts/weather,scripts/route,scripts/ui -Filter 'test_*.mjs' | ForEach-Object { $_.FullName }
node --test $tests
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/terrain-hierarchy-app-build'}});"
```

The application-only build intentionally omits unrelated external GFS publication
validation/copying. No normal startup or CI dependency on this service or products
was added. No `meridian-private` material was inspected.
