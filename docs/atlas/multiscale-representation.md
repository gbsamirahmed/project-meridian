# Atlas multiscale representation — baseline and research synthesis

Recorded 2026-10-06 from clean `main` at
`e3edd0f32ca109175cb456581abb804dc542519c`; fetched origin divergence 0/0.
This is research and production-baseline characterization, not a rendering contract
or implementation. **Regional elevation foundation remains established and closed.**
The multiview appearance branch remains waiting for external swisstopo provisioning;
no work, contact, acquisition or extension of that branch occurred here.

## Decision and evidence boundaries

Atlas needs distinct physical, information and display scales. The supported direction
is **discrete eligible source/product levels, coherent within-family refinement, local
screen-space footprints, and independently controlled depiction**. No evidence here
requires universal context/planning/close modes, additional generalization of every
geometry product, or a new IGOR strength curve. Preserve supported geometry first;
establish whether depiction needs scale treatment before proposing changed geometry.

Evidence classes used below:

- **MERIDIAN EVIDENCE**: pinned production-code audit, retained product identities,
  frozen-camera captures, measured telemetry and read-only diagnostics.
- **EXTERNAL EVIDENCE**: established methods, attributed to their authors/providers.
  They are available approaches, not methods validated on Meridian by this task.
- **RESEARCH HYPOTHESES / DIRECTIONS**: the conceptual architecture assessment and
  ordered next questions. These are not new runtime invariants or empirical truths.

The reproducible [frozen plan](multiscale-representation-plan.json) has SHA256
`e69e14c79596c450bf15ad9b3cd4dd899178a4a7c94887c07076677db9301719`.
The [measurement/evidence index](multiscale-representation.json) retains exact
camera values, selected centre levels, physical/rendered surface probes, capture
hashes, product revisions, software versions and limitations. Large evidence lives
under `meridian-data/experiments/atlas/multiscale-representation-v1`, not Git.

## Five layers of information

1. **World**: physical surfaces, material, morphology and changes; includes forms a
   heightfield cannot represent, such as overhangs.
2. **Observation**: sensor sampling, viewing direction, illumination, acquisition
   epoch, blur and noise. A sample interval is not guaranteed independent information.
3. **Product**: source-derived or synthetic representation, filtering, resampling,
   prepared parents, masks, native height semantics and processing lineage.
4. **Display**: loaded delivery levels, interpolated mesh, texture footprint, pitch,
   exaggeration, device resolution and cartographic portrayal.
5. **Interpretation**: whether people can recognize landforms and relationships.
   Sampling calculations are necessary constraints, not a recognition threshold.

A smooth surface can be inaccurate; a detailed image can be noisy; a legible relief
can be deliberately enhanced. None is a substitute for provenance or terrain accuracy.

## Scale vocabulary and calculation

| Quantity | Meaning and potential use |
| --- | --- |
| Geographic/map scale | Map distance versus represented physical distance. A screen ratio requires display dimensions; it varies under perspective. |
| Camera range/altitude | Physical camera-target relationship; not interchangeable with zoom, especially over terrain. |
| MapLibre zoom | Dimensionless delivery/camera control. Depends on latitude, projection, tile size and renderer; not physical information scale. |
| Map-plane m/CSS pixel | Local spherical-Mercator sampling near the stated latitude. Useful to freeze reproducible cameras. |
| Surface m/CSS pixel | Local screen-to-heightfield mapping; directional and spatially variable under slope/pitch. Use both principal axes, not one universal number. |
| Source GSD/grid/posting | Nominal sampling interval of imagery/elevation. Preserve CRS and its documented meaning. |
| Information resolution/ceiling | Supported information beyond which finer delivery adds interpolation rather than observations. Often uncertain, spatially heterogeneous and directional. |
| Delivery sampling | Pixel/cell interval of a particular tile level, separate from upstream observations. |
| Mesh sampling | Renderer tessellation; may refine without finer DEM evidence. |
| Terrain wavelength/feature size | Physical extent of variation or a particular landform; wavelength is not a semantic feature classifier. |
| Projected feature size | Feature extent in screen pixels, dependent on orientation, depth and perspective. |
| DPR/display resolution | Device pixels per CSS pixel; not additional source information or a human acuity measurement. |

For local Mercator latitude phi, radius R=6378137 m and camera world size 512 pixels:

`map_mpp = 2*pi*R*cos(phi) / (512*2^zoom)`.

Delivery spacing substitutes the actual tile size (256 DEM, 512 imagery) and its
actual canonical tile level. `samples_per_CSS_pixel = map_mpp / delivery_spacing`;
its inverse is CSS pixels per delivered sample. A physical wavelength lambda has
nominal display extent `lambda/map_mpp` pixels, before slope/perspective effects.
For example, 16 m occupies 0.125, 2 and 32 pixels at 128, 8 and 0.5 m/pixel.
This does not establish detectability or image/terrain accuracy.

