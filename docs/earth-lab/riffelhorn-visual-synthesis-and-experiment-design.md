# Riffelhorn: evidence synthesis and finite visual research programme

Research/design checkpoint, 2026-10-02. Starting main:
`d01218f4a285cc20b628319046ccb31e6e228859`.
**No experiment is implemented or assigned a new Lab number here.**

## Executive conclusion

The observations already support substantial mountain geometry. The current
whole-mountain output also has appearance limitations that the cliff experiments
did not test: weak geometric shading, photographic shadows and steep-face texture
stretching. More triangles are not a justified general remedy. The next useful
question is how clearly the existing measured form can be communicated, and where
the orthophoto cannot supply the required surface appearance.

Recommend two core experiments, in order: **terrain-lighting readability**, then
**orthophoto projection and baked-illumination diagnosis**. Reserve a third,
conditional experiment for **normal representation from the same terrain**. Do not
automatically use that slot. Stop and synthesise after the programme; no rolling
sequence of shader, interpolation or material experiments follows.

## What the previous Labs established

| Evidence | Established result | What does not follow |
| --- | --- | --- |
| [Lab 011](tryfan-011-observed-surface-height.md) | Paired 2021 Tryfan DSM−DTM contains coherent multi-metre differences, entangled with slope and provider classification. Structure can already exist in the DTM. | Residuals are not rock/vegetation labels or heights above true ground. |
| [012A](bluesky-012a-aerial-reconstruction.md) | A fixed 25 cm DSM retained 16 million vertices / 31,984,002 triangles. Native 25/12.5/5 cm RGB information was preserved, including tiled 5 cm imagery. Finer imagery disclosed additional close-range appearance. | Imagery does not repair geometry or unseen faces. The sources were not proved co-temporal; differences are not attributable to GSD alone. |
| [Swiss acquisition](../atlas/riffelhorn-data-discovery.md) | Complete 4 km² coverage; 2021/2022 LiDAR, derived surface raster, composite 2024 terrain and 2023 RGB mosaic. SWISSIMAGE has 25 cm native information on a 10 cm distributed grid. | Same extent/release does not mean same observation. Output spacing is not independent measurement resolution. |
| [012B](riffelhorn-012b-mountain-reconstruction.md) | Each native 0.5 m DTM/DSM mesh has 16 million unique vertices / 31,984,002 triangles, 64 chunks, no simplification or exaggeration. 50,546,426 raw returns were analysed. Broad form, ledges and ground undulations survive. | The simple comparison shader was not a calibrated terrain-lighting or photorealistic material solution. |
| [012C](riffelhorn-012c-raw-lidar-retention.md) | Sloping control median/p95 distance 0.017/0.053 m; rough ground 0.025/0.116 m; cliff 0.060/1.109 m, maximum 6.61 m. Coherent metre-to-several-metre cliff information is altered. Ordinary normals are substantially retained. | Neither universal sub-metre completeness, a blanket LiDAR normal layer, nor overhang topology is established. |
| [012D](riffelhorn-012d-adaptive-cliff-heightfield.md) | Refinement partly improves extreme tails, but worsens overall held-out agreement. Holes, bridges and fragile strips prevent acceptance of a stable replacement. Outcome E in its decision framework. | Finer sampling is not a demonstrated solution or accepted saturation resolution. |
| [012E](riffelhorn-012e-robust-cliff-heightfield.md) | Orientation constraints also fail acceptance. Reliable local planes coexist with gaps and conflicts; the intervening face is not uniquely constrained. Outcome F in its framework. | Failure does not prove either an exclusively estimator-caused problem or non-heightfield topology. |

**The Riffelhorn heightfield-reconstruction branch is closed.** No additional
interpolation, adaptive reconstruction or true-3D experiment is recommended by this
synthesis. The provider representation remains the visual control. The Swiss
DSM−DTM mean is dominated by southern ice/debris differences, with temporal and
processing confounds; it is not a global missing-rock estimate.

012C's predominantly sub-pixel displacement at about 600 m concerns its local
1280×720, 50° diagnostic. It is not a universal distance threshold for every
1920×1080 Atlas view. Local cliff defects remain real, but cannot explain faint
relief on otherwise well-represented ground throughout the AOI.

