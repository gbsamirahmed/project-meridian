# Terminal Riffelhorn protected-priority two-band transition

2026-10-05. Baseline: `53b9efbc9e1e2d9393291a1b3fe90abcfcf3f7d0`.
This is one synthetic visual-representation experiment, not an accurate fused DEM,
an analytical elevation product, a datum transformation or production adoption.
The frozen specification is
[riffelhorn-final-reconciliation-experiment.json](riffelhorn-final-reconciliation-experiment.json).
Its historical `design-only-not-implemented` status is retained as part of the
unchanged design record; implementation/result records live alongside it.

## MERIDIAN EVIDENCE — inputs and frozen implementation

Clean main at the expected checkpoint and zero local/remote divergence were
confirmed. Production visual AWS, independent analytical AWS z15, strengthened
IGOR, exaggeration1.45, Weather, Traverse, satellite and projection/lifecycle
remain unchanged. No application module or normal Vite configuration imports
this experiment. There was no new elevation, imagery, glacier inventory or
registration/datum acquisition and no source-product mutation.

| Immediate immutable input | Identity | Semantics / role |
| --- | --- | --- |
| Swiss regional support product | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` | swissALTI3D2024, 100 official0.5m distributed LV95 tiles; DTM/LN02; existing z12–18 delivery |
| Swiss regional-parent diagnostic | `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672` | Unencoded z14 basis restricted recursively; complete/partial/absent support retained |
| Common Copernicus product | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2` | Frozen2021 public GLO-30 distribution, exact sub-release unknown; edited DSM/EGM2008; six retained assets, two z8 roots, z8–13 |

The regional source covers LV95 `[2620000,1087000,2630000,1097000]`.
Its Valais acquisition basis is2021/22 LiDAR plus2023 photogrammetric updates;
per-cell epoch remains unknown. Common one-arcsecond postings, Swiss distributed
grid spacing, delivery spacing, observation resolution and renderer mesh are
different concepts. No new measurement information is claimed from resampling.
Existing official source hashes, product identities, retained parent arrays,
used PNG hashes and SGI1973/2016/2023 records are verified by the reused input
validator and the final output verification.

The recipe/build identity is
`d4324edea4678aa62ae3ab29ff9968fa97c86fd09dcd99a88749a1e4be0c75a2`.
The final sparse inventory also has its own content identity, listed in
[two-band-completion.json](two-band-completion.json). Adding evaluated tiles
extends that inventory without changing the immutable recipe or source assets.
Large products and captures are external:

```text
${MERIDIAN_DATA_ROOT}/derived/atlas/riffelhorn/riffelhorn-two-band-transition-v1/
${MERIDIAN_DATA_ROOT}/experiments/atlas/riffelhorn-two-band-transition-v1/
```

### One rule, no tuning

Centre LV95 `[2625000,1092000]`; protected radius1500m; broad accommodation
1500–4000m; detail fully retained to3000m and withdrawn3000–4000m; common from
4000m. These are frozen experimental parameters, not Atlas defaults. No other
width, centre, broad level or weighting curve was tried after inspecting results.

```text
q(t) = 1 − 10t³ + 15t⁴ − 6t⁵, t clamped to [0,1]
b = q((r−1500)/2500)
d = q((r−3000)/1000)
Tz = Cb + b(Sb−Cb) + d(Sz−Sb) + (1−d)(Cz−Cb)
```

Broad controls are z12, using the retained unencoded Swiss z14 parent chain and
decoded common z13 under identical recursive2×2 uniform Mercator-pixel-area
means. Complete cells only; bilinear pixel-centre prolongation requires all four
supported neighbours. This is the frozen comparison-scale operator, not a claim
about either sensor's point-spread function or terrain accuracy. Regional z12–14
uses complete retained parent cells; z15–18 uses immutable fine PNG elevations.
Common above13 is explicitly bilinear overzoom. Each output level is independently
encoded as 256px XYZ/Web-Mercator Terrarium PNG, nearest1/256m step.

Pure endpoint branches copy the applicable source signal rather than relying on
floating cancellation. New z11/z10 diagnostic parents summarize unencoded T12;
pure common cells retain the canonical common context. Below10 remains common.
The lower handoff and finite common perimeter are recorded, not repaired by
generating parents to0. The broad controls and circle were not shifted to obtain
better support or a prettier boundary.

