# Atlas global reference and stable-overlap assessment

2026-10-04. Baseline: clean `main`, `68fccda1516515bf08ad63867ace8696362ad796`,
local `origin/main` divergence 0/0. No remote refresh was needed for that check.
This is a bounded source/overlap assessment, not reconciliation or a terrain
hierarchy. **Production remains unchanged on AWS Terrarium.**

## Conclusion and decision boundary

**MERIDIAN EVIDENCE + EXTERNAL EVIDENCE:** recommend **Copernicus DEM GLO-30 as
the candidate common/coarse reference** for the next local preparation step.
It is substantially more interpretable than the hosted AWS derivative, permits
derived delivery, and has a tighter relationship to the authoritative Swiss
surface on independently selected terrain. This recommendation concerns the
published elevation product; it does not select a tile hosting service, assume
the latest release was tested, certify local accuracy or accept a Swiss seam.

Distinguish **global reference terrain** from **best available visual terrain**.
The former supplies accountable common/coarse support; the latter may preserve
better regional information at useful scales. This is a documented role
distinction using existing source/product types, not a new resolver or runtime
dependency. Analytical elevation is a third, independently configured policy.

**RESEARCH HYPOTHESES / DIRECTIONS:** the smallest next implementation is one
bounded, deterministic **local Copernicus common/coarse delivery product**, using
an explicitly frozen release, known height semantics, source-edge/ocean/missing-
land rules and measured average-parent behavior. It should cover the Swiss asset
and sufficient perimeter context. Initially keep it separate from pure Swiss
terrain: no blended heights, seamline or general source selection. If moving to
current CDSE inputs, first record that exact release and rerun this overlap check;
the tested 2021 mirror must not silently stand for a newer product. Integration
still needs an explicit height and support policy; this task does not perform it.

## Reference role, criteria and candidate set

The common/coarse foundation should have broad land coverage, explicit surface
and reference semantics, accountable lineage, stable release/assets, accessible
inputs, compatible derivative rights and practical parent generation. It need
not be the most detailed surface everywhere, analytical ground truth or the
terrain shown at every scale. Honest gaps and limitations matter more than a
sharp picture or the lowest single RMS.

The [protocol](global-reference-protocol.json) was frozen before acquisition and
numerical results. It specifies semantic/vertical clarity, identity/provenance,
coverage, rights, stable-overlap/registration evidence, coarse support and
operational feasibility as decision criteria. Only **AWS baseline and Copernicus
GLO-30** were investigated. One realistic alternative suffices: no extra DEM was
added to make a larger table, and Mapterhorn is relevant prior evidence rather
than another candidate endpoint.

| Requirement | Current hosted AWS Terrarium | Published GLO-30 / tested COG selection |
| --- | --- | --- |
| Surface/height semantics | Heterogeneous derivative; hosted height reference not established | Edited DSM; declared EGM2008 metres |
| Provenance | Contributor hints, incomplete normalization/processing lineage | Published observation/editing/filling lineage; per-post identity incomplete in retained COGs |
| Revision/reproduction | Cached tile hashes and object versions possible; whole hosted release unclear | Named publication and immutable selected file hashes; mirror sub-release remains unspecified |
| Coverage | Existing broadly usable land/ocean visual fallback | Broad published land coverage; older public mirror has restricted/missing land; no bathymetry |
| Local stable overlap | Broad and aspect-dependent residuals | Much tighter robust spread, with important outliers and registration limitations |
| Coarse support | Existing working visual hierarchy, scientifically opaque source mixture | Documented averaging; retained overviews numerically checked; final Atlas hierarchy not built |
| Rights | Multiple contributor-specific credits/terms | GLO-30 F licence permits derivative delivery with explicit obligations |
| Decision | Retain production; do not presume physical common reference | Preferred reference candidate; not adopted or globally certified |

## External source review

**EXTERNAL EVIDENCE**, primary sources accessed 2026-10-04:

Copernicus publishes an edited **DSM**, including surface objects rather than
bare earth. Its principal basis is TanDEM-X stereo radar; acquisition primarily
December 2010–January 2015, with other-epoch filling. The documented horizontal
reference is WGS84-G1150, geographic distribution identified as EPSG:4326;
heights use EGM2008 (EPSG:3855), metres. GLO-30 is a one-arcsecond latitude grid,
not independent 30 m observations or metre-scale terrain. Longitudinal posting
varies at higher latitudes. The published global accuracy specifications are
not guarantees for these mountain pixels.
[Official collection](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM),
[handbook issue 5](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf).

