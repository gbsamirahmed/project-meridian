# Riffelhorn steep-face observation-support feasibility

2026-10-06. Baseline `1de9e44968dcb5c2f8601c4f6844f1b626522b4b`, clean `main`, fetched origin, divergence 0/0. **PARTIAL — COVERAGE WITHOUT SUFFICIENT GEOMETRY.** Published 2023 strip coverage exists, but no target-specific calibrated observation direction or visibility is established. No aerial pixels were acquired. This closes the metadata assessment at one precise missing prerequisite, not at permission to order imagery.

## Frozen targets and acquisition gate — MERIDIAN EVIDENCE

Question: do authoritative acquisition records establish a different observation direction that could better support the existing problematic Riffelhorn surfaces? The [source-derived baseline](swissimage-source-derived-baseline.md), [appearance proposal](appearance-baseline-and-architecture.md) and [012G record](../earth-lab/riffelhorn-012g-projection-and-illumination.md) supply the targets; none was reselected. The [evidence JSON](riffelhorn-observation-support.json) pins the geometry, receipt hashes, normals, footprints and pre-evaluation gate.

The unchanged benchmark is LV95 `[2624000,1091000,2626000,1093000]`, four retained 2023 SWISSIMAGE tiles, exactly 4 km². Geometry remains original Swiss support revision `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` and regional parents revision `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`. Native 0.5 m LV95/LN02 DTM is the same underlying heightfield used for the baseline stretch diagnostic. No exaggeration is applied to physical normals. The four frozen Atlas cameras remain context 12.4/b0, planning 14.2/b0, close 16.2/b0 and opposed close 16.2/b180, pitch 55; no renderer was run or changed here.

| Target | LV95 centre / square side | Median / p95 slope | Median / p95 orthographic stretch | p95 nominal tangent footprint | Mean horizontal normal azimuth |
| --- | --- | --- | --- | --- | --- |
| Steep (primary) | `[2624805,1092330]`, 60 m | 44.0056° / 80.7066° | 1.39030 / **6.1923198567** | **1.5480799642 m** | 6.67° |
| Summit | `[2624810,1092252]`, 150 m | 52.1221° / 79.8704° | 1.62871 / 5.68583 | 1.42146 m | 105.44° |
| Dark-context | `[2624740,1092318]`, 150 m | 42.9402° / 76.5136° | 1.36600 / 4.28791 | 1.07198 m | 353.60° |

These are complete patch distributions, not one favourable normal or a previous first-visible triangle population. Steep and dark-context normals predominantly face north; summit mixes multiple directions, so its weak mean horizontal vector is not a representative single face. Eight-bin aspect counts for all cells and the stretch>2 subset are retained. The primary patch has 14,400 cells, of which 3,898 (27.0694%) have stretch>2. It is useful because source variation survives Atlas display there but steep projection support remains limited. Opposed-close b180 supplies the strongest baseline source/display comparison; b0 showed stretching without traceable patch signal statistics.

**Gate frozen before fresh candidate evaluation:** a calibrated candidate must have inverse incidence factor ≤2 (incidence≤60°) for at least half of the primary patch cells whose vertical-control factor exceeds 2, and a direction separation of at least 15° from the vertical orthographic control. This bounds foreshortening at a physically interpretable angle, applies to a substantial difficult population and excludes nearly duplicated direction. It is an experimental acquisition gate, not a universal quality/accuracy threshold. Visibility and calibrated sampling must be assessed separately. The original freeze receipt, timestamp and hash are retained. No candidate results were available when it was declared; the gate was not tuned afterward.

## Authoritative acquisition records — EXTERNAL EVIDENCE