The full fixed footprint passed support preflight at every level. Circle-touching
tile counts12–18 are5,11,29,92,318,1191,4603 respectively; missing support is zero
at every level, including interpolation halos. This check is separate from the
smaller sparse evaluated output inventory. No Swiss edge extrapolation, partial
cell mean masquerading as a full height, AWS padding or fabricated regional data
was used.

### Provenance and height accounting

[two-band-product.json](two-band-product.json) uses the existing Atlas product
model. Immediate contributors are explicit product references, not an anonymous
DEM. Pure common, pure regional, broad transition with full regional residual,
broad/detail-taper transition and derived parents have distinct categorical labels.
Per-tile NPZ records retain b,d,labels,change proxy and whether that classification
is known. Parent-support supplements distinguish the fraction of z12 descendants
requiring the regional operator from b/d mean influence and complete common support.

The equivalent signed operator is
`d Sz + (1−d) Cz + (b−d) Sb + (d−b) Cb`.
Some coefficients are negative. Therefore b/d are geometric controls, not
confidence, accuracy, simple source percentages or a convex mixture guarantee.
The operator, input identities, generalisation and parent operations are necessary
for reconstruction. Parent influence masks alone do not reconstruct the terrain.

Swiss stays LN02; Copernicus stays EGM2008. Mixed scalar heights have explicitly
heterogeneous semantics and no single accepted physical vertical CRS. Original
products remain intact. This output must never be sampled as analytical elevation
or described as observed terrain. No fitted offset, translation, height transform
or glacier bias/error correction occurs.

## MERIDIAN EVIDENCE — numerical evaluation

Measurements use the complete retained z14 envelope, dense fixed radial profiles,
705 prior protected sample locations at levels10–18 and delivered-cell checks.
These are preparation/representation diagnostics, not physical accuracy tests.
Raw arrays, profile coordinates, full statistics, hash ledgers and figures are
external; compact results are in [two-band-completion.json](two-band-completion.json).

### Preservation, operator and band boundaries

All160255 eligible z14 protected cells have exactly zero unencoded change.
All705 previous protected sample positions have exactly zero delivered difference
at each level14–18. Final verification additionally compares every protected cell
in the evaluated delivery inventory against its immutable regional level.
All2071674 z14 cells outside4km have zero unencoded common difference; evaluated
delivered outer cells are exact encoded common. Normal coarse aggregation remains
a representation operation and is not counted as fine source mutation.

Independent signed expansion closes to1.37e−12m; the independent finite-difference
radial derivative agrees with the analytic induced term within6.51e−11m/m.
Endpoint weights are exact, monotone within floating tolerance: b/d are1/1 at1500m,
0.31744/1 at3000m and0/0 at4000m. Regional residual is retained through3000m;
common residual gradually replaces it only in the specified outer band.

The slope-accounted introduced intercept proxy across the three endpoints is at
most1.62e−8m across72 bearings, below the frozen0.1m guard. Actual adjacent height
changes include real steep terrain: the worst1m change at1500m is3.43m. It would
be incorrect to call that terrain slope a transition wall. Terrarium rounding
and sampled tile-edge differences are checked independently.

### Broad accommodation is substantial

| Radius band (m) | T−Swiss range (m) | T−Swiss RMS (m) |
| --- | --- | --- |
| 0–1500 | 0 / 0 | 0 |
| 1500–2000 | −2.01 / +5.21 | 0.59 |
| 2000–2500 | −18.37 / +28.83 | 3.67 |
| 2500–3000 | −45.14 / +55.29 | 8.69 |
| 3000–3500 | −62.91 / +114.87 | 16.13 |
| 3500–4000 | −102.62 / +102.71 | 17.77 |

This is source accommodation, not evidence that either terrain was wrong.
The interior's broad Swiss−common RMS is39.59m and it is deliberately preserved.
The collar's large displacements must survive in provenance even when visually
smooth. No percentage of detail versus error is inferred from correlated bands.

### Induced gradients and terrain forms