The pitched diagnostic uses two-CSS-pixel screen displacements, `unproject` and
loaded terrain height queries. Local spherical ENU vectors form a 2x2 Gram matrix;
its eigenvalue square roots give directional surface lengths. MapLibre queries
include exaggeration, so physical heights divide by 1.45; rendered heights are
retained separately. These are finite first-hit estimates, unreliable as differentials
across silhouettes, occlusion boundaries or large depth changes. They are not exact
mesh normals, calibrated camera footprints, or an ellipsoidal survey calculation.

## Production baseline — unchanged

**MERIDIAN EVIDENCE**, audited against installed MapLibre 6.11.2 and all 113 tracked
`src/` file hashes frozen before capture:

- Visual terrain is AWS Terrarium through canonical registry -> selector -> adapter
  -> existing imperative lifecycle. Production registers one common family; it does
  not dynamically introduce regional families as the camera approaches them.
- XYZ geometry uses 256 px tiles, levels 0–14; the separate relief DEM uses levels 0–15.
  Analytical elevation remains the independent AWS z15 policy. The same endpoint
  does not merge the visual and analytical contracts.
- Terrain exaggeration remains 1.45. Renderer terrain tiles use a 128-step mesh;
  source-to-render tile management has a one-level delta and a 512 terrain tile size.
  Four decoded height texels are bilinearly reconstructed; mesh triangles interpolate
  between vertices. Finer tessellation/overzoom of fixed DEM data is not new evidence.
- Globe below zoom 5.5, then Mercator/terrain activation and ordering guards; style
  restoration, camera behavior, bundled worker and satellite interactions remain
  unchanged. Captures here are above that projection threshold.
- IGOR illumination is map-anchored at 315 degrees. Its explicit linear strength
  stops are `(5.5,0),(7,.09),(9,.30),(11,.54),(12,.45),(13,.36),
  (14,.33),(15,.30),(16,.30)`; the last strength persists. This is cartographic
  depiction, not an acquisition-Sun or actual-light model.
- **Additional implicit scale behavior** exists in the pinned hillshade preparation
  shader: a Horn-style 3x3 height derivative has a source-level adjustment. In its
  relevant branch, effective gain is `2^[0.3*(15-z_DEM)]`: approximately 2.30 at z11,
  1.52 at z13 and 1 at z15. Earlier branches differ. This precedes encoded derivative
  clamping/quantization and latitude/IGOR processing; final contrast cannot be inferred
  from the explicit strength curve alone. IGOR further scales derivatives by twice
  strength, with nonlinear slope/aspect portrayal. No shader or curve was changed.
- Production imagery is MapTiler `satellite-v2`, JPEG XYZ, configured 512 px, advertised
  levels 0–22, opacity 1, fade 180 ms, linear resampling. Terrain stays active beneath
  it; IGOR strength is suppressed in satellite mode. Acquisition light in photographs
  therefore remains separate from the terrain-basemap relief.
- Pinned raster rendering uses mipmap-aware filtering and available anisotropic
  filtering under pitch; draped terrain render textures are filtered again. These
  mechanisms address sampling/aliasing, not missing observation or cartographic
  generalization. Actual loaded levels are measured rather than inferred from zoom.
- AWS local effective information resolution remains unknown in canonical metadata;
  a historical EU-DEM remark is not a calibrated local source-information statement.
  MapTiler local GSD/MTF, sensor, acquisition date and mosaic revision likewise remain
  unknown. Service maxzoom 22 is not evidence of independent z22 observations.

