# Atlas native-grid window and scientific-closure feasibility

## Result and starting gate

**DEMONSTRATED**, bounded to the complete declared retained Riffelhorn read profile,
its three immutable pins, the checked PROJ 9.5.1 coordinate operation and Windows
NTFS. A conservative native **column strip**, retaining every original row, supports
the profile without adopting the unproved 94 × 66 estimate. It is substantially
smaller, not a minimum crop. Scientific support and query capabilities are unchanged.

9 October 2026: public `gbsamirahmed/project-meridian`, clean `main` at
`ebbc0cc305dc9f31c443d8c2a916da12722bddf4`; fetched `origin/main`, divergence 0/0.
Reviewed Foundations [summary](../foundations/summary.md), [decisions](../foundations/decisions.md),
[engineering](../foundations/engineering.md), [platform](../foundations/platform.md),
[evolution](../foundations/evolution.md), economics and roadmap; frozen
[semantic contract](../atlas/semantic-evidence-contract.md),
[derived lifecycle](atlas-derived-understanding-lifecycle.md),
[read contract](../atlas/portable-read-contract.md), accepted
[preparation](atlas-riffelhorn-preparation.md), [retrieval](atlas-riffelhorn-retrieval.md),
[reference cases](atlas-portable-read.md), [independent projection](atlas-portable-projection.md),
[hardening](atlas-portable-projection-hardening.md) and
[resource study](atlas-portable-projection-reduction.md). The existing builder,
Reader, verifier, Store, shared owner and tests were inspected before extraction.

The [frozen experiment design](../../scripts/atlas/portable-spike/native-window/README.md)
preceded implementation. Acceptance: whole-profile closure independent of frozen
coordinates; unchanged complete semantic envelopes; original source-grid identities;
bit-exact stored pixels; all other scientific members unchanged; deterministic
regeneration; fail-closed verification and exact pins; last-ready preservation,
restart and post-open consistency; bounded measured desktop resources. Exclusions:
minimum latitude crop, general raster engine/compression, scientific reinterpretation,
production format/installer, terrain rendering, mobile deployment and private access.

## Original evidence and immutable generations

The original projection remains byte-identical:
`a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c`.
Preparation `357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`
and the twelve retained source prerequisites remain unchanged. The existing
[source inventory](../../scripts/atlas/portable-spike/reduction/source-inventory.json)
contains full headers, qualifications, rights references and source/preparation identities.

| Pin | Exact scientific generation | Population |
|---|---|---|
| before | `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd` | 81 world records, 32 edges |
| after | `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289` | 81 world records, 32 edges |
| legacy | `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8` | 49 world records, no runtime-derived edges |

Original Copernicus GLO30-F DSM SHA256 is
`638c155dd9a5f0b7ee818146def740093da33cee4606071b2bbf7ce3fa00ab95`,
42,594,792 bytes, 3600 × 3600 float32, EPSG:4326, Point registration, no nodata
sentinel. Original affine, expressed as longitude/latitude for absolute column/row:
`lon = 6.9998611111111115 + column/3600`,
`lat = 46.00013888888889 - row/3600`.
Provider vertical provenance remains EGM2008 / EPSG:3855; accepted scalar-unit
qualification remains explicitly unknown. No datum conversion or inferred unit.
The DSM includes surface objects/possible infill. Broad 2010–2015 acquisition and
infill do not become an exact observation epoch: evidence-epoch remains unknown;
product-reference retains documented 2021 distribution and unknown exact subrelease.

The four complete Swiss DTM tiles total 65,607,404 bytes, with LN02 / EPSG:5728
provenance, 0.5 m sampling and mixed acquisition qualifications. WorldCover raster
remains 5,046 bytes; full native vector geometry remains 5,386,941 bytes / 38 features.
All ten non-DSM scientific members, including the three generation documents, are
byte-identical. DSM is not fused with DTM. The accepted Swiss/AWS negative finding
remains unchanged. Missing inventory, unknown time and no-match are not physical absence.

## Scientific closure over every supported query

### Operation order and domain

The accepted Reader transforms a point or a rectangular area (32 segments per edge)
from EPSG:2056, EPSG:4326 or OGC:CRS84, then intersects it with the closed EPSG:2056
core `[2624000,1091000,2626000,1093000]`. Only that intersection is converted to a
raster's native CRS. Every resulting point/vertex is inside the core, including
valid large or partially intersecting requests originating outside it. Queries
without a spatial predicate retain the same qualified metadata; they do not read
an unbounded raster. Full vector geometries and WorldCover centre-mask logic stay intact.