The induced radial term is `(Sb−Cb)b′ + (Rs−Rc)d′`, excluding gradients already
present in the sources. Across979335 mixed eligible z14 cells, absolute p95 is
0.02332m/m, p99 is0.03759, maximum0.11328. About0.119% exceed0.05. Exactly four
connected cells exceed0.10; their graph witness is19.92m and even their maximum
possible four-cell simple path is below100m. Both frozen gradient guards pass.

| Class | Absolute induced-grade p95 | Maximum |
| --- | --- | --- |
| Stable candidates | 0.00469 | 0.03786 |
| Non-ice | 0.00633 | 0.06848 |
| Steep non-ice | 0.02130 | 0.06417 |
| Historical glacier/change proxy | 0.03191 | 0.11328 |

Smooth endpoints do not guarantee harmless terrain. There are692 new same-cell
minimum flags and732 maximum flags; one-ring prominences reach4.62m/3.37m.
Most are small (p95 depths0.59m/prominences0.66m). T can exceed both pointwise
source heights by11.30m or fall below both by11.41m because the operator is signed.
Neither an envelope violation nor a shifted cell extremum alone proves a new
landform.

Independent fixed-outlet priority-flood checks of the eight strongest minimum
patches distinguish shifted existing Swiss pits from newly closed depressions.
The non-ice northwest4.62m flag lies close to a deeper existing Swiss depression;
it is not evidence that the entire valley was invented. At LV95 approximately
`[2625624,1088745]`, r3314m in the historical change proxy, T has a3.19m closed
depression while both inputs have zero local spill depth, including the53m
neighbourhood check. Another smaller1.35m change-terrain pocket is also absent
from either local input. These are synthetic local-form warnings, not observed
glacier pits or source errors. Patch/profiles and outlet assumptions are retained.

D8 direction diagnostics show median0° and p9545° change against Swiss;
686 mixed cells have no descending neighbour where both input cells have one.
Five-point curvature changes are recorded. These are representation checks,
not a hydrological validation. They prevent equating removal of a wall with
preservation of all terrain morphology.

### Parent/child behaviour

| Same-coordinate delivered refinement | Protected705 RMS (m) |
| --- | --- |
| T10→T11 | 6.27 |
| T11→T12 | 2.90 |
| T12→T13 | 1.32 |
| T13→T14 | 0.7107 |
| T14→T15 | 0.4405 |
| T15→T16 | 0.2633 |
| T16→T17 | 0.1496 |
| T17→T18 | 0.0724 |

The prior39.82m Copernicus13→Swiss14 discontinuity does not return in the protected
interior. The0.71m result remains internal LOD change, not accuracy or registration.
Common9→derived10 is41.84m RMS over the same705 positions (−98.91 to+93.98m).
It is an explicit remaining source-family handoff, not ordinary LOD. It is retained
in `coarse-handoff.json`, not solved by another propagation phase.

The complete z14 protected-cell population13→14 RMS is1.12m, distinct from the705
positions above. Broad collar1500–3000m RMS is1.08m; taper3000–4000m0.67m;
outside4000–4500m0.00063m. Differences in sample populations/operators matter;
these figures cannot be substituted for the historical705-position comparison.

## MERIDIAN EVIDENCE — renderer, controls and navigation

The isolated evaluation adapter supplies one stream to the existing MapLibre6.11.2
terrain path. Both visual DEM sources retain the production IGOR curve/direction,
mesh128 and exaggeration1.45. Only evaluation delivery URL, finite bounds and
available levels change; analytical sampling and production files are untouched.
No shader, skirts, morph, viewport resolver or visual retuning was introduced.

The frozen [camera enumeration](two-band-cameras.json) covers24 central views,
128 boundary views (eight azimuths, four radii, four bearings),18 control positions,
three satellite checks and40 navigation segments across centre/west/south cold
and warm sequences. Moving and settled frames, requested levels, actual mesh
parents, HTTP outcomes, body hashes and production file hashes are recorded.
Cold means a new MapLibre page/cache; shared browser HTTP/cache and server product
cache are not claimed to be cold. These are bounded local observations, not a
general performance benchmark.

