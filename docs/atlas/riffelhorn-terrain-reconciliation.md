# Riffelhorn regional/global terrain reconciliation

Bounded investigation, 2026-10-03; public sources accessed on that date. Started
from clean canonical `main`, `fe8addcbce4b7b7966dc41c93361d69d6c416f49`, equal to
locally recorded `origin/main`. No remote refresh was needed for the baseline.

## Decision and stopping point

**No reconciliation method is accepted for production.** The small research crop
and uncertain global height semantics are insufficient to support defensible
fusion. Two established blending principles remove the mathematical edge step,
but either substantially reshape the collar or consume useful regional interior.
The adaptive diagnostic also exposes along-edge contribution artifacts. This is
not evidence that every implementation of adaptive or multiresolution fusion fails.

The next architectural decision needs a **protected regional interior and an
explicit, adequately supported overlap outside it**, source quality/epoch masks,
and an accountable height-reference policy. An arbitrary research rectangle or
delivery-tile edge is not a scientifically justified seamline. A larger overlap
could permit a better join; this investigation does not establish that it will.
No additional Swiss acquisition, provider evaluation or universal resolver began.

Production stays AWS. Every `src/` file, visual/analytical configuration, Traverse,
Weather, camera/projection/lifecycle, imagery, satellite policy and exaggeration
remains unchanged. All new tooling is isolated under `scripts/atlas`; normal
startup and CI do not require external products or the loopback server.

## Evidence discipline

- **MERIDIAN EVIDENCE (M):** verified retained inputs, deterministic difference
  analysis, two diagnostic controls, profiles and inspected application captures.
- **EXTERNAL EVIDENCE (E):** cited primary methods and official processing/reference
  documentation. These do not establish which AWS pixels have which error.
- **RESEARCH HYPOTHESIS / DIRECTION (H):** causal explanations and future support,
  reconciliation or hierarchy choices that remain unverified.

## Exact surfaces and frozen presentation

### Regional (M, with retained official source provenance)

The unchanged parent is `riffelhorn-regional-terrain-v1`, identity
`4fc837f299271c7238591865a393f98facc6fa7b93d9cc75305160df900b1fe5`.
Its manifest SHA256 is
`778745c36f2208e72a28a99923d00d81fcd0bd7f90e8759ba3f03362ccfc4627`.
The verifier checks all 1,094 tile/mask hashes, canonical catalogue/code identity,
four official source hashes and retained AWS contributors.

The four inputs are `swissalti3d_2024_{2624-1091,2624-1092,2625-1091,2625-1092}_0.5_2056_5728.tif`.
Each is a 2000² float32 0.5 m LV95 grid, nodata −9999 with no missing cells here.
Together they cover EPSG:2056 `[2624000,1091000,2626000,1093000]`. Source LN02 heights
in metres are retained, not transformed to a guessed AWS datum. The 2024 release
uses Valais 2021/22 LiDAR with later photogrammetric updates; it does not give a
per-cell acquisition date. Grid spacing is not independent measurement resolution.
Exact inputs/hashes/receipts and processing are in the unchanged
[parent record](riffelhorn-regional-terrain-prototype.md) and
[catalogue](riffelhorn-data-catalog.json); the new machine-readable record also
retains the verified source inputs.

Parent output: EPSG:3857, XYZ, 256-pixel Terrarium PNG, z7–18 populated within a
z5–18 preparation contract; average reprojection through z17, bilinear at z18,
pixel-centre regional masks. Swiss pixels retain LN02; other pixels are AWS,
including explicit cross-parent z15 overzoom above z15. Encoding rounds to 1/256 m
(maximum quantization 1/512 m). Independent parent transfer RMS was 0.047 m at z18,
not a claim of 2 mm total accuracy. Horizontal transformation has a stated 1 m
operation accuracy. No existing TIFF or parent product was modified.

### Global: what is and is not established (M/E)

