# Riffelhorn same-level seam-corridor feasibility

2026-10-05; baseline `9827b17923442a8c61e813fea103bc291bb11cef`.
Status: **negative under the declared stable/change-support constraints**.
No height, terrain product, vertical reference, registration or renderer changed.

## Question and result

Does the existing supported overlap contain a connected corridor surrounding the
protected Riffelhorn interior that could plausibly support a future source handoff?

**MERIDIAN EVIDENCE:** no enclosing cycle exists in the primary permitted domain
at either z12 or z13, even with unlimited admitted height disagreement. Changing
source-edge guards or glacier buffers from 100 to 500 m does not change this result.
The obstruction is spatial support/change topology, not a poorly tuned seam cost.
There is no finite compatibility threshold for an admissible closed corridor.

A deliberately inadmissible control that disables glacier/snow exclusions closes
at 19.417 m (z12) / 19.862 m (z13) maximum absolute disagreement. Its witness routes
are approximately 80–83% glacier-excluded and only 1.8–1.9% candidate stable support.
These are not proposed seamlines and do not justify blending.

**Decision:** do not perform a transition experiment next. Assess the geographic
extent of the connected glacier/change barrier using retained inventories before
choosing any enlarged Swiss acquisition. Existing support is sufficient to expose
the failure, not sufficient for the requested stable surrounding corridor.

## Frozen products, protocol and verification (M)

The [protocol](seam-corridor-plan.json) was written before real-data analysis.
The [measurements](seam-corridor-measurements.json) and
[diagnostic manifest](seam-corridor-diagnostic.json) retain identities, source
hashes, array hashes, constraints, masks, software and output hashes.

| Input | Identity / semantics |
| --- | --- |
| [Larger Swiss product](riffelhorn-swiss-support-product.md) | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`; 100 official 2024 inputs; DTM, distributed 0.5 m LV95 grid, LN02; 10×10 km support. |
| [Regional parents](regional-parent-diagnostic.md) | `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`; separate unencoded z14-derived sum/count chain; complete/partial/absent support. |
| [Common product](copernicus-common-product.md) | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2`; six frozen 2021 public GLO-30 assets, exact sub-release unknown; edited DSM, EGM2008. |
| [Overlap evidence](global-reference-assessment.md) | Retained 25 m independent glacier/land-cover/stable-support fields; all array hashes verified. |

Verified all 100 Swiss source files, six common source files, both manifest
identities and source lineage; all 35 regional-parent files/support arrays; every
common tile actually read; three retained SGI inventory archives. The recreated
SGI250 m mask matches the retained mask exactly. The original 11,429 Swiss fine
tiles were not all rehashed: they are not diagnostic inputs and no code writes to
them. No terrain was regenerated, no data acquired and meridian-private untouched.

Predecessors: [first hierarchy](terrain-hierarchy-prototype.md),
[reconciliation controls](riffelhorn-terrain-reconciliation.md),
[research review](spatial-terrain-reconciliation-research.md).
Internal regional LOD improvement 39.82→0.71 m RMS remains distinct from this
same-level spatial comparison and from accuracy/translation.

## Same-level support and height policy

Primary z13 compares Swiss-derived parents with decoded common z13 at identical
XYZ/Web-Mercator cell centres. z12 repeats one coarser level. Near the benchmark,
ground cell spacing is 13.28/26.56 m respectively. Swiss counts must equal 4/16
supported z14 basis cells. Partial observed-subset means never become valid nodes.

These levels are representations, not measurement accuracy. Common z13 samples
interpolated GLO-30 information; it adds no observations beyond its one-arcsecond
source postings. Swiss values come from the retained unencoded parent chain;
common values from its exact Terrarium delivery. The common quantization bound
is 1/512 m; this asymmetry is insignificant to the metre/tens-of-metres thresholds,
but is explicitly preserved rather than silently re-encoding Swiss.

Swiss remains LN02; common remains EGM2008. Neither is transformed or shifted.
The known local sub-metre frame diagnostic is context only. Raw disagreement is
compatibility between estimates, not terrain error or proof of accuracy. No fitted
offset, new co-registration, height smoothing, blend or transition DEM exists.

## Topology and hard constraints

The graph has DEM cell centres as vertices and four-neighbour grid edges. A valid
candidate must contain a **simple closed cycle enclosing the entire 1.5 km circle**
around LV95 `[2625000,1092000]`. Nodes within one local cell diagonal beyond the
circle are excluded, so graph edges cannot cut the protected interior. There is
no prescribed rectangle, radial/star-shaped route or privileged favorable sector.