At camera9.4 the actual central mesh uses z8; at11.4 it uses9/10; at12.4 it uses
9–12; at13.2 it uses10–13; at14.2 it uses10–14; at16.2 it uses a range through15.
Hillshade requests extend through18 at the closest view. Camera zoom is therefore
not an exact active DEM level. `queryTerrainElevation` in captures includes the
configured exaggeration; those values are not raw source elevations.

All128 frozen boundary views and their four bearings were inspected, including
west/south, diagonal sectors and the4250m outside control. The transition no
longer presents the abrupt regional-support wall seen in the hard control.
West and north generally show progressively coarser landform texture. South/east
ice terrain retains broad displaced landforms and coarse faceting inherited from
the common representation. No dominant circular endpoint wall or continuous
replacement relief band was identified across the matrix. This is bounded visual
evidence, not proof that every synthetic landform is harmless. Sharp painted
polygons/white texture patches also occur in controls and are not independently
attributed to the transition.

Close central views retain Swiss channels, ledges and summit structure under all
four bearings. Detail becomes less pronounced across the outer band, consistent
with the declared residual withdrawal. Satellite checks use the existing provider
and geometry, with no imagery processing or provider change. Coarse mesh/near
foreground faceting remains visible in some pitched views.

The40 primary navigation segments cover approach, lateral west/south movement,
return and cold/warm parent loading. Moving frames show texture/relief sharpening
as data arrive; no return of the large common13→Swiss14 switch was established
in the interior. At the outward landscape step, common context/perimeter and
parent loading remain visible. Frame sampling every200ms cannot prove absence of
shorter transients. The low common9→derived10 source change is unresolved.

The required south close sequence has a severe foreground curtain and black
clipped triangle at its first approach, both cold and warm; other near views
also expose large steep faces. The matched **pure common control**, using the
same frozen six south segments in both cache states, reproduces that artifact.
This separates it from a new Swiss/Copernicus handoff wall: it is consistent with
shared camera/terrain rendering behaviour, but its exact cause is not established.
It still prevents claiming that every required navigation view is usable. No
camera, terrain band, renderer or exclusion was changed to hide it.

Primary output includes335 captures; the matched south common control adds38.
The eight accepted phase reports contain7476 local terrain HTTP responses, all200;
7470 bodies complete and match the final immutable inventory, six become
unavailable during cancellation. There are221 cancelled terrain requests and
four other cancellations; all225 have `net::ERR_ABORTED`, no failed terrain status
or page exception. The41 console503 messages are the explicitly disabled Weather
publication in this terrain-only fixture. They are not terrain service failures.
Normal application Weather remains unchanged.

One initial satellite fixture attempt timed out before the map was fully ready.
Waiting for the existing map to settle before activating satellite completed the
same three frozen cameras. Its failed record is retained externally. This changed
capture readiness only; no terrain rule was changed. Numerical bookkeeping/name
repairs and independent diagnostic indexing fixes also did not change the frozen
terrain generator. No variant or parameter search was conducted.

Hard control is the frozen regional-parent whole-supported-tile handoff, not a
new circle hard-join algorithm. Within fully regional support it also supplies
the pure regional control. Pure common is independently rendered at the same18
positions. Older fixed/adaptive AWS feather controls remain historical evidence:
different sources/extent prevent a fair numeric algorithm ranking. Their large
collar deformation and channel warning remain relevant acceptance concerns.

## Result, limits and the next task

**PARTIAL / ARCHITECTURALLY USEFUL. No production adoption.**

The source-preserving, independently controlled bands and explicit synthetic
representation are demonstrated. The frozen method does not satisfy all success
criteria. Its local synthetic pits, large collar deformation, unresolved lower
handoff and unusable close-camera frames remain acceptance limits. They are not
fixed by passing the intercept/gradient guards or by visually smooth endpoints.
There is no demonstrated new dominant circular ramp/channel comparable with the
earlier adaptive-control failure, but absence of one does not erase the new local
depressions. Their practical significance is not established by these captures.