## Inspection and rendering conditions

Read the reports, measurements and validation records for 012B–012E, current Atlas
architecture, recent development log and the rendering scripts where necessary.
The acquisition catalogue remains the source/provenance authority.

Existing external products were read only, under `${MERIDIAN_DATA_ROOT}/`:

- `experiments/earth-lab/riffelhorn-012b/observed-mountain-v1/`: comparison contacts
  for overview, oblique, alpine path, loose deposits, water edge and glacier
  transition; original 1920×1080 DSM neutral/RGB pairs for overview, oblique,
  alpine path and close structural view. Original pairs were inspected at native
  resolution, not inferred from the four-times-reduced contacts.
- `sources/atlas/riffelhorn/swisstopo-2021-2024/diagnostics/`:
  `riffelhorn-distributed-10cm-crop.png`, a labelled native-grid 150 m crop.
- 012C `raw-retention-v1/cliff-180m-comparison.png`; 012D
  `adaptive-heightfield-v1/cliff-60m-comparison.png`; 012E
  `robust-plane-heightfield-v1/cliff-60m-comparison.png` and `sections.png`.
  These confirm branch closure, rather than define the whole-mountain benchmark.

The actual [012B Unreal material](../../scripts/earth_lab/unreal_riffelhorn_012b.py)
is **unlit**, with emissive output:

```text
colour × (0.65 + 0.35 × max(dot(VertexNormalWS, (0.4,-0.3,0.8660254)), 0))
```

This supplies a fixed analytic normal response, not terrain cast shadows or a
physical sun/skylight material. Normals derive from the existing height grid.
RGB is sRGB, native 2510² tiles, trilinear filtering, simple-average mipmaps,
LOD bias zero and resident full-size resources (approximately 2.15 GB per RGB
pass). There is no demonstrated hidden texture resize. Exposure adaptation is
off; atmosphere and cast-shadow additions are absent. An atmospheric haze
explanation therefore does not fit these captures. PBR roughness/specular
behaviour has not been tested; it is absent, not measured incorrectly.

## Concrete visual diagnosis

Observation means directly inspected output; hypothesis is a possible cause;
established evidence comes from implementation, provenance or measurements.

| Scale / output | OBSERVATION | HYPOTHESIS | ESTABLISHED constraint |
| --- | --- | --- | --- |
| Landscape: overview | Major ridges and gullies exist in neutral geometry, but their grey separation is slight. RGB locates paths, lake, ground-cover and rock boundaries; dark regions interrupt readable form. | The high ambient floor compresses geometric contrast; photo contrast competes with shading. | The shader multiplier spans only 0.65–1 for unit normals. Neither geometry nor atmosphere was changed between the pair. |
| Intermediate: oblique | Summit outline and large foreground ledges are visible. Grooves across neutral slopes are faint. A broad foreground face is almost black in RGB despite visible neutral geometry. | Source shadows conceal appearance; multiplying them by another lighting term cannot reveal missing reflectance. | The downloaded Riffelhorn crop already contains a large dark face and illuminated fractured rock. Exact source sun direction and pixel-level correspondence are not established here. |
| Intermediate/close: steep faces | Long vertical colour streaks follow steep foreground walls. The structural RGB view is largely dark while its neutral partner shows a continuous face. | Plan-view draping allocates little independent photographic information to steep surface area; source shadow/occlusion may compound this. | 2023 imagery is conventional terrain-orthorectified imagery. Complete XY coverage does not establish complete observation of every face. Local raster curtains are also established by 012C. |
| Close: alpine path | Neutral ground undulations and protrusions are present, but weakly shaded. RGB clearly locates branching paths and surface boundaries. Some photographic markings have little corresponding relief. | Material appearance can dominate interpretation of shallow form; close output samples imagery more finely than its independent information. | Good raw-to-raster agreement on ordinary terrain; 25 cm native imagery remains 25 cm information on its finer storage grid. |
| Loose deposits / water / southern transition contacts | Surface geometry changes some roughness and edges; RGB adds many smaller marks. Southern DTM/DSM differences are conspicuous. | Temporal change, interpolation and classification can contribute alongside representation. | These products are not co-temporal; snow/ice/water are unsuitable acceptance references for a stable-rock appearance test. |
| Local cliff diagnostics | Provider ramps/curtains differ from measured lower bands; reconstructed alternatives have gaps and fragmented panels. | Intervening shape lacks sufficient unique constraint and tested estimators reject some locally supported structure. | No accepted replacement or defensible overhang was established in 012D/E. This problem remains local and closed. |

