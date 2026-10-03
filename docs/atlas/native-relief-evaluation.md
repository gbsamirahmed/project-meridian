# Production Atlas native relief evaluation

Evaluated 2026-10-03 from clean canonical `main` at
`669fbd09239ce5cf16935e33c92749de693ea32c` (locally equal to `origin/main`).
This is a bounded production presentation evaluation, separate from the closed
012A–G programme. No terrain-source evaluation or new Earth Lab is implied.

## Decision

Retain native IGOR, geographic north-west illumination, and satellite hillshade
suppression. Increase the existing terrain-basemap hillshade strength stops by
1.5, preserving their continuous planning-scale peak and closer-view taper.
The inspected views support a modest improvement in ridge/valley definition and
slope modelling without a material loss of planning-information legibility.
This is a parameter increase, not a claim of 50% greater perceptual contrast:
IGOR's response is nonlinear. Geometry exaggeration remains **1.45**.

## Frozen baseline and controls

Authoritative files: `src/atlas/map/terrainLayers.ts`, `atlasVisuals.ts`,
`visualTerrainConfig.ts`, `AtlasMap.ts` and `satelliteLayer.ts`.

- MapLibre **6.11.2** native `hillshade-method: igor`; direction **315°**, anchor
  **map**; linear resampling. Shadow `#17211f`, highlight `#f4efe0`, both opaque.
- Configured altitude **42°** and accent `#586b66` are **ineffective under IGOR**
  in the installed fragment shader. They remain configured for historical
  compatibility, but were not treated as active baseline controls.
- Linear interpolation in zoom; no separate hillshade opacity. The strength
  parameter multiplies the prepared derivatives before IGOR's arctangent slope
  response. The native prepare shader also has its own zoom amplification below
  z15, latitude correction and quantized derivative texture. This is cartographic
  relief, not physical surface illumination or a measured surface normal product.
- Optional native elevation coloring: existing elevation ramp, opacity **0.7**
  when enabled, otherwise **0**; underneath hillshade. No ramp changes.
- Terrain basemap: OpenFreeMap Liberty with relief below geographic linework and
  labels. Satellite: unchanged MapTiler imagery, opacity 1, 180 ms raster fade,
  linear resampling, existing labels/credits; hillshade strength zero by default.
- DEM unchanged: AWS Terrarium
  `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`,
  Terrarium encoding, 256 pixels, geometry ceiling z14, visual relief ceiling z15.
  These are delivery settings, not an asserted scientific native resolution.
  Source IDs, credits and newly independent analytical z15 policy remain unchanged.
- Geometry exaggeration **1.45**; existing globe below zoom 5.5 / Mercator terrain
  at and above 5.5, transition guards and terrain stack boundary retained.
- Sky `#07111e`, horizon `#9eb4ba`, fog `#bdc9c6`; fog-ground blend 0.42,
  horizon-fog 0.72, sky-horizon 0.82. Atmosphere interpolation remains
  `(0,1), (4,0.9), (7,0.25), (9,0)`. Native ground fog is invisible below pitch
  60°, so it did not influence the 0°/45°/55° comparison views. High-pitch fog
  interactions were not separately evaluated.

| Zoom | Baseline IGOR strength | Selected strength |
| --- | --- | --- |
| 5.5 | 0 | 0 |
| 7 | 0.06 | 0.09 |
| 9 | 0.20 | 0.30 |
| 11 | 0.36 | 0.54 |
| 12 | 0.30 | 0.45 |
| 13 | 0.24 | 0.36 |
| 14 | 0.22 | 0.33 |
| 15 | 0.20 | 0.30 |
| 16 and higher | 0.20 | 0.30 |

## Native alternatives and evidence boundaries

Installed implementation inspected: MapLibre's
`src/shaders/glsl/hillshade.fragment.glsl`, `hillshade_prepare.fragment.glsl`,
`src/webgl/program/hillshade_program.ts`, `src/webgl/draw/draw_hillshade.ts`,
`src/style/style_layer/hillshade_style_layer.ts` and `src/webgl/render_to_texture.ts`.
These are dependency implementation facts, not Meridian perceptual evidence.

