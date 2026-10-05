# Atlas information scale and broad-surface disagreement

2026-10-05. Baseline `4130fa20b99ca921167cd5015fe38feb7a778aed`.
Status: **partial but useful decomposition; one terminal experiment designed,
not implemented. Production unchanged.**

## Decision

Separating representation bands clarifies the problem, especially on steep
terrain. It does not remove the broad Swiss/Copernicus discrepancy. At the
declared z12 broad scale, whole-overlap RMS changes from **20.35 to 19.94 m**;
the Swiss detail component is **2.10 m RMS**. Buffered glacier/change terrain
retains **27.18 m broad RMS** versus **27.62 m raw**. Suppressing fine information
alone cannot resolve these broad offsets.

A closed ring of mutually stable observations is a **preferred opportunity,
not a hard integration prerequisite**. Stable ground remains necessary evidence
for justified error/registration fitting; it need not surround every product.
Changed terrain can be represented by explicit source priority or an explicitly
synthetic transition without pretending it is stable or a measurement error.
The completed corridor failures remain valid under their declared domain.

The single next test is [protected-priority two-band representation transition](riffelhorn-final-reconciliation-experiment.json).
It tests whether broad-shape accommodation and progressive detail loss can be
controlled independently outside the preserved interior. It is **not** an
accuracy-improving fusion claim. Its fixed geometry/rule may fail. No transition
was generated here, and neither source family was altered.

## Evidence and frozen problem

**MERIDIAN EVIDENCE (M)** is reproducible local measurement or retained renderer
evidence. **EXTERNAL EVIDENCE (E)** is primary practice/documentation below.
**RESEARCH HYPOTHESES / DIRECTIONS (H)** are design choices still awaiting testing.
The decomposition is an established operation reproduced; its application and
next-test design are Meridian engineering, not a new DEM-fusion invention.

The baseline was clean `main`, matching locally recorded `origin/main` 0/0.
Actual visual configuration remains AWS Terrarium256px, geometry ceiling14 and
relief ceiling15. Analytical AWS256px/z15 remains independently configured.
Actual terrain code retains IGOR315°, map anchor, existing strengthened curve,
colors/filtering, exaggeration1.45 and satellite suppression. No `src/`, package,
Vite, Weather, Traverse, projection/lifecycle or startup file changes.

Reviewed predecessors, preserving their historical decisions:
[direct regional terrain](riffelhorn-regional-terrain-prototype.md),
[reconciliation controls](riffelhorn-terrain-reconciliation.md),
[metadata architecture](terrain-source-product-architecture.md),
[larger Swiss support](riffelhorn-swiss-support-product.md),
[common-reference assessment](global-reference-assessment.md),
[common delivery](copernicus-common-product.md),
[first hierarchy](terrain-hierarchy-prototype.md),
[regional parents](regional-parent-diagnostic.md),
[methods review](spatial-terrain-reconciliation-research.md),
[corridor feasibility](seam-corridor-feasibility.md) and
[glacier-aware extent](support-extent-assessment.md).

Keep these components distinct:

| Component | Established fact / limit |
| --- | --- |
| Internal regional LOD | Swiss-derived13→14 reduced705-point RMS39.82→0.71 m. This is refinement displacement, not accuracy or registration. |
| Vertical frame | Native Swiss LN02 versus common EGM2008. Retained diagnostic +0.166…+0.752 m; combined accuracy unresolved, no accepted transform. |
| Horizontal registration | Prior sector-unstable (−0.85,+2.89) m signature does not justify a shift. |
| Surface | High-quality Swiss DTM versus edited global DSM; resolution alone cannot explain all differences. |
| Epoch / change | Swiss2024 release incorporates2021/22 LiDAR and2023 photogrammetry; Copernicus principally earlier observations. Cell epochs unknown; glacier residual is not established error. |
| Information scale | Different observation footprints and generalisation alter ridge/valley/ledge representation. Grid spacing, effective information, delivery and mesh remain separate. |
| Spatial handoff | A cross-family wall is not ordinary same-family refinement. Moving the handoff downward did not eliminate it. |

