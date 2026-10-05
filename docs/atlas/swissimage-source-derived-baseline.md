# SWISSIMAGE / Riffelhorn source-derived appearance baseline

Baseline: `6f2eb0217c167630154fe4e9d4aa6c8c5d59a76e`. Result: **baseline proof established, with explicit interpretation limits**. The [appearance architecture](appearance-baseline-and-architecture.md) remains a proposal; no AppearanceHierarchy runtime was implemented. The regional elevation foundation remains closed.

## Question and frozen controls — MERIDIAN EVIDENCE

What does the retained regional orthophoto add before appearance correction? Information gain, scale, geometric support, source/display signal and illumination knowledge are evaluated separately. This is not an accuracy, reflectance or albedo test.

The four retained 2023 SWISSIMAGE tiles are `2624-1091`, `2624-1092`, `2625-1091`, `2625-1092`. Native support is LV95 `[2624000,1091000,2626000,1093000]`, exactly 4 km². **All retained bytes matched the catalogue; nothing was reacquired or expanded.** The [evidence record](swissimage-source-derived-baseline.json) retains their complete paths, hashes, sizes, product identity, diagnostics and capture index. The [original catalogue](riffelhorn-data-catalog.json) retains upstream STAC/download identities and receipts.

Geometry was identical in both imagery cases: existing Swiss-derived z12/13 parents, revision `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`, and original Swiss support z14–18, revision `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`. All 30 parent-product tiles and 11,429 original product tiles were hash-verified; the native VRT and its 100 source DEM hashes were verified. This is the existing regional geometry, **not the final synthetic terrain transition**. Whole-tile eligibility, explicit AWS fallback outside complete support, selection and heightfield adapter use the existing terrain machinery. No elevation preparation/experiment occurred. These exact geometry identities are display dependencies, not the unknown geometry revision used upstream to orthorectify SWISSIMAGE.

The frozen cameras from [two-band cameras](two-band-cameras.json) are:

| Pose | Zoom | Bearing | Purpose |
| --- | ---: | ---: | --- |
| `centre-12.4-b0` | 12.4 | 0° | Context, geographic source edge |
| `centre-14.2-b0` | 14.2 | 0° | Planning, ordinary-ground detail |
| `centre-16.2-b0` | 16.2 | 0° | Close support/stretch limitations |
| `centre-16.2-b180` | 16.2 | 180° | Opposed face, dark-region legibility |

All centre `[7.76121329,45.97910794]`, pitch 55°, viewport 1920×1080, DPR1. Returned pitch differs by ~7×10⁻¹⁵ degrees from floating-point conversion. Eight primary captures, plus one 12.4→14.2→16.2→14.2 navigation sequence per imagery case. No additional pose, AWS-geometry pair, lighting control, crop/year/filter search or correction was introduced. MapLibre 6.11.2, Chromium 151.0.7922.34, mesh128, exaggeration1.45, existing sky/fog, satellite opacity1, linear raster filtering, fade180ms, IGOR zero-strength expression, elevation overlay off. Weather data requests were isolated in evaluation; normal Weather/Traverse code was untouched.

Common control is the actual configured MapTiler `satellite-v2` service, JPEG/XYZ/configured512, directly requested by the unchanged satellite lifecycle. Its local GSD, contributing observations, dates, calibration and immutable revision are unknown. Provider tiles were not exported into an offline imagery archive. Captures remain local research evidence; this does not grant public redistribution rights to MapTiler's upstream imagery. Credentials are removed from retained network diagnostics.

## Source semantics and rights — EXTERNAL EVIDENCE