Code anchors: [visual configuration](../../src/atlas/map/visualTerrainConfig.ts),
[terrain layers](../../src/atlas/map/terrainLayers.ts),
[relief policy](../../src/atlas/map/atlasVisuals.ts),
[satellite provider](../../src/atlas/map/satelliteProvider.ts).
Renderer audit: `node_modules/maplibre-gl/src/render/terrain.ts`,
`tile/terrain_tile_manager.ts`, `shaders/glsl/_prelude.vertex.glsl`,
`hillshade_prepare.fragment.glsl`, `hillshade.fragment.glsl`,
`webgl/draw/draw_raster.ts`, and `draw_terrain.ts`. Pinned source establishes details;
[living style documentation](https://maplibre.org/maplibre-style-spec/layers/)
is only contextual.

## Frozen benchmark and evidence design

All centres are recovered from existing records, not chosen after inspection.
Tryfan (-3.999, 53.115) covers rugged ridges/gullies; Riffelhorn (7.76121329,
45.97910794) covers steep Alpine and glacier terrain. The two additions reuse
[existing native-relief benchmarks](native-relief-evaluation.md): South Downs
(-0.766, 50.908), rolling terrain, and Cambridge (0.12, 52.20), low relief.
They use production sources only. No new specialist source data was acquired.

Viewport is 1440x900 CSS px, DPR 1, bearing 0 degrees. Mountain top-down sequences
freeze **128, 32, 8, 2, 0.5, 0.125 m/CSS px**, a factor-four physical progression,
not arbitrarily chosen integer zooms. Nominal viewport widths are 184.32, 46.08,
11.52, 2.88, 0.72 and 0.18 km; these are local map-plane widths, not exact terrain
footprints. South Downs/Cambridge use only 128, 8 and 0.5 m/px. Mountain secondary
views use pitch 55 degrees at 8 and 0.5 m/px, same centres/bearing.

| m/CSS px | Tryfan zoom | Riffelhorn zoom |
| --- | --- | --- |
| 128 | 8.519741 | 8.731120 |
| 32 | 10.519741 | 10.731120 |
| 8 | 12.519741 | 12.731120 |
| 2 | 14.519741 | 14.731120 |
| 0.5 | 16.519741 | 16.731120 |
| 0.125 | 18.519741 | 18.731120 |

There are 22 frozen scenes and **54 settled captures**: 22 production AWS terrain,
8 Tryfan regional, 8 Riffelhorn regional, and 16 Riffelhorn common/regional imagery
on matched Swiss geometry. No camera, lighting, colour, filter or crop tuning.
This is settled-frame evidence, not a navigation/popping test or a perceptual study.

Retained products, unchanged:

| Product | Frozen revision | Information and scope |
| --- | --- | --- |
| `tryfan-welsh-regional-v2` | `db8e4d87b5fa609d455d1e0f8ec3fdebc834579a7e102f69f4d0b0283efa690c` | 1 m distributed DTM, BNG, native vertical reference unknown; complete deliverable z14–17. |
| Swiss regional-parent diagnostic | `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672` | Swiss-derived coarse parents, used at z12/13. |
| `riffelhorn-swiss-support-v1` | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` | 0.5 m distributed grid, LV95/LN02, source-family pyramid used at z14–18; not a claim of independent 0.5 m observations. |
| `riffelhorn-swissimage-baseline-v1` | `f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b` | Frozen four 2023 tiles/4 km², 0.1 m distributed pixels with documented nominal 0.25 m information; prepared z12–18. |

The imagery product remains lossless RGBA PNG/512, with declared assumed-sRGB
linear-light premultiplied area averaging and coherent regional parents. No correction,
new preparation or larger selection. The comparison uses the retained Swiss parent/
support geometry for both imagery families, not the synthetic transition experiment.
The product record preserves source/epoch/height/colour unknowns and licences.

The research-only Vite harness exposes camera/tile telemetry and supplies experimental
configurations without editing `src/`. Regional geometry follows the canonical
registry -> selector -> delivery adapter and a whole-tile support gateway. Unsupported
regional tiles fall back to declared AWS; the retained proof cache explicitly overzooms
AWS z15 above its ceiling where required. This experimental common geometry/relief
configuration is not identical to production max14/max15 at every unsupported tile.
Source family and actual levels must therefore accompany visual conclusions.
Normal production AWS captures use the unmodified production configuration.

For imagery, the existing Satellite button/lifecycle is used; one provenance-labelled
research raster overlays MapTiler within retained support. This does not implement an
AppearanceHierarchy. Weather requests are intentionally disabled in this Atlas-only
harness; production Weather code and configuration are unchanged.

## Measured delivery, screen-space limits and information ceilings

**MERIDIAN EVIDENCE**: actual canonical source tile containing the camera centre,
not highest requested level anywhere in the viewport. Each sequence lists scales
128, 32, 8, 2, 0.5, 0.125 m/px in that order.

| Configuration | Centre geometry levels | Centre relief levels |
| --- | --- | --- |
| Production AWS, both mountains | 7, 9, 11, 13, 14, 14 | 10, 12, 14, 15, 15, 15 |
| Tryfan regional + declared fallback | 7, 9, 11, 13, 15, 17 | 10, 12, 14, 16, 17, 17 |
| Riffelhorn regional + declared fallback | 7, 9, 11, 13, 15, 17 | 10, 12, 14, 16, 18, 18 |

These are not a single terrain LOD. At Tryfan 8 m/px, Welsh relief z14 is present
while centre geometry remains common z11. At 2 m/px Welsh relief z16 is present,
but complete Welsh geometry z13 is unavailable. At Riffelhorn 32 m/px, Swiss-derived
relief parents can appear while geometry is common; at 8 m/px Swiss relief z14 is
present beneath common geometry z11. Coherent available parents do not eliminate
the distinct coarse source-family handoff. Its prior limitation is preserved.

At 0.125 m/px, AWS z14 centre geometry has delivery intervals **5.735 m (Tryfan)**
and **6.640 m (Riffelhorn)**: about **45.9 and 53.1 CSS px per DEM sample**.
More mesh vertices cannot recover absent structure. Fine regional centre geometry
is z17: approximately 0.717/0.830 m delivery intervals, or 5.74/6.64 CSS px per
sample. The native 1 m Welsh and 0.5 m Swiss grid intervals occupy 8/4 CSS pixels
at this view. These are sampling intervals, not native measurement resolution.
Even a 0.717 m Welsh delivery cell does not imply independent 0.717 m evidence.

Pitched probes demonstrate why nominal mpp alone is inadequate. At Tryfan pitch55,
production AWS centre physical surface principal intervals are **7.172–35.768 m/px**
at nominal 8 m/px, and **0.429–4.040 m/px** at nominal 0.5 m/px. The corresponding
regional 0.5 m view is 0.404–1.095 m/px. Geometry changes the intersection as well
as slope. Large finite-probe differences are not universal stretch or accuracy
estimates; exact upper/centre/lower measurements and exaggerated counterparts are
retained. They establish directional variation, not a calibrated visibility model.

Source-information ceiling is therefore an **evidence envelope**, not necessarily
one number: nominal sampling, documented effective information, direction/support,
epoch and processing, plus uncertainty. Delivery may continue beyond it legitimately
for portrayal if overzoom/interpolation is explicit. A useful display range additionally
depends on geometry, projection, contrast and recognition; it is not interchangeable
with source GSD or a universal metadata constant.

## Geometry and IGOR findings across scale

Matched captures show broad mountain/valley form under AWS at 128/32 m/px, local
ridge/gully structure at finer views, and increasingly interpolated geometry after
the geometry delivery ceiling. Regional Tryfan and Swiss views expose finer ledges,
slope breaks, gullies and moraine texture where eligible. The 0.5 m pitched Tryfan
regional ridge is much more articulated than the AWS counterpart.

However, some intermediate gains are **depiction-source** changes, not geometry
refinement: regional relief is already available while common geometry remains.
The capture matrix does not isolate those two causal contributions. Broader common
geometry also reflects declared level eligibility, not proof that regional information
is perceptually useless there. No universal source-switch scale is inferred.

South Downs at 8 m/px gives readable rolling slopes without alpine roughness;
Cambridge has little visible relief and vector portrayal dominates. This expands the
regime audit without assuming low relief means absent microtopography. Neither site
establishes a hillshade optimum or a quantitative human-legibility threshold.

Existing IGOR supports broad and intermediate structure with its continuous strength
curve, source-level derivative adjustment and high-zoom floor. Finer relief source
sampling can add texture even without finer geometry. Strong slope-derived contrast
can potentially overemphasize small wavelengths; no measured general noise boundary
or justified replacement curve emerges here. Satellite suppression separates this
cartographic depiction from photographic illumination. Pitch changes sampling and
silhouettes without changing map-anchored lighting policy.

The earlier [regional-parent experiment](regional-parent-diagnostic.md)
and [scale decomposition](terrain-scale-decomposition.md) remain the evidence for
within-family coherence and different source estimates. The Swiss protected z13->14
0.71 m RMS was internal LOD change, not accuracy. Comparable ~27 m raw/broad overlap
RMS 20.35/19.94 m and stable-candidate 5.56/5.06 m showed broad disagreement remains;
this task does not assign percentages to detail versus error or rerun reconciliation.

## Appearance findings across scale

**MERIDIAN EVIDENCE**: current matched captures plus established findings from the
[source-derived SWISSIMAGE baseline](swissimage-source-derived-baseline.md).

Common imagery centre levels are 9, 11, 13, 15, 17, 19 across the six scales;
regional overlay levels are unavailable, unavailable, 13, 15, 17, 18. The first two
regional-labelled captures contain only common imagery because the research overlay
begins at z12. Their identical broad appearance is an **ineligibility/withholding
control**, not proof that higher source resolution would never help broad views.

At 8 m/px the regional footprint/colour handoff is salient; 2 m/px exposes local
surface patterns. At 0.5 m/px both products show texture, with different contrast,
colour and structure. At 0.125 m/px, regional delivery is capped at z18 (~0.207 m
map-plane samples here); nominal 0.25 m source information occupies two CSS pixels.
Common imagery still delivers z19 (~0.104 m samples), but its independent information
resolution is unknown. Extra grain is not proof of better observations.

A fixed 400x400 CSS-pixel central capture window, interpreted as sRGB and converted
to linear luminance, gives regional/common gradient mean-square:

| Nominal scale | SWISSIMAGE | MapTiler |
| --- | --- | --- |
| 0.5 m/px | 0.0045134 | 0.0043852 |
| 0.125 m/px | 0.0012991 | 0.0020840 |

This deliberately modest statistic describes captured signal, not source optical
MTF, quality, accuracy or a fixed ground population. It includes filtering, contrast,
epoch and remaining labels. The reversed finest-view ordering rules out treating
higher screenshot-frequency energy as universal proof of regional superiority.
Pitched matched views likewise exhibit different local colour/texture without a new
illumination control. No correction or sharpening was attempted.

The prior geolocated baseline remains more targeted evidence of useful information:
planning ordinary-patch gradient 0.001140 versus 0.000972; opposed-close 0.000664
versus 0.000336. Its broad ordinary 60 m lattice had only 31 unique screen pixels,
limiting inference there. Its source/display luminance correlation was 0.9045,
with no dominant opposed-close Atlas black-crushing evidence. Its steep-patch p95
geometric stretch was 6.192x: nominal 0.25 m map-plane information corresponded to
1.548 m tangent-surface sampling. Original observation occlusion was not established.
These are **retained results**, not newly rerun patch diagnostics.

Thus regional detail can be useful while its utility varies by scale, patch and
representation. Better sampling does not supply missing viewing directions, recover
unobserved texture, change acquisition illumination, or resolve imagery/geometry
registration. Orthophoto information is anisotropic on steep represented surfaces.
Hard appearance boundaries remain permitted and unreconciled. This task provides no
new source-darkness/illumination diagnosis and does not reenter the waiting branch.

## Read-only terrain wavelength diagnostic

**MERIDIAN ADAPTATION of established spectral analysis**, used only to describe
physical scale, not prepare generalized terrain or identify real-world accuracy.
Two retained 1024 m squares use fixed native centres: Tryfan BNG [266400,359300],
Riffelhorn LV95 [2625000,1092000]. Sample 512x512 at 2 m via declared native
cell-centred bilinear reconstruction; no vertical transformation. Remove a
least-squares plane, apply a separable Hann window, calculate radial FFT power and
normalize by mean window squared. Fixed bands are 4–16, 16–64, 64–256 and 256–1024 m.

| Horizontal wavelength | Tryfan RMS (m) | Swiss RMS (m) |
| --- | --- | --- |
| 4–16 m | 0.880 | 1.056 |
| 16–64 m | 2.762 | 2.855 |
| 64–256 m | 10.271 | 10.100 |
| 256–1024 m | 88.366 | 36.524 |

Parseval closure error is at most 7.28e-12 m². This window-normalized amplitude is
not a residual against common terrain, an error percentage or a terrain quality
score. Native sampling and product provenance are recorded separately. The earlier
comparable-scale decomposition supplies the cross-source evidence; no new causal
frequency attribution is made from these one-source patches.

Wavelength gives a useful bridge to display extent. Small elevation amplitude can
still have substantial slope effect: a sinusoid of amplitude A and wavelength lambda
has derivative amplitude `2*pi*A/lambda`. Relief derived from slope can therefore
emphasize information with small elevation RMS. Height simplification and hillshade
simplification are different operations; filtering a shaded image need not equal
shading filtered geometry.

Limitations: bilinear downsampling is not a rigorous anti-aliasing filter, so finest
band amplitudes are diagnostic, subject to aliasing and window leakage. Radial diagonal
coefficients below 4 m and DC/one-cycle coefficients at or above 1024 m are retained
only for closure, not interpreted as independently resolved bands. The finite patch,
plane removal and isotropic aggregation hide orientation and larger-scale form. No
native measurement PSF, feature topology or morphology-preservation claim follows.

## Bounded established-practice review

**EXTERNAL EVIDENCE**, accessed 2026-10-06. Review depth is stated to avoid turning
abstracts into validated recommendations. No techniques below were implemented here.

| Primary source / scope | What it solves or preserves; relevance and limits |
| --- | --- |
| [Wood 1996 thesis record](https://figshare.le.ac.uk/articles/thesis/The_geomorphological_characterisation_of_Digital_Elevation_Models_/10152368) and [author's multiscale extract](https://www.staff.city.ac.uk/~jwo/landserf/landserf180/thesis/) | Geomorphometric derivatives/form classification depend on neighborhood scale and direction. Physical neighborhood size helps separate landform from grid spacing. This is analysis, not a source PSF or a renderer LOD rule; thesis extracts, not the full archive, reviewed. |
| [Losasso & Hoppe 2004, geometry clipmaps](https://hhoppe.com/geomclipmap.pdf) | Nested filtered elevation grids, distance-dependent sampling and continuity mechanisms address real-time terrain budgets. Deliberately lose finer geometry with distance. Synthesized detail in that system would require explicit synthetic provenance in Atlas; continuity is not morphology/accuracy. Paper reviewed. |
| [Hoppe 1998, view-dependent LOD](https://www.microsoft.com/en-us/research/publication/smooth-view-dependent-level-of-detail-control-and-its-application-to-terrain-rendering/) | View-dependent approximation and temporal geomorphs manage projected error/popping. Geometry error is not equivalent to ridge/drainage preservation or physical source uncertainty. Author publication record reviewed. |
| [Chen et al. 2016, watershed/tree DEM generalization](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0159798) | Nested watershed structure and selected ridge/valley feature points guide reconstruction rather than uniform decimation. Terrain skeleton matters alongside elevation error. Study-specific thresholds and terrain do not provide an Alpine default or universal topology guarantee. Paper sections reviewed. |
| [Fugacci, Kerber & Manet, topology-preserving terrain simplification](https://arxiv.org/abs/1912.03032) | Explicit topological constraints supplement geometric approximation. Relevant if simplification creates/removes critical forms; topology alone does not ensure perceptual clarity or metric fidelity. Abstract-level review only. |
| [Leonowicz, Jenny & Hurni 2010](https://berniejenny.info/pdf/2010_Leonowicz_Small_Scale_Relief_Shading.pdf) | Low-pass terrain with curvature-based ridge/valley enhancement gives clearer small-scale relief than unfiltered detail. Deliberately changes depiction geometry. Suppression/enhancement is cartographic, not new observations, and may distort form if excessive. Paper reviewed. |
| [Jenny 2001, interactive relief shading](https://berniejenny.info/pdf/2001_Jenny_Reliefshading.pdf) | Local light-direction adjustment, lowland/steep treatment and aerial perspective improve readable relief. This distinguishes designed illumination from literal Sun rendering; adaptation can mislead if mixed with acquisition-light interpretation. Paper reviewed. |
| [Samsonov & Jenny 2015](https://berniejenny.info/pdf/2015_Samsonov_JennySmall-scaleAndMulti-scaleReliefMapping.pdf) | Hierarchies of terrain structure and gradual portrayal changes address small/multiple map scales. Openness and related surface measures supplement illumination. Stylization/feature emphasis is not a faithful replacement for authoritative geometry. Relevant paper sections reviewed. |
| [Jenny 2021, line-integral-convolution generalization](https://research.monash.edu/en/publications/terrain-generalization-with-line-integral-convolution/) | Direction-aware smoothing aims to reduce detail while retaining ridge/flat transitions. Possible depiction-preparation control, not adopted from its abstract; author abstract-level review only. |
| [PBRT fourth edition, image textures](https://www.pbr-book.org/4ed/Textures_and_Materials/Image_Texture) | Prefiltered image pyramids, trilinear and EWA anisotropic filtering address minification/aliasing and directional texture footprints. They remove unresolved signal; they do not identify important terrain features, reconcile mosaic epochs or recover occlusions. Technical chapter reviewed. |
| [GDAL overview practice](https://gdal.org/en/stable/programs/gdaladdo.html) | Explicit overview kernels, nodata/support and reproducible preparation manage geospatial image pyramids. Kernel/colour handling affects fidelity and aliasing, but overview pixels are not new observations. Official documentation reviewed. |
| [USGS JACIE 2024 guide](https://pubs.usgs.gov/publication/ofr20241023) | Geometric/radiometric characterization separates sampling from measures such as MTF and noise. Supports retaining uncertainty about effective information, rather than declaring GSD identical to resolution. Official record/summary reviewed, not a calibration of Atlas imagery. |

Mature practice: [ETH relief guidance](https://ikgrelief.ethz.ch/design/generalization/)
explicitly removes detail and emphasizes structure for a limited scale range.
[University of Zurich cartographic work](https://www.geo.uzh.ch/en/units/gis/research/computational-cartography.html)
frames generalization as maintaining meaningful structure while reducing complexity.
For physical surfaces, **selection** may withhold unsupported detail; **simplification**
removes smaller variations; **aggregation** groups nearby structure; **enhancement/
exaggeration** gives legible relief. **Displacement, collapse and typification** can
serve schematic portrayal but should not silently move or replace Atlas's physical
heightfield. Their relevance here is bounded depiction, not roads/labels or hiking tasks.

Engineering patterns: [Cesium's documented screen-space error](https://cesium.com/learn/cesiumjs/ref-doc/Cesium3DTileset.html#maximumScreenSpaceError)
drives discrete tile refinement from projected approximation error and resource
budgets; this is not an independent-information threshold. [USGS 3DEP's elevation
map service](https://www.usgs.gov/news/technical-announcement/new-elevation-map-service-available-usgs-3d-elevation-program)
provides separate elevation-derived hillshade, multidirectional depiction, slope and
aspect. These establish geometry/portrayal separation and multiple depiction products,
not scientific superiority of one lighting treatment. No proprietary-system behavior
is inferred from screenshots; no method is credited as a Meridian invention.

## Geometry versus depiction, and representation honesty

**Synthesis from external practice and Meridian evidence**: geometric LOD controls
approximation and rendering cost; depiction controls readable structure and visual
contrast. A finer mesh over the same DEM only reduces renderer approximation.
A lower-pass terrain representation deliberately removes shape; a lower-pass shaded
image removes visual contrast instead. A feature-enhanced relief DEM can be a declared
portrayal dependency without replacing physical geometry or analytical elevation.

Change represented geometry when a declared approximation/anti-aliasing operation or
specific morphology failure justifies it. Prefer portrayal changes when evidence is
about clutter, illumination hierarchy or broad-form readability. Ridge/drainage and
extrema checks would be necessary before accepting morphology-changing preparation.
No universal new geometric generalization requirement was demonstrated in this task.

Honesty principles for subsequent decisions:

- Interpolation, overzoom and mesh refinement do not create observations.
- Keep nominal sampling, effective information and useful display range distinct;
  unknown local information resolution stays unknown.
- Preserve source/product/representation identity and the lineage of intentionally
  removed, selected, enhanced or synthesized information.
- Smoothness, visual prominence and contrast are not confidence or accuracy.
- Cartographic illumination is not actual acquisition illumination; orthophoto RGB
  is not albedo. Renderer adjustments do not rewrite source provenance.
- Within-family refinement and cross-family handoff are separate; continuity is not
  automatic merely because parents are available.
- Geometry, relief dependency and imagery may use different levels. Report each
  before attributing a visual change to finer physical surface information.
- Preserve independent analytical elevation. No visual choice silently changes
  gradients, ascent/descent, Traverse timing or Weather altitude.

## Control variables and ownership — proposal, not implementation

| Concern | Likely control variables | Responsibility / behavior |
| --- | --- | --- |
| Source-family eligibility | Valid support, available levels, provenance policy, source information, explicit fallback | Representation selection; discrete family decision. TerrainHierarchy already expresses this. |
| Coherent geometry LOD | Product level, projected approximation error, local surface footprint, resource budget | Prepared parents plus renderer refinement; discrete levels with continuous transition mechanisms where justified. Source handoff is independently classified. |
| Relief depiction | Physical feature/wavelength hierarchy, projected structure, local sampling, terrain regime | Offline declared depiction preparation plus continuous/piecewise runtime portrayal. No new universal strength law yet. |
| Imagery refinement | Source GSD/information uncertainty, parent lineage, directional texture footprint, support | Prepared anti-aliased colour-aware parents; discrete available levels, renderer texture filtering. Unknown source resolution cannot justify a precise useful-scale cutoff. |
| Overzoom/withholding | Delivery ceiling, source uncertainty, projected samples, user-visible honesty | Explicit selection/display policy; no new information claim. |
| Human legibility | Feature contrast, orientation, clutter, display and viewing regime | Bounded empirical evaluation; cannot be replaced by tile zoom or FFT energy. |

**Source/product preparation** owns deterministic resampling, supported parents,
anti-aliasing/colour assumptions, derived generalization if justified, source ceilings,
masks and lineage. Preparing a dedicated relief dependency must not silently alter the
rendered/analytical heightfield. Do not bake view-specific lighting into source products.

**Representation selection** owns eligibility, declared family priority, support,
available product levels, fallback and provenance. Screen-space requirements can be
translated to a scale request at a renderer adapter boundary without making geographic
metadata depend on MapLibre zoom or a particular device.

**Runtime rendering** owns mesh/texture sampling, projected error, continuous portrayal,
DPR, anisotropic filtering and render-only continuity. Offline preparation is preferable
for reproducible view-independent processing; view-dependent filtering remains rendering.

The frozen [TerrainHierarchy](terrain-hierarchy-contract.md) and
[runtime selection](terrain-runtime-selection.md) already cover the required identities,
support, levels, coherent parents and fallback. No contradiction or schema change was
found. It should not become a renderer configuration framework. The
[AppearanceHierarchy proposal](appearance-baseline-and-architecture.md) should retain
its own GSD/band/colour, parent/support/time and source-information semantics. Observation
geometry is separate from scale representation and remains on the waiting branch.

Concrete future gaps are **descriptive scale telemetry at the camera/renderer adapter**,
independent identification of relief dependencies, and evidence-scoped useful display
ranges. A small ScaleContext might later record nominal and local directional sampling,
DPR, actual levels and uncertainty, but no new type/runtime is introduced here. Avoid
universal useful-range constants or a general geospatial framework. The needed tests
come before an architecture commitment.

## Ordered next work and stopping conditions

Only the first two questions are presently justified; the third is conditional.
None was executed here.

1. **Isolate scale-dependent relief depiction from geometry.** Unknown: can broad/local
   structure be made more legible without changing the represented physical surface?
   Established cartographic filtering and feature-aware relief solve much of the method
   problem; the Meridian question is portrayal under its actual geometry/display.
   Freeze retained eligible mountain geometry, rolling/low-relief controls, the physical
   camera sequence and one light direction. Compare current IGOR against **one** labelled,
   established scale-separated depiction control; no curve/illumination search, source
   acquisition or reconciliation. Inspect ridge/gully organization, clutter/aliasing,
   induced depiction forms and provenance. Stop with accept/reject evidence for separate
   depiction treatment, without changing production or analytical geometry.
2. **Establish an information-aware display/selection envelope.** Unknown: when should
   supported information refine, overzoom or be withheld across devices and pitch?
   Existing parents/filtering/selection supply most machinery. After the first result,
   reuse the same products and sequence with a bounded DPR1/DPR2 and oblique pair at
   observed transitions. Record actual family/levels, directional sampling and visible
   structure; preserve unknown source ceilings. Stop with scoped eligibility/usefulness
   constraints before implementing selection policy. No three-mode system or universal
   minimum-feature-pixel rule is assumed.
3. **Conditional depiction-preparation morphology check.** Only if the first experiment
   exposes lost landform structure that portrayal alone cannot address, compare one
   established feature-preserving depiction preparation with ordinary parents on one
   retained patch. Check ridge/valley positions and new extrema as well as readability.
   Stop at the control's result. This is not an automatic new elevation-method programme,
   modified analytical terrain, Riffelhorn reconciliation or a geometry-generalization
   implementation branch.

## Evidence, limitations and reproduction

Local evidence index: four terrain/appearance contact sheets plus
`scale-and-wavelength.png`, 54 full captures and their telemetry/hash records.
`multiscale-representation.json` contains the relative paths and hashes; inspect originals
for fine features rather than deriving thresholds from downsampled contact sheets.
Capture software was Chromium 151.0.7922.34, MapLibre 6.11.2. Analysis was Python3.12.6,
NumPy2.5.3, rasterio1.4.3/GDAL3.9.3, pyproj3.7.2 and the recorded Pillow version.

Common imagery/AWS tiles are live services without a pinned local upstream mosaic
revision. Camera and diagnostic reconstruction are deterministic, but a future service
capture need not reproduce identical pixels. Provider query credentials are removed
from retained telemetry; screenshots remain local research evidence, not cleared
public redistribution. No generic metric of perception, accuracy, local PSF, temporal
truth or useful-scale optimum was produced. No zoom navigation sweep, device comparison,
frequency-separated common/regional residual experiment, user study, or new geometry
visibility test occurred. These limits constrain the synthesis rather than being hidden.

From repository root, using the existing data environment (PowerShell):

```powershell
$atlasData = 'C:/Users/gbsam/Documents/Projects/meridian-data'
$atlasPython = "$atlasData/earth-lab/.venv/Scripts/python.exe"
node --test scripts/atlas/test_multiscale_math.mjs
& $atlasPython -m unittest discover -s scripts/atlas -p 'test_multiscale*.py'
& $atlasPython scripts/atlas/multiscale_spectrum.py --data $atlasData
& $atlasPython scripts/atlas/analyze_multiscale.py --data $atlasData
npm.cmd run lint
```

The existing plan is immutable. `freeze_multiscale.mjs` refuses overwriting it.
Independent capture repetition, if authorized later, needs the configured production
client key and the existing proof cache (first command in a separate terminal):

```powershell
& $atlasPython scripts/atlas/terrain_proof_cache.py --root "$atlasData/cache/atlas/tryfan/second-region-proof/aws" --port 4187
foreach ($atlasMode in @('aws','tryfan-regional','riffelhorn-regional','riffelhorn-appearance')) {
  node scripts/atlas/capture_multiscale.mjs $atlasData $atlasMode repeat
}
```

The optional label writes `captures-repeat/<mode>` and refuses existing capture records.
It does not overwrite accepted evidence; analyzer uses accepted captures only. Local
ports4173/4188 are research-only. Normal startup and CI need no meridian-data/service
availability. Synthetic tests use tiny temporary arrays/raster fixtures only.

Validation: ten asset-free synthetic tests pass (Mercator inverse/latitude/tile-size,
physical/rendered scale math, Gram anisotropy, audited curve interpolation, known
wavelengths/Parseval, plane removal, native cell-centre/orientation, missing support,
centre-level telemetry, captured signal and frozen scope). Repeated diagnostic outputs
are byte-identical: spectrum SHA256
`d7032674a186c5da8c230554f36a888172faece344cb3211a87a69b4c42d069a`, summary SHA256
`72f4166f01c2036735b07f0f320a27456ada3837d4ce6f30fc652fda59c494b4`.
All source/product/capture hashes and frozen cameras pass, including 100 Swiss terrain
assets and four SWISSIMAGE source files. All113 production files remain unchanged.
No page errors or failed local product deliveries; HTTP503 Weather requests are deliberate
harness isolation and navigation-cancelled requests are recorded separately. Non-failing
upstream rasterio/NumPy deprecation warnings remain. Lint, syntax, JSON/local references
and final diff checks are recorded at the commit; application tests/build were not rerun
because no application/shared-runtime files changed.

**Stop:** baseline characterization, bounded literature and conceptual multiscale model
are complete. No scale-aware rendering implementation, visual tuning, source acquisition,
multiview work, correction, Weather/Traverse change or new elevation benchmark occurred.
Next is the first isolated depiction question above, under its own bounded task.