| User success criterion | Result and evidence |
| --- | --- |
| 1 Protected interior unchanged | PASS:705 fine positions and every eligible delivered protected cell exactly match the declared regional level. |
| 2 No artificial handoff cliff/crack | PASS for the composed surface: introduced endpoint intercept≤1.62e−8m; no endpoint wall identified in the frozen boundary matrix. Shared near-camera clipping is separate. |
| 3 No severe replacement relief band | QUALIFIED: no dominant continuous radial band identified under four bearings; broad ice faceting and source-character changes remain visible. |
| 4 No substantial new depression/channel | FAIL strict local-form preservation:3.19m and1.35m synthetic local closed pits are present; no dominant broad invented channel demonstrated. This blocks unqualified acceptance. |
| 5 Bounded interpretable induced gradients | PASS declared guards: p950.02332, four connected cells above0.10 over<100m. Collar height changes still exceed100m. |
| 6 Independent regional detail withdrawal | PASS algebra/masks: full residual through3km, frozen taper3–4km, zero outside4km. Fine structure remains in close interior views. |
| 7 Common recovered outside transition | PASS for12–18: all evaluated outer cell heights exactly encoded common. Derived10/11 footprints can straddle4km due to normal parent aggregation. |
| 8 Contributor/provenance recoverable | PASS: immutable inputs, full signed operator, b/d/category/support/change records and product/output identities retained; no confidence or observation claim. |
| 9 Glacier/change explicit | PASS: retained historical change proxy and unknown cell epoch; synthetic native-height transition, no fit or correction. |
| 10 Boundary views coherent under rotations | PARTIAL: many useful boundary views and no endpoint wall; severe close foreground clipping/faceting in some south views also reproduced by pure common. All-view visual success not established. |
| 11 Navigation avoids severe popping/walls | PARTIAL: coherent regional13→14;40 segments complete without terrain HTTP failure. Lower9→10 change remains41.84m RMS and close-camera artifacts remain. |
| 12 General concept informs contract | YES, with limits: separate immutable source families, regional parents, explicit derived boundary representation and independent numerical/visual acceptance; no general reconciliation algorithm established. |

No fundamental violation of interior/support/provenance occurred. The local
landform and rendering/scale limitations prevent SUCCESS; the evidence is useful
for the contract without requiring another reconciliation family. The experiment
is closed. The next task is **Atlas Terrain Hierarchy Contract**, carrying these
failure/qualification records. No further Riffelhorn elevation-method experiment
is recommended and no contract/generic resolver is implemented in this commit.

Even a useful visual coexistence demonstration does not establish common physical
height semantics, an uncertainty model, source accuracy, correct glacier history,
hydrological conditioning, a national product or global coastline/polar policy.
The local finite common perimeter and missing levels0–7 remain inherited limits.
Neither the circle nor widths become generic Atlas constants.

## EXTERNAL EVIDENCE — contribution discipline

This reproduces/adapts established raster restriction/prolongation, band residual
decomposition and smooth geometric weighting for a Meridian representation test.
It does not claim to invent DEM fusion, produce uncertainty-weighted observations
or establish physical datum reconciliation. Closest prior art, its assumptions
and the world-model/rendering distinction remain in
[spatial reconciliation research](spatial-terrain-reconciliation-research.md) and
[information-scale decomposition](terrain-scale-decomposition.md). This task
performed no additional literature survey.

## RESEARCH HYPOTHESES / DIRECTIONS — contract implications only

The next task is the Atlas Terrain Hierarchy Contract, regardless of this result.
It must preserve regional parent families, independent scale/spatial support,
immutable sources, explicit derived representation identity, signed processing
lineage, temporal/change masks and failure behaviour. Physical terrain reference
and synthetic visual representation cannot become interchangeable by encoding.
Numerical and visual acceptance remain distinct. No final contract or generic
resolver is frozen here and no further Riffelhorn elevation-method experiment is
recommended. Generic implementation and a second region are later tasks.

## Reproduction and validation

Use the existing scientific environment and retained products. Do not run normal
production publication/build to generate this terrain. In a separate terminal:

```powershell
Set-Location C:/Users/gbsam/Documents/Projects/project-meridian
$terrainPython = 'C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
$terrainData = 'C:/Users/gbsam/Documents/Projects/meridian-data'
& $terrainPython scripts/atlas/two_band_transition.py preflight --data $terrainData
& $terrainPython scripts/atlas/two_band_transition.py serve --data $terrainData
```

Numerics and capture runs (retain the server above):