Source identities are frozen in the [diagnostic plan](terrain-scale-plan.json):

| Product | Identity |
| --- | --- |
| Swiss support, original z12–18 | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` |
| Swiss-derived parents z10–14 | `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672` |
| Common/coarse z8–13 | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2` |

## Narrow established-practice review (E)

Primary sources accessed2026-10-05; living pages describe their current state,
not an undocumented guarantee about prior releases.

* [GDAL overview averaging](https://gdal.org/en/stable/programs/gdaladdo.html)
  defines non-nodata contributing-pixel averages and partial-pixel weighting.
  Explicit averaging provides an interpretable summarisation rule; it does not
  identify a sensor's effective spatial resolution. Default nearest sampling
  is unsuitable for this mean-preserving diagnostic.
* [Losasso & Hoppe, geometry clipmaps](https://hhoppe.com/geomclipmap.pdf)
  describe filtered coarse levels and prediction residuals, separately from
  geometry morphing/stitching for continuity. This supports the mathematical
  broad-plus-residual distinction. It does not settle which independent DEM
  should define a world-model elevation. The author-hosted PDF carries draft
  markings; no exact filter is claimed as an Atlas standard.
* [Karkee et al.,2008](https://www.sciencedirect.com/science/article/pii/S1537511008002493)
  is specific prior art for frequency-domain DEM fusion after co-registration
  and void filling. Publisher search abstract was available; full text was
  inaccessible during this review. Sensor-specific complementary error bands
  are its premise, not demonstrated here. Its cut-off is not transferred to
  Swiss/Copernicus and regional residuals are not automatically trustworthy noise-free bands.
* [Petrasova et al.,2017](https://link.springer.com/article/10.1186/s40965-017-0019-2)
  distinguish updating a subregion from homogeneous-error fusion. Their
  distance-weighted transition can preserve the preferred interior while
  modifying an overlap. They explicitly require aligned/co-registered inputs
  and leave common resolution/reinterpolation application-dependent. Their
  water-flow case studies do not validate alpine glacier fusion or a universal
  blend width. This is relevant prior art, not evidence that any smooth collar
  is acceptable for Atlas.
* [Ames Stereo Pipeline dem_mosaic](https://stereopipeline.readthedocs.io/en/latest/tools/dem_mosaic.html)
  documents first-source priority retained except within a specified boundary
  band, alternate aggregation rules and external weights. This establishes
  explicit preservation/transition policy in mature tooling, not a requirement
  for a stable enclosing ring or a statistically justified uncertainty field.
* [ArcticDEM current mosaic description](https://www.pgc.umn.edu/data/arcticdem/)
  describes median contributors, Copernicus-based water treatment and reference
  adjustment, with separately delivered reduced-resolution mosaics. Its mosaic
  combines observations across years; it is not a single acquisition.
* [REMA production description](https://www.pgc.umn.edu/data/rema/)
  distinguishes time-dependent strips from mosaics and describes pixel time/error
  estimates. This supports retaining temporal and derived-product provenance
  when terrain changes, rather than treating all differences as instrumental bias.
* [Nuth & Kääb,2011](https://tc.copernicus.org/articles/5/271/2011/)
  diagnose shifts and biases using stable support, including limited stable
  terrain. Their registration requirement does not imply a stable closed
  perimeter. It cannot justify the rejected Meridian translation merely because
  a fit lowers RMS.

**H:** use these practices for a source-priority visual representation test,
not to assert uncertainty-optimal, hydrologically correct or physically observed
fusion. Neither a measured local error model nor a common vertical error budget
has been established.

## Diagnostic method (M)

The [protocol](terrain-scale-plan.json) preceded numerical work; its single
fine-profile supplement was recorded before reading those fine tiles.
No acquisition, transformation, registration, smoothing of source files,
transition raster, seam optimisation or application render occurred.

Use the retained complete Swiss-derived z13 cells and decoded common z13 at
**identical pixel centres**. Swiss is already an area-generalised representation.
Apply the same aligned recursive2×2 **Web Mercator pixel-area mean** to both
families, first to z12, then to z11 as one scale sensitivity. Accumulation is
float64. Reconstruct each coarse field on the original z13 centres by bilinear
prolongation, requiring four complete finite neighbours. Partial parent means
and unsupported interpolation are rejected, never extrapolated or filled.
The Swiss restriction agrees with independently retained parent fields to
floating-point rounding. Common quantisation already exists in its input PNGs.

At the benchmark: z13 spacing≈13.28 m, broad z12≈26.56 m, sensitivity
z11≈53.12 m. These are local delivery spacings with latitude accounted for,
not measurement resolution, sharp frequency cut-offs or the Copernicus PSF.
Copernicus postings remain approximately21.5×30.9 m here; interpolation cannot
create observations. Swiss distributed0.5 m grid is not independent0.5 m information.
Box restriction plus linear prediction is reproducible and mean-preserving,
but is not an ideal spectral separator, and can retain aliasing/phase effects.
No Gaussian width or claimed sensor transfer-function match is invented.

Let fine retained representations be S,C; identical restriction/prediction is L:

```
raw D = S - C
broad B = L(S) - L(C)
regional detail Rs = S - L(S)
common detail Rc = C - L(C)
D = B + (Rs - Rc)
```

Also retain asymmetric `L(S)-C` for the common practice of generalising only
the regional source. Common residual is demonstrably nonzero, so it cannot be
omitted in an exact two-family decomposition. This is a representation identity,
not an independent estimate of noise, temporal change, datum error or accuracy.

Population: finite complete overlap with200 m native-source-edge guard. Every
reported band uses the **same cells** within each broad-scale test. Existing
conservative stable candidates are regridded by exclusion maximum; separate
steep non-ice≥45°, buffered historical glacier/change proxy and protected-circle
strata are reported, including inconvenient outliers. Classes are not mutually
exclusive, and glacier union/buffer is not a verified per-cell change measurement.
The stable population differs from the older25 m centre-sampled reference study;
their medians must not be interpreted as changed calibration.

## Results (M)

| Population | Raw RMS | Broad z12 RMS | Swiss detail z12 RMS | Broad z11 RMS | Swiss detail z11 RMS |
| --- | ---: | ---: | ---: | ---: | ---: |
| all | 20.35 | 19.94 | 2.10 | 19.37 | 4.54 |
| stableCandidates | 5.56 | 5.06 | 1.55 | 4.48 | 3.64 |
| steepNonIce | 16.32 | 14.34 | 4.53 | 12.15 | 8.41 |
| glacierChangeProxy | 27.62 | 27.18 | 2.31 | 26.53 | 4.94 |
| protected | 39.82 | 39.58 | 2.01 | 39.18 | 4.21 |

RMS metres; complete distributions, medians, NMAD, tails, correlations, sectors
and energy terms are in [measurements](terrain-scale-measurements.json). The
fine-profile fields/statistics are diagnostic measurements, not Earth accuracy.

At z12, all-support raw median−1.510 m/NMAD4.504 m becomes broad
median−1.298 m/NMAD3.919 m. Stable candidates: raw−0.168 m/NMAD1.611 m;
broad−0.190 m/NMAD1.148 m. Steep non-ice broad NMAD7.095 m versus raw8.980 m;
glacier/change broad NMAD8.747 m versus raw9.379 m. Broad outliers persist.

The all-support mean-square identity at z12 is:
`414.140 = 397.465 + 3.998 + 12.677` m² (broad, residual-difference, cross term).
At z11: `414.140 = 375.304 + 14.622 + 24.214` m².
Broad terms are about96.0%/90.6% of raw squared amplitude, but these are
**not percentages of error causes**: correlated components are not orthogonal,
and filtering is not an attribution model. The declared representation band
removes only a small part of the whole-support amplitude; no reliable fraction
of the complete source disagreement can be assigned to expected fine detail.

Broad disagreement remains spatially coherent: z12 broad lag correlation at
approximately106 m is0.805 east-west/0.781 north-south, while detail-difference
correlation is0.010/0.002. At≈505 m broad remains0.525/0.346; the residual is
near zero. Broad structure includes the southern/eastern negative corridor and
localized high ridge differences. Swiss detail amplitude correlates with slope
(all-support≈0.424 at z12); raw/broad absolute disagreement does not have a
simple monotonic all-support slope relationship. Ice/epoch/terrain sectors confound
it. No correlation is interpreted as causal registration evidence.

### Profiles and finer information

Four frozen20 m-step LV95 profiles cover northern mixed stable context,
Riffelhorn rough terrain, southern change context and the west-boundary approach.
Names describe contexts, not verified stable land along every point. Exact
endpoints and full samples reside in the protocol/external measurements.
They are profiles **approaching** the old hard boundary, not a generated join.
The former rectangle crossing/wall evidence remains in historical controls.

Read-only z16 sampling adds≈1.66 m delivery information to these profiles.
Each touched existing tile is hash checked; missing whole regional tiles remain
absent. No common substitute is used. This supplements the z13 band without
regenerating a fine regional field.

| Profile | Fine valid samples | z16 Swiss minus common RMS | z16 Swiss minus z12 broad Swiss RMS |
| --- | ---: | ---: | ---: |
| North mixed stable context | 251 | 9.09 m | 2.30 m |
| Riffelhorn rough | 151 | 25.64 m | 4.04 m |
| South change context | 326 | 14.27 m | 3.69 m |
| West boundary approach | 107 | 18.34 m | 1.86 m |

The rough profile reaches≈153 m fine Swiss/common difference, while regional
detail relative to its broad component reaches≈29 m. The broad mismatch survives
generalisation. North contains a localized broad discrepancy amid otherwise close
agreement; south retains spatially persistent differences and edge-like structures;
west retains an offset over a relatively smooth segment. None proves a specific
physical cause. Fine ledges/channels can remain valuable despite low area-wide
detail RMS; area statistics alone cannot assess their visual usefulness.

Inspected diagnostic images: `decomposition.png` and `profiles.png` under
`C:/Users/gbsam/Documents/Projects/meridian-data/experiments/atlas/terrain-scale-decomposition-v1-final/`.
Black circle is protected interior; purple contour is conservative250 m buffered
historical glacier union. Blue/red show native-height disagreement, not errors.
No actual Meridian captures were needed for this diagnostic; subsequent visual
claims are explicitly future tests or previously recorded renderer findings.

**Outcome: B, partial decomposition + clear final experiment.** A useful band
separation exists, but broad disagreement is dominant in this retained comparison.
Steep terrain benefits more from generalisation; glacier/change sectors retain
large broad mismatch. There is no natural frequency threshold proving compatible
source heights, and no fitted correction is accepted.

## Corridor, temporal and provenance decisions

The old stable-domain test proved no enclosing route under its hard exclusions,
even with unlimited disagreement; glacier-aware expansion did not justify new
Swiss acquisition. It does not prove that an explicitly derived representation
cannot cross changed terrain. Further ring hunting and transboundary audits are
not prerequisites for the next test.

Stable support retains three roles: constrain a physically justified registration
or bias model, indicate unusually compatible handoff opportunities, and validate
behaviour outside change sectors. It is **preferred for transition placement**,
not a mandatory closed loop. Small disagreement is compatibility, never truth.

| Term | Meaning |
| --- | --- |
| Source-derived terrain | One identified source family plus declared reprojection/resampling/generalisation; not necessarily untouched measurements. |
| Regional detail / prediction residual | Higher-band structure relative to a declared same-family coarse predictor; no inherent accuracy/confidence claim. |
| Reconciled / transition representation | Intentionally constructed multi-family or adjusted terrain, retaining methods/contributors/support; synthetic where appropriate. |
| Render-only continuity | Stitching/skirts/morphs that change visual continuity without resolving the represented elevation's source meaning. |

Genuine temporal change requires source priority plus retained epoch/change
metadata. Prefer the authoritative regional family within its declared pure
support without assuming every cell is newest. A transition across historical ice
has synthetic, mixed temporal support, not an interpolated observation date or
glacier-change estimate. No glacier residual may train an instrumental correction.
Missing per-cell epochs/uncertainties remain explicit; do not invent them.

Native height references remain distinct. A physical numerical fusion requires
justified common-frame accounting and its limitations. The proposed visual test
instead declares its scalar transition **heterogeneous native-height synthetic
terrain**. It cannot claim a common physical CRS, accurate fused DEM or analytical
height policy. The known local datum effect is context, not a constant correction.
This deliberately limits what a successful representation test would establish.

## Architectural direction (H, not frozen contract)

Prefer a **hybrid**: immutable common/regional pyramids, prepared reproducible
derived representations when their support/scale need coexistence, simple
evaluation delivery through the existing single MapLibre raster-dem stream.
Avoid mutating canonical perimeter heights and avoid frame-by-frame viewport
dependent terrain URLs/cache identities. Pure static reconciliation obscures source
priority; clever dynamic viewport switching adds cache/lifecycle instability.
Prepared provenance-aware terrain is sufficient to test the immediate problem.

However, a transition pyramid's regional-derived parents can influence landscape
geometry. Do not suddenly replace them with unrelated common parents and recreate
the39.82 m source-switch jump. Common/generalised-looking terrain is not necessarily
common-source terrain. The final test must measure this cost; it cannot promise
pure Copernicus at every distant level while preserving incompatible local parents.

Previous1440×900 views span about173 km landscape,43 km wide planning,16 km close
and2 km detail in conservative axis-aligned bounds. Thus the close view can cross
the10 km study edge while central detail remains inside. Lateral detail movement
still crosses a boundary. Geometry/relief/loaded-parent DEM levels differ: this is
the boundary-critical case, not a single camera-zoom threshold or proof of uniform
screen resolution. Numerical continuity must test height intercepts/derivatives
and scale mismatch; visual continuity must independently test hillshade, silhouette,
motion, loading, rotation and satellite geometry. Neither substitutes for the other.

## One final experiment, then stop

The machine-readable [design](riffelhorn-final-reconciliation-experiment.json)
freezes exact inputs, support, rule, controls, metrics, cameras and failure guards.
Only this test is proposed; no competing widths, fitted surfaces or additional crop.

* **Support:** existing10 km source rectangle; circular evaluation footprint
  radius4 km around LV95[2625000,1092000], providing1 km source-edge margin.
  Protected radius1.5 km remains pure regional; this is an engineering footprint,
  not a proven physical seamline. Check actual complete-cell/halo support first.
* **Two controls:** broad-shape accommodation through1.5→4 km; regional-detail
  taper only through3→4 km. Use one fixed quintic weight in each band. The broad
  component uses the tested z12 restriction/prediction; this is representation
  separation, not source-error filtering. The exact formula keeps both Swiss and
  common residuals, and copies pure endpoint branches exactly.
* **Pyramid:** z12–18 transition evaluation, regional-owned fine values inside;
  diagnostic derived z11/10 parents from the resulting z12 representation.
  Use complete retained parent cells at coarse levels rather than falsely
  equating old whole-tile publication with valid cell support. Missing support
  stops the test; no Swiss extrapolation, more acquisition or silent collar shift.
* **Identity:** pure common, pure regional, same-family generalisation, derived
  transition/parents. Preserve the full signed band operator, b/d controls,
  support and temporal masks. With different band weights the operation is not
  a simple convex two-source average; coefficients can be negative. Weights
  are neither confidence nor fractions of observation truth.
* **Controls:** pure families and frozen hard parent/source handoff. Hold IGOR,
  exaggeration1.45, basemap, projection/camera and satellite behaviour fixed.
* **Metrics:** exact interior and outside preservation, reconstruction, dense
  radial/sector worst-section profiles, added slope terms, new extrema/channel
  artifacts, radial detail retention, scale-to-scale differences, tile support
  and hashes. Report all broad collar deformation, not just edge-step reduction.
* **Visual:** established9.4/11.4/12.4/13.2/14.2/16.2 central views, four bearings,
  eight azimuths at collar radii3000/3500/4000/4250 m, original west/south cameras,
  cold/warm zoom and west/south lateral crossing/return, satellite geometry checks.
  Record requested and actual mesh/relief parents, cancellations and responses.
* **Predeclared rejection guards:** any fine protected or outside-common change
  beyond1/256 m; fabricated support; source-edge intercept>0.1 m after genuine
  local slope is accounted for; induced-gradient p95>0.05 m/m or a connected
  ≥100 m section above0.10 m/m; new synthetic ridge/depression/channel; persistent
  wall/crack/strong band/severe popping in any required view; lost provenance.
  These are conservative engineering guards, not surveyed accuracy tolerances.
  Visual failure overrides passing numerical guards. Smoothness alone never passes.

The design intentionally permits declared synthetic broad accommodation only
outside the protected interior. Whether this distortion is acceptable is the
experiment's question, not an assumption. Existing broad mismatch makes failure
plausible. This tests an established priority/residual-transition family adapted
to Meridian, not an uncertainty-optimal fusion algorithm.

Immediately afterwards, **regardless of success or fundamental failure**, record
the result and freeze the Terrain Hierarchy Contract with demonstrated invariants
and limitations. One narrow implementation defect may be repaired; no new method
branch, widening search, acquisition or glacier ring. Generic implementation and
second-region validation are separate later tasks. They are not authorized here.

## Reproduction, verification and limits

The canonical diagnostic is external; only protocol, compact measurements,
manifest, tooling and tests belong in Git. Original products remain immutable.

```powershell
$py = 'C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
$data = 'C:/Users/gbsam/Documents/Projects/meridian-data'
& $py scripts/atlas/terrain_scale.py --data $data --suffix=-final
& $py scripts/atlas/terrain_scale.py --data $data --suffix=-rebuild
& $py -m unittest discover -s scripts/atlas -p 'test_*.py'
node --test scripts/atlas/test_terrain_scale.mjs scripts/atlas/test_terrain_policies.mjs scripts/atlas/test_terrain_metadata.mjs
git diff --check
```

Generation refuses an existing diagnostic manifest; use a new explicit suffix to
reproduce again. Both frozen runs independently reproduce all output hashes and
identity. Preparation output is diagnostic arrays/maps/profiles, **no terrain tiles**.
Verified100 Swiss and6 common canonical hashes/lineage,35 regional-parent files,
every decoded common tile, three retained SGI archives and all retained overlap
array hashes. Fine profile PNGs are verified individually; the entire11,429-tile
fine estate is not unnecessarily rehashed. No writer targets source/product roots.

Deterministic identity `f3ddeac64b54213f5380968e0cd60a9dda16e8bfdc5e48d715932a1fcef7e53c`; 28 files / 183,024,027 bytes per run, all matching. Algebraic closure maximum 0 m. Independent scalar RMS and separate norm/median checks agree. Canonical source, parent and used fine-tile hashes were reverified after analysis. 60 Python tests pass; focused Node record/policy/model checks and local-reference/diff checks are recorded at completion. Existing rasterio/NumPy deprecation warnings persist. No app/build/lint/TypeScript rerun is warranted because no runtime/dependency/build configuration changed.

Limitations: exact sensor PSFs, cell acquisition times, source-specific spatial
uncertainty, accepted registration and combined height-transformation accuracy
remain absent. Filter choice identifies a representation band, not every physical
cause. Interpolation-support exclusion and the guarded fixed population affect
sample counts; profile locations are illustrative, not random samples. No terrain
reconciliation or renderer performance was measured in this task. The proposed
experiment is unimplemented. Production and analytical behaviour remain unchanged.
