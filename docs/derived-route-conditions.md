# Derived environmental conditions v1

## Contract and execution

The pipeline is terrain → unchanged movement schedule → expected-arrival raw
weather → pure derived context → presentation. `RouteConditions.derived` is
built once after raw sampling. It contains aligned samples, family-specific
availability, coverage and typed events. Sample indexes and evidence field keys
resolve the original terrain, arrival and per-field provenance; the raw object
is not copied. Selection/hover and route-colour changes do not request data.

No weather feeds back into pace, breaks, target planning, arrival or uncertainty.
The earliest/latest arrival range remains visible but is **not** weather-sampled.
All atmospheric context remains GFS 0.25°, not a local terrain-airflow simulation.

## Vertical references

[Mapzen's Terrarium source documentation](https://www.mapzen.com/blog/terrain-tile-service/)
describes elevation in metres above/below sea level. Meridian uses its AWS
Terrarium z15 pixels, bilinear sampling and existing smoothed route elevations;
MapLibre's visual terrain exaggeration is not used in analysis. Terrarium is a
composite, not a per-pixel documented survey-datum transformation.

Both retained GFS freezing diagnostics are geopotential heights (`gpm`) relative
to mean sea level. For an explicit approximate comparison we convert them to
spherical geometric height: `altitude = R × H / (R − H)`, `R = 6,371,000 m`.
This follows the
[ECMWF explanation of geopotential/geometric height](https://confluence.ecmwf.int/pages/viewpage.action?pageId=226496389).
It does not convert an ellipsoid height or reconcile every regional geoid/datum.
The correction is ~0.16 m at 1 km and <10 m through the retained run's maximum
~7.6 km. These corrections are small compared with the display band below, but
are made explicitly. Raw geopotential values remain unchanged in provenance.

Cloud ceiling is different: the retained GFS diagnostic is **above the model
surface**, with the ~20,000 no-ceiling sentinel already removed before numeric
interpolation. [NOAA UPP ceiling documentation](https://noaa-emc.github.io/UPP/upp_v11.0.0/AVIATION_8f.html)
explains that reference and sentinel. No model-surface/orography field is in the
current nine-field catalogue. The [official GFS inventory](https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.f003.shtml)
offers surface height, but a tenth
field is unnecessary for this milestone: there is no trustworthy absolute
ceiling altitude in the current sampled contract. Ceiling stays raw, explicitly
surface-relative, and is not plotted against terrain. No cloud intersection or
combined cloud/visibility classifier is inferred; ceiling is not cloud base.

## Centralised display policies

`DERIVED_THRESHOLDS` contains these deterministic policies. None is a risk band,
probabilistic confidence interval, ice detector, or personalised threshold.

| Context | Rule | Rationale |
| --- | --- | --- |
| Freezing separation | route elevation minus converted 0°C height; below <−100 m, near −100…+100 m, above >+100 m | No standard hiking “near-level” band is claimed. A 100 m display/debounce margin is deliberately larger than 5 gpm storage precision and the <10 m spherical correction; it avoids metre-level certainty from a coarse model and composite DEM. Actual atmospheric error may be larger. |
| Freezing structure | highest minus lower >100 m: multiple levels indicated; <−100 m: inconsistent; otherwise no separated levels indicated | Inspecting all 24 retained native grids found a 95th-percentile difference of 1.12 gpm, 99th percentile 1304.64 gpm, maximum 3429.44 gpm. 96.07% differ by ≤5 gpm. The 100 m margin separates packing-scale differences from materially distinct diagnostics without claiming a unique inversion structure. |
| Comparable diagnostics | same run and selected valid time, correct units/reference | Different forecasts or missing highest level leave structure unknown, not “single”. Gust excess similarly requires matching forecasts. |
| Calm / light wind | sustained <1 knot (~0.514 m/s): calm; <3 knots (~1.543 m/s): light; otherwise compare absolute along/cross components | Anchored in [Met Office Beaufort calm/light-air conventions](https://weather.metoffice.gov.uk/guides/coast-and-sea/beaufort-scale). Directional dominance also needs a ≥1 knot difference; otherwise mixed. This avoids emphasising tiny components, not a hazard classification. |
| Model visibility | very poor <1000 m; poor 1000…<3704 m; moderate 3704…<9260 m; good ≥9260 m | [Met Office marine visibility vocabulary](https://weather.metoffice.gov.uk/guides/coast-and-sea/glossary): 2 and 5 nautical miles are 3704 and 9260 m. Reused only as distance descriptions, not mountain operating limits. Exact boundaries enter the higher-distance category. Raw approximate model visibility stays visible. |

The retained run is 2026-09-02 18Z, f001–f024. Native paired-height inspection
covered 24,917,760 pairs: 872,893 (~3.50%) differed by >100 gpm, none by <−100 gpm.
This is evidence for keeping both diagnostics, not a claim that every distinct
crossing is resolved after coarse-grid interpolation. Sensitivity at 50/200 gpm
gave 915,884/806,526 pairs; the decision does not depend on an isolated cutoff.

## Interpretations and events

- Freezing context states approximate above/near/below the lower diagnostic.
  Multiple/inconsistent levels are called out; unknown highest-level evidence
  stays unknown. Above the lower height does not establish sub-zero air at every
  level, let alone ice or snow on the route. The 2 m temperature stays separate.
- Sustained route-relative signs are unchanged: positive along-route is
  tailwind; positive cross-route flow goes right, hence wind **from left**.
  Gust is speed-only. Signed gust excess is retained only with comparable
  sustained evidence; there is no gust direction or near-calm ratio.
- Visibility context keeps the model number and category separate from cloud
  facts. Missing ceiling does not disable visibility. “Good model visibility”
  is not a claim of unlimited local sight distance.
- Freezing crossing events require progression from below −100 m to above
  +100 m or the reverse. Oscillation inside that band cannot create repeated
  events. Missing, incompatible, multiple or unknown structure resets continuity.
  Zero-sign samples bracket the change; an exact zero sample is retained.
  The bracket midpoint is an approximate route/time locator, **not temporal
  interpolation of weather**. A timestep switch can itself change the context.
  UI rounds locators to ~0.5 km and ~5 minutes and links back to the sample.
- Contiguous poor/very-poor visibility samples form a section, broken by missing
  coverage. Boundaries are known samples, not claims about conditions in gaps.
  Peak gust, strongest head/crosswind and minimum visibility are one extremum
  event each (earliest tied sample), not an alert system or severity score.

## Presentation and limitations

The inspector shows arrival/terrain first, then wind/gust, visibility/cloud and
freezing context. Raw values and provenance are expandable. Summary coverage
counts are **scheduled samples**, not a percentage of elapsed time or distance.
Freezing transitions can focus the existing map/profile point; other events
provide a small typed contract without adding an alerts panel.

The profile overlays the lower freezing diagnostic as a dashed spatially and
temporally varying line on the existing elevation axis. It is clipped to that
axis to avoid flattening a low-relief route beneath a several-kilometre forecast
height; an approximate range and off-scale notice retain that context. Gaps are
not bridged. The legend cautions that multiple levels may exist; the inspector
retains the higher diagnostic and ambiguity. No ceiling curve is drawn.

No new global field, preprocessing, network request, cache or dependency is
introduced. No production terrain or movement constants change. No ice/snow,
cloud immersion, danger score, terrain-amplified wind, or arrival-window forecast
is inferred.

## Manual acceptance

Run `npm.cmd run dev` and open the reported local URL. For retained-data checks,
choose a departure within the catalogue horizon (for this run, 2026-09-03 03:00
BST is 02:00 UTC). Import a short lowland route, a mountain route and a long
route; inspect context, expandable raw provenance, unchanged route colours and
profile focus using pointer, touch and arrow keys. On the long route, advance
departure and confirm the available-section boundary moves earlier. At 390×844,
verify panel scrolling and profile selection. Terrain/Satellite, pitch/rotation,
overview condition colours and the earlier precipitation seam need actual
browser/manual acceptance; server-rendered tests are not a substitute.