```powershell
& $terrainPython scripts/atlas/analyze_two_band.py --data $terrainData
& $terrainPython scripts/atlas/finish_two_band.py --data $terrainData
$terrainCaptures = "$terrainData/experiments/atlas/riffelhorn-two-band-transition-v1/captures"
node scripts/atlas/capture_two_band.mjs transition $terrainCaptures central
node scripts/atlas/capture_two_band.mjs transition $terrainCaptures edges
node scripts/atlas/capture_two_band.mjs transition $terrainCaptures navigation
node scripts/atlas/capture_two_band.mjs common $terrainCaptures controls
node scripts/atlas/capture_two_band.mjs hard $terrainCaptures controls
node scripts/atlas/capture_two_band.mjs transition $terrainCaptures controls
node scripts/atlas/capture_two_band.mjs transition $terrainCaptures satellite
& $terrainPython scripts/atlas/verify_two_band_outputs.py --data $terrainData
& $terrainPython scripts/atlas/two_band_transition.py rebuild --data $terrainData --suffix=-rebuild
```

The optional final capture argument is a distinct loopback Vite port for
independent concurrent capture phases, not an experiment parameter. Determinism
applies to generated terrain/masks/numerical arrays, not animation scheduling,
network request order or live basemap screenshot bytes.

The final sparse inventory identity is
`cb50566a80e27a9ed015c6fa35c176cb111de6fa568da85a5c41dc4dfb7037f2`.
All4251 PNGs and4251 contribution records reproduce exactly in a separate output
directory. The transition subset is2297 tiles: z8–18 counts2,8,28,56,50,82,110,223,
733,373,632; PNGs200.37MB and masks325.69MB. Controls add656 common and1298 hard
tiles (57.79MB/114.59MB PNG). These are sparse evaluated footprints, not a complete
regional/global delivery asset or a storage estimate for production. Transition
PNG minimum/median/maximum are29,678/84,832/161,226bytes. No storage optimization
or universal timing/performance claim is made.

Independent output verification checks every evaluated protected cell at12–18:
10,014;40,057;160,255;641,013;2,564,045;10,202,758;40,175,309 respectively, allzero
change. These are delivery samples, not independent observations. All evaluated
outer cells and all masks satisfy the exact frozen rules. Strict annulus/interpolation
support, original100Swiss/sixCopernicus source hashes,35retained regional-parent
files, change inventories and used tile hashes pass. Maximum encoding discrepancy
is0.001953125m within rounding tolerance. Parent support records preserve partial
operator footprints without pretending those are independent Swiss observations.
The21 numerical arrays/records/figures rebuild byte-identically, including independent
operator/derivative and fixed-outlet pit checks.

68 Python tests pass, including eight new offline synthetic transition tests;
180 Node application/policy/model tests pass with one existing optional external
Weather test skipped. Lint, TypeScript, application-only Vite build, metadata,
document/reference and diff checks pass. Existing scientific deprecation warnings
remain. The app-only build uses `configFile:false` and never publishes Weather.
No test requires the external experiment/service at normal CI/startup.

Additional reproduction/validation commands:

```powershell
& $terrainPython scripts/atlas/finish_two_band.py --data $terrainData --hierarchy
& $terrainPython scripts/atlas/rebuild_two_band_diagnostics.py --data $terrainData
& $terrainPython scripts/atlas/record_two_band_metadata.py
node scripts/atlas/capture_two_band.mjs common "$terrainData/experiments/atlas/riffelhorn-two-band-transition-v1/common-navigation-control" navigation 4177 south
& $terrainPython scripts/atlas/record_two_band_completion.py --data $terrainData
& $terrainPython -m unittest discover -s scripts/atlas -p test_*.py
$terrainTests = Get-ChildItem scripts/atlas,scripts/route,scripts/weather,scripts/ui -Filter test_*.mjs | ForEach-Object { $_.FullName }
node --test $terrainTests
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/two-band-app-build'}});"
```

`record_two_band_metadata.py` currently uses the established local data root;
all main generation/analysis commands take explicit `--data`. The compact
completion ledger independently checks accepted response hashes, immutable
production-file hashes, final full rebuild equality and diagnostic hashes.
Raw captures contain live-provider requests and stay external; only secret-free
counts/hash records are retained in Git.