The dark crop supports a source-illumination limitation, but does not prove that
every dark rendered pixel is a shadow rather than material, projection or sampling.
The 267 unflagged black source pixels are a separate, tiny anomaly; they do not
explain the large dark face. No source anomaly is repainted.

At landscape scale, terrain legibility and output sampling are the useful first
targets. At intermediate scale, relief contrast and steep-face appearance both
survive. At close scale, local geometry errors, photographic projection and
unsupported fine relief are separate limits. Texture sharpness cannot establish
that a small photographic fracture has measured 3D shape.

## Remaining variables and experiment allocation

| Factor | Current evidence / remaining uncertainty | Scale | Isolated test / slot |
| --- | --- | --- | --- |
| Terrain geometry | Strong ordinary terrain; measured local cliff loss. No supported reconstruction accepted. | Mainly close cliffs | Already investigated; no slot, branch closed. |
| Imagery spatial resolution | Native information preserved in 012A/B. Finer imagery can add appearance, not unseen structure. | Close; output-limited landscape | Do not repeat resolution comparison or acquire imagery. |
| Imagery projection | Steep-face streaks, conventional orthophoto, unknown face visibility. Important remaining uncertainty. | Intermediate/close | Existing RGB, geometry and diagnostic UV ruler: core experiment 2. |
| Baked illumination | Dark source crop; new shading multiplies photographed illumination. Extent of conflict remains unmeasured. | All scales, especially faces | Source/output correspondence and channel ablation: experiment 2; guard in 1. |
| Geometry normals | Native terrain supplies ordinary orientations; blanket LiDAR corrections unjustified. Shader transfer is untested. | All scales | Freeze normal input in 1; conditional representation audit/test in 3. |
| Measured LiDAR orientation | Local cliff planes exist but do not uniquely connect the surface. | Local close cliffs | No further normal/reconstruction slot; 012C/E already address this. |
| Appearance/detail normals | RGB contains appearance, not measured normals. Same-grid normal encoding might alter shading without new information. | Close/intermediate, possibly landscape | Conditional experiment 3 only for an identified representation discrepancy. |
| Material response | Current uniform analytic response, not calibrated albedo/PBR. Surface-specific roughness is unobserved. | Close/intermediate | Neutral/RGB controls in 1/2; no artistic PBR or procedural-detail sweep. |
| Terrain lighting | Limited response, no cast self-shadows. Large untested readability variable. | Whole mountain | Core experiment 1, first. |
| Atmosphere | Absent in inspected output; cannot cause current flattening. | Landscape | Keep absent; no slot. |
| Camera/display sampling | Overview target sampling about 2.23 m/pixel; close views about 7 cm/pixel. | All scales | Fixed benchmark, pixel-footprint reporting in each experiment; no camera tuning slot. |

Normal information must retain its origin. Mesh normals communicate represented
geometry. LiDAR planes are measured local orientation with support uncertainty.
RGB-derived normals would be an inference from appearance; synthetic/material
normals would be invented appearance. Neither of the latter becomes measured
terrain through a shader. Their possible aesthetic usefulness remains untested,
but is outside this observation-preserving programme.

## FATMAP evidence and its limits

Repository searches, including historical documentation, found FATMAP as a
quality/legibility reference in [product direction](../product-direction.md),
not a technical account of its algorithms. A limited external check was therefore
necessary; this does not imply a new architecture investigation.