| Hard exclusion | Rationale / limitation |
| --- | --- |
| Protected circle plus conservative grid guard | Preserve regional information; no transition through the benchmark. |
| Incomplete Swiss or nonfinite/missing common support | A partial parent is not a full-cell elevation; finite tile envelopes are not source coverage. |
| Swiss source-edge guard 200 m | Retained support-screen convention; test 100/500 m. Not an accepted future transition width. Conservative eight-point cell footprint distances use native LV95 bounds. |
| SGI 1973/2016/2023 union +250 m | Retained independent cross-epoch glacier/change exclusion. Test 100/500 m; union is conservative, not a current ice classification or a per-cell epoch model. |
| WorldCover retained water 80 / snow-ice 70 classes | Avoid known water/change comparisons; 25 m nearest-class evidence is a diagnostic proxy, not validated complete shoreline/snow extent. |

Binary exclusions are conservatively reprojected by maximum with explicit 255
nodata. Unknown mask support is excluded; maps/statistics distinguish it from
known supported cells. No terrain heights are reprojected or smoothed here.
Slope is **not** a hard exclusion. The prior bare/sparse, 5–40° stable-fit mask is
tested separately; it is not automatically a seam mask or confidence.

The first pass established the domain failure. A recorded protocol addendum then
added glacier-only and snow-only exclusion ablations to identify the obstruction.
They are attribution controls, not new admissible candidates or relaxed successes.

## Method and independent evidence fields

