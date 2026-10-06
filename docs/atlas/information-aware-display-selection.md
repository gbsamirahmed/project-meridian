# Atlas information-aware display and selection limits

Recorded 2026-10-06 from clean `main` at
`ca74a84713b443d408467dd17835083bbbf0771a`; fetched origin divergence0/0.
This final bounded multiscale characterisation does not implement its recommendations.
Elevation remains closed, the [negative relief control](scale-separated-relief.md)
is not reopened, and morphology preparation is not activated. Multiview remains parked
awaiting external provisioning; no acquisition, contact or experiment in that branch.

## Decision and scope

**Combined C/D, depending on source:** a separate view-local *sampling diagnostic*
is justified, together with scoped numerical information statements where evidence
supports them. Automatic informational-usefulness ranking is **not established**:
common-source effective resolution, acquisition geometry and human legibility remain
unknown. Existing metadata can honestly describe these cases; no mandatory new schema,
resolver, renderer or production change is required now.

Eligibility differs from usefulness. A supported fine product may add useful structure
at one view and be display-suppressed at another. Dense interpolated delivery from a
common product does not establish fine observations. Neither nominal ratios nor sharper
screenshots decide that comparison. Keep TerrainHierarchy's identity/support/levels/
parents/fallback role. Any future view-local policy consumes its eligible choices;
camera and DPR do not belong inside it. No such policy is implemented here.

**The current multiscale research branch can close.** No demonstrated foundational
blocker requires another experiment. Perception, terrain accuracy, cross-source seams
and renderer limitations remain unresolved, without becoming prerequisites for closure.
The immediate change is this maintained terminology, evidence and ownership record.
A separately authorised implementation could add read-only sampling diagnostics and
structured numeric statements already supported by source metadata. This programme
justifies no production source, portrayal, zoom restriction or geometry change.

Evidence labels: **MERIDIAN EMPIRICAL FINDING** for captured state, hashes and scoped
measurements; **ESTABLISHED EXTERNAL KNOWLEDGE** for attributed sampling/filtering
principles; **MERIDIAN ADAPTATION** for local Jacobians applied to Atlas;
**PROPOSED ARCHITECTURE** for ownership; **UNRESOLVED** for optical response,
visibility and perception. No new method, accuracy or universal quality score is claimed.

The [pre-inspection plan](information-display-plan.json), SHA256
`2abb6d57c0f646ae93ac8236336ee5090e542ed4419f703f207c27e88aa3eb50`, pins all113
production-source hashes,11 MapLibre-source hashes and the previous camera plan.
The [measurement record](information-display.json) retains exact cameras, immutable
product revisions, footprints, flags, capture hashes and DPR comparisons. Large
captures and failed collector runs remain under
`meridian-data/experiments/atlas/information-display-v1`.

## Frozen subset

1440 x900 CSS viewport;22 captures, not another54-capture baseline.
DPR is emulated in headless Chromium151.0.7922.34, running the actual unchanged
Meridian/MapLibre6.11.2 path. These are browser rasterisation conditions, not three
physical-panel or human-acuity tests. Node24.11.0/Python3.12.6 versions are retained.

| Configuration | Existing camera | Requested DPR | Question |
| --- | --- | --- | --- |
| AWS | Tryfan0.125 m/CSS px, pitch0 | 1/2/3 | Extreme representation oversampling |
| AWS | South Downs128, Cambridge8, pitch0 | 1 | Broad/low-relief controls |
| Welsh regional | Tryfan0.5, pitch0 | 1/2/3 | Distributed grid versus delivery/mesh |
| Swiss regional | Riffelhorn0.5, pitch0 | 1/2/3 | Independent geometry/relief levels |
| Swiss regional | Riffelhorn8, pitch0/35/55 | 1 | Local orientation and perspective |
| Matched Swiss geometry + common/regional appearance | Riffelhorn0.125, pitch0 | 1/2/3 each | Texture stages |
| Same appearance pair | Riffelhorn8, pitch55 | 1 each | Oblique texture projection |