The [literature record](../research/literature/terrain-representation.md#terrain-visualization-and-cartographic-lighting)
supplies established cartographic motivation: multiple directions can reduce
single-direction bias, while contrast must support landform comprehension.
MapLibre's multidirectional implementation averages basic cosine-shading colors
from independent lights; it is **not** the USGS oblique-weighted algorithm.
[012F](../earth-lab/riffelhorn-012f-terrain-lighting.md) motivates testing rendering
with geometry held constant, but does not establish these production settings.

The controlled comparison used only four configurations:

| ID | Method / direction | Strength | Color treatment |
| --- | --- | --- | --- |
| baseline | IGOR / 315° map | old curve | existing opaque colors |
| igor-strong | IGOR / 315° map | old curve × 1.5 | existing opaque colors |
| multi | multidirectional / 225°, 270°, 315°, 0° map, altitude 30° | old curve | existing shadow/highlight RGB with alpha 0.35 |
| basic | basic / 315° map, altitude 30° | old curve | same alpha 0.35 |

30° makes flat ground neutral in the native basic/multidirectional transfer
(`sin(30°)=0.5`). Different methods do not have equivalent strength semantics.
An initial opaque ×1.5 cosine/multidirectional probe was too dark; the restrained
configuration above was used for the accepted comparisons. Initial captures also
exposed stale in-place paint updates and are not the controlled acceptance record.
Legacy `standard` and slope-emphasizing `combined` were inspected in source but
not visually swept: neither was needed to answer the bounded comparison.
No shader, cast shadow, derived product, physical lighting or detail normal was added.

## Representative conditions and reproducibility

Headless Playwright Chromium, 1440×900, device scale 1, en-GB, Europe/London.
Production map code, worker, AWS DEM, OpenFreeMap and configured MapTiler imagery
were used. No mocked terrain or imagery. Every variant retains the exact camera,
DEM source specifications, terrain configuration and queried center elevation.
Successful AWS tile responses are hashed in the capture manifests.

| Purpose / scene | Center (longitude, latitude) | Zoom | Pitch | Bearing |
| --- | --- | --- | --- | --- |
| Tryfan landscape | -3.999, 53.115 | 9.4 | 45° | 0° |
| Tryfan planning | -3.999, 53.115 | 11.4 | 45° | 0° |
| Tryfan close | -3.999, 53.115 | 13.2 | 55° | 0° |
| South Downs rolling control | -0.766, 50.908 | 11.4 | 45° | 0° |
| Cambridge flat control | 0.12, 52.20 | 11.4 | 0° | 0° |
| Tryfan rotation | same planning camera | 11.4 | 45° | 90°, 180° |
| Tryfan elevation coloring | same planning camera | 11.4 | 45° | 0° |
| Snowdonia route, rain off/on | -4.073, 53.102 | 11.4 | 45° | 0° |
| Satellite | same Tryfan planning and close cameras | 11.4 / 13.2 | 45° / 55° | 0° |

These scales describe evaluation purposes, not universal zoom categories.
Baseline/strong IGOR/multi were compared throughout. Basic was a limited
single-direction control at Tryfan planning and South Downs. Satellite compared
suppression with IGOR at old strength ×0.2 and multi at old strength ×0.2,
retaining multi's alpha 0.35. No stronger satellite treatment was pursued.

The route is the checked-in non-private `scripts/route/fixtures/snowdonia-smoke.gpx`,
imported through normal Journey UI and prepared with the unchanged real analytical
sampler. Displayed facts remained 3.6 km, 253 m ascent, 308 m descent and about
1 h 35 min across the comparisons. Precipitation is an explicitly **synthetic**,
uniform 1 mm / 1 h numeric tile fixture through the unchanged production Weather
renderer (approximately 0.62 effective overlay alpha). It checks a substantial
color wash and route/label legibility, not forecast correctness, patch boundaries,
wind particles or every combination of overlays. No external data root was read.

The bounded reproducer is `scripts/atlas/capture_native_relief.mjs`. Run from the
repository root, with installed Chromium and normal network access, one phase at
a time, without a concurrent build/test/browser workload:

```sh
node scripts/atlas/capture_native_relief.mjs core
node scripts/atlas/capture_native_relief.mjs rotation
node scripts/atlas/capture_native_relief.mjs overlays
node scripts/atlas/capture_native_relief.mjs satellite
node scripts/atlas/capture_native_relief.mjs verify
```

It uses a capture-only Vite transform to access the map; no hook or experimental
control enters production. Output is ignored `test-results/atlas-relief/`: 38 main
comparison PNGs plus three fresh-production PNGs, JSON camera/style records,
image and DEM response hashes, redacted network diagnostics and browser version.
`verify` checks the selected default without paint overrides and repeated
2.8 → 5.5 → 2.8 → 11.4 projection/terrain transitions. Satellite requires the
existing optional key; missing imagery is reported rather than substituted.
Live providers/browser revisions mean future whole-image byte equality is not
promised. The fixed cameras/settings and manifests provide reproducibility;
qualitative inspection is not a blinded user study or universal readability score.
No page exceptions or HTTP errors occurred. Diagnostics include `ERR_ABORTED` tile
request cancellations during view/visibility/projection changes; these are retained,
not misreported as provider failures or hidden. Captured views settled with valid
terrain.

**Capture limitation discovered:** some scalar paint updates left cached terrain
textures unchanged. Native RTT fingerprints track source revision, source tiles,
zoom and visible layer IDs, rather than every paint value. Comparisons therefore
use zero-duration hillshade-strength transitions and a public hidden/visible
layer cycle, waiting for loaded tiles and rendering to settle. The reproducer
also waits for native `idle`. Fresh-production captures independently confirm the
selected appearance. This is an evaluation precaution, **not a shipped lifecycle
workaround**. Live paint-update/cache behavior is a separate issue if subsequently
investigated; this change does not rewrite it.

## Findings and limits

**Meridian evidence (M), within the cameras and controls above:**

- Landscape: stronger IGOR improves recognition of mountain masses and connected
  valleys while roads and place labels remain readable. It does not add geometry.
- Planning: clearer ridge shoulders, valley walls and connected slope transitions;
  this is the strongest practical gain. Multidirectional relief shows some additional
  orientation-dependent boundaries but emphasizes narrower dark bands and gives
  weaker continuous modelling of broad slopes in the restrained configuration.
- Close: stronger IGOR has a smaller useful gain in slope definition. Existing smooth
  geometry and some banding remain. It does not recover rock, channels or ledges
  absent from the current source/rendered representation.
- Controls: South Downs valleys and scarp structure become clearer without an
  excessive general texture wash. Cambridge remains quiet; slight source texture
  is still visible. More contrast is not a license to classify that texture as landform.
- Rotation: the IGOR gain persists at 90° and 180°. Map-anchored light moves on screen
  with the geography; it is not screen-relative lighting. Multidirectional light is
  less dependent on one azimuth but still has directional bias with this north-west
  group. Neither treatment proves immunity to perceptual relief inversion.
- Optional elevation colors: stronger IGOR remains usable with the existing ramp;
  labels and water remain distinct. Multi can accentuate edges here, but does not
  supply a consistently better default across the other views.
- Route/rain: the stronger relief remains supporting context beneath the substantial
  blue wash. Route casing, endpoints, roads and labels stay legible. No Weather or
  Traverse changes were required.
- Satellite: weak treatments slightly alter tone but do not establish materially
  better comprehension than the photographed shading. No severe double-lighting
  artifact was established by this small test; equally, it does not justify adding
  synthetic illumination globally. Keep suppression.

This accepts a small IGOR presentation improvement, not a general rejection of
multidirectional cartography, nor a decision about future scale representations.
Existing continuous zoom emphasis is sufficient for this change. Source LOD,
smoothing and quantization remain technical constraints; no terrain generalisation
or separate landscape/close representation has been introduced.

Later questions remain separate: broader human/region coverage; high-pitch fog and
other Weather combinations; live paint/RTT caching; alternative sources; and physical
appearance recovery. Lighting cannot repair displaced geometry or unobserved
appearance. Closed Riffelhorn interpolation/reconstruction and blanket detail-normal
branches remain closed. The bounded 012G brightness result is not evidence against
physically informed appearance recovery. None of these directions is implemented here.