**EXTERNAL EVIDENCE:** planar cut/cycle duality relates an enclosing cycle to
separation of interior and exterior faces. See
[Erickson's computational-topology notes](https://jeffe.cs.illinois.edu/teaching/comptop/2020/notes/16-minimum-cut.html),
accessed 2026-10-05. This diagnostic uses simple threshold/flood connectivity, not
the notes' advanced minimum-cut optimization algorithm.

At a threshold T, retain a primal edge only when both endpoints satisfy the hard
constraints and `abs(Swiss-common) <= T`. Traverse dual faces across absent primal
edges. An interior-to-outer-face path certifies failure. If no escape exists, a
boundary of the reached faces contains an enclosing permitted cycle. Polygonize
that boundary, expand grid edges and split repeated-vertex walks into simple
cycles; validate enclosure and every node/threshold. Four-neighbour adjacency is
explicit: diagonal contact alone does not create a physical corridor.

First test unlimited T. Only if the domain encloses do we binary-search sorted
observed differences for the exact minimum threshold. Tests protect worst-node
behavior, monotonicity, broken rings, nonfinite support, wrong-side cycles and
simple-cycle extraction. This certifies feasibility in the sampled graph, not all
continuous terrain or an exact final seam. Returned cycles are deterministic
boundary witnesses, **not shortest routes** or globally optimized seamlines.

No composite cost or invented confidence is used. Independent evidence fields:
absolute/signed disagreement; 3×3 median absolute disagreement as a robust local
diagnostic; Swiss same-level gradient slope; four-neighbour relief residual;
distance to protected interior/source edge; stable-class membership; exclusions.
The median operates on differences for analysis only. It never changes heights.

Independent primary-domain distributions are recorded before threshold analysis:

| Evidence field, median /p95 | z12 | z13 |
| --- | ---: | ---: |
| 3×3 median absolute disagreement, m |1.43 /11.04|1.58 /12.34|
| Swiss same-level slope, degrees |26.11 /46.25|26.74 /48.30|
| Four-neighbour relief residual, m |1.21 /5.31|0.53 /2.62|
| Source-edge clearance, m |1,584 /3,288|1,591 /3,309|
| Distance from benchmark centre, m |3,869 /5,784|3,867 /5,803|

The roughness measure depends on evaluation scale and is not a physical accuracy
estimate. Within the primary permitted z13 population, slope and roughness correlate
with absolute disagreement (0.372 /0.431); edge clearance and centre distance have
little linear association (0.006 /0.010). This is association, not identification
of source error. Small individual minima exist in every sector but do not establish
a passage. The excluded south/glacier population is assessed separately below;
these distributions must not be mistaken for the complete regional population.

## Connectivity, sensitivity and bottleneck result (M)

| Check | z12 | z13 |
| --- | ---: | ---: |
| Primary permitted nodes |54,724|224,315|
| Primary enclosing cycle, unlimited T |No|No|
| Edge guard 100 /500 m |No /No|No /No|
| Glacier buffer 100 /500 m |No /No|No /No|
| Strict stable-mask domain |No|No|
| Glacier-only exclusion attribution |No|No|
| Snow-only exclusion attribution |No|No|
| Primary thresholds 0.5,1,2,5,10,20,40,80,160 m |All fail|All fail|

Thus no finite primary connectivity threshold or admissible route length/cost
exists. This is a robust **negative topology result** across the small declared
sensitivity set, not a parameter search that failed to find a pretty route.

The primary dual escape runs south from the protected region through independently
excluded glacier/change terrain to the source edge and exterior. Its wholly
supported, outside-protected segment spans approximately LV95 north 1090477 to
1087213 at z13 (about 3.26 km), near east 2625000. All 247 crossed edges in that
segment have glacier-excluded endpoints; 92.5% of those endpoints are also snow
classified. z12 independently gives 122 such edges over about 3.21 km. Unsupported
exterior cells are not used to infer glacier coverage. The dual certificate crosses
no permitted primal edge, so raising disagreement tolerance cannot repair it.

### West, south and corners

z13 sectors below use north/south/east/west wedges and independent quadrants;
they overlap where stated. Excluded fractions use the fully supported outer
annulus before glacier/snow exclusion. Compatibility statistics use only permitted
nodes. These are population diagnostics, **not connected best passages**.

| Sector | Permitted nodes | Absolute difference p95 /max, m | Change-excluded annulus |
| --- | ---: | ---: | ---: |
| West wedge |69,191|16.17 /90.82|42.1%|
| South wedge |2,520|8.90 /30.09|97.9%|
| NW quadrant |115,636|16.28 /102.54|3.4%|
| NE quadrant |91,056|7.86 /42.89|23.8%|
| SW quadrant |15,212|9.90 /90.82|87.3%|
| SE quadrant |2,411|12.64 /27.75|97.9%|

North/east contain many compatible patches. West retains high-gradient/high-
disagreement sites. Southern isolated patches cannot traverse the continuous
excluded barrier. Low south population statistics therefore do not rescue the
known problematic sector.

One-kilometre corner patches explicitly tested: SE is 100% change-excluded and has
zero permitted nodes at both levels. SW has 72.1% change exclusion at z13 and 962
permitted nodes; NW/NE have 3,347/3,398. Their respective full-support corner
disagreement maxima are 93.52/49.78/36.12/79.45 m for NW/NE/SW/SE. Favorable corner
cells do not imply that corners can be joined into a permitted enclosing route.

## Inadmissible control and rectangle comparison

| Quantity | z12 relaxed control | z13 relaxed control |
| --- | ---: | ---: |
| Minimum max-disagreement threshold |19.417 m|19.862 m|
| Witness length (not minimum length) |35.77 km|39.25 km|
| Mean /p95 absolute disagreement |9.26 /18.86 m|12.06 /19.47 m|
| Glacier250-excluded route vertices |80.3%|82.9%|
| Snow-class route vertices |46.6%|45.9%|
| Stable-fit route vertices |1.8%|1.9%|
| Slope p95 /maximum |57.85 /71.71°|60.71 /78.95°|
| Minimum distance beyond protected circle |37.67 m|18.78 m|
| Minimum source-edge support |214.74 m|201.76 m|

These loops retain complete elevation support but fail change support. They also
hug both protected and source constraints; they do not establish room for a
future collar. Their approximate outward common-root clearance is 47.5 km, so
finite common support is not the current limiting factor. Distances to its root
edges use local Mercator ground-scale conversion, not an exact geodesic clearance.

At z13 the worst relaxed-control node lies near LV95 `[2629791.49,1092050.58]`,
Swiss-minus-common −19.862 m, slope 11.65°, with glacier/snow exclusion and only
201.82 m source-edge clearance. West/south route maxima remain 19.82/19.85 m;
SE contributes most route vertices. Even this counterfactual does not demonstrate
that low slope makes a valid seam. Below the minimum threshold closure fails;
at it closure succeeds. This is a mathematical bottleneck, not a tolerated error
standard or a guarantee of inter-cell compatibility.

Rectangle control samples the fully supported strip within 1.5 cell diagonals
of the original native 10 km source boundary; it is not the changing whole-tile
delivery frontier. It has no room beyond the source edge for a Swiss collar.

| Rectangle control | z12 | z13 |
| --- | ---: | ---: |
| Absolute disagreement p95 |20.14 m|21.56 m|
| Absolute maximum |207.81 m|201.87 m|
| Glacier/snow excluded fraction |63.1%|61.4%|

The largest rectangle residuals are southern/SE. The counterfactual terrain-aware
route reduces the sampled maximum greatly but does so mostly in inadmissible
terrain. That is **not** a demonstrated defensible advantage. No accepted
corridor-versus-rectangle transition or terrain product exists. Difference maxima
are not adjacent composed-surface jumps; do not compare them directly with the
old 167 m wall metric.

## Support sufficiency and single next prerequisite

**M:** the 10 km support does not contain a closed corridor under the stated
non-changing-support policy. No candidate has legitimate support on both sides
all the way around. Its northern support/compatibility is not the missing factor;
the connected southern change barrier is.

**H — single smallest next investigation:** a **glacier-aware support-extent
feasibility assessment**, using the already retained official inventories to
determine whether a bounded larger Swiss selection can surround the connected
glacier/change system intersecting the protected interior. Identify the necessary
extent before acquisition; do not just grow a square or shrink exclusions.
No such assessment or acquisition was performed here.

An enlargement is geographically necessary for a stable-only enclosure under
the present masks, but its required size/practicality and availability of an
actual stable surrounding route remain unknown. Historical union/buffers are
conservative; more area alone does not establish stability or epochs. This is
not proof that every future change-aware handoff policy is impossible.

No transition method family is authorized by this result. If later supported
corridor evidence succeeds, the research review's priority-preserving constrained
transition remains a conditional candidate with declared common-height accounting,
registration acceptance and protected-terrain constraints. Current evidence does
not justify another feather, fit or datum correction. A final hierarchy contract
or generic resolver is premature.

## External diagnostic, provenance and operations

Final external directory:
`${MERIDIAN_DATA_ROOT}/experiments/atlas/riffelhorn-seam-corridor-v1-final/`.
Independent sibling: `riffelhorn-seam-corridor-v1-final-rebuild/`.
Final identity:
`253fdd01d661a0282fd241b915358d1b6c980efae74797bb2af78999b8816cf5`.

Seven files total 37,441,570 bytes (about 35.7 MiB), plus the small manifest:
two NPZ field/support/witness collections, two maps, two native-LV95 witness JSON
files and measurements. Maps show exclusions and obstructions, not reconciled
terrain. Witness JSON explicitly declares EPSG:2056 and is not RFC7946 lon/lat
GeoJSON. Every input contributor and output array/file is hash identified.

The first pass informed only the attribution addendum and map/certificate clarity;
it did not change primary constraints or terrain. Final generation 45.85 s,
independent rebuild 46.86 s in this environment, including input checks. All seven
files, arrays and manifest reproduce byte-for-byte. No browser service, renderer
stream, tile pyramid or new terrain is produced. No new dependency was added.

## Validation and reproduction

- 100 Swiss + 6 common source hashes; 35 regional-parent files/support fields;
  all used common tile hashes; three glacier archives; retained overlap array hashes.
- Independent rebuild: identical manifest identity and all seven files/array hashes.
- 46 Atlas synthetic Python tests pass, including 8 new graph tests.
- 171 active Node application/policy/model tests pass; one existing optional skip.
- Lint, TypeScript and application-only Vite build pass. Existing deprecation and
  bundle-size warnings retained. No unrelated test changed.
- Local document references, JSON/provenance records, diff and unchanged production
  checks pass. No normal startup or CI dependency on external diagnostic assets.

The normal `npm run build` was also inadvertently run: it passed and copied the
existing Weather publication into ignored `dist`. It had completed before a stop
was possible. No forecast was calculated/acquired/updated. The intended isolated
application-only build below was then run separately and passed. No Weather or
build configuration was changed to conceal that distinction.

```powershell
$terrainPython = "$env:MERIDIAN_DATA_ROOT/earth-lab/.venv/Scripts/python.exe"
& $terrainPython scripts/atlas/seam_corridor.py --suffix=-final
& $terrainPython scripts/atlas/seam_corridor.py --suffix=-final-rebuild
# Immutable directories already exist: use distinct named siblings for another reproduction.
& $terrainPython -m unittest discover -s scripts/atlas -p 'test_*.py'
$taskTests = @(rg --files scripts/atlas scripts/route scripts/ui scripts/weather | Where-Object { $_ -match 'test[^\\/]*\.mjs$' })
node --test @taskTests
npm.cmd run lint
npx.cmd tsc -b --pretty false
node --input-type=module -e "import {build} from 'vite';import react from '@vitejs/plugin-react';await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/seam-corridor-app-build'}});"
git diff 9827b17 -- src vite.config.ts package.json package-lock.json
git diff --check
```

Compare sibling manifests and each listed file SHA-256 for deterministic
reproduction. Source/product/mask drift fails before analysis. Tool and protocol
hashes identify the diagnostic-specific policy; constraint changes require a new
reviewed record and build. Synthetic tests and Node record tests require no
external terrain assets. Exact external roots
follow the established storage contract.

## Production and evidence limits

Production visual terrain remains AWS, analytical terrain independently AWS z15;
IGOR 315° map-anchored with the strengthened curve, exaggeration 1.45; Weather,
Traverse, satellite, projection/lifecycle and startup remain unchanged. No runtime
module imports the diagnostic. Source and product metadata foundations remain
non-production.

**MERIDIAN EVIDENCE:** sampled graph infeasibility, sensitivity, field/support
statistics and exact reproducibility. **EXTERNAL EVIDENCE:** prior cut/cycle and
DEM-support principles, retained official inventories. **RESEARCH HYPOTHESES /
DIRECTIONS:** whether enlarged support admits a stable enclosure, and any future
transition method. There is no accuracy claim, universal seam-cost model,
validated uncertainty field, correction, seamless product or new Lab.