Centres/bearings/zooms are reused from [3d406ae's plan](multiscale-representation-plan.json).
Only pitch35 is added, before inspection, at the identical Riffelhorn8 camera.
No post-inspection camera, source, colour or parameter tuning. These are controls,
not universal modes or useful-scale thresholds. No new landscape/data acquisition.

## Information chains and evidence states

**Terrain:** physical surface -> measurement -> source sampling/information response ->
prepared product -> coherent representation pyramid -> delivered encoded samples ->
interpolated mesh -> exaggerated camera projection -> framebuffer/composition ->
display -> human interpretation.

**Appearance:** physical appearance -> observation with viewpoint/illumination/optics ->
GSD/information response -> orthorectification/mosaic -> prepared pyramid -> delivered
texture -> filtering and terrain draping -> framebuffer/composition -> display ->
human interpretation. Orthophoto processing is not a raw observation.

Extra interpolation, vertices, texels or raster pixels create no new observation.
They *can* expose more of the existing representation than a coarser display did.
Higher DPR is therefore neither new source evidence nor necessarily useless.

**KNOWN** is a published statement or verified asset/implementation fact.
**BOUNDED** is a calculation under stated assumptions/range. **INFERRED** is an
interpretation without direct measurement. **UNKNOWN** remains explicit.

| Stage | Status here |
| --- | --- |
| World shape/material and subgrid truth | UNKNOWN |
| Published grid/GSD statements | KNOWN where supplied; scope differs by source |
| Effective source resolution/MTF | UNKNOWN locally; Alpine orthophoto nominal statement only |
| Prepared identities, delivery grid/levels, resampling | KNOWN regional products; live common revision uncertain |
| Loaded buffers, mesh and textures | KNOWN pinned renderer telemetry |
| Local sample-to-screen footprint | BOUNDED finite Jacobian, delivered heightfield, spherical ENU |
| Filtering algorithm selection | KNOWN implementation; hardware footprint/response not measured |
| CSS/framebuffer dimensions | KNOWN; physical panel size/optics not measured |
| Human feature recognition | UNKNOWN; no observer study |

## Information-support envelope

Use *information-support statement/envelope* when “ceiling” implies an optical cliff.
It records whether finer sampling can be claimed to expose additional **observed**
spatial information, not an automatic camera/filtering rule.

1. **Hard known limit:** explicitly finite observation/support or documented bandlimit,
   if supplied. Maximum native delivery is a hard *delivery* limit, not optical cutoff.
   No measured optical cutoff is available for these sources.
2. **Nominal sampling limit:** distributed grid, GSD or nominal information statement;
   not proof that every smaller feature is absent or an exact resolvable wavelength.
3. **Estimated information limit:** measured response such as MTF, with method,
   uncertainty, direction, conditions and revision. Not available locally here.
4. **Unknown information limit:** retain unknown despite known sampling/delivery.

[USGS JACIE practice](https://pubs.usgs.gov/publication/ofr20241023/full) distinguishes
GSD from sharpness/MTF and SNR. Only that targeted distinction is used; no local
optical response is inferred from screenshots.

| Source/product | Known statement | Unknown / separate |
| --- | --- | --- |
| Welsh Tryfan DTM | Distributed1 m grid; coherent z14-17 product | Independent measurement/effective resolution, native vertical reference |
| Swiss regional | Distributed0.5 m LV95 grid, LN02; coherent regional parents/support | Variable upstream observation support, effective resolution |
| AWS production | Terrarium256; geometry max14, independent relief max15 | Local effective resolution, epoch, upstream revision |
| Retained SWISSIMAGE2023 | Distributed0.1 m RGB; nominal Alpine0.25 m information; PNG512 z12-18 | Optical cutoff/MTF, original camera/time/Sun/visibility |
| MapTiler satellite-v2 | JPEG XYZ512; current declared max22 | Local GSD/effective resolution, epoch/view/mosaic lineage |

Immutable regional revisions and manifest hashes are in the measurement record.
No product preparation/correction occurred. Delivery zoom is not information resolution.

## Local projection model

At each of nine fixed CSS positions, unproject/query elevation at +/-1 and +/-2
CSS pixels on both axes. Convert differences to local east/north/up metres. Divide
rendered queried heights by1.45 for physical-height metrics, retaining rendered
metrics separately. The camera is still the actual exaggerated display camera.

Let J be the3x2 physical-surface metres/CSS-pixel Jacobian, A its east/north rows,
and D the measured framebuffer/CSS ratios. Singular values of J and J D^-1 give
major/minor surface metres per CSS/framebuffer pixel. Retain J, not only a scalar.
A^-1 times map-plane spacing projects an isotropic grid sample to CSS pixels;
D A^-1 gives its framebuffer projection. This is not a sensor footprint.

Solve A-transpose times slope-gradient = J's height row. The map-plane-to-surface
mapping has principal stretches sqrt(1+gradient-squared) and1. Slope stretches
one direction; it does not multiply every direction equally. Surface wavelength L
projects to [L/major(J), L/minor(J)] CSS pixels, depending on its orientation.

Normals depend on the delivered/interpolated heightfield, not native ground truth.
Finite stencils can cross slope changes. Predeclared reliability flags: >25% principal
change between1/2-pixel stencils or >2 CSS-pixel project/unproject error. Missing/
singular mappings stay unavailable. These flags are not quality/eligibility thresholds.
Synthetic flat/sloping/rotated-oblique/inverse-grid/wavelength tests validate the maths.

Facing, away-facing and cross-slope surfaces have different directional footprints.
Perspective varies by viewport position even on a plane. Zoom or pitch alone therefore
cannot describe a view-wide physical-surface sampling rate.

## DPR and terrain results

**MERIDIAN EMPIRICAL FINDING:** the fixed CSS viewport remains1440 x900. DPR1/2
produce1440 x900 /2880 x1800 framebuffers. DPR3 requests3 but actual canvas/drawing
buffer is4096 x2560:2.8444 backing pixels/CSS pixel, constrained by unchanged4096
maxCanvasSize. Browser screenshots are4320 x2700 atDPR3; their density includes
compositing/resampling of that smaller canvas. Requested ratio, framebuffer ratio
and screenshot/device density are therefore three different measured statements.
The [MapLibre API](https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#getpixelratio)
explicitly notes requested and applied ratios can differ.

Mesh128, RTT1024 and qualityFactor2 persist at all testedDPRs. Depth-framebuffer
bookkeeping remains1440 x900 forDPR1/2, but reports1365.33 x853.33 atDPR3 because
this version divides clamped painter size by browserDPR. Those are implementation
bookkeeping dimensions, not verified fractional GPU allocations. No renderer fix
or new clipping/navigation experiment follows from this observation.

| Frozen terrain view | Encoded level at probes | Median major CSS pixels/encoded sample | Local physical surface m/CSS pixel, minor minimum to major maximum |
| --- | --- | --- | --- |
| AWS Tryfan0.125 | z14 | 51.34 | 0.092-0.261 |
| Welsh Tryfan0.5 | z15 | 5.71 | 0.439-3.116 |
| Swiss Riffelhorn0.5 | z15 | 6.93 | 0.397-1.411 |
| AWS South Downs128 | z7 | 6.03 | 126.153-128.905 |
| AWS Cambridge8 | z11 | 5.86 | 7.958-8.050 |

At nominal Tryfan0.125, AWS z14 grid interval is approximately5.735 m:
45.9 nominal CSS pixels/sample, reproducing the baseline extreme; local camera/surface
mapping yields51.34 major-axis median. DPR2 doubles those *framebuffer* extents and
applied2.8444 multiplies them atDPR3. It neither shrinks the native delivery interval
nor establishes local AWS effective source resolution. The finer mesh interpolates
that same encoded field. More rasterisation cannot recreate unresolved ridges.

Regional source inputs remain immutable and level families remain regional. Their
1 m/0.5 m distributed source grids are finer than the *selected* z15 delivery samples
in these0.5 m cameras. Higher DPR does not automatically select all available fine
regional levels. This separates source-support potential from the representation
actually delivered and depicted. No source selection is changed here.

Exact full tile-set equality is not universal: AWS DPR2/3 have two fewer listed
relief tiles at the same z15; Welsh DPR3 has different padded DEM-buffer hashes for
four tile identities, while levels/input products and all nine interior footprints
are unchanged. DEMData backfills neighbour borders in this pinned renderer; padding/
loading is a plausible explanation, not a proven byte-level attribution. Retain this
qualification rather than claim the entire Welsh rendered field is byte-identical.
AWS and the Swiss0.5 geometry signatures otherwise agree acrossDPR; the Swiss
appearance-close DPR2 group also differs in padded-buffer hashes at unchanged levels.
All four common/regional appearance pairs match full geometry signatures within
each DPR/camera pair. This test is about fixed
products and observed LOD, not forcing mesh/loading state or hiding boundary effects.

## Oblique and surface-orientation results

The nine Swiss terrain probes at the same nominal8 m camera scale yield:

| Pitch | Local surface principal-scale envelope (m/CSS px) |
| --- | --- |
| 0 | 7.259-12.328 |
| 35 | 6.885-54.690 |
| 55 | 3.691-30.782 |

The35-degree case is not universally less distorted than55: terrain orientation,
position and perspective matter more than a global monotonic pitch multiplier.
Encoded geometry at these probes is z11, with z12 also present at55. The plan's
sensitivity/error checks are retained for all probes, including strong gradients.
This diagnoses displayed-heightfield footprints, not visibility or ground-truth slope.

Reuse, rather than rerun, the retained steep orthophoto patch result:
p95 major map-plane-to-surface stretch6.192, nominal0.25 m ->1.548 m tangent major
sampling; the local minor direction remains0.25 m in that geometric model. This is
an anisotropic map-to-surface mapping, not an isotropic1.55 m source resolution.
It does not establish original observation occlusion. Extra DPR or delivery pixels
cannot supply missing viewing directions. The multiview branch is untouched.

## Appearance and visual findings

At the fixed close-view centre probe (CSS fraction0.55,0.5), allDPRs select Swiss
geometry z17 at approximately0.830 m encoded spacing. MapTiler's texture is z19,
approximately0.104 m/pixel; prepared SWISSIMAGE is z18, approximately0.207 m/pixel.
The shared draping grid is approximately0.104 m/texel. These are measured delivery
statements: MapTiler's finer delivered pixels do not establish finer source observations.

| Centre-probe statement | CSS principal pixels/sample | Framebuffer atDPR2 | Framebuffer at requestedDPR3 |
| --- | --- | --- | --- |
| Encoded geometry0.830 m | 6.85 /6.29 | 13.70 /12.57 | 19.49 /17.88 |
| MapTiler delivery / draping0.104 m | 0.856 /0.786 | 1.713 /1.572 | 2.436 /2.235 |
| SWISSIMAGE delivery0.207 m | 1.713 /1.572 | 3.426 /3.144 | 4.872 /4.471 |
| Nominal orthophoto0.25 m statement | 2.064 /1.894 | 4.127 /3.788 | 5.870 /5.387 |
| Distributed orthophoto0.1 m grid | 0.825 /0.758 | 1.651 /1.515 | 2.348 /2.155 |

Thus common imagery/draping is slightly minified atDPR1 but magnified atDPR2/3 in
this probe; prepared regional pixels are magnified already atDPR1. A larger framebuffer
can expose existing texture variation formerly combined into one raster pixel, without
selecting a finer source or creating observations. This table is a local grid proxy,
not an exact optical footprint or measured GPU per-fragment mip response.

At the8 m/pitch55 appearance view, only one of nine probes lies inside the frozen
4 km² imagery source bounds. That probe has z13 texture spacing about6.640 m and
nearest prepared alpha1; another probe has alpha0, while seven have no regional tile
at their locations. Alpha is area support, not shadow/quality/visibility confidence.
The coarse image represents regional-derived parents with common appearance outside;
the centre's terrain selection is explicitly common, not silently labelled Swiss.
No information statement is assigned to unsupported regional locations. This is why
viewport-wide claims based only on the camera centre/source name are unsafe.

Visual inspection of the fixed centre-crop index, full close captures, oblique view,
rolling and low-relief controls is secondary evidence. AWS extreme close terrain stays
smooth/interpolated despite more framebuffer pixels. Common/regional appearance keeps
its source character; the DPR change does not reveal a new observation direction or
new independent terrain structure. The oblique view includes stretched foreground
appearance and a limited regional footprint; no correction or support expansion.
South Downs/Cambridge remain normal production cartography; no new prominence/noise
is introduced by this audit. A downsampled contact sheet is an index, not a device
acuity comparison or sharpness test. Human legibility is not experimentally quantified.

The prior SWISSIMAGE baseline's useful regional information gain remains established;
this task neither re-evaluates absolute image quality nor ranks providers. Unknown
MapTiler effective information remains unknown. The selected DPR conditions do not
establish that higher DPR never helps at heavily minified/broad views. Their evidence
establishes these pipeline limits, not a universal device/LOD policy.

External diagnostics: `diagnostics/sampling.png` (directional/raster sampling) and
`diagnostics/capture-index.png` (nine fixed close-crop entries). Original22 PNGs and
capture manifests are indexed by captureDirectory/filename/hash in the measurement
record. No large capture or prepared product is committed.

## Pinned renderer behaviour

MapLibre6.11.2 source is inspected locally, with eleven hashes pinned in the plan.
No renderer, shader, style expression or production module is changed. This is a
version-scoped implementation audit, not reverse engineering a proprietary system.

- CSS transform dimensions drive camera/tile covering. Requested browser DPR is not
  an instruction to fetch independently observed finer tiles. Covering can change
  with camera/footprint/source constraints; actual loaded levels are measured.
- DEM textures use nearest texel access, then the terrain shader explicitly decodes
  and bilinearly interpolates four cell-centred neighbours. A128-cell terrain mesh
  samples that field; triangles introduce another interpolation stage. More vertices
  do not create measurements. Borders/padding260 are not260 independent terrain cells.
- Terrain render-tile size512 and qualityFactor2 give1024-pixel render-to-texture
  targets. This draping grid is distinct from the input DEM/raster and final framebuffer.
- The unchanged separate relief source can refine independently of geometry. Horn
  derivatives, source-level gain `2^[0.3(15-z)]` below15, clipped encoded slope channels,
  latitude correction and stock IGOR/continuous strength remain cartographic depiction.
  Increased framebuffer density does not remove a derivative-buffer information limit.
- Raster draw uses linear magnification and LINEAR_MIPMAP_NEAREST minification when
  mipmaps exist; Texture.bind falls back to LINEAR when they do not. Terrain draping
  uses linear magnification and LINEAR_MIPMAP_LINEAR minification of its RTT.
- Above the default20-degree pitch, the raster path requests anisotropic filtering
  when the extension and mipmaps are available. This environment exposes maximum16.
  It is a filtering capability, not measured source information or a guarantee of
  equal surface resolution. Exact per-fragment GPU mip/anisotropy footprints were
  not read back; intermediate RTT and later filtering can still constrain display.

These filtering names follow [Khronos sampler terminology](https://wikis.khronos.org/opengl/Sampler_Object)
and the [WebGL anisotropic extension](https://registry.khronos.org/webgl/extensions/EXT_texture_filter_anisotropic/).
Minification combines existing samples; magnification interpolates them. Neither
recovers information lost to observation direction, optics, preparation or an earlier
rasterisation stage. Mipmaps address sampling/aliasing, not cartographic interpretation.
The exact texture-state enums and dimensions are retained in capture manifests.

Production remains AWS visual through registration/selector/adapter, independent AWS
analytical z15, geometry exaggeration1.45, unchanged IGOR315-degree map anchoring and
strength curve. MapTiler satellite-v2 JPEG/XYZ512, opacity1/fade180/linear and normal
satellite hillshade suppression remain. Terrain is active beneath satellite. Weather,
Traverse, lifecycle/style restoration/projection and application ownership are unchanged.

## Overzoom, undersampling and wavelength

Keep three separate statements:

| Term | Meaning | What it does not establish |
| --- | --- | --- |
| Delivery overzoom | Render/request beyond maximum native delivery level | Finer upstream observations |
| Representation oversampling | One representation sample covers many raster pixels | A source optical cutoff or useless camera |
| Source-information oversampling | Sampling finer than an evidenced source-information statement | Physical accuracy or automatic filtering/zoom policy |

Use *relative to nominal grid* when that is all the source supports; use *unknown*
when information is unknown. A representation may be oversampled even below delivery
maxzoom, because terrain mesh/tile selection differs from camera zoom. A coarse pyramid
may withhold existing source information. Conversely finer delivery can already be
interpolated from coarser observations. These are not equivalent events.

At broad views multiple source/product samples contribute to one CSS/device pixel.
This is a display/portrayal limitation at that view, not proof the fine source has
no value. Filtering can manage aliasing while removing variation; this task does
not implement or optimise a filter. More DPR can resolve additional *existing*
representation variation where a previous framebuffer undersampled it, while leaving
source, mesh and RTT bottlenecks intact. Imagery and relief have intermediate raster
stages that geometry does not share in the same way.

For a physical wavelength L, source sampling, information response, prepared level
and projected pixel extent are separate checks. A two-samples-per-cycle bound is a
necessary sampling-theory condition for ideal bandlimited signals along a direction,
not a guarantee of terrain morphology, feature recognition, illumination contrast or
optical resolution. Native grid spacing alone cannot establish that bound for real
source-observed information. Camera projection makes the display bound directional;
the same L may project to markedly different extents across an oblique viewport.
No universal recognition threshold or physical wavelength category is frozen.

## Architecture ownership and truthful calculations

| Responsibility | Owns | Excludes |
| --- | --- | --- |
| Source metadata | Nominal grid/GSD, information-response evidence/unknowns, acquisition/reference and rights | Camera/device rendering policy |
| Product/representation metadata | Immutable lineage, resampling, level/grid/encoding, generalisation, information claims scoped to contributors | Invented source accuracy |
| Hierarchy/eligibility | Support, levels, parents, explicit handoff/fallback/provenance | Camera/DPR or perceptual quality ranking |
| Optional view-local diagnostics/policy | Local projected sample footprints, requested/actual raster scale; usefulness only when evidence permits | Rewriting source metadata or treating all eligible sources as equally observed |
| Rendering | Mesh, filtering, RTT, rasterisation and independent portrayal | Creating observations or silently mutating provenance |
| User provenance/explanation | What a sampling statement means, what is interpolated/unknown | A noisy universal warning or fake confidence score |

Atlas can reliably measure CSS/backing dimensions, applied ratios, tile/mesh/texture
identities and delivery intervals. It can calculate local directional projection and
nominal grid ratios within the explicit approximation flags. It can preserve exact
product/source lineage and distinguish within-family LOD from source handoff.
It cannot infer local optical resolution, source accuracy, visibility, sensor geometry,
material identity, panel perceptual response or human usefulness from these ratios.

Existing TerrainSource gridSpacing and Knowledge-based nominal/measurement resolution,
product/family informationCeiling and level sampleSpacing can describe present facts
and unknowns. No contradiction or schema amendment is needed. **Future numeric
automation** should use scoped statements with value/unit, coordinate/surface domain,
direction, evidence kind (distributed/nominal/estimated/hard), method/uncertainty and
source/product revision. Parsing prose into a guessed constant is not acceptable.
This is a bounded metadata recommendation, not an implemented type system.

TerrainHierarchy does **not** need camera projection/device resolution. A future
view-local layer may calculate diagnostic usefulness envelopes over eligible choices;
automatic selection is deferred until source-comparison evidence warrants it. Nothing
here justifies changing current priority/fallback behaviour.

The separate proposed AppearanceHierarchy should preserve distributed pixel spacing,
GSD/nominal information, effective resolution/unknowns, mosaic lineage and observation
geometry. Surface-projected orthophoto information is *derived against identified
geometry*, not a new invariant GSD field. Keep camera/illumination/occlusion and
imagery semantics out of TerrainHierarchy. No AppearanceHierarchy runtime is built.

The renderer needs honest implementation-state telemetry for a future diagnostic,
not scientific-confidence constants. Selection, filtering and portrayal remain
separate; no new zoom limits, blur, pixelation, warnings, sharpeners or source switches
follow automatically from exceeding a nominal information statement. Users can still
inspect interpolated structure, overlays or spatial relationships beyond that point.

## Programme synthesis and closure

- [3d406ae baseline](multiscale-representation.md): discrete eligible source/product
  levels, coherent regional parents, local screen-space footprints and independent
  depiction; no three modes, universal zoom thresholds or universal geometry smoothing.
- [ca74a84 relief experiment](scale-separated-relief.md): reducing fine derivative
  variation did not consistently improve legibility and also softened useful narrow
  structures. Negative for that control; no demonstrated geometry deficiency.
- This task: local, anisotropic and actual-framebuffer sampling is knowable; effective
  source information and perception frequently are not. More raster pixels are not
  more observations. Eligibility cannot alone express view-local usefulness.

**Justified now:** the architecture separation, sampling/provenance vocabulary,
explicit unknowns and this evidence record. **Justified for a separately authorised
implementation:** an optional read-only local sampling diagnostic, and numeric scoped
metadata when existing evidence supplies it. Neither requires new research first.
**Renderer change justified now:** none. **Research:** no foundational blocker in the
current multiscale programme; observer/optical studies would need their own concrete
product requirement rather than automatic continuation.

**Not justified:** replacement IGOR, universal geometry generalisation, morphology
preparation, universal modes/zoom thresholds, automatic source-quality ranking,
zoom blocking, blur/pixelation or a general renderer framework. Scale-separated
portrayal is not a complete established solution, but its negative result is also
not evidence that geometry must change. Source-faithful geometry remains separate.

Close this research branch. No next multiscale experiment is recommended. The waiting
source-image comparison remains a separate externally provisioned programme, not a
next step executed here. Do not acquire frames or implement this synthesis.

## Validation, implementation corrections and reproduction

Ten asset-free mathematical tests and two frozen-plan/source-code checks pass.
Checks cover CSS/backing ratios, Mercator scale, normals/aspects, anisotropic footprints,
facing/away/cross-slope planes, de-exaggeration, inverse-grid ratios, wavelengths,
missing/singular mappings and coverage. The CRS84 frozen Riffelhorn centre transforms
to LV95[2625000.00035,1092000.00116], matching the retained benchmark within0.002 m.
All198 probes are available; none exceeds the predefined sensitivity/error flags.
Maximum project/unproject error is1.55e-6 CSS pixels; maximum1/2-pixel principal-scale
change0.208. These checks do not establish exact mesh derivatives or physical accuracy.

All22 expected scenes, exact cameras, terrain exaggeration1.45, mesh128, screenshot
hashes/dimensions and satellite opacity/suppression pass. All regional product files
are hash-verified by existing preparation helpers (Swiss11429 support +30 parents,
Welsh295 manifest files);100 Swiss source DEMs and four retained imagery sources match
the earlier frozen identities. All113 production source and11 pinned renderer hashes
match. Repeated diagnostic rebuilds are byte-identical: measurement SHA256
`c07bde8d65394b6457cc2025736e848e070a0b9b122b9af594e230c7f4f58757`.
Full diagnostics remain external at `diagnostics/full-metrics.json`, SHA256
`4fa575ef823c5063c9a8e3c006c0bb56991667e01443b670849b1d0470aff768`;
the compact Git record retains all probe Jacobians/geometry ratios and a full centre
example per scene, plus the full-record pointer/hash.

Research collector corrections are explicit: the first run used the wrong private
transform property; a second assumed every candidate render tile had a cached RTT.
Those observers were corrected without changing rendering. Failed records remain in
`captures/aws` and `captures-collectorfix/aws`. Two satellite activation retries and
one metadata-ready synchronisation run timed out on a freshDPR2 page: UI Satellite was
selected but the layer absent. Inspecting the existing style-ready guards indicates
a lifecycle timing issue; it is not established as a source or sampling defect.
Accepted appearance capture reuses the public AtlasMap presentation method after
style readiness if initial activation returns early, plus unchanged-byte metadata
response synchronisation. No tile URLs/configuration, paint, source selection, geometry
or production lifecycle is patched. Failed activation records remain external.
This is harness synchronisation, not a production fix or visual tuning.

Accepted runs: `captures-validated/{aws,tryfan-regional,riffelhorn-regional}` and
`captures-controller-ready/riffelhorn-appearance`. The latter records thirteen
`ERR_ABORTED` requests during navigation; all settled captures pass loaded-state
checks, successful gateway responses/hash checks, and no page errors or unexpected
HTTP failures. Intentional research Weather503 responses isolate the atmosphere;
Weather source/configuration is unchanged. Live common services/loading/UI timing
prevent a promise of future screenshot-byte equality; retained telemetry, inputs and
mathematical rebuilds are deterministic. This is not a reliability/performance study.

From the repository, with the existing data environment (`DATA` is the meridian-data
root; `PY` is its earth-lab/.venv/Scripts/python.exe), use the checked-in plan:

```text
node --test scripts/atlas/test_information_display_plan.mjs
PY -m unittest discover -s scripts/atlas -p test_information_display_math.py
PY scripts/atlas/terrain_proof_cache.py --root DATA/cache/atlas/tryfan/second-region-proof/aws --port 4187
# Keep that retained-cache helper running; capture serially in another shell:
node scripts/atlas/capture_information_display.mjs DATA aws REBUILD_LABEL
node scripts/atlas/capture_information_display.mjs DATA tryfan-regional REBUILD_LABEL
node scripts/atlas/capture_information_display.mjs DATA riffelhorn-regional REBUILD_LABEL
node scripts/atlas/capture_information_display.mjs DATA riffelhorn-appearance REBUILD_LABEL
# Exact retained evidence analysis (no live services):
PY scripts/atlas/analyze_information_display.py DATA --appearance-run controller-ready
PY scripts/atlas/plot_information_display.py DATA
npm.cmd run lint
```

Capture labels refuse overwriting. For an independent capture rebuild, point the
analyzer explicitly with `--terrain-run REBUILD_LABEL --appearance-run REBUILD_LABEL`; do not refreeze cameras or
select runs by prettiness. The freeze script is historical preparation atca74a84,
not an instruction to overwrite the committed plan at anotherHEAD. Maths/plan tests
have no external terrain/service dependency. Snapshot source-code checks deliberately
validate the research version, not a permanent ban on later authorised production edits.
No shared/runtime code changed, so application tests/build are unnecessary. Syntax,
local document references and final diff checks pass. Normal CI/startup gains no
external-data dependency. Production AWS visual/analytical terrain, IGOR, exaggeration,
satellite, Weather/Traverse and lifecycle remain unchanged. No appearance product,
multiview work, filtering, correction or new DEM is produced.