In a [first-person historical account by PauliusLiekis, May 2021](https://www.reddit.com/r/gis/comments/nld669/using_exaggerated_lighting_to_highlight_mountains/),
the author describes increased normal-map resolution, deliberately exaggerated
terrain lighting, an in-house terrain engine and fading that lighting at close
range because it conflicts with photographed shadows. This is a self-reported
developer account, not an independently audited implementation specification.
It does not establish the normal source, precise shader, mesh topology, source
DTM/DSM resolutions or a general use of true-3D cliff meshes.

The useful untested idea is **scale-aware communication of existing terrain form**,
not copying an undocumented engine. High-resolution normal representation is a
conditional rendering question; it does not overturn 012C's measurement result.
No claim about current FATMAP operation or exact proprietary algorithms is made.

## Shared visual benchmark proposal

Freeze the complete 012B swissSURFACE3D geometry as the primary input. Historical
DTM comparisons remain references, not another changing variable. Use three core
012B cameras, plus one steep-face diagnostic control only in experiment 2.
All arrays below are exact local Unreal metres: east, south, up. Origin is LV95
`(2624000,1093000)` with LN02 vertical offset 2500 m; Unreal uses 100 cm/m.
Look-at targets determine orientation, with the historical captured pose retained
for validation. Import exact arrays/poses from [metadata](riffelhorn-012b-metadata.json)
and [camera validation](riffelhorn-012b-validation.json), not rounded table distances.

| Role / existing name | Position m | Target m | Target distance / approximate perpendicular pixel size |
| --- | --- | --- | --- |
| Landscape `overview` | `[1000,1000,4600]` | `[1000,1000,0]` | 4600 m / 2.2344 m |
| Mountain face `riffelhorn_oblique` | `[1030,398,690.280029296875]` | `[810,748,430.280029296875]` | 488.36 m / 0.2372 m |
| Close, well-represented ground `alpine_path` | `[1310,580,346.282470703125]` | `[1240,470,291.282470703125]` | 141.51 m / 0.0687 m |
| Projection control `riffelhorn_structure` | `[865,550,376.34503173828125]` | `[805,670,296.34503173828125]` | 156.20 m / 0.0759 m |

Freeze HFOV 50°, 1920×1080, 0.1 m near clip, existing perspective far behaviour,
D3D11, geometry/texture hashes, UVs, triangle diagonal, seam handling, normal input
unless deliberately varied in 3, colour decoding, mip/filter policy, exposure/tone
treatment, disabled adaptation, atmosphere absent and anti-aliasing policy unchanged.
No displacement, exaggeration, LOD or new source content. Each future isolated
experiment must copy its renderer into its own external product state; never
overwrite 012B or previous Lab products. Retain **© swisstopo**.

Before varying anything, reproduce the old neutral/RGB baseline and record hashes
and settings. Predeclare image-space regions for existing summit ridge/gully,
illuminated alpine ground/path and dark steep face. Use neutral geometry to
identify ridge versus channel; do not infer form from photographic shading.
Exclude tile-cut boundaries, snow/ice and water from acceptance. Compare native
frames and identical crops; contact sheets are navigation aids. Approximate pixel
sizes above describe the target plane, not the entire oblique image.

## Experiment 1 — lighting and geometric readability

**Question:** Can stronger, controlled illumination of the unchanged terrain make
whole-mountain ridges, gullies and shallow ground form reliably easier to read?
**Hypothesis:** The existing ambient floor hides useful geometric contrast; a
stronger response may help map distances but conflict with photographic lighting
at close distance. This is visual relief emphasis, not elevation exaggeration.

**Inputs/area:** Complete 4 km² DSM, existing normal input and SWISSIMAGE; three core
cameras. Neutral and RGB materials are paired controls in every condition.
**Variable:** Illumination components, one at a time, in three predeclared states:

1. L0: exact historical `0.65 + 0.35 × max(n·l,0)`.
2. L1: `0.35 + 0.65 × max(n·l,0)`, same direction and peak. This is a deliberately
   specified contrast test, not a physical albedo measurement or tuned optimum.
3. L2: same L1 with directional terrain visibility applied only to its directional
   term, using the unchanged surface to test self-shadow contribution. Keep the
   ambient term and direction fixed; no AO, atmosphere, exposure or extra lights.
   If the isolated renderer cannot implement this without broad changes, record
   that limit and terminate after L0/L1; do not build a lighting engine.

**Outputs:** At most 18 native frames; paired comparisons at three scales. Record
linear/display luminance distributions, clipped/dark pixel fractions and ridge/
channel contrast profiles in the frozen regions. These are diagnostics, not an
automated realism score. Verify silhouettes/depth and geometry remain identical.
Inspect whether the correct convex/concave interpretation is easier to read,
whether path-adjacent form survives RGB, and whether source shadows become worse.

**Acceptance:** A condition improves identification of the predeclared ridge and
channel at both overview and oblique scale, without reversing form or merely
crushing pixels. Close alpine and RGB checks must report any conflict. A
map-distance gain with close failure permits a scale-specific rendering conclusion,
not a universal lighting choice. Neutral gain without RGB gain points to imagery;
no neutral gain means the tested lighting is not sufficient. Do not claim missing
cliff geometry is repaired by shade.

**Stop:** One baseline reproduction, the three fixed conditions (or documented
L2 constraint), one comparison/report. No direction/contrast parameter search.
Freeze one accepted condition, or L0 if none accepted, for later experiments.
Do not create normal maps, change geometry, relight/de-shadow RGB or integrate
production rendering. Strong success can remove the need for experiment 3.

## Experiment 2 — projection and photographed illumination

**Question:** Which remaining face deficits arise from planar orthophoto coverage/
illumination rather than storage resolution or geometric shading?
**Hypothesis:** Dark and steep regions contain insufficient face appearance even
when the mesh retains form; well-lit ordinary ground is the control.

**Inputs/area:** Same geometry, UVs and RGB, fixed condition from 1. Whole-AOI
overview context; oblique, alpine and steep-face cameras. Physical diagnostic
windows are the existing 150 m Riffelhorn source crop, 60 m steep-face patch centred
at LV95 `(2624805,1092330)` and 60 m alpine patch centred at `(2625240,1092530)`.
This does not reconstruct or reinterpret the closed summit patch.

**Variable/controls:** Appearance channel only: illuminated RGB, neutral geometry,
and a labelled planar UV ruler at known 1 m/0.25 m spacings. The ruler is a synthetic
measurement aid, never observed rock detail. Also inspect source RGB in plan view;
one RGB-only emissive diagnostic can remove the added shading term, explicitly
labelled as a lighting ablation rather than another reconstructed scene.
Freeze texture filtering/mips; no colour correction, sharpening or triplanar
replacement that paints unobserved faces. At most 16 native frames, with matching
source windows, orientation/UV-footprint diagnostics and attribution.

**Measurements:** Trace frozen rendered regions into source texels, compare source
and displayed contrast, and record view/mip footprint. Under an ideal horizontal
projection, a planar surface with unit normal vertical component `|nz|` has nominal
25 cm information footprint `0.25/|nz|` along the steepest tangent and area
`0.25²/|nz|`. This geometric diagnostic becomes singular at a vertical face; it is
not actual sensor visibility, optical MTF or a calibrated accuracy claim. The
distributed 10 cm samples do not replace 25 cm independent information. Catalogue
coverage alone cannot establish occluded-face coverage.

**Decision criteria:** Matched low source contrast with visible neutral relief
supports an acquisition-illumination limit. Ruler stretching with slope supports
projection loss independently of photographic content. If useful source contrast
is lost chiefly in the render on well-observed slopes, record a filtering/sampling
uncertainty rather than blaming acquisition. If these tests disagree, mark the
cause unresolved; exact seamlines, flight rays and source albedo are not known.
Separate projection effects, local geometric curtains and temporal differences.

**Stop:** One fixed diagnostic set and source/output audit. The result is a map of
limitations, not a new texture solution. No new imagery, inferred face completion,
de-shadowing, acquisition-date harmonisation or new terrain representation. A
source-limited result can terminate the programme without using slot 3.

## Experiment 3 — conditional same-terrain normal representation

**Entry gate:** Only use this slot if 1/2 leave inadequate form readability on
well-observed, well-represented ordinary terrain, and a shader/input audit identifies
a specific normal-sampling or normal-normalisation discrepancy. If current
interpolation already preserves the same orientation, skip this experiment.
Lack of photographic rock detail alone does not satisfy the gate.

**Question/hypothesis:** Does how the renderer evaluates orientation suppress
useful shading from the already represented 0.5 m surface? The hypothesis concerns
rendering an existing signal, not missing sub-metre measurements or a new normal
source. Freeze geometry, lighting from 1, imagery, camera and display controls.

**Area/scales:** Whole-AOI context with the three core cameras; alpine 60 m window
is the close control. Do not tune on the closed summit cliff.
**Variable:** Normal evaluation only. Compare historical imported smooth normals
with normals computed per fragment from the exact mesh triangles, and, only if
the audit justifies it, a consistently normalised field using the same finite-
difference gradients from the native 0.5 m height grid. No arbitrary sharpening,
extra frequency, RGB-derived normals, raw-LiDAR correction layer or procedural map.
The latter field can be sampled finely by the renderer but adds no measured
resolution. A change in surface shading does not change its physical silhouette.

**Outputs:** At most 18 frames (three modes × neutral/RGB × three core views),
angular differences against the existing normal input, fixed-region luminance/
contrast and visible faceting/aliasing. Record storage and effective normal
sampling; identical depth/silhouette is a required control.
**Acceptance:** A reproducible gain on ordinary intermediate/landscape form without
new facets, false fine relief or destabilised close shading supports that specific
representation change. Near-identical output closes the normal-representation
question; faceting or invented-looking relief rejects it. None of these outcomes
justifies saying the LiDAR contains extra sub-metre rock normals.

**Stop:** Audit plus the bounded modes, one report. If the proposed normal field
is equivalent to the current shader, stop at the audit. Do not replace this slot
with an artistic material, roughness, procedural-detail or normal-strength sweep.

## Order, dependencies and programme terminal condition

Lighting is first because its untested response affects the complete mountain,
uses no new observations, and may expose how much useful shape is already present.
Projection comes second with a frozen lighting condition, separating hidden source
appearance from unreadable geometry. A normal representation test is conditional
on a remaining, named discrepancy; it is not a mandatory FATMAP imitation.

After the two core experiments and, only if warranted, one conditional third,
**stop for synthesis before any further terrain Lab**. Retain rejected variants
as experimental evidence, not as production features. Classify the result by scale:

- **A — Rendering sufficient:** the frozen terrain makes the predeclared major
  ridges/gullies and path-adjacent form legible at overview/oblique distance, with
  the documented close limits accepted. This establishes the benchmark use case,
  not universal photorealism or automatic architecture approval.
- **B — Source dominated:** remaining important regions lack useful face appearance
  or trustworthy shape support. Record the evidence required before contemplating
  new acquisition; do not acquire it in this programme.
- **C — Available observations insufficient for the desired appearance:** additional
  detail would require inference/invention. State that distinction; do not silently
  manufacture it or equate synthetic realism with measurement.
- **D — Scale-dependent mixture:** map readability improves, while close cliffs
  remain observation/projection-limited, or another documented mixture applies.

An unresolved result also ends the programme; it does not authorize three more
experiments. There is no automatic new numbered Lab, new phase or architecture
decision. Desired visual quality must be assessed against these concrete benchmark
tasks, not an unspecified resemblance to a tourism photograph.

## Implications, non-goals and validation

For Riffelhorn, preserve strong ordinary geometry and explicitly label close-face
limits. For Tryfan, transfer the method of separating shape, projection and shading,
not Swiss resolutions, PCA thresholds or acquisition assumptions. For Atlas, these
are experimental rendering questions; no permanent world model or service choice
follows. Photographic realism and navigation legibility are related but distinct.

No production/Weather/Traverse/App change, Tryfan change, previous Lab mutation,
new data, reconstruction, normal map, material, lighting state, capture, LOD,
true-3D topology or procedural detail was created during this synthesis.
Only this document and the development-log entry change.

Read-only SHA-256 checks preserve the 16 Swiss originals and four extracted LAS
sources, all 260/209/46/51/30 canonical 012A/B/C/D/E products and 28 recorded 012B
raw frames. Documentation checks cover internal links, referenced paths, JSON
parseability, private paths/credentials, whitespace and changed-path scope.
No application tests/build or renderer execution is necessary for these two
documentation files. Historical validation results are evidence, not new test runs.