The [official product page](https://www.swisstopo.admin.ch/en/orthoimage-swissimage-10), retained per-tile metadata and [discovery record](riffelhorn-data-discovery.md) establish a processed RGB orthophoto mosaic, not raw aerial observation. The selected Alpine tiles document nominal **25 cm information**, distributed on a **10 cm** grid: each COG is 10000×10000, three uint8 bands, LV95/EPSG:2056, internal YCbCr JPEG95. Four files total **186,259,028 bytes**. No new Meridian lossy encoding was added.

2023 is mosaic-year evidence. The provider's year convention concerns the images supplying at least 70% of a tile; it is not a pixel timestamp. Exact sensor, pixel acquisition date/time, view rays, exposure, calibrated colour transfer and Sun geometry remain **UNKNOWN**. The retained intersecting 2023-09-07 LUBIS flight is a plausible contributor, not a proven pixel-to-flight mapping. The official page explicitly says detailed mosaic seamlines/date breakdown are unavailable. No Sun was guessed or reconstructed.

[swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices), version1.3.2021, permit use, processing and distribution with source acknowledgement, retained as **©swisstopo**. These are custom terms, not an invented CC licence. The general product's Planet notice for large lake imagery must not be discarded in future distributions; the selected retained catalogue has no established Planet contribution. Source-specific notices still govern public delivery. The proof neither acquires a new product generation nor alters the historical assets.

## Preparation and immutable product — MERIDIAN EVIDENCE

Product: `riffelhorn-swissimage-baseline-v1`, identity `f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b`; manifest SHA256 `3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934`. Origin is **source-derived regional appearance**. Lineage is upstream orthophoto → declared Meridian horizontal reprojection/resampling → regional image pyramid → Atlas raster display. No physical appearance correction, sharpening, filling, colour matching, exposure adjustment or geometry modification occurred.

The method was declared before inspection:

- XYZ/EPSG:3857, 512 px, lossless RGBA PNG, z12–18.
- Finest z18: bounded source-window reads, explicit assumed-sRGB decode, premultiplied RGB/validity area averaging through GDAL, one thread; independently quantize/encode.
- Parents: recursive unencoded 2×2 equal-Mercator-area means of premultiplied linear RGB and alpha. No common-source parents.
- Alpha represents source-area support fraction. It is not confidence, darkness, snow or an observation-quality mask. Absent children contribute transparent support. Black pixels remain valid where the TIFF validity mask is valid.
- Assumed sRGB is a declared colour-resampling convention, **not an authoritative source radiometric calibration**. The output is not reflectance. Finite RGB/alpha bounds and endpoint behavior are checked.

| Level | Tiles | Partial tiles | Ground delivery sampling near Riffelhorn |
| --- | ---: | ---: | ---: |
| z12 | 1 | 1 | 13.28 m |
| z13 | 2 | 2 | 6.64 m |
| z14 | 4 | 4 | 3.32 m |
| z15 | 9 | 8 | 1.66 m |
| z16 | 36 | 20 | 0.83 m |
| z17 | 110 | 38 | 0.415 m |
| z18 | 380 | 74 | 0.207 m |

The precise per-level partial counts in the JSON/manifest are authoritative if rounded descriptions differ. z18 slightly oversamples the nominal25cm upstream information; z18 delivery and the native10cm distributed grid add no observations. Higher overzoom only enlarges/resamples that representation. The frozen close views actually used imagery z15–17 depending on footprint; they do not demonstrate exhaustion of every 25cm source detail.

Total542 tiles / **269,852,875 bytes**; unencoded support/colour fields **1,294,380,168 bytes**. Generation194.07s on this machine; speed is operational evidence, not an optimization target. An independently generated sibling matched the manifest and every output-file hash. The manifest covers1,084 PNG/field files. Retained source hashes still match after preparation.

## Transfer and parent fidelity — MERIDIAN EVIDENCE

Verification decodes every PNG and compares it with independently encoded declared field values; RGBA bytes agree exactly. Independent four-child arithmetic checks give maximum parent linear-field difference **2.98×10⁻⁸**, from float32 rounding. Maximum decoded-linear RGB quantization difference over fully supported pixels is **0.004455** (an encoding difference, not terrain/image accuracy).

Four finest tiles at the geographic control patches were recomputed from retained source windows: unencoded fields and encoded pixels matched exactly. This is a repeat source-transfer calculation through the declared kernel, not an independent photogrammetric reference. Synthetic tests independently check RGB transfer round-trip, native source seams, valid black pixels, alpha-weighted parents, grid continuity and deterministic PNG/field writing. Spatial averaging intentionally attenuates fine detail at coarser levels; its differences from native pixels are not measurement errors. Existing upstream JPEG artifacts/calibration limits remain in the source.

## Matched appearance and scale — MERIDIAN EVIDENCE

At context, only a small central area changes. The crop's colour/material handoff is visible; native fine patterns occupy very few screen pixels. In the ordinary60m control,961 lattice samples project onto only **31 unique displayed pixels**. Context is not evidence that native25cm detail is perceptually available.

At planning, regional rock/grass boundaries, small ground markings and paths become more legible; the source colour boundary remains obvious. The ordinary control occupies334 unique pixels. At the same geographic lattice, regional gradient energy is **0.001140** versus common **0.000972** (~1.17×). Summit gradient energy does not increase in this view, so information gain is neither uniform nor reducible to one score.

At close bearing0, fine photographic texture is available but steep vertical streaking dominates the view. The frozen geographic patches are not first-visible in this pose, so no patch signal-retention statistic is claimed for it. The camera was not moved to manufacture a better comparison.

At close bearing180, SWISSIMAGE makes scree/rock patterns, paths, material edges and shadow variation more legible. In955 matched first-visible steep-patch samples, regional geographic-lattice gradient energy is **0.000664** versus common **0.000336** (~1.98×). This is a linear-luminance diagnostic at matching map positions, not an optical-resolution, perceptual-quality or accuracy score. Epoch, illumination, processing and contrast differ between products; a frequency increase alone cannot establish that the gain was caused solely by GSD.

Coherent regional parents are verified numerically and show progressive feature loss/refinement across the fixed views. Two navigation sequences recorded36 intermediate states; completed geometry, common imagery and regional imagery deliveries had HTTP200. No missing-parent colour substitution was used. No spontaneous level-wide colour seam is established inside the regional family; the intended common/regional crop boundary remains. Navigation telemetry is not a perceptual movie, and transient popping cannot be universally excluded from these sampled states.

## Steep-surface support — MERIDIAN EVIDENCE / ESTABLISHED EXTERNAL METHOD

For a single-valued heightfield, map-plane/surface-area ratio gives stretch `sqrt(1+|∇h|²)=1/cos(slope)`. A nominal tangent footprint is0.25m×stretch. This is established geometry, not a new photogrammetric method. Native0.5m Swiss heights at the fixed patches give:

| Patch | Median slope | Median / p95 area factor | Nominal tangent footprint median / p95 |
| --- | ---: | ---: | ---: |
| Ordinary60m | 19.65° | 1.062 / 1.258 | 0.265 / 0.314 m |
| Steep60m | 44.01° | 1.390 / 6.192 | 0.348 / 1.548 m |
| Summit150m | 52.12° | 1.629 / 5.686 | 0.407 / 1.421 m |
| Dark-context150m | 42.94° | 1.366 / 4.288 | 0.341 / 1.072 m |

In the steep patch,27.07% of cells exceed2× stretch and6.83% exceed5×. Ordinary ground has0.82% /0.021%. The full fixed patch includes gentler ground; it is not the previous012G first-visible dark-face triangle population. Do not compare its median44° with that population's63.51° as an improvement. The JSON separately records stretch under renderer exaggeration1.45; physical and exaggerated shape are not conflated.

The observed vertical streaks are **consistent with limited orthographic support**. A delivered map-plane pixel is not an equally dense observation of the draped steep surface. Native DTM gradients, render mesh geometry and missing overhangs differ; these metrics do not prove original camera visibility or calibrated sensor footprint. The Atlas project→terrain-unproject test identifies current first-visible surfaces, not historical aerial-source occlusion. Actual source occlusion remains unproven without acquisition geometry. More source pixels improve represented horizontal texture, but cannot supply missing view directions or genuinely unobserved faces.

## Source darkness versus Atlas display — MERIDIAN EVIDENCE

Controls are exactly the frozen ordinary/steep60m and summit/dark150m patches from012G. The source steep patch contains real variation and no exact-black pixels: assumed-linear luminance p05/median/p95 **0.00180/0.00457/0.01130**, versus ordinary **0.16372/0.26973/0.49895**. Source darkness is therefore substantial; it is not a missing-alpha region.

Screen probes must be within the viewport, outside the conservative UI guard and agree with the current first-visible surface within2m horizontal round-trip. Corresponding prepared samples use the actual loaded tile level at each location, not a camera-zoom guess. Nearest screen sampling, filtering, mesh differences, labels and atmospheric blending remain limitations; sRGB is assumed for diagnostics.

The opposed close view provides the strongest dark-face comparison:

| Steep patch,955 traceable samples | p05 | Median | p95 |
| --- | ---: | ---: | ---: |
| Prepared regional, actual z17 | 0.002292 | 0.004814 | 0.009998 |
| Atlas regional capture | 0.002323 | 0.004851 | 0.009304 |
| Atlas common capture | 0.000890 | 0.001932 | 0.003771 |

Regional prepared/display luminance correlation **0.9045**, with most of this low-luminance range retained. Dark-context correlation is0.9733 on688 traceable samples. This does **not** reproduce the Unreal012G black-crushing result; it must not be transferred to Atlas as a finding. No dominant loss caused by Atlas black clipping is established here. At context, filtering/few screen pixels limit discriminability; at planning the steep patch is not visible, and at close bearing0 no frozen patch is traceable. Those cases are not evidence that source signal vanished.

Darkness classification: **source darkness demonstrated; geometric stretching demonstrated; source acquisition illumination plausible but quantitatively unknown; severe Atlas display suppression not demonstrated on the traceable close patch**. The source's shadows remain in the photograph when the viewer rotates. IGOR stays suppressed, so this is not Atlas's cartographic light rotating across the source. Existing MapLibre terrain atmosphere uses a gamma2.2 fog compositor; it can alter distant appearance, but this baseline is not a fog ablation or calibrated radiometric instrument.

## Delivery, provenance and architecture feedback — MERIDIAN EVIDENCE

The isolated Vite entry point substitutes experimental terrain configuration only in its module pipeline, exposes the existing map for capture, and adds one raster layer above the unchanged common imagery. Source-derived regional product identity is pinned; outside its valid alpha support, normal common imagery remains visible. Per-pixel partial alpha is sampling of finite source support, not a feathered reconciliation collar. Product-level four-asset lineage suffices here; upstream per-pixel mosaic observations remain unknown. No full regional appearance resolver, production import, tone parameter, correction or source-specific selection branch was added.

The final run recorded430 terrain,50 imagery and126 MapTiler successful responses; zero HTTP failures/page errors. Ten failed requests were navigation cancellations (`ERR_ABORTED`). These are bounded evaluation counts, not performance benchmarks. Credentials are scrubbed. Capture/configuration identities and production code hashes are retained.

Before the accepted run, the harness represented a connected terrain tile union as separate row polygons. Whole-footprint eligibility incorrectly rejected fine tiles and selected coarse parents. That implementation defect was corrected by tracing the exact outer tile boundary, regression-tested, and the identical cameras rerun. Rejected captures are segregated externally and excluded from findings. Satellite activation also waits for style readiness, following the existing lifecycle; no production lifecycle repair occurred. Neither correction altered products or experiment parameters.

The proposed Appearance model can describe these semantics without redesign. This proof reinforces the distinction between **deliverable map-plane validity** and **informative surface observation**, exact draping-geometry revision versus upstream orthorectification geometry, and acquisition metadata knowledge versus an inferred lighting explanation. Preserve partial alpha/support, colour-transfer assumptions and actual loaded imagery levels. No new universal imagery-quality field or full runtime is warranted.

## Acceptance and next task — RESEARCH HYPOTHESES / DIRECTIONS

| Criterion | Result |
| --- | --- |
| 1. Source identity/semantics | Passed; four hashes, exact scope; acquisition/Sun/rays explicitly unknown |
| 2. Reproducible source-derived product | Passed; immutable identity, independent full rebuild |
| 3. Preparation fidelity | Passed for declared resampling/encoding; no source accuracy claim |
| 4. Regional refinement | Established by same-family parents, fixed views and bounded telemetry; transient popping not exhaustively excluded |
| 5. Useful regional gain | Demonstrated, strongest in opposed close view; not uniform or attributed solely to GSD |
| 6. Context/planning/close behavior | Established; few screen samples/context, useful planning detail, close projection constraints |
| 7. Steep support/stretch | Geometric/visual limits established; historical aerial occlusion remains unknown |
| 8. Source/display suppression | Tested on traceable patches; no dominant close-view black crushing established |
| 9. Illumination knowledge | Limits established; no justified exact Sun reconstruction |
| 10. Dominant limitation | Worst steep-face appearance: orthographic support/stretch, with source darkness; not simply delivery resolution |
| 11. One next task | Bounded acquisition/multiview-support feasibility proof; no correction authorized here |
| 12. Production preservation | Passed; no production/runtime/analytical code changes |

**Decision gate: MIXED, led by orthographic support on the difficult steep faces.** The next task is **one bounded Riffelhorn steep-face acquisition/multiview-support feasibility assessment**, limited to the same four-tile footprint and frozen steep/summit/dark patches. Use existing/authoritative lightweight observation footprint and orientation/timestamp metadata to determine whether a demonstrably different source view could support those faces, what observation identity/time/geometry is actually available, and whether a later bounded multiview comparison is technically/legally feasible. Do not acquire frames or expand support in that assessment. Stop at a verifiable feasible observation set or a documented missing/unavailable prerequisite. No automatic reconstruction follows.

This is an acquisition-support prerequisite, not another open-ended correction survey. Physical topographic correction is not justified against guessed Sun/rays, and cannot repair projection or unobserved surfaces. A source-independent tone change could change legibility, but it is not selected as a parallel branch. No hidden texture, reflectance, albedo or true source visibility has been recovered. Elevation research remains closed.

## Reproduction, evidence index and validation

All large outputs are external under `meridian-data/derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1`; captures under `experiments/atlas/riffelhorn-swissimage-baseline-v1/captures`. The JSON's eight filename/hash entries are the visual index. Direct source controls are `ordinary-source.png`, `steep-source.png`, `summit-source.png`, `dark-context-source.png`; source/probe and signal JSON files retain full numerical evidence. Do not redistribute MapTiler captures as a tile product. New data is not a normal startup/CI dependency.

From the repository root, using the existing scientific environment:

```powershell
$data='C:/Users/gbsam/Documents/Projects/meridian-data'
$python="$data/earth-lab/.venv/Scripts/python.exe"
$product="$data/derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1"
$captures="$data/experiments/atlas/riffelhorn-swissimage-baseline-v1/captures"
# Existing immutable product: verify. To prepare from retained inputs, use an absent named output.
& $python scripts/atlas/swissimage_baseline.py verify --data $data --out $product
& $python scripts/atlas/swissimage_baseline.py build --data $data --out "$product-rebuild"
& $python scripts/atlas/analyze_swissimage_baseline.py probes --data $data --out $product
# Separate terminal, explicit local legacy geometry fallback cache:
& $python scripts/atlas/terrain_proof_cache.py --root "$data/cache/atlas/riffelhorn/appearance-baseline/aws"
# With that cache running and the existing MapTiler key configured:
node scripts/atlas/capture_swissimage_baseline.mjs $data $captures
& $python scripts/atlas/analyze_swissimage_baseline.py captures --data $data --out $product --captures $captures
& $python scripts/atlas/record_swissimage_baseline.py --data $data
& $python -m unittest discover -s scripts/atlas -p test_swissimage_baseline.py
node --test scripts/atlas/test_swissimage_baseline.mjs
```

The existing rebuild sibling is immutable too: choose another absent sibling for a new run, then compare manifests/hashes; do not overwrite one. The recorder expects the retained `-rebuild` sibling. Hosted common imagery and GPU/text rendering are not guaranteed byte-reproducible; fixed cameras/configuration, source preparation and diagnostic arithmetic are reproducible. Check the accepted report and matched cameras rather than silently treating new common bytes as the same upstream release.

Validation: four imagery/100 geometry source hashes,11,459 existing geometry tile hashes,1,084 generated file hashes; complete independent imagery rebuild; independent parent arithmetic; repeat diagnostic hashes; eight Python/five Node focused tests; existing application tests, lint, TypeScript and application-only Vite build; metadata/local-reference checks and final diff. The build retains the existing large-bundle advisory. No new external-data CI dependency. Production visual AWS through TerrainHierarchy, analytical AWSz15, MapTiler satellite, IGOR suppression, exaggeration, Weather, Traverse and map lifecycle/projection are unchanged.

Contribution classes: resampling/pyramids and projection geometry are **ESTABLISHED EXTERNAL METHODS**; isolated delivery/probe integration is a **MERIDIAN ADAPTATION**; matched source/display/scale measurements are **MERIDIAN EMPIRICAL FINDINGS**; unresolved acquisition visibility, temporal confounding and projection limits are **NEGATIVE RESULTS / LIMITATIONS**; alternative-view usefulness remains a **RESEARCH HYPOTHESIS**. No standard image-processing method is presented as a Meridian invention.
