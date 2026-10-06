# Scale-separated terrain relief depiction

Bounded experiment recorded 2026-10-06. Started on clean `main` at
`3d406aee212a5be071728d85db443111e483e7bf`; fetched origin divergence 0/0.
The [multiscale baseline](multiscale-representation.md) remains unchanged. Elevation
is closed and multiview waits for external provisioning. No appearance or source-data
research was reopened.

## Question and frozen control

Can scale-separated cartographic relief improve legibility across scale while the
physical geometry remains identical? Geometry, derived relief and legibility are
separate. No outcome establishes improved terrain accuracy or actual illumination.

The [pre-inspection plan](scale-separated-relief-plan.json), SHA256
`cd89a84734449659e8ba2256f1be1257ff0f717c63c437f3a7ea7c0912f3e203`, freezes one
control, its parameters, camera reuse, navigation steps, limitations and criteria.
No parameter, camera, source or colour tuning follows capture inspection.

**EXTERNAL EVIDENCE:** low-pass preparation for shaded relief is established
cartographic practice. [Leonowicz, Jenny & Hurni 2010](https://berniejenny.info/pdf/2010_Leonowicz_Small_Scale_Relief_Shading.pdf)
distinguish pre-shading terrain filtering from post-shading image filtering and show
that indiscriminate smoothing can erase ridge/valley structure; their full method adds
curvature-based enhancement. [Samsonov & Jenny 2015](https://berniejenny.info/pdf/2015_Samsonov_JennySmall-scaleAndMulti-scaleReliefMapping.pdf)
discuss generalization and gradual portrayal across map scales. These provide precedent,
not a claim that the present control reproduces their complete algorithms.

**MERIDIAN ADAPTATION:** apply Gaussian scale-space to the already prepared relief
slope channels, before stock nonlinear IGOR shading. This is the smallest isolated
low-pass control with explicit physical scale. It does not generate or deliver a
filtered elevation product. No geometry buffers, DEMs, mesh vertices or source
products are changed.

Curvature/ridge enhancement, line-integral-convolution generalization and local
light adaptation would add feature classification or amplification parameters.
Multidirectional shading would change illumination. They are not required for this
one filtering-versus-current-depiction test and were not implemented.

Let D be MapLibre's prepared derivative vector. At nominal map-plane display sampling
m metres/CSS pixel, sigma=m metres. Define `L_sigma=G_sigma*D` and
`F_sigma=D-L_sigma`. The control depicts L_sigma and withholds F_sigma **from relief
only**. Displayed terrain geometry still represents the same source heights. There
is no invented residual amplification or weighted artistic combination.

The Gaussian uses normalized nonnegative weights on a 13x13 derivative-texel lattice,
radius6. Local tile latitude and derivative texture dimensions translate physical sigma
to texels. Shader samples the encoded derivative RG channels, then follows unchanged
latitude correction and IGOR. When disabled, its branch returns the original single
texture lookup. Normalized weights preserve constant slopes and cannot exceed the
local neighborhood's largest vector magnitude; nonlinear portrayal is still capable
of changing local apparent contrast/aspect.

One nominal CSS pixel is a frozen sampling-based experimental choice, not an Atlas
constant or a tuned legibility optimum. Continuum derivative response at wavelength
lambda is `exp(-0.5*(2*pi*sigma/lambda)^2)`: at 2, 8 and 32 nominal CSS pixels,
responses are about0.0072,0.7346 and0.9809. These describe a filter, not human thresholds.
Finite sampled kernels depart from that curve, especially when sigma is much smaller
than a delivered derivative texel: then the control approaches the identity.

## Exact baseline and implementation boundary

Stock MapLibre 6.11.2 IGOR is unchanged: map-anchor 315°, shadow #17211f,
highlight #f4efe0, the existing continuous strength stops
`(5.5,0),(7,.09),(9,.30),(11,.54),(12,.45),(13,.36),(14,.33),(15,.30),(16,.30)`.
The source-level Horn derivative adjustment, encoded/clipped slope buffer, latitude
correction and IGOR's nonlinear slope/aspect combination remain in both cases.
For the delivered levels here, the prepare shader multiplies Horn derivatives by
`2^[0.3(15-z)]` below level 15, before clipping/encoding; at/above 15 the gain is 1.
This inherited source-level adjustment remains separate from the explicit camera-zoom
strength. The fragment shader then applies latitude correction and IGOR's `2 × strength`
derivative factor. Geometry exaggeration 1.45 is independent of the relief strength. Normal satellite
suppression and MapTiler opacity1 are untouched; no Satellite view is activated here.

The research hook intercepts only WebGL2 hillshade fragment compilation and supplies
one depiction uniform. It does not patch a terrain vertex/elevation shader, production
module or node_modules file. The derived filter runs before the unchanged IGOR
operator, not on the final map screenshot, vectors, colours or photograph pixels.
The exact GLSL/operator identity and compiled shader hashes are retained.

A research-only capture harness reuses canonical regional registration, selector,
delivery adapter and existing geometry configuration from the baseline. Each paired
capture releases draped texture caches using the pinned renderer's existing method,
then waits for settled tiles and pending RTT updates. Cache invalidation changes
portrayal resources, not source/geometry. Prepared relief has no persistent new DEM;
its reproducible representation is the declared runtime operator plus frozen inputs.

Known implementation limits frozen in advance:

- The input slope field is already clipped/quantized; filtering cannot undo losses.
  This differs from filtering native heights before differentiation.
- The prepared slope texture has one-texel neighbor padding. Filter taps beyond it
  clamp to the texture edge. Tile-edge effects are prototype limitations, not a
  demonstrated flaw in all Gaussian relief preparation.
- Nominal map-plane scale is used under pitch, not a calibrated per-fragment footprint.
  The separate device-resolution/oblique selection experiment is not executed here.
- This unoptimized research hook uses 169 texture taps. It is not a production renderer
  design or an interactive performance claim.

## Benchmarks, comparisons and evaluation rules

Reuse all 22 frozen baseline scenes, viewport 1440x900 CSS pixels, DPR 1, bearing 0°:
Tryfan[-3.999,53.115], Riffelhorn[7.76121329,45.97910794], South Downs[-.766,50.908],
Cambridge[.12,52.20]. Mountain sequences are128,32,8,2,.5,.125m/CSS pixel;
rolling/low-relief controls128,8,.5. Mountain pitch 55° views at8/.5 assess whether
nominal-scale filtering causes a different depiction issue under oblique portrayal.
No camera is moved to improve the result.

Tryfan uses the retained v2 Welsh family/AWS fallback configuration; Riffelhorn uses
the retained Swiss parent/support configuration, never synthetic transition terrain.
South Downs/Cambridge use unmodified production AWS. **There is no Welsh-vs-AWS or
Swiss-vs-common primary comparison**: both depictions at a scene use exactly the same
source selection, data, representation and geometry LOD. Production IGOR's operator
and style are the baseline in all cases.

Frozen criteria: preserve understandable broad mountain/valley organization; improve
or retain ridge/gully traceability while reducing unresolved clutter; preserve useful
fine structure where resolved; avoid false prominence/noise in rolling/low relief;
avoid material method-induced pumping, moving emphasis or seams; preserve numerical
geometry/data/cameras. Visual judgments are scoped observations, not a user study or
objective perceptual quality score.

Two bounded navigation sequences use the same mountain centres, bearing 0/pitch 0,
8→2m/CSS pixel in nine logarithmically spaced steps. Both depictions are captured at
each settled step. This checks settled portrayal/LOD changes and moving emphasis; it
does not prove frame-rate, mid-loading continuity or smooth interactive animation.

## Evidence and quantitative diagnostics

All **40 pairs / 80 captures** pass exact equality of loaded terrain-buffer SHA256,
source/render tile identities, camera, queried heights, terrain configuration and
mesh size 128. This comprises22 primary pairs and18 navigation pairs. The unchanged
geometry exaggeration is1.45 throughout. The [machine-readable results](scale-separated-relief.json)
retain every capture hash, camera, source identity, shader identity and contact-sheet
index. Evidence is in `meridian-data/experiments/atlas/scale-separated-relief-v1`.

A small offline diagnostic reproduces the pinned Horn derivative/gain/8-bit encoding,
then applies the same sampled Gaussian to a central 64x64 derivative window from the
centre-containing tile. This is a **gain-adjusted derivative proxy**, not physical
slope, terrain accuracy, an exact GPU readback or a fixed geographic population. Its
physical window changes with delivery level. The baseline and control use the same
window at each camera; comparisons across cameras must respect this limitation.

Filtered/stock derivative-vector RMS ratios (1 means essentially unchanged):

| Benchmark |128m/CSS px|32|8|2|0.5|0.125|
|---|---:|---:|---:|---:|---:|---:|
|Tryfan|0.898|0.995|0.859|0.899|0.948|1.000|
|Riffelhorn|0.921|0.954|0.849|0.959|0.921|0.999|
|South Downs|0.858|—|0.893|—|1.000|—|
|Cambridge|0.845|—|0.836|—|1.000|—|

These reductions demonstrate withholding derivative variation, **not improved
legibility**. Positive averaging bounds vector norm by the neighborhood maximum;
it does not guarantee that every local percentile, aspect or nonlinear shade decreases.
South Downs8m illustrates this: vector RMS falls to0.893 of control, but derivative
p95 rises0.0704→0.0747 as neighboring responses spread. Do not turn that into a fake
accuracy/confidence score or universally monotone contrast claim.

At 8m the derivative spacing is5.735m Tryfan,6.640m Riffelhorn,6.025m Downs and5.857m
Cambridge; sigma is1.395,1.205,1.328 and1.366 derivative texels respectively. At 0.125m,
Tryfan's level 17 has0.717m delivered cells and sigma0.174; Riffelhorn's level 18 has
0.415m cells and sigma0.301. Thus the finite filter becomes effectively identity
when portrayal already enlarges delivered information. It does not recover detail
from overzoom. Delivery spacing is not independent source information resolution.

The continuum response is0.0072/0.7346/0.9809 at wavelengths2/8/32 nominal CSS pixels.
For the six mountain scales these correspond to physical horizontal wavelengths:

|sigma metres|2sigma|8sigma|32sigma|
|---:|---:|---:|---:|
|128|256m|1024m|4096m|
|32|64m|256m|1024m|
|8|16m|64m|256m|
|2|4m|16m|64m|
|0.5|1m|4m|16m|
|0.125|0.25m|1m|4m|

These are filter-response coordinates, not universal terrain categories or evidence
that every wavelength is observed. `filter-response.png` visualizes this declared
response; no spectral optimization or terrain-frequency accuracy claim is made.

A fixed central 400x400 CSS-pixel capture window records assumed-sRGB linear luminance
range and mean absolute change on[0,1]. At 8m mean change is0.00459 Tryfan,0.01658
Riffelhorn,0.00229 Downs and0.00121 Cambridge. This checks that depiction affects the
captured map, but includes residual basemap/vector effects and different ground
footprints across scales. It is not a perceptual quality measure. The full result
file contains those quantities separately, never a composite score.

## Matched visual findings

**MERIDIAN EMPIRICAL FINDINGS**, scoped to the frozen views and visual inspection,
not a psychophysical study:

|Benchmark|Broad form|Intermediate and fine structure|Interpretation|
|---|---|---|---|
|Tryfan|Regional landscape organization preserved at 128/32m.|At 8/2m dense ridge/gully texture is softer, but some traceable narrow features lose crispness. At 0.5m the main spine remains; at 0.125m the depictions converge.|No consistent gain over IGOR. The hard regional relief-support rectangle remains in both.|
|Riffelhorn|Major Alpine valleys and mountain mass remain readable at 128/32m.|At 8m roughness is reduced; at 2/0.5m ledges, slope breaks and gullies also soften. Closest view largely converges.|Less texture does not consistently improve structure interpretation.|
|South Downs|Rolling slopes remain credible.|Subtle softening at 8m; at 0.5m AWS-delivery oversampling makes the control nearly identity.|No obvious added false prominence/noise, but no material legibility improvement.|
|Cambridge|Broad low-relief portrayal remains subdued.|Basemap features dominate; the difference is slight at128/8m and negligible at 0.5m.|No obvious noise amplification; no demonstrated additional terrain understanding.|

Both mountain pitch 55° checks retain broad shape. The Riffelhorn close view retains
severe foreground faceting/stretch in both depictions. This experiment does not
isolate its cause, repair geometry or convert it into a filter failure. Under pitch,
a single nominal map-plane sigma is not the actual terrain-surface footprint. That
is a declared limit, not evidence supporting a universal oblique threshold.

Broad derivative structure is comparatively retained by construction; resolved
intermediate structure and unresolved variation are not semantically separated by
Gaussian averaging. The control can suppress useful gullies together with clutter.
No new dominant landform was identified visually, but shaded extrema can spread or
move: preserving geometry does not guarantee morphology-faithful **depiction**.

Inspect the four `*-relief.jpg` contact sheets for the matrix, then original paired
PNGs for small structure. In particular `tryfan-2m--*` and `riffelhorn-2m--*` show the
loss of narrow-feature contrast; `downs-8m--*`/`cambridge-8m--*` provide the less dramatic
controls. Contact sheets are indexes, not the basis for fine-feature thresholds.

## Navigation continuity and artefacts

Two nine-step8→2m sequences were inspected as settled frames. Within one delivered
level the sigma change is continuous and no additional dominant wall or wandering
broad relief feature was identified. This does **not** validate interactive FPS,
loading-frame popping or smooth animation. No real-time performance claim is made.

Discrete relief-source refinement remains important. Tryfan levels14→15→16 give
stock derivative p95 approximately 0.680→1.372→3.388 in their respective tile windows;
filtered responses at the transition steps are0.600→1.166 and1.256→2.740. Riffelhorn's
14→15 step changes stock p95 0.683→2.100, filtered0.606→1.750. These are changing
source/window populations, not a fixed-point physical elevation jump. Matched
captures show contrast/refinement changes in both portrayals. The filter reduces
some contrast without solving source-level portrayal changes; its attenuation also
resets when the derivative texel spacing changes. Therefore continuous sigma alone
does not establish end-to-end continuous relief.

Existing family/support edges are retained, not reconciled. The one-texel halo and
clamped wider filter support can produce tile-edge bias; no universal seam-freedom
is claimed. Input clipping/quantization is inherited. These prototype limits and
169-tap cost constrain renderer feasibility even if a particular screenshot appears
acceptable. No parameter was changed to conceal them.

## Provenance and renderer feasibility

The operator is **cartographic / derived relief**, not physical light, new observation
or improved terrain accuracy. Terrain identity and relief-operator identity remain
separate. The result record retains the frozen plan, operator/source-code hash,
pinned original prepare/fragment shader hashes, actually compiled shader hashes,
illumination/strength identity, physical sigma rule, combination rule and output hashes.

Immutable terrain revisions reused:

- Welsh `tryfan-welsh-regional-v2`:
  `db8e4d87b5fa609d455d1e0f8ec3fdebc834579a7e102f69f4d0b0283efa690c`,
  all 295 manifest files verified.
- Swiss regional parents:
  `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`,
  30 tiles; support revision
  `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`,
  11,429 tiles verified against their immutable manifests.
- Swiss source identity
  `b24a4fdc7b378ba79d442d0ce216a031dfb95a6bc6eed5ad9c33be61175651f4`:
  all 100 retained source assets reverified without modification.
- AWS upstream revision remains unknown. Within-pair loaded-data equality is proven,
  but future live-service bytes are not promised identical.

The experiment needs an experimental shader hook because stock MapLibre hillshade
has no declared physical-scale derivative filter. This is feasible research tooling,
not an approved production technique. A future validated method could prepare
full-halo derived slope/relief levels offline and select/blend them at display scale,
or use a dedicated runtime relief pass. Static preparation alone cannot represent
every view-dependent footprint; a runtime kernel alone incurs cost and boundary
requirements. Those are feasibility boundaries, not implementation authorization.
Do not put depiction controls into TerrainHierarchy or mutate its immutable products.

## Decision and architecture answer

**NEGATIVE for the selected frozen control.** Current IGOR is as useful or more useful
for the tested structure-reading purpose. The Gaussian derivative control reduces
fine contrast, but does not demonstrate a material cross-scale legibility improvement;
some useful intermediate/fine structure becomes less distinct. Technical isolation
succeeded; the depiction hypothesis did not meet its acceptance criteria.

|Predeclared criterion|Result|
|---|---|
|Broad landform remains understandable|Supported in the inspected matrix.|
|Ridge/gully traceability improves or is retained with less clutter|Not consistently met; useful narrow structure also softened.|
|Useful resolved fine structure retained|Partly met; preservation is not feature-aware.|
|Rolling/low relief avoids false prominence/noise|No obvious new prominence/noise observed; no user-study claim.|
|Scale transitions avoid distracting method-induced changes|Bounded settled-step check found no new dominant discontinuity, but shared discrete source refinement remains; interactive continuity unverified.|
|Geometry/data/cameras/exaggeration identical|Verified for all 40 pairs.|

**Keep source-faithful geometry and independent depiction as the current architecture
boundary.** The evidence proves that contrast can be changed independently of geometry.
It does not establish that this filter, or depiction alone, solves multiscale terrain
legibility, nor that depiction should replace product eligibility/information limits.
No comparison demonstrates a geometry deficiency requiring simplification. Consequently
**morphology-preserving geometry/preparation is not activated**. The elevation foundation
stays closed; this negative portrayal result is not permission to reopen it.

**RESEARCH HYPOTHESIS / DIRECTION:** local screen-space sampling and inherited relief
source LOD may be more consequential than one nominal map-plane filter width. This
remains unproved beyond the bounded observations above. Do not tune thresholds or
compare another relief family here.

Exact next task: **Characterize information-aware display and selection limits, using
bounded device-resolution and oblique-view comparisons**, as ordered by the multiscale
baseline. It should establish local display/support limits before any production
portrayal decision. It is not executed in this task. Multiview remains parked; no
appearance/correction experiment, relief algorithm sweep or new terrain benchmark follows.

## Validation, reproducibility and limits

Nine asset-free synthetic tests cover normalized/symmetric nonnegative weights,
constant slopes, decomposition reconstruction, physical wavelength response,
discrete sinusoid attenuation, non-amplification bound, identity under oversampling,
flat prepared terrain and physical metres-to-texels conversion. Capture validation
checks the exact 22 frozen cameras, all 18 navigation pairs, captured hashes and
40 matched loaded geometry/LOD states. The 113 frozen tracked production `src/` file
hashes pass. Shader source inspection independently agrees with the offline derivative
formula; proxy quantization is not substituted for exact GPU fidelity.

One metadata-only implementation correction removed an inherited first-camera
`igorStrength` field from Tryfan navigation descriptors. Actual cameras, zoom-expression
paint, pixels, filter and geometry never changed. It is recorded in that capture
manifest; later descriptors omit the redundant field. No tuning followed inspection.

No browser page errors or failed local terrain deliveries. HTTP503 Weather responses
are deliberate research-harness isolation; two aborted Tryfan requests during camera
changes are recorded, with settled captured deliveries unaffected. No shared runtime
files changed; full application tests/build are unnecessary here. Lint, syntax,
JSON/local references and final diff pass. Eight rebuilt diagnostic products are
byte-identical, including summary SHA256
`19b611199301e6991b3080025ff364991e66e153a7e92d6c804765cac901448f`.

Software: MapLibre 6.11.2, Chromium 151.0.7922.34, Node 24.11.0, Python 3.12.6,
NumPy 2.5.3; exact Pillow/Matplotlib versions are in the result record. All captures
remain outside Git. Service/vector-map captures are local research evidence, not a
public redistribution clearance. No optical/terrain accuracy, confidence, universal
useful scale, performance or perceptual quality score is claimed. No new DEM/source
product or geometry generalization was generated; only derivative portrayal changed.

From the repository root, using the existing data environment:

```powershell
$atlasData = 'C:/Users/gbsam/Documents/Projects/meridian-data'
$atlasPython = "$atlasData/earth-lab/.venv/Scripts/python.exe"
node --test scripts/atlas/test_relief_scale_control.mjs
& $atlasPython -m unittest discover -s scripts/atlas -p test_relief_scale_analysis.py
& $atlasPython scripts/atlas/analyze_relief_scale.py --data $atlasData
npm.cmd run lint
```

Analyzer rebuilds accepted evidence, including contact sheets and response plot, and
writes matching external/Git summaries. Independent capture repetition requires the
existing configured client key and AWS fallback cache helper; it is not normal CI.
Run the helper in a separate terminal, then the three modes serially:

```powershell
& $atlasPython scripts/atlas/terrain_proof_cache.py --root "$atlasData/cache/atlas/tryfan/second-region-proof/aws" --port 4187
foreach ($atlasMode in @('aws','tryfan-regional','riffelhorn-regional')) {
  node scripts/atlas/capture_relief_scale.mjs $atlasData $atlasMode repeat
}
```

The optional label writes `captures-repeat/<mode>` and refuses existing manifests.
Ports 4173/4188 are ephemeral research paths. Frozen plan bytes match their external
copy; original baseline cameras and reports remain unchanged. Normal application
startup/CI requires no research data or external service availability.

**Stop:** one control evaluated, no production promotion. AWS visual terrain,
independent AWS analytical z15, IGOR, exaggeration 1.45, MapTiler satellite-v2,
opacity 1, satellite IGOR suppression, Weather/Traverse and projection/lifecycle
are unchanged. Appearance/multiview work was untouched. No next experiment began.