Water/hydrological editing, void filling and radar/ice effects distinguish this
surface from an unedited contemporaneous DTM. Named fills include SRTM, ASTER,
AW3D30 and national data. EDM, FLM, HEM and WBM ancillary layers exist; the two
public COGs retained here do not carry those layers or exact per-post epochs.
HEM concerns random measurement error, not every systematic error or edited
height. Dry-firn penetration and differing observation dates complicate glacier
comparison. None of these causes can be inferred from one residual map alone.
[Product handbook](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf).

The **tested distribution** is Sinergise's public COG mirror, explicitly based
on a **2021 release**, without an established exact sub-release. The official
catalogue now lists releases through 2024_1; current CDSE distribution and this
older mirror must remain distinct. No credentials or complete global dataset
were accessed. The mirror generally has no updates except changes to its public
tile list. Missing objects can be ocean or unavailable/restricted land; only
established ocean support can justify zero sea-surface context. It supplies no
seafloor bathymetry.
[Mirror registry](https://registry.opendata.aws/copernicus-dem/),
[official release catalogue](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

The mirror removes duplicated eastern columns and southern rows, preserves
base float32 elevation posts, compresses losslessly and builds averaged
overviews. Its documented tile width changes with latitude. Here both files
are 3600² with `AREA_OR_POINT=Point`. GDAL's transform already places outer
corners half a posting away from integer-degree centres; our sampler subtracts
half a pixel once, not twice. Files were mosaicked before interpolation across
46°N. Geographic posting and Web Mercator delivery are different contracts.
[COG conversion documentation](https://copernicus-dem-30m.s3.amazonaws.com/readme.html).

### Fair AWS baseline

The public Terrain Tiles service is a derived Mapzen/Tilezen mosaic, not one
global measurement campaign. Public documentation lists sources including
3DEP, ArcticDEM, CDEM, UK LiDAR, EU-DEM, SRTM, GMTED and ETOPO; DTMs, surface
models and bathymetry occur in different regions/levels. The public source
description dates v1/v1.1 builds to 2016/2017, with updates as needed rather
than a regular revision cycle. Terrarium is 3857/XYZ, RGB heights in metres.
[Dataset registry](https://registry.opendata.aws/terrain-tiles/),
[source/zoom composition](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md),
[format documentation](https://github.com/tilezen/joerd/blob/master/docs/formats.md).

**MERIDIAN EVIDENCE:** all **169** retained z15 tiles used over the expanded AOI
name `eudem/eudem_dem_5deg_n45e005.tif` in contributor headers and have November
2017 Last-Modified dates. Their hashes, original headers and object versions
remain in the external assessment record. These are headers from bounded
October 2026 acquisition, not proof of an immutable complete service revision.

Upstream EU-DEM is described as SRTM/ASTER-derived surface terrain, nominal one
arcsecond, with ETRS89/EVRS2000 (EGG08) semantics. That establishes an upstream
description, **not the currently hosted Terrarium vertical reference**. The
public documentation's EGM96 statement specifically covers Skadi; it does not
establish normalization of every Terrarium input. The available public code
does not reconstruct exact ingestion of this EU-DEM object. Full resolution,
filtering, height normalization and revision lineage therefore remain unknown.
[EU-DEM validation](https://ec.europa.eu/eurostat/documents/7116161/7172326/Report-EU-DEM-statistical-validation-August2014.pdf),
[hosted formats](https://github.com/tilezen/joerd/blob/master/docs/formats.md).

AWS remains a useful production visual fallback. Contributor-specific
[attribution and terms](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
must survive derivative use; server code licensing is not a blanket data
licence. Unknown hosted height lineage makes it a weak physically interpretable
common reference even where its local visual detail is good.

## Frozen inputs and reproduction identity

**MERIDIAN EVIDENCE:** [acquisition record](global-reference-acquisition.json)
contains every URL, access timestamp, full selected-file SHA-256, bytes and HTTP
metadata. Inputs total **215,838,141 bytes** (including supporting documents,
inventories and geoid grids); the two DEMs total **84,371,542 bytes**.

| Retained input | Identity / scope |
| --- | --- |
| `Copernicus_DSM_COG_10_N45_00_E007_00_DEM.tif` | SHA-256 `638c155dd9a5f0b7ee818146def740093da33cee4606071b2bbf7ce3fa00ab95` |
| `Copernicus_DSM_COG_10_N46_00_E007_00_DEM.tif` | SHA-256 `426e3d1492d94e4f23d444843f852ff5be675da5c4c14e661b5642006864047d` |
| GLAMOS SGI1973 r1976, SGI2016 r2020, SGI2023 r2026 | Three official glacier footprint inventories; exact ZIP hashes/layers retained |
| ESA WorldCover 2021 v200 | Bounded source-pixel window of `N45E006`; retained crop hash and upstream ETag, **full upstream SHA unknown** |
| CHGeo2004 ETRS89/LN02 and NGA EGM2008 2.5′ | Frozen PROJ-distributed grid files and upstream descriptions |
| Expanded Swiss source/product | Same 100 official 2024 source hashes and product identity `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` |
| AWS | Same cached z15 input estate; 169 object hashes, no new DEM provider or resampling policy |

The existing Swiss product was fully verified at baseline: all 100 sources and
11,429 delivery tiles. The assessment rechecks all source files, source VRT,
candidate/mask/grid hashes and acquisition identity. Large inputs and outputs
remain outside Git. No Swiss terrain was acquired or regenerated.

External paths beneath `${MERIDIAN_DATA_ROOT}`:

- Inputs: `sources/atlas/riffelhorn/global-reference-assessment-v1/`.
- Original source VRT: `derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/source-mosaic.vrt`.
- Outputs: `experiments/atlas/global-reference-assessment-v1/`: `assessment.json`,
  `fields-and-mask.npz`, `reference-fields.png`, `reference-profiles.png`.
- Lightweight Git outputs: protocol, acquisition, measurements and
  [owned model examples](global-reference-metadata.json).

Assessment identity:
`6be6712a8b099ca06127be1fa953402dfd1b9183db11609810aba832d16dc045`.
Independent repeat matched this identity and **all 18 array hashes**. Output
arrays/mask, pipeline and software identity matter; wall-clock times are not
scientific revision identifiers. Diagnostic outputs are approximately **10.8 MB**,
not a terrain tile pyramid. No normal CI/startup dependency on these files.

## Stable-overlap method

**EXTERNAL EVIDENCE:** Nuth & Kääb separate registration from change by using
stable, sloping, aspect-diverse terrain. Translation creates a slope/aspect
signature; flat ground cannot establish its horizontal components. Later
gradient-based treatments explain the relationship and limitations of linear
models. Spatial correlation and slope/curvature-dependent errors preclude
treating every grid cell as an independent equally precise observation.
[Nuth & Kääb 2011](https://tc.copernicus.org/articles/5/271/2011/),
[Li et al. 2023](https://tc.copernicus.org/articles/17/5299/2023/),
[xDEM stable-terrain/error practice](https://xdem.readthedocs.io/en/stable/advanced_examples/plot_standardization.html).

**MERIDIAN EVIDENCE:** a 400², **25 m LV95** diagnostic grid spans the retained
10 km square. Swiss heights are area-averaged over 50² native 0.5 m cells.
Copernicus posts are bilinearly sampled from the geographic mosaic. AWS is
pixel-centred cross-tile bilinear z15 sampling from frozen cache. Equal
horizontal sampling does **not** equalize underlying measurement footprints.
No source pixels or analytical sampler were altered.

Primary stable-terrain **candidate** support is defined before differencing:

1. ESA WorldCover class 60 (bare/sparse vegetation) only; any other class in a
   diagnostic cell excludes it. Forest, grass, buildings, snow/ice and water
   therefore cannot silently dominate DTM/DSM comparison. Missing support also
   excludes a cell. Class 100 moss/lichen is conservatively excluded, not called
   unstable by definition.
2. Union of GLAMOS 1973, 2016 and 2023 glacier outlines, all-touched rasterization
   plus a **250 m** buffer. Historical outlines conservatively guard formerly
   glaciated terrain across differing acquisition epochs; they are not a claim
   that deglaciated ground remains ice today.
3. At least **200 m** from the Swiss source-selection edge.
4. **5–40°** slopes measured on Swiss 25 m terrain smoothed at sigma 30 m; avoids
   flat fit degeneracy and strongly representation-sensitive extremes.

[GLAMOS inventories/CC BY 4.0](https://doi.glamos.ch/),
[WorldCover 2021 v200/CC BY 4.0](https://esa-worldcover.org/en/release-worldcover-map-2021).
These thresholds are conservative diagnostic choices, not production terrain
classification rules. Rockfall, persistent snow, dead ice, surface objects,
classification error and unknown per-cell epochs remain possible. No final
stable-ground mask or temporal-change attribution is claimed.

**11,205 cells / 7.003 km²** qualify. Counts NW/NE/SW/SE are
1,960 / 6,379 / 2,567 / 299. Only **738 cells / 0.461 km²** lie inside the
protected circle. This selection provides useful comparison support in several
sectors and all aspect bins, but not uniform support for a perimeter correction.
Two upslope-azimuth bins (225–270° and 270–315°) have relatively little support.
The reported aspect bins use gradient/upslope azimuth; conventional downslope
aspect is 180° opposite. Translation signatures use the explicitly signed gradients. Whole-field and
excluded glacier/cover results are retained; inconvenient residuals were not
discarded. Primary statistics have no residual-based clipping.

Planned sensitivities use ice buffers 100/500 m and slope ranges 3–45°/10–35°.
Huber weights affect the translation fit only; all original differences remain
in the statistics. Exclusion reasons and masks are individually retained.
A focused synthetic test protects against GDAL interpreting a valid binary
exclusion value as nodata during conservative class resampling.

## Vertical-reference handling

**EXTERNAL EVIDENCE:** swisstopo publishes CHGeo2004 variants relating ETRS89
ellipsoidal heights to LN02/LHN95; the LN02 variant is required here. PROJ also
distributes NGA-derived EGM2008 grids. These provide a documented diagnostic
route rather than an arbitrary fitted datum offset.
[swisstopo geoid](https://www.swisstopo.admin.ch/en/geoid-en),
[Swiss grid lineage](https://cdn.proj.org/ch_swisstopo_README.txt),
[NGA grid lineage](https://cdn.proj.org/us_nga_README.txt),
[PROJ vertical-grid operation](https://proj.org/en/stable/operations/transformations/vgridshift.html).

**MERIDIAN EVIDENCE:** with network disabled and both frozen grids explicitly
available, PROJ exposes one non-ballpark compound operation from
`EPSG:2056+5728` to `EPSG:4326+3855`. The complete pipeline is retained in
measurements/metadata, including ellipsoid/frame steps. Combined stated
accuracy is **unknown (-1)**, despite the documented centimetre-level Swiss
geoid component; EGM2008 grid interpolation and frame/epoch uncertainty remain.
The 2.5′ posting describes the geoid grid, not terrain detail.

Swiss EGM2008-diagnostic minus original LN02 heights ranges **+0.166…+0.752 m**,
median **+0.394 m**. Numerical inverse closure is below a micrometre; that checks
implementation, not real geodetic accuracy. Compound versus ordinary 2D
horizontal coordinates differ by 0.039–0.100 m. Copernicus sampling uses the
compound coordinates consistently. This small distinction cannot account for
the metre/tens-of-metres residuals. Both raw and transformed comparisons are
preserved. Neither Swiss source/product nor AWS is height-corrected. No AWS
datum transformation is defensible from its presently established lineage.

## Numerical comparison and fields

**MERIDIAN EVIDENCE:** differences are **Swiss minus candidate**, metres.
NMAD is 1.4826 times median absolute deviation. RMS includes all selected
outliers; pixels are correlated and sample counts are not independent accuracy
trials. The Swiss DTM is the authoritative higher-quality regional comparator,
not declared infallible ground truth.

| Primary candidate support | Mean | Median | NMAD | RMS | 5th–95th percentile |
| --- | ---: | ---: | ---: | ---: | ---: |
| Swiss LN02 − AWS, unknown datum | +7.85 | +7.85 | 9.46 | 14.88 | −9.94…+25.23 |
| Swiss LN02 − Copernicus EGM2008, raw | −0.02 | −0.60 | 1.78 | 5.93 | −4.51…+5.42 |
| Swiss EGM2008 diagnostic − Copernicus | +0.37 | −0.22 | 1.79 | 5.93 | −4.14…+5.77 |

Across all 100 km², AWS median/RMS is +1.35/30.08 m; Copernicus common-height
diagnostic is −1.41/19.77 m. Those whole-field results include ice, vegetation,
extreme slopes and temporal/representation differences. They must not be read
as stable-ground accuracy.
These are the frozen 25 m diagnostic statistics, not replacements for the prior
10 m support-product measurements; averaging/sampling support differs.

The AWS difference map retains the broad southern/eastern negative corridor
seen previously. Copernicus also disagrees strongly there, although its
surrounding ordinary terrain differences are generally much smaller. Much of
the corridor overlaps excluded glacier/snow support. Glacier-buffer regions
have RMS 39.92 m (AWS) and 26.86 m (Copernicus diagnostic). Observation epochs,
radar penetration, glacier change and measurement representation are plausible
contributors; their separate shares are **not measured here**. The small known
height adjustment does not explain the broad corridor.

On primary support, Copernicus quadrant medians are −0.44…−0.11 m and NMAD
1.25…2.15 m; AWS medians +6.58…+9.79 m and NMAD 8.43…10.46 m. Mask sensitivities
retain the finding: Copernicus median −0.33…−0.16 m, NMAD 1.70…1.91 m, RMS
3.64…6.64 m; AWS median +7.57…+8.24 m, NMAD 9.13…9.77 m, RMS 12.73…15.55 m.
The 500 m ice guard reduces tails, but does not eliminate them.

Rougher terrain has greater spread: Copernicus NMAD grows from roughly 1.35 m
in the least-rough bin to 5.59 m in the roughest; AWS from 5.37 to 15.60 m.
Slope and elevation bins are also retained. There is no accepted universal
elevation-dependent correction or inferred causal label for these patterns.

**Negative finding:** the primary-mask largest Copernicus discrepancy is still
**+116.78 m** near LV95 `[2624737.5,1092262.5]`, on the narrow benchmark ridge;
AWS reaches +173.16 m at that cell. Coarse slope screening does not identify
every sub-grid ridge/steep-face representation problem. Protected-interior
primary Copernicus median/NMAD is +0.31/1.70 m but RMS **17.97 m**. A tighter
global relationship cannot replace the superior Swiss interior or establish a
seam through it. This outlier remains in every relevant statistic.

Masked pair correlations are about 0.65 east-west at 100 m for Copernicus,
0.31 at 250 m and 0.03 at 1 km; north-south correlations decay faster. AWS has
similar short-range correlation on this restricted support. This describes
residual correlation within the selected terrain, not a unique global error
length scale or proof the earlier whole-field broad disagreement vanished.

Maps and profiles are external products; no browser source switch or visual
beauty contest was performed. Source review, fields, support and numerical
registration address this task without repeating the Mapterhorn evaluation.

## Registration diagnostic

Robust first-order regression uses
`Swiss − global ≈ dx × dSwiss/dEast + dy × dSwiss/dNorth + intercept`.
It is a **translation signature** related to slope/aspect co-registration
practice, not the full iterative Nuth & Kääb algorithm, an accepted displacement
or a correction applied to terrain. Statistics before and after fitted
residual removal are separately named; no product is shifted.

AWS whole-support signature is approximately **(+9.58, −10.57) m**, intercept
+5.40 m. Sector estimates differ: east +0.89…+13.91 m, north −12.21…+0.77 m.
Spatial held-out NMAD improves only modestly (about 9.3–9.6 to 8.1–8.8 m).
Registration may contribute, but a rigid shift does not account for the
structured and resolution-dependent AWS disagreement.

Copernicus diagnostic signature is **(−0.85, +2.89) m**, intercept +0.38 m.
The north component is relatively consistent across sectors (+2.64…+4.07 m),
but the east component changes sign (−2.40…+2.29 m). Alternating independent
1 km training/held-out blocks give east −0.23/−1.40 m, north +2.95/+2.74 m;
held-out NMAD changes from 1.77–1.81 to 1.22–1.24 m. The ~3 m magnitude is
plausible against published horizontal specifications, not proof of a uniform
physical shift. Surface smoothing, footprint/epoch and frame differences can
also create gradient-correlated residuals. **No correction is accepted.**

The broader asset is sufficient for this bounded reference recommendation;
stable support is not sufficient to assert uniform local registration or a
legitimate transition around all edges. A future correction would require
locally verified stable support, resolution-aware fitting and independent
validation, not an RMS-driven adjustment.

## Coarse-scale feasibility, rights and operational cost

**MERIDIAN EVIDENCE:** retained COG overview factors 2/4/8 were compared with
direct block means of base posts. RMS disagreement is below 0.00006 m and
absolute differences below 0.001 m, consistent with float32 rounding. This
establishes reproducible local averaging, not a completed world-scale
MapLibre hierarchy or continuity with Swiss children. Adjacent source files
are mosaicked before sampling; no half-pixel seam or duplicate row is added.

The frozen public tile list contains **26,450** files. Applying the documented
latitude-dependent dimensions gives roughly **0.892 TB of uncompressed base
float32 arrays** for that older public selection, excluding overviews/masks.
Compressed global volume is not estimated from two alpine files. A fully
populated XYZ pyramid through z12 has a theoretical 22,369,621 tile positions;
that upper combinatorial count is not a storage forecast or chosen zoom
policy. Ocean omission, land gaps, polar/Web-Mercator limits, ancillary masks,
compression, caches and release updates need explicit future decisions.
No global infrastructure or mirror was built.

**EXTERNAL EVIDENCE:** GLO-30 **F** terms permit reproduction, distribution,
adaptation and combination without a non-commercial-only restriction. Derived
hosting is feasible subject to the full attribution, liability, non-endorsement
and downstream obligations. The applicable modified/unmodified credit text is
in Article 6; a short metadata summary is not a legal delivery notice.
[Free/open licence, pages 20–22](https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf).
GLAMOS/WorldCover use CC BY 4.0; the Swiss/NGA transformation-grid descriptions
state CC0/public-domain terms respectively. Source-specific terms remain
attached to inputs; no software licence substitutes for terrain rights.

Mapterhorn previously demonstrated useful global browsing and regional detail
with Copernicus fallback. Meridian-controlled source/product preparation would
improve revision identity, parent generation, vertical accounting and processing
provenance. It would **not** automatically recover unretained per-post upstream
observations or solve DSM/DTM, temporal or regional-boundary disagreements.

## Metadata and unchanged production

[Model instances](global-reference-metadata.json) use the existing Atlas types:
retained GLO-30 source selection, Sinergise COG derivative, and explicitly
transformed Swiss diagnostic. Original Swiss LN02 semantics stay intact.
Immediate contributor completeness does not imply complete observation/fill
lineage. The diagnostic support mask has a hashed external asset reference;
its comparison validity is separate from unknown transition support.
The existing AWS example keeps unknown hosted vertical/revision semantics.
No model extension or normal production import was necessary.

Baseline visual AWS/256/geometry z14/relief z15, independent analytical AWS
z15/256, strengthened IGOR curve, direction 315°/map anchor/colors, exaggeration
1.45, satellite suppression, atmosphere/projection/lifecycle, Weather and
Traverse have **no source diff**. Normal application startup still works without
the external estate or an evaluation service. No reconciliation, blending,
hierarchy, imagery, second global candidate or regional resolver was created.

## Reproduction and validation

From the repository in PowerShell (explicit external data root, existing
scientific environment; optional research dependencies are pinned separately):

```powershell
$env:MERIDIAN_DATA_ROOT = 'C:\Users\gbsam\Documents\Projects\meridian-data'
$referencePython = Join-Path $env:MERIDIAN_DATA_ROOT 'earth-lab/.venv/Scripts/python.exe'
# Optional in a fresh isolated environment:
# & $referencePython -m pip install -r scripts/atlas/global_reference_requirements.txt
& $referencePython scripts/atlas/acquire_global_reference.py
# Reuses verified frozen assets. Missing inputs are acquired explicitly;
# mutable upstream downloads are not assumed to reproduce old bytes forever.
& $referencePython scripts/atlas/assess_global_reference.py
& $referencePython scripts/atlas/build_global_reference_metadata.py
& $referencePython -m unittest discover -s scripts/atlas -p 'test_*.py'
node --test scripts/atlas/test_terrain_policies.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_global_reference_metadata.mjs
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/global-reference-app-build'}});"
```

The offline assessment never fetches missing AWS tiles or PROJ grids and verifies
frozen inputs before processing. Existing Gaussian/statistics/sampling helpers
are reused without invoking previous reconciliation experiments. Fresh source
acquisition requires network; normal deterministic tests require neither the
data estate nor online services. Only pyshp was added to the existing scientific
environment; production package dependencies were unchanged.

Validation: all 23 synthetic Atlas Python tests pass (6 new focused checks),
all 156 active Node application tests pass with 1 existing optional skip,
including 5 new metadata checks; lint and TypeScript pass; application-only
production bundle passes with the existing large-chunk warning. Full external
Weather publication/public-data copying was deliberately omitted from the build.
The first suite invocation used an invalid in-repository empty data root; it
was rerun with an empty **external** root and passed. No unrelated test changed.
The clock-dependent workspace test passes on this run.

Input/hash validation, independent repeat, owned-model validation, document
references and final diff/production-invariant checks complete this bounded
assessment. No production deployment or subsequent hierarchy work follows it.