The comparison uses **retained AWS Terrarium z15**, 256-pixel EPSG:3857/XYZ RGB
metre encoding and pixel-centre cross-tile bilinear sampling. Nine cached tiles
cover the analysis and 100 m outside profile portions. All nine have
`x-amz-meta-x-imagery-sources: eudem/eudem_dem_5deg_n45e005.tif`.
Their raw bytes, metadata, versions and hashes are frozen in the new record.
Header contributor identity is not an exact per-pixel provenance mask.

The official [joerd data-source record](https://github.com/tilezen/joerd/blob/0b86765156d0612d837548c2cf70376c43b3405c/docs/data-sources.md)
identifies EU-DEM for Europe, published terrain versions from 2016/2017 and no
regular-update commitment. Cached Last-Modified dates in November 2017 are
consistent with that history; they do not prove a precise build/version.
[EU-DEM's official validation report](https://ec.europa.eu/eurostat/documents/7116161/7172326/Report-EU-DEM-statistical-validation-August2014.pdf)
describes a SRTM/ASTER-derived DSM on a one-arcsecond grid, ETRS89 and
EVRS2000/EGG08 heights, with edited/normalized water features. Those are **upstream
semantics**, not proof that this AWS derivative retains the same height reference,
version or every upstream processing choice. Roughly 30 m nominal source sampling
and approximately 3.32 m z15 delivery sampling at Riffelhorn are different facts.

The inspected pinned public joerd tree has **no EU-DEM source module**. Its
[compositor](https://github.com/tilezen/joerd/blob/0b86765156d0612d837548c2cf70376c43b3405c/joerd/composite.py)
shows source-priority replacement and GDAL resampling, but does not recover the
hosted EU-DEM ingestion, vertical handling or generalisation history. The
[format record](https://github.com/tilezen/joerd/blob/0b86765156d0612d837548c2cf70376c43b3405c/docs/formats.md)
specifies Terrarium metre encoding; its explicit EGM96 statement is under **Skadi**
and cannot safely be copied to every Terrarium contributor. Low zoom can use other
sources. No ocean/bathymetric contribution is indicated by these alpine z15 headers;
exact lake treatment and global nodata semantics remain incompletely established.

### Renderer (M)

The fixed production treatment is IGOR, map anchor, 315°, linear DEM filtering,
shadow `#17211f`, highlight `#f4efe0`; configured accent `#586b66` and altitude 42
remain ineffective for this method. Strength stops are
`(5.5,0),(7,.09),(9,.30),(11,.54),(12,.45),(13,.36),(14,.33),(15,.30),(16,.30)`.
Exaggeration is 1.45; optional elevation color behavior is unchanged, and satellite
hillshade stays suppressed. Sky/atmosphere and the globe/Mercator guard are frozen.

Production visual ceilings remain geometry 14 / relief 15. The private captures retain
the **existing regional prototype's** geometry 18 / relief 18, tile 256 and mesh 128 for
all three controls. No candidate gains a denser mesh than the hard regional control.
Neither relief strength nor renderer configuration is tuned to conceal a join.
Analytical AWS z15/tile 256 remains an independent policy.

## Difference field (M)

Analysis is an aligned 1000² **2 m LV95 diagnostic grid**. Swiss heights are 4×4
area averages of the official 0.5 m cells; AWS is sampled at those centres after
the same available horizontal transformation. This analysis excludes sub-2 m
detail and is not a replacement delivery product. Native 0.5 m bilinear samples
are used separately for the 1 m profiles.

| Swiss minus AWS, metres | Result |
|---|---:|
| Mean / median | −35.547 / −8.309 |
| Standard deviation / NMAD | 58.953 / 38.415 |
| RMS difference | 68.840 |
| 5th / 95th percentile | −124.031 / +35.645 |
| Minimum / maximum | −153.588 / +184.079 |

This is strongly **mixed-scale and nonstationary**. A broad southern negative
region dominates; northern terrain is nearer agreement, with positive ridge
lobes and adjacent negative valley/face structure. Gaussian diagnostic smoothing
at σ10/30/100/250 m leaves residual RMS 2.094/5.457/15.168/26.770 m respectively.
At σ100 m the smoothed field retains 90.7% of the original standard deviation.
Map colors saturate at ±150 m (difference) and ±30 m (residual); extrema remain
in the statistics. That ratio is not an orthogonal variance decomposition, a physical bias estimate,
or a reason to subtract the field from the authoritative regional surface.
Reflected filter boundaries are synthetic; 3σ interior residuals are recorded
separately (18.590 m RMS for σ100 m).

At separation 256 m, difference correlation is 0.819 east–west and 0.618
north–south; at 512 m, 0.796 and 0.270. There is no defensible single stationary
correlation length for this 2 km window. Difference/elevation correlation is 0.835:
the lowest two elevation quintiles have medians −114.127/−102.973 m, whereas the
highest two have +6.942/+8.636 m. Correlations with σ30 m slope, absolute σ30 m
roughness and σ100 m relative landform height are 0.386, 0.216 and 0.513.
Landform height is only a ridge/valley proxy. Spatially correlated samples and
geographic confounding prevent causal or independent-sample significance claims.

Robust gradient regression, diagnostic of a translation model, gives whole-window
east/north/vertical coefficients about `[42.7,18.0,−45.2]` m and 57.25 m residual
RMS on its 2,500 samples. Quadrant fits vary substantially, including north shifts
from −8.7 to +98.5 m and vertical terms from +11.6 to −109.3 m. **No shift is
applied:** there are no independent controls or stable-terrain/epoch masks here.

The original TIFF joins at easting 2625000 / northing 1092000 were checked. Strong
adjacent differences also occur in the Swiss surface itself at steep terrain;
these line samples do not establish an acquisition seam or tiled-source defect.
The new difference map does not justify labelling all ridge lobes as registration
error or all high frequencies as new measurement detail.

### Contributions and uncertainty

- **A — broad product disagreement (M):** directly measured; not a constant bias.
- **B — finer regional structure (M):** retained interior detail is established by
  the parent web comparison. Difference residuals also include displaced/smoothed
  global forms; frequency alone cannot identify genuine missing detail.
- **C — source/measurement/epoch differences (E/H):** upstream radar/optical DSM
  fusion differs from current Swiss terrain production. Exact AWS cell lineage,
  surface epoch and error mechanism remain unknown.
- **D — vertical reference (E/H):** unresolved for AWS. Swiss-system differences
  quantified below cannot explain the whole field.
- **E — preparation (M):** parent ~0.047 m transfer RMS and quantization are much
  smaller than broad tens-of-metres disagreement. This does not bound absolute
  horizontal misregistration or steep-face sensitivity to a metre of displacement.
- **F — real change (H):** the catalogue identifies southern glacier/moraine
  transitions, coincident with much of the negative field. SRTM was acquired in
  [February 2000](https://www.usgs.gov/publications/shuttle-radar-topography-mission-srtm-0),
  much earlier than Swiss inputs. Glacier thinning/retreat is plausible, but no
  dated stable/ice mask or cell lineage supports attributing a measured fraction
  to it. No snow/ice change correction or regression on assumed stable terrain.

## Established methods and production practice (E)

| Method/practice | Assumption and consequence for this case |
|---|---|
| [Nuth & Kääb 2011](https://tc.copernicus.org/articles/5/271/2011/) co-registration; [2023 comparison](https://tc.copernicus.org/articles/17/5299/2023/) | Diagnose 3D shifts and structured residuals on stable terrain before change interpretation. A glacier-influenced overlap without controls is insufficient to validate a correction. |
| [Petrasova et al. 2017](https://link.springer.com/article/10.1186/s40965-017-0019-2) heterogeneous DEM fusion | Aligned grids, known source suitability, fixed or discrepancy-dependent overlap weights. Larger disagreements require wider transitions. Continuity does not establish which source heights are correct. |
| [GRASS r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html) / [r.patch.smooth](https://grass.osgeo.org/grass-stable/manuals/addons/r.patch.smooth.html) | First-valid priority selection versus explicit weighted overlap smoothing. The latter requires aligned grids and exposes overlap controls/masks; it is not automatic datum reconciliation. |
| [GDAL VRT](https://gdal.org/en/stable/programs/gdalbuildvrt.html) / [warp](https://gdal.org/en/stable/programs/gdalwarp.html) | Ordinary last-valid priority with nodata fallback is not harmonisation. Vertical operations require defined vertical CRS/grids; explicit warp options matter. Current 3.12 VRT aggregation features are not assumed available in installed GDAL3.9.3. |
| [USGS lidar production requirements](https://www.usgs.gov/ngp-standards-and-specifications/lidar-base-specification-data-processing-and-handling-requirements) | Agree/document horizontal and vertical references, assess overlap consistency, preserve source identification and deliver edge-matched tiles. Snow/water exclusions demonstrate why stable-terrain assessment matters. These are production requirements, not a supplied fusion algorithm. |
| [PDAL merge](https://pdal.io/en/latest/stages/filters.merge.html) / [reprojection](https://pdal.io/en/2.9.1/stages/filters.reprojection.html) | Combining point streams does not reconcile DEMs; explicit CRS/geoid transformations have a different role. No point processing was performed. |
| [Burt & Adelson 1983](https://ai.stanford.edu/~kosecka/burt-adelson-spline83.pdf) multiresolution splines | Different frequency bands can use different overlap widths. This is image-mosaic continuity evidence, not validation of blended physical elevations. |
| [DEM spectral fusion study](https://www.sciencedirect.com/science/article/pii/S1537511008002493) | Frequency-selective fusion needs evidence of complementary source error bands. Its dataset-specific cutoff cannot be transferred to Swiss/AWS simply because the difference contains broad structure. |

Overlap bias fitting, smooth correction surfaces and uncertainty-weighted fusion
are defensible only with justified reference/error models. Here forcing regional
low frequencies toward AWS could erase a genuinely changed glacier surface or
better measured valley. No such correction was implemented. A seamline can avoid
large disagreement if adequate coverage/quality masks permit; none was selected
inside this artificially limited rectangle. Hydrological conditioning enforces
water-flow constraints, not generic mountain source agreement, and is unjustified
for this visual-only glacier/rock case. More elaborate constrained/Laplacian fits
would add degrees of freedom without resolving the missing physical evidence.

## Vertical-reference finding (E/M)

Swisstopo's [reference-system formulas](https://www.swisstopo.admin.ch/dam/en/sd-web/c46Fz-MHIc3u/refsys-EN.pdf)
describe LN02–LHN95 differences roughly −0.2 m in the north to +0.5 m at high Alpine
peaks, represented through HTRANS. The
[GeoSuite manual](https://www.swisstopo.admin.ch/dam/de/sd-web/VsievEd8MROR/geosuite_manual_de.pdf)
illustrates a maximum of 0.6 m; these published approximate ranges are not a
locally evaluated transformation. [REFRAME](https://geodesy.geo.admin.ch/reframe/index.html)
supports LN02/LHN95/ellipsoidal conversions; CHGeo2004 relates LHN95 to ellipsoidal
heights. European-frame relationships and normal versus orthometric heights must
not be conflated. See also [height transformations](https://www.swisstopo.admin.ch/en/transformations-in-height).

Even a 0.6 m Swiss-system contribution is under 0.6% of a 112 m edge difference
and about 1% of the observed 58.95 m field spread. This is a published scale
comparison, **not a locally evaluated LN02→AWS transformation**.
An ellipsoidal/geoid confusion could be larger; AWS's target semantics are not
known sufficiently to select an operation. No grid/geoid was acquired, no vertical
API was called and no height was transformed. Mathematical blend zones therefore
have mixed, unreconciled height semantics and must never be described as a new
authoritative LN02 terrain measurement.

## Bounded experiment (M)

Research and the field analysis preceded candidate implementation. Hard replacement
is retained as the known-bad baseline. Only two numerical/presentation controls:

1. **250 m linear feather:** `C=G+w(S−G)`, `w=min(distance/250,1)` inside coverage,
   zero outside. Established fixed-overlap control; 250 m is a compact diagnostic
   collar, not a recommended universal width or vertical correction.
2. **Discrepancy-dependent 3° control:** width from
   `abs(nearest-edge(S−G))/tan(3°)`, minimum 2 m, smoothed at σ30 m, never capped to
   fit the rectangle. The same weight formula uses this width. Inspired by the
   published adaptive-overlap principle, **not a port/run of GRASS**: nearest-side
   extrapolation and two-dimensional smoothing differ from its edge handling.
   The nominal angle controls one term, not total terrain slope or corner behavior.

Both preserve contributor fields in `fields.npz`. Analysis uses 2 m heights; the
capture server instead weights the **unchanged native prepared web tiles**, so no
2 m analysis downsampling is substituted for the finest Swiss rendering. It is
offline for prepared/cached inputs; missing coarse context redirects to AWS as in
the parent. Missing high-zoom frozen inputs fail honestly, never encode zero.
URLs include the method; no cross-method cache identity is shared.

| Property | Hard | Linear250 | Adaptive3° diagnostic |
|---|---:|---:|---:|
| Pure regional fraction of 2 m AOI | 100% | 56.25% | 33.28% |
| Change to Swiss, ≥500 m inside: RMS | 0 m | 0 m | 37.953 m |
| Largest positive change ≥500 m inside | 0 m | 0 m | 101.110 m |
| σ10 m detail RMS ratio, ≥500 m inside | 1.000 | 1.000 | 0.794 |
| Same detail correlation | 1.000 | 1.000 | 0.934 |
| Steepest slope-decile height-change RMS | 0 m | 6.411 m | 28.546 m |
| Largest `abs(S−G)*abs(gradient(w))` | 0 interior | 0.583 m/m | 4.041 m/m |

The detail ratio excludes sub-2 m structure and measures a filtered diagnostic,
not perceptual comprehension or accuracy. The AOI maximum lies at its east edge,
not at the Riffelhorn summit; both blends move that same-point height by about
−24.8 m. No claim that Riffelhorn summit itself moved follows from that statistic.

Twenty edge profiles (five positions on each edge) use 1 m sampling, from 100 m
outside to 1,000 m inward. Four corner bisectors move 1 m on each coordinate axis
per sample (√2 m along-track); their coordinate parameter and spacing are explicit
in the record. All outside changes are zero. In the ±100 m **edge** portions,
maximum adjacent 1 m changes are hard 111.52 m, linear 1.32 m and adaptive 1.24 m;
corner adjacent √2 m changes reach 100.60/1.34/1.36 m respectively.
These are **ideal sampled control surfaces**,
not the parent encoded MapLibre result; the prior 70.17 m composed-sample maximum
is retained separately and is not contradicted by the different registration.
Native steep gradients elsewhere in a profile must not be labelled seam artifacts.

The smooth controls eliminate the point discontinuity yet introduce different
terrain. Fixed feathering changes the collar by up to +130.64 m/−59.12 m. Its
additional weight-gradient term reaches 0.583 m/m, even though useful interior
heights remain exact. Adaptive width has p95≈2.24 km, beyond this crop's maximum
1 km inward support. It modifies interior valleys broadly, suppresses some useful
detail, and nearest-edge/width variation adds strong lateral artifacts. The 3°
label is **not** a measured maximum-slope guarantee. This negative diagnostic
does not establish the same artifacts in GRASS's mature implementation.

### Source-support result

Unsmoothed edge-disagreement width at 3° has median 371 m, p95≈2.21 km, maximum
2.50 km; even at 5°, p95≈1.33 km. These are geometric budgets for a particular
overlap principle, not acquisition specifications. A 2×2 km rectangle cannot
both accommodate those large discrepancies at all edges and preserve its whole
interior. Arbitrary tile boundaries compound the problem; source coverage, epochs
and quality need to determine where a collar/seam is supportable. Expanded source
support should protect the desired interior and permit evaluating an external
collar, not silently smooth the desired terrain into the global baseline.

## Visual results and limitations (M)

See accepted capture manifests under ignored
`test-results/atlas-riffelhorn-reconciliation/`; eight identical cameras per method,
Chromium 151, 1440×900, device scale 1, en-GB, Europe/London. Centre
`[7.76121329,45.97910794]`: landscape z9.4/p45/b0, planning 11.4/45/0,
close 13.2/55/0, detail 16.2/55/0. West, south and northwest cameras come unchanged
from `scripts/atlas/riffelhorn-boundary-cameras.json` (15.2/55, b0 except NW45).
West repeats at b180. Existing parent east/north/outside/rotation captures remain
reference evidence; all four edges/corners have fresh numerical controls.

All 24 accepted captures have no DEM HTTP errors or page exceptions. Paired
hillshade/elevation paints, terrain/exaggeration, sky and mesh size match; camera
conditions match within floating-point tolerance. Mercator uses the native default
at these zooms; no fresh globe-transition validation is claimed.

Landscape differences are difficult to distinguish at this framing, demonstrating
that distant views can hide the integration failure. At planning/close scale the
hard rectangular patch is evident. Linear feather removes the vertical dark wall
but retains a straight relief/texture band and changes the southern transition
surface. The adaptive control removes that wall while producing a new deep,
fork-like depression and shaded channel near the southwest transition. The
quantified contribution-gradient field makes this more than a subjective seam
judgment. The northwest control is comparatively benign; it cannot validate the
other edges. Rotation to 180° changes visibility but does not cure the hard join
or the adaptive depression.

Close detail on the central Riffelhorn rock face remains strong with linear feather;
the protected interior is visibly and numerically retained there. The adaptive
control also retains much of this face, while changing broader southern forms and
losing detail in affected interior sectors. This is not cliff-topology reconstruction
or a claim of accuracy. No method is accepted from its attractive interior image.
The source data and fixed renderer remain the same across all controls; finer LOD
does not reconcile conflicting broad heights. No full multiscale error guarantee
is inferred from these discrete cameras or per-level pixel-centre weights.

Existing basemap shield/sprite warnings and ordinary cancelled connection writes
remain. An initial capture assertion treated 55.00000000000001° as different from
55°; tooling was corrected to a 1e−8 camera tolerance before all accepted captures.
An initial loopback cancelled-client write trace was handled explicitly as ordinary
cancellation before final captures; it was not a missing-data response. Final
records distinguish edge 1 m and diagonal √2 m profile spacing. Neither correction
changes terrain values or production behavior.

The prior prototype established finite map terrain, interior gains, normal
projection/lifecycle and independent route sampling. No fresh Weather overlay,
route-timing, satellite or globe test is claimed here; Weather publication is an
explicit 503 fixture. Normal policy/application tests and unchanged source code
cover protected behavior. No new FPS/network-load benchmark or provider evaluation.

## Provenance and architecture implications

The analysis manifest links the parent product, source catalogue, four raw sources,
receipts, nine raw AWS tiles/headers, canonical-LF script hash, method parameters,
tool versions and generated output hashes. `fields.npz` retains Swiss/AWS heights,
differences, adaptive widths and **both unquantized regional contribution masks**;
global weight is 1−regional. Pure regional/global versus blended roles remain
recoverable. Renderer style is separately recorded in capture manifests.

A future delivery product needs source versions, spatial support, mask/weight and
processing identity at each relevant pyramid level, explicit blended-height
semantics, and invalidation by product revision. Per-point scientific confidence
cannot be inferred from a weight or attribution string. These are requirements
exposed by this investigation, not an implemented provenance UI or resolver.

**H:** an offline harmonized hierarchy is a sensible place to evaluate alignment,
seam/support policy and scale-consistent processing before MapLibre delivery.
The parent's single-active-terrain-source finding supports composed delivery;
it does not select a hosting/service architecture. The current evidence favors
preserving authoritative regional broad forms, investigating a supported collar
and stable-terrain/global-reference semantics, then making a deliberate regional
architecture decision. Neither a new global reference nor a larger acquisition
was evaluated in this task.

## Products, reproducibility and validation

Generated analysis lives outside Git:

```text
MERIDIAN_DATA_ROOT/experiments/atlas/riffelhorn-reconciliation-v1/
  manifest.json
  analysis.json                 # full statistics and 24 native profiles
  fields.npz                    # 7 float64 grids, including contributor weights
  difference-and-controls.png
  profiles.png
```

About 61.83 MB excluding the small manifest; no new tile pyramid or source copy.
The loopback server generates transient weighted tile bodies in RAM. New captures
are temporary/ignored, rather than a permanent screenshot estate. The checked-in
[lightweight record](riffelhorn-reconciliation-product.json) supplies exact identity,
hashes, compact results and accepted capture hashes/cameras.

From the repository, with the retained scientific Python environment (NumPy,
Pillow, rasterio/GDAL, pyproj, Matplotlib; no new dependencies installed):

```powershell
# Optional absolute MERIDIAN_DATA_ROOT; otherwise documented sibling default.
$terrainPython='C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
& $terrainPython scripts/atlas/riffelhorn_reconciliation.py
& $terrainPython scripts/atlas/riffelhorn_reconciliation.py --verify
& $terrainPython -m unittest discover -s scripts/atlas -p 'test_riffelhorn*.py'

# Dedicated evaluation terminal; Ctrl+C after capture. Not normal app startup.
& $terrainPython scripts/atlas/riffelhorn_reconciliation.py --serve
# Second terminal, sequentially:
node scripts/atlas/capture_riffelhorn_reconciliation.mjs hard
node scripts/atlas/capture_riffelhorn_reconciliation.mjs linear250
node scripts/atlas/capture_riffelhorn_reconciliation.mjs adaptive3deg
```

Analysis refuses uncached AWS input; it does not acquire missing data. It verifies
the retained parent before explicitly regenerating diagnostic outputs. The server
verifies analysis identity, code, outputs, parent and recorded AWS metadata.
External estate/browser availability checks are separate from deterministic tests.

Thirteen synthetic Python tests pass (six parent and seven reconciliation checks):
filter registration/constant preservation, native bilinear registration, source
weights/outside behavior, uncapped overlap support, no downloads on missing cache,
diagnostic translation fit and manifest/output drift. The existing ten policy
tests also pass, including all three control endpoints through actual terrain
configuration and numeric analytical sampling. Full active Node suite: 137 passes,
zero failures, one live-publication skip (138 tests). Forecast Workspace passes
unchanged. ESLint and TypeScript/application Vite build pass; the existing large
chunk warning remains. The build uses the existing ignored application-only config
(`build.copyPublicDir:false`) rather than publishing/copying unrelated external GFS
products. No external-service test was added to normal CI.

Independent regeneration reproduces the complete analysis identity, including all
recorded output hashes. The analysis verifier checks product/input provenance.
All protected application files compare unchanged against `fe8addc`. JS syntax,
Python compilation and final diff checks pass. Full Weather publication, unrelated
historical research suites, other browsers and load/performance benchmarks were
not run. Local capture services are stopped after evaluation.

This investigation stops at the demonstrated preservation/support problem. No
production adoption, invented datum correction, new Lab, resolver implementation,
imagery processing or increasingly elaborate reconciliation search followed.