The [official digital strip page](https://www.swisstopo.admin.ch/en/digital-image-strips) identifies 2005–2025 ADS pushbroom strips, forward/nadir/backward data, LUBIS discovery and order-based delivery. The [federal layer metadata](https://api3.geo.admin.ch/rest/services/api/MapServer/ch.swisstopo.lubis-bildstreifen?lang=en) states that ordered strip files include orientation elements. This establishes a real source-data opportunity, not an actual ray for a target cell.

A bounded `MapServer/identify` envelope query, EPSG:2056, tolerance0, limit200, returned 31 strip records; the response is below its limit. Four records are from 2023. Two exact detail requests confirmed the same limited attributes. No national strip vector archive or sample-image bundle was downloaded. Receipts retain URL, UTC retrieval time, byte count and SHA256; source-map dataset status was 20261005. Public records expose date, strip ID, footprint, purpose, GSD, length and start-map coordinates. They do **not** expose camera altitude/trajectory, calibrated per-line orientation, view-specific footprints, line timestamps or instrument serial/head. A start-map coordinate is not a 3D camera centre; a time-like ID substring is not an established UTC exposure time.

The [ADS SDK manual](https://www.swisstopo.admin.ch/dam/en/sd-web/SY847qTX5GBh/Leica-ADS-UserManual-EN.pdf), §§4 and6, documents time-dependent scan-line orientation and calibration/support files. ADS100 DEM-corrected L1 uses EOP/calibration metadata and line mapping; one frame pose is inadequate. No SDK installation or rectification occurred. The [sensor datasheet](https://www.swisstopo.admin.ch/dam/en/sd-web/YrB1lMAoTxha/ADS100-datasheet-EN.pdf) documents multiple look groups and different head configurations. Nominal sensor-family angles cannot substitute for the actual strip rays or head identity.

## Published coverage and relationship to the retained mosaic — MERIDIAN EVIDENCE

| Strip ID | Published date | Purpose / GSD | Frozen targets covered |
| --- | --- | --- | --- |
| `20230907_1035_12504` | 2023-09-07 | SWISSIMAGE / 0.25 m | All cell centres in all three patches |
| `20230821_0907_12501` | 2023-08-21 | CRYOSPHERE MONITORING / 0.10 m | All cell centres in all three patches |
| `20230821_0913_12501` | 2023-08-21 | CRYOSPHERE MONITORING / 0.10 m | None of the three patches |
| `20230823_0952_12501` | 2023-08-23 | CRYOSPHERE MONITORING / 0.125 m | None of the three patches |

All four intersect the benchmark envelope; envelope intersection is not target coverage. Coverage is tested against the published polygon at every native target cell centre and at the patch centre. Selected polygons are single-ring; unsupported multi-ring geometry is explicitly rejected instead of guessed. These samples prove published footprint coverage, **not** historical terrain visibility, per-look coverage or optical image quality.

September7 is a plausible retained-mosaic contributor by year, purpose and overlap. August21 is a separate monitoring acquisition 17 days earlier, not established as a mosaic contributor. The [SWISSIMAGE FAQ](https://www.swisstopo.admin.ch/en/orthoimage-swissimage-10) explains the dominant-year convention and unavailable detailed seamline/date breakdown. Neither strip is proven to supply the retained steep-face pixels. Their broad polygon shapes do not establish actual viewing azimuths or directional diversity. Multiple strips and a documented stereo-capable sensor are not sufficient evidence of useful multiview texture support.

## Newer generation, separately assessed — EXTERNAL / MERIDIAN EVIDENCE

The [digital aerial image page](https://www.swisstopo.admin.ch/en/digital-aerial-images) describes 2026-onward frame images and `.gori` orientation/calibration in LV95/LHN95. The [transition notice](https://www.swisstopo.admin.ch/en/new-aerial-imaging-sensor) distinguishes DMC-4S from the earlier ADS system. This cannot establish2023 observation geometry.

The official linked [text catalogue](https://data.geo.admin.ch/ch.swisstopo.lubis-luftbilder_digital/lubis-luftbilder_digital.csv) was inspected: **8,413,709 bytes / 26,601 records**, last-modified2026-09-25, published SHA256 `19560a1b890b8ddd2df1b67604f6d6c37396df54e99f679a0543d6c05955a598`, matching retained bytes. It contains frame/line/UUID, capture-time strings, sensor, focal/pixel parameters, camera easting/northing/altitude, omega/phi/kappa and calibration-certificate reference. The same digital layer was not exposed by the tested map API (HTTP400); that failed API is not interpreted as missing coverage. The officially linked CSV was used instead; no raster example or calibration/image bundle was fetched.

No catalogue camera centre lies within 20 km of the primary target. The nearest is 94,909.355m away, frame `20260423_064_090649_271_41219`, capture string `2026-04-23T09:15:59`, sensor41219/DMC-4S. It is a **remote record**, not a candidate, and no Riffelhorn coverage is inferred from it. This snapshot establishes no local alternative-generation opportunity; it does not rule out unpublished acquisitions. No flight-time timezone, rotation convention or calibrated ray is assumed from CSV field names. The national text catalogue is external; Git retains only its receipt and nearest-centre diagnostic.

## Geometry, visibility and illumination limits

**ESTABLISHED GEOMETRY / MERIDIAN ADAPTATION:** for heights h(x,y), upward ENU normal is `(-hx,-hy,1)/sqrt(1+hx²+hy²)`. Raster rows increase south; the code reverses the north derivative explicitly. Horizontal normal points downslope; aspects use LV95 grid north. Vertical-control stretch is `1/nz`. Candidate incidence would use the unit target→camera vector v and `mu=n·v`, with projected-area inverse `1/mu` only when mu>0; it is not a complete calibrated anisotropic sampling model.

The retained orthographic stretch percentiles were reproduced to 1e-12 tolerance. Native mean unit normals and aspect distributions are retained; no source elevation, height datum or terrain mesh was changed. Heightfields cannot represent overhangs, and native DTM orientation differs from exaggerated/decimated render triangles.

**Candidate range, azimuth/elevation, incidence, directional separation and tangent sampling remain UNAVAILABLE.** The frozen gate cannot be evaluated without actual candidate rays. **Visibility is UNKNOWN**; no camera centre exists for either relevant ADS candidate, so no terrain line-of-sight test was attempted. Even favourable incidence would not prove visibility. Temporal effects (17-day difference, shadows/snow and mosaic choices) remain explicit. Dates alone do not justify acquisition-Sun reconstruction; no Sun angles were computed. Exact observation support and illumination cannot be recovered from the delivered ortho or inferred from nominal sensor angles.

## Access, cost and provenance

The strip page specifies order-based provisioning with a quotation, not a free direct image download. Published aggregate density is 1.1 GB per strip-km for25cm, four-channel forward/nadir/backward data; 87.04km for the September strip implies roughly 95.7 GB if an entire strip were provisioned. This is a rough source-density estimate, **not** a quoted order size, available crop, RGB-only size or recommendation to acquire it. Individual-look/window provision, metadata-only access, price and exact file package remain unknown. TIFF16-bit and WGS84/ellipsoidal geometry are documented at product level, not verified local bytes. The newer frame product's approximate 1 GB/frame is not a 2023-strip estimate.

Official pages link [swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices); acknowledge **©swisstopo**. Open reuse and an order/provisioning charge are separate questions. No public pixel redistribution or product order occurred; exact deliverable/access terms should be confirmed before a future acquisition. Metadata retained here contains no credentials or private data.

**Appearance architecture feedback:** make source observation identity explicitly capable of a strip/view/scan-line subset as well as a single frame. Preserve observation-set identity; time-dependent camera centre/orientation, calibration, coordinate/height references, angular conventions, line mapping, native precision/timezone, footprint role, geometry dependency, derived rays/visibility/Sun, selection reason and uncertain mosaic relationship. Existing source/product/representation distinctions suffice; clarify the time-dependent form in future observation typing rather than add a runtime framework. Published acquisition records, derived geometric quantities and inferred support must remain distinguishable. No hierarchy/schema/runtime changes are made here.

## Decision and exact next prerequisite — RESEARCH HYPOTHESES / DIRECTIONS

**PARTIAL — COVERAGE WITHOUT SUFFICIENT GEOMETRY**, not GO and not evidence of no alternate observation. Two relevant 2023 footprints exist, but material incidence improvement, directional complementarity and visibility have not been established. The newer catalogue does not supply a local candidate. Do not acquire pixels speculatively.

The **single next task** is one metadata-only swisstopo request concerning `20230907_1035_12504`, restricted to the three exact target rectangles within the same 4 km² footprint. Ask whether a small pixel-free package can supply:

1. actual forward/nadir/backward look identifiers and target-specific footprint/scan-line coverage;
2. calibrated camera centres and exterior orientation/rays with line↔time mapping, timestamps/timezone, sensor/head/calibration, axes/units and height reference;
3. sufficient trajectory context for a frozen-heightfield visibility test, and whether view/substrip provisioning is available with its size/cost/rights;
4. any known link to retained 2023 SWISSIMAGE pixel contributors, explicitly allowing that this lineage may be unavailable.

Stop with a usable geometry-only reply or a documented unavailable prerequisite. No email was sent in this task; this is the exact bounded query to authorize next, not an image order. Until it resolves the gate, **no future frame set is justified**. The generic “one contributing frame plus one alternate frame” plan does not fit an ADS pushbroom source; any later acquisition would need identified views/substrips. Do not start correction, source archaeology or another provider/mountain branch from this partial result.

Contribution classes: normal/incidence and pushbroom geometry are **ESTABLISHED EXTERNAL METHODS**; bounded parsing/verification/maps are **MERIDIAN ADAPTATION**; exact polygon/target overlap, orientation distributions and catalogue distance are **MERIDIAN EMPIRICAL FINDINGS**; absent local rays/visibility/lineage are **NEGATIVE RESULTS / LIMITATIONS**; improved alternate support remains a **RESEARCH HYPOTHESIS**.

## Evidence, reproduction and validation

External root: `meridian-data/experiments/atlas/riffelhorn-acquisition-support-v1`. It contains the original freeze, bounded JSON/detail receipts, official CSV and `diagnostic/analysis.json`, `diagnostic/footprint-map.png`. The map is clipped to the frozen 4 km² benchmark, shows published footprints and the exact target patches/mean-normal arrows; it is not an image acquisition or expanded study extent. Record hashes in the evidence JSON bind these files. Metadata totals 8,640,829 bytes; larger catalogue/map stay outside Git. The CSV's provider checksum is verified; public mutable endpoints are not immutable future catalogue revisions.

```powershell
$data='C:/Users/gbsam/Documents/Projects/meridian-data'
$python="$data/earth-lab/.venv/Scripts/python.exe"
$metadata="$data/experiments/atlas/riffelhorn-acquisition-support-v1"
& $python scripts/atlas/riffelhorn_observation_support.py --data $data --metadata $metadata --out "$metadata/diagnostic-rebuild"
& $python -m unittest discover -s scripts/atlas -p test_riffelhorn_observation_support.py
# Optional later metadata-only refresh into an ABSENT directory; no image endpoints allowed.
& $python scripts/atlas/riffelhorn_observation_support.py --refresh-metadata --metadata "$metadata-refresh"
```

Offline reruns verify retained receipts, four imagery source hashes, all 1,084 prepared files and frozen diagnostic hashes, product identity, native target DEM source/VRT, both geometry manifests and production file hashes. Tests cover north/south sign, unit normals, vertical/frontal/backface incidence, polygon-versus-envelope support, invalid catalogue, fixed targets, CRS roundtrip and rejection of image endpoints without a network request. Two offline rebuilds match JSON and map hashes. Upstream rasterio/NumPy emits an existing shape-deprecation warning during read; no numerical failure. Documentation links/JSON, diff and untouched production scope are checked. No shared runtime change, hence no application test/build rerun or live-service CI dependency.

Production remains AWS visual through TerrainHierarchy, independent analytical AWS z15, MapTiler satellite-v2 JPEG/XYZ/configured 512 opacity 1, satellite IGOR suppression, exaggeration 1.45, Weather/Traverse and lifecycle/projection unchanged. The baseline sources, geometry and cameras remain frozen; regional elevation research stays closed. No frame acquisition, correction, reconstruction, texture generation or next experiment occurred.