Thus the closure domain is the **entire core rectangle after clipping**, not the
60 requests, sampled points, a bounding-box replacement for geometry, or the original
unclipped geographic rectangle. The argument follows the implemented densified-query
semantics; it does not claim exact geodesic polygon transformations.

### Conservative longitude argument

[closure.py](../../scripts/atlas/portable-spike/native-window/closure.py) records the
exact installed inverse-somerc/Bessel Cartesian translation/WGS84 operation and rejects
a different definition or PROJ version. Its inverse-projection equations were checked
against [PROJ somerc 9.5.1](https://github.com/OSGeo/PROJ/blob/9.5.1/src/projections/somerc.cpp)
and the longitude step against [PROJ cart 9.5.1](https://github.com/OSGeo/PROJ/blob/9.5.1/src/conversions/cart.cpp)
on 9 October 2026. The following interval argument is Meridian's derivation from
that fixed operation, not a PROJ guarantee of arbitrary cropping.

Expand the core by one metre as an arithmetic/clipping guard. Relative to the Swiss
false origin, x is [23999,26001] m, y is [-109001,-106999] m. Bessel constants give
R = 6,378,815.903647821 m and c = 1.0007291384305088; use deliberately loose
bounds R ∈ (6.3,6.5) million m and c ∈ (1,1.01). The rotation latitude
`p0=asin(sin(lat0)/c)`, with physical origin lat0=46.9524055555556°, satisfies
sin(p0) ∈ (.72,.74), cos(p0) ∈ (.67,.70). Inverse spherical terms satisfy
`sin(phi2)=tanh(y/R)`, `lambda2=x/R`, `cos(phi2)>.9998`, `cos(lambda2)>.99999`.

Bound `sin(phi1)=cos(p0)*sin(phi2)+sin(p0)*cos(phi2)*cos(lambda2)` with
sign-aware interval products: [0.7077387875728918,0.7289718684137096]. Therefore
`cos(phi1)` lies in (.68,.71). Applying monotonic asin to
`lambdaB=lambda0+asin(cos(phi2)*sin(lambda2)/cos(phi1))/c`
encloses Bessel longitude in **[7.734525455871762,7.787331344588186]°**.
These inequalities enclose the continuum, not merely corners or empirical samples.

The ellipsoid inverse latitude equation F(phi) is strictly increasing:
`F'(phi)=(1-e²)/(cos(phi)*(1-e²*sin²(phi)))>0`. Its target is between
0.8789311363952742 and 0.9227902223227199; F(40°)=0.7586154980716486 and
F(60°)=1.3111680471846614. Consequently latitude is between 40° and 60°,
so the zero-height Bessel horizontal Cartesian radius exceeds 3.15 million m.
The XY translation has norm `hypot(674.374,15.056)` m and turns longitude by at
most `asin(norm/3150000)` = **0.012269337387549942°**. Z translation does not
change atan2(Y,X). Combined real-arithmetic longitude is within approximately
[7.72225,7.79961]°. Reserve the still wider **[7.71,7.81]°** interval.

Translate that interval onto the original affine grid, extend each side by more
than a native cell, and choose **[column=2554,row=0,width=366,height=3600]**.
Its west/east extent is [7.709305555555556,7.810972222222222]°. Half-open absolute
column selection inside the reserved interval is strictly inside stored columns
2554 through 2919. **Every source row is retained**, so latitude extrema, source
north/south nodata/edge behaviour and transformed-area row bounds need no guessed
crop argument. Original source-grid clipping and conservative windows remain unchanged.

### Mathematical bounds versus tested arithmetic

The interval enclosure is a mathematical argument for the fixed real-arithmetic
operation. Large spatial margins, the metre guard and extra columns are deliberate:
ordinary double rounding and the pinned inverse solver's 1e-10-radian convergence
criterion are far smaller than the remaining longitude margin. No query-dependent
fudge moves a sample or index. Exact native half-open selection still uses the
accepted Reader and installed affine/PROJ operations.

This is **not formal verification of PROJ machine code, libm, every platform or hostile
concurrent filesystem writes**. Version/operation checks fail closed; another build
needs review and conformance. Finite differential tests support implementation
behaviour, not a proof by sampling of all coordinates. The generous bound avoids
relying on an unproved exact-error maximum near the cropped edge. Any unexpectedly
requested pixel outside the strip raises integrity failure, never a valid empty result.

Height areas return original conservative source support/window descriptors, not
bulk values or an aggregate. The full-core descriptor remains `[2694,43,94,66]`;
that descriptor is an answer under accepted semantics, **not the proven stored extent**.
This experiment establishes no general source replacement outside the read profile.

## Experimental representation and implementation

Experimental schema `atlas-native-window-experiment/v1`; identity
`ec6308b7c195af38190eebd4239fcfbe32b416308e2404b80777c598538363f9`.
Original semantic identity is distinct from that local package identity and configured
path. The outer manifest embeds the unchanged original manifest/pins and records:
original source seal/header; absolute window; local stored shape/affine; lossless
storage method/modification notice; cropped file seal; little-endian float32 row-major
pixel seal; fixed-operation closure. It does not claim the crop is the original file.

Stored DSM SHA256:
`ebf729998643aa287b590625de9db59acd512ce27e3e62c537db33cc0df09d90`.
Pixel-stream SHA256:
`931449248b5517d9dc73ed093c2c87a5c0fda2b50ee0f671342ae9b6180263dc`.
Local shape is 3600 rows × 366 columns, with source index translation
`absoluteColumn = localColumn + 2554`, `absoluteRow = localRow`.
DEFLATE/predictor 3, float32 and Point registration preserve all 1,317,600 stored
pixels bit-for-bit. No resampling, interpolation, quantisation, reprojection or
harmonisation. Source overviews are not used by the read profile and are not recreated
in this query-only storage member; this is not a terrain-rendering asset.

[build.py](../../scripts/atlas/portable-spike/native-window/build.py) verifies the accepted
baseline and extracts a native Window, copies every other member exactly, checks
read-back bits and validates the completed candidate. No frozen requests or expected
answers are builder inputs. Two fresh builds reproduce all twelve members, including
manifest, byte-for-byte: 3227.25 / 3283.97 ms. No generated TIFF is committed or published.

[window.py](../../scripts/atlas/portable-spike/native-window/window.py) validates schema,
identity, bounded closure/seals, fixed source/pins, header/Point/nodata, pixel identity,
qualification bindings and existing generation/relationship closure. A captured grid
view exposes original dimensions/affine to accepted query logic and translates only
integral contained native reads to the stored window. Complete envelopes and original
absolute indices remain intact. The original v1 Reader rejects the experimental schema.

Three narrowly scoped factories in the existing spike Reader, Store and shared owner
allow this experimental snapshot. Default v1 behaviour and Store commit ordering are
unchanged and regression-tested. No authoritative runtime, scientific query algorithm,
new installer or general GIS engine is written. `WindowReader`, `WindowShared` and
`WindowStore` are the bounded public experiment interfaces; the existing projection
and default Reader/Store remain usable as the reference.

## Offline readiness, recovery and post-open consistency

Use the accepted owned-directory store: copy into an unready stage; verify all physical
and scientific members; rename to the immutable package identity directory; verify
again; atomically replace a ready record; separately verify/select that exact package.
An old ready package is preserved. Scientific pin selection remains explicit and
independent of package installation selection; no silent generation fallback.

Missing/truncated crop, inconsistent source/local metadata, wrong offset/schema,
unknown pin and damaged members fail. Injected write failure, interruption before
ready and immediately after ready retain the prior selection. The latter can leave
a fully verified ready-but-unselected candidate; it is not an incomplete ready package.
Restart opens and verifies the exact selection; selected deletion clears selection,
with no automatic return to the old scientific state. Explicit old identity still opens.

Captured MemoryFiles preserve held answers when an owned crop is replaced and the
whole directory deleted. Fresh opens reject corruption. Sharing three views keeps
one capture; no mutable-path reread, cross-process cache or concurrent-thread claim.
Baseline forced process-termination tests exercise unchanged commit boundaries;
new-representation faults use deterministic event/write injection and a real fresh
child-process restart. Ordinary process tests do not establish power-loss durability,
directory fsync guarantees or mobile filesystem semantics. Hashes establish integrity
relative to an expected identity, not publisher authenticity or legal origin.

## Measurements

[results.json](../../scripts/atlas/portable-spike/native-window/results.json) records raw
trials, distributions, closure/bindings and toolchain. Host: Intel i7-12700H, Windows
NT 10.0.26200, NTFS C:, about 16 GiB; Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3 /
GDAL 3.9.3, Shapely 2.1.2 / GEOS 3.13.1, pyproj 3.7.2 / PROJ 9.5.1. Node 24.11.0
is needed only for authority/regressions. No installation or geographical acquisition.

| Storage | Original | Experiment |
|---|---:|---:|
| Package, twelve files | 116,692,961 B | **77,412,208 B** |
| DSM | 42,594,792 B | **3,306,806 B** |
| DSM stored cells | 12,960,000 | 1,317,600 |

Package reduction **33.66%**; DSM reduction **92.24%**. Removing unused native columns,
then losslessly encoding the retained values, produces this reduction; no change in
scientific applicability. Other raster, geometry and metadata obligations remain.

Twelve serial fresh processes, three per representation/view count, measure one or
three explicit generation views sharing one snapshot in **both** modes. OS storage
caches are retained: process-cold, not storage-cold. Peak working set includes imports,
verification and queries, and is a process high-water mark, not retained live heap.

| Mode | Verified owner/open + views median (range), ms | Peak median (range), decimal MB |
|---|---:|---:|
| Original, one | 1095.41 (1068.92–1114.05) | 333.31 (332.50–333.35) |
| Window, one | 1071.55 (1069.32–1100.03) | 320.37 (320.18–320.41) |
| Original, three shared pins | 1050.40 (1048.12–1066.10) | 332.87 (332.77–333.46) |
| Window, three shared pins | 1075.18 (1070.54–1086.70) | 320.32 (320.00–320.51) |

The memory benefit is only about **3.8%**; opening is essentially unchanged. Crop
verification additionally decodes all stored pixels to verify their identity. Full
Swiss tiles, geometry, qualified documents, allocations and native libraries remain;
file-size savings do not imply proportional memory savings. No allocation attribution
profiler was run. The previous 599 MB result concerned three independent captures,
not this shared-owner baseline, and must not be used as the crop comparator.

Warm after-pin query medians: median of three trial medians, 15 repeats/type/pin.

| Complete query | Original three shared pins, ms | Window three shared pins, ms |
|---|---:|---:|
| Native point, all applicable families | 32.43 | 12.46 |
| Native area | 19.34 | 17.20 |
| Exact identity | 1.15 | 1.14 |
| Transitive lineage | 14.82 | 14.12 |

These are bounded host measurements, not guaranteed differences or Android timings.
The smaller retiled DSM changes physical decode work; qualifications stay identical.
Legacy also remains measured/queryable; its absent derived edges are not invented.

Three serial owned-store trials: original install median 4822.08 ms (4081.64–4975.51),
window replacement 4611.13 ms (4565.68–4766.95). Window stage 546.87 ms, candidate
verification 1467.40 ms, final verification 1260.11 ms, ready-record work 15.50 ms,
selection including reopening 1306.25 ms. These separate medians need not sum exactly.
Three-pin reopen/identity median 1292.42 ms; real fresh-process reopen 1717.59 ms;
injected failed-stage cleanup/reopen 1319.78 ms. Lifecycle process peak 422.90 MB.

One old ready + one window ready occupies about 194.11 MB including records. A full
window replacement stage would add 77.41 MB; keeping a baseline-sized stage instead
adds 116.69 MB. Measured early failed-stage store footprint is 194,110,205 B, not a
measurement of a complete staged duplicate. Two regenerated window outputs add
154.82 MB outside the store. Conservative combined scratch maximum about 465.63 MB
(under 512 MiB); Store independently enforces its existing 512 MiB bound. All recorded
reader/lifecycle peaks remain below the 768 MiB desktop limit. Temporary copies are
owned, serial and removed; original authority/baseline is never a fault target.

## Scientific, rights and portability assessment

All qualifications, CRS/datum distinctions, unknowns, native source/preparation/method
lineage, rights references, exact membership and historical envelopes are retained.
No source record is overwritten or invented. The copied original rights document's
unchanged-byte preparation note describes the historical accepted preparation;
the separate experimental storage notice explicitly records this later crop.

Reviewed provider [GLO30-F Annex, pp.20–22](https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf)
on 9 October 2026; URL serves version headed 15 February 2024. Article 4 provides
modification/distribution rights subject to the licence. Cropping is a modification:
Article 6's adapted-product credit, downstream liability information and obligations,
and non-endorsement requirements apply. Original copyright dates/provider references
must not become Meridian preparation dates. The manifest records the changed storage
method and terms reference, **not a complete legal distribution notice**. Exact notice
assembly, licence acceptance, code/native-library rights and end-user offline package
review remain unresolved. No generated raster is distributed; this is not legal clearance.
Original accepted rights references remain intact; the prior source-by-source register
still governs the unchanged Swiss, WorldCover, GeoCover and GLAMOS members.

The reader still needs the same Python, NumPy, GDAL/TIFF, GEOS and PROJ stack. It needs
neither original source files nor the authoritative Node/Python query implementation
nor network access in isolated tests. No dependency removal, cross-language reader,
mobile performance, final schema/format or phone offline lifecycle is demonstrated.
The analytic strip does not justify other regions, source grids or CRS pipelines.

## Validation and preservation

| Executed validation | Passed | Failed / skipped |
|---|---:|---:|
| Frozen original corpus, three fresh isolated processes | 180 comparisons | 0 / 0 |
| Frozen window corpus, three fresh isolated processes | 180 comparisons | 0 / 0 |
| Authoritative reference, 60 cases | 120 indexed/full comparisons | 0 / 0 |
| Novel deterministic complete envelopes | 436 comparisons | 0 / 0 |
| Window scientific/lifecycle tests | 8 | 0 / 0 |
| Default Reader and hardening/lifecycle tests | 44 | 0 / 0 |
| Shared-owner regression tests | 9 (159 additional comparisons) | 0 / 0 |
| Native reader regression tests | 31 | 0 / 0 |
| Frozen-fixture tests | 12 | 0 / 0 |
| Runtime/lifecycle/registration/retrieval tests | 259 | 0 / 0 |

Novel queries use deterministic seed 20261009: 80 arbitrary core interiors, corners,
Swiss seams and representable neighbours, native DSM boundaries, supported CRS
transformations, partial/oversized areas, source/time/class conjunctions, unknown
knowledge, absent identities and real lineage. A directly calculated DSM cell centre
asserts original row 70/column 2740 and direct full-source value; all 1,317,600 stored
pixel bits are compared to the full source. Differential agreement shares accepted
query/kernel logic, so these independent anchors and the analytic enclosure are
necessary qualifications, not claims of a second independent scientific engine.

Expected rejections count as passes: nine in each frozen replay. Isolation denies
source/authority repository opens, original baseline access for the window reader,
network and child dispatch. Full closure/corruption/failure checks use owned copies.
Frozen expectations are never regenerated. Determinism compares every physical member.

Lint, TypeScript and application-only Vite build pass; existing large-chunk and GIS
library deprecation warnings remain. The full Weather/data-materialising build,
unrelated UI suites, actual disk exhaustion, storage-cold trials, power cuts, hostile
concurrent writers, Android/iOS and rights-release certification were **not run**.
Preservation checks verify 42 status rows, 113 production hashes, all original scientific
files/publications/fixtures and the negative Swiss/AWS finding. Navigation additions
are append-only; complete diff/links/whitespace are reviewed before commit.
**58/58 preservation, scope, conformance-receipt, resource and navigation safeguards
passed**; 1,164 existing files outside the ten bounded edits remain unchanged.

## Decisions and exactly one subsequent bounded task

**DECIDE NOW:** this conservative native strip is sufficient for the declared profile
on the checked operation; original source and stored representation must remain separate;
keep exact offsets, full qualifications and failure semantics. Shared captures remain
useful for multiple pins, while the package reduction does not remove GIS dependencies.

**PROVISIONAL DIRECTION:** retain this as an isolated storage-binding experiment.
**DEFER PENDING EVIDENCE:** smaller latitude crops, portable kernels, mobile resource
budgets, power-loss guarantees, authenticity and legal offline notice assembly.
**REJECT:** resampling, bounding-box geometry replacement, fixture-coordinate crops,
Swiss/DSM fusion, implicit generation fallback or production format/framework selection.
No earlier accepted result is rewritten.

Exactly one subsequent bounded task — **MERIDIAN ATLAS PORTABLE READER GEOMETRY AND
CRS DEPENDENCY FEASIBILITY — NOT BEGUN**.

Uncertainty: which available, rights-compatible geometry/CRS deployment options can
preserve the finite profile without the present desktop-only packaging assumptions?
It matters because 320 MB desktop peaks and the unchanged native dependency stack
remain more limiting than this DSM payload for a field reader. Prerequisites: the
unchanged contract/60 cases, this exact window binding, current dependency inventory
and novel boundary/CRS cases. Permitted scope: a bounded dependency/capability inventory
and, only if available locally, one small independent adapter comparison; no custom
GIS engine, new acquisition, SDK installation, phone deployment, framework choice,
private access or production integration. Deliver a concrete dependency/rights matrix,
semantic boundary results and a justified next hardware/build prerequisite. Acceptance:
no lost qualifications or weakened predicates; complete conformance where executable;
explicit unsupported cases and resource/toolchain limits otherwise. Stop at a measured
feasible option or precise prerequisite blocker. Do not begin it in this task.
