# Physical-surface source inventory

Companion to [the domain review](physical-surface-semantics.md). Reviewed
2026-10-06 from primary documentation/catalogues; **no products acquired**.
This is a bounded inventory, not source selection. The later
[source-native comparison](source-native-semantic-comparison.md) acquired small
WorldCover/NRW/GeoCover subsets and the smallest GLAMOS distribution; the review
above itself acquired no data. Access listed means documented
mechanism, not verified download success. Sampling, MMU and quality are distinct.
Unknown means not established in this review. Every future acquisition must retain
its actual version, observation period and exact terms; portal availability alone
is not permission. Institutional authority does not remove classification error.

## Global

### ESA WorldCover 2020 v100 / 2021 v200

ESA consortium; global 10 m categorical maps, 11 classes, Sentinel-1/2 inputs.
These two released epochs are not a verified continuing annual series. Algorithms
differ between versions, so differences are not pure physical change. Reported
2021 global overall accuracy is 76.7%; it is not local confidence. Input-quality
layers do not supply universal per-pixel class probabilities. CC BY 4.0 with
product/year attribution and modified Sentinel notice. COG tiles, AWS, Earth
Engine and WMS; rendered WMS RGB is not analytic class data. Broad labels such as
bare/sparse do not identify rock versus scree.
[Access, versions, quality and rights](https://esa-worldcover.org/en/data-access),
[product manual](https://worldcover2021.esa.int/data/docs/WorldCover_PUM_V2.0.pdf).

### Copernicus global dynamic land cover

CLMS/VITO: legacy 100 m Collection 3 annual 2015–2019 includes 23 classes,
cover fractions and class/change confidence. The newer global annual 10 m service
uses Sentinel-2; 2020 v1 is documented as available. A 2020–2026 service plan does
not verify publication of every year. Its page marks validation status but has
an incomplete thematic-accuracy statement; no number is inferred. Versions,
legends and confidence meaning need individual manuals. CLMS free/full/open
policy with source credit; CDSE/CLMS access. Different generations cannot be
stitched into a homogeneous change record.
[Service](https://land.copernicus.eu/en/products/global-dynamic-land-cover),
[10 m 2020](https://land.copernicus.eu/en/products/global-dynamic-land-cover/land-cover-2020-raster-10-m-global-annual),
[legacy variables](https://documentation.v1.dataspace.copernicus.eu/APIs/SentinelHub/Data/clms/land-cover-and-land-use-mapping/global-dynamic-land-cover/lc_global_100m_yearly_v3.html).

### Dynamic World v1

Google/WRI partnership: global 10 m, June 2015 onward, per qualifying Sentinel-2
observation rather than guaranteed daily coverage. Nine estimated class
probabilities and argmax label; cloud/shadow masks and algorithm/QA versions.
Model context and single-image ambiguity affect crops and reflective surfaces;
probabilities are not area fractions or independently certified truth. CC BY 4.0
with partner and Sentinel notices; Earth Engine access also has platform terms.
Observation timestamp and composite method must survive any temporal aggregation.
[Producer dataset documentation](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1).

### MODIS MCD12Q1 Collection 6.1

NASA/USGS annual global 500 m land-cover product, 2001 onward. MODIS temporal
reflectance classification supplies multiple legends, including five legacy
schemes and three LCCS property layers, QA and LCCS posterior assessments. Do not
interpret every legend as the same property. Stage-2/cross-validation and product
quality are not local pixel certainty. Sinusoidal HDF delivery through Earthdata;
NASA open-data policy applies to NASA mission data. Coarse mixed footprints and
annual classification are unsuitable for claiming individual fine surface edges.
[Primary user guide](https://lpdaac.usgs.gov/documents/1409/MCD12_User_Guide_V61.pdf).

### Hansen Global Forest Change 2025 v1.13

UMD/Google/USGS/NASA: Landsat-derived approximately 30 m tree-cover percentage
for 2000 (vegetation taller than 5 m) and annual stand-replacement loss through
2025. The gain layer remains 2000–2012; do not extend it to 2025. Loss is not all
forest-use change and does not itself prove land conversion. Product validation
is distinct from a per-pixel probability. CC BY 4.0; individual 10-degree GeoTIFFs
and Earth Engine. The current download page contains legacy loss-year prose;
verify encoded-year definitions against the exact release before processing.
[Release/download](https://storage.googleapis.com/earthenginepartners-hansen/GFC-2025-v1.13/download.html),
[versioned catalogue](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2025_v1_13).

### GEDI vegetation structure

NASA/University of Maryland lidar, approximately 25 m footprints with separated
tracks, latitude coverage about 51.6° N/S; **not wall-to-wall vegetation** and not
Tryfan coverage. Waveforms, height/vertical profile products, spatial summaries
and biomass models are different derivations. L2B v002 HDF5 contains observation
and quality information; granule dates must be queried, not inferred from product
publication. Mission began in 2019; this review does not certify every later
availability interval. NASA policy and dataset citation. Missing footprints are
not absence of trees; interpolation introduces model dependence.
[Technology](https://gedi.umd.edu/mission/technology/),
[products](https://gedi.umd.edu/dataproducts/products/),
[L2B identity](https://doi.org/10.5067/GEDI/GEDI02_B.002).

### JRC Global Surface Water v1.5

EC JRC/Google: Landsat-derived 30 m water histories and occurrence, current
release extends 1984–2024 (updated August 2026). Occurrence is conditional on
observations, not a ground-truth probability. Summary and yearly/monthly histories
have different delivery ranges; assembling earlier history needs the older
assets. Documentation reports corrections and a remaining sparse-observation
monthly-recurrence limitation. Free Copernicus use with JRC/Google acknowledgement;
GeoTIFF, Earth Engine, WMS and XML metadata. Water detection is not network,
depth, flow or all water beneath canopy.
[Authoritative release, limitations and access](https://global-surface-water.appspot.com/download).

### MODIS MOD10A1 Collection 6.1 snow

NASA/NSIDC daily global approximately 500 m sinusoidal snow-cover/albedo product,
2000 onward, derived from MODIS observations. NDSI and QA/cloud/night masks have
specific meanings: NDSI is not directly snow fraction. Cloud gaps remain; the
separate gap-filled A1F is not A1. Product validation and algorithm documentation
do not establish current state beneath obscuring cloud/canopy. HDF-EOS2 through
Earthdata/NSIDC, NASA open-data policy and product citation. Snow class/index,
estimated albedo and underlying material must stay separate.
[Versioned product](https://nsidc.org/data/mod10a1/versions/61),
[user guide](https://nsidc.org/data/documentation/modis-snow-products-collection-61-user-guide).

### Randolph Glacier Inventory 7.0

GLIMS/international glacier inventory: global outlines excluding Antarctic and
Greenland ice sheets, aiming at approximately 2000 with heterogeneous actual
observation dates; minimum glacier area 0.01 km². Dated vector objects and
attributes, not a current exposed-ice mask, ice thickness model or uniform annual
change series. Source/outline quality varies; no pixel confidence is implied.
Regional shapefile downloads through NSIDC use CC BY 4.0 with dataset citation
and appropriate contributor acknowledgement. Inventory identity and visible
debris/snow cover are independent claims.
[Inventory and rights](https://rgidata.org/user_guide/01_introduction.html),
[glacier product definitions](https://www.glims.org/rgi_user_guide/products/glacier_product.html).

### GHSL built surface, R2023A

EC JRC: GHS-BUILT-S estimates built-up area in m² per cell, with non-residential/use
related components that must not become physical material classes. Multitemporal
1975–2030 outputs at 100 m/1 km include interpolation/extrapolation; the 10 m anchor
is 2018, not a verified 10 m observation at every epoch. Source imagery and models
vary; neither footprint precision nor future observations are implied. CC BY 4.0
with exact product/method citations; downloadable tiles. Newer releases listed
on the portal are not assessed as substitutes here.
[Datasets](https://human-settlement.emergency.copernicus.eu/datasets.php),
[R2023A manual](https://human-settlement.emergency.copernicus.eu/documents/GHSL_Data_Package_2023.pdf),
[citation/rights](https://human-settlement.emergency.copernicus.eu/GHSLhowToCite.php).

### SoilGrids 2.0 — scope contrast

ISRIC: global 250 m predictions of depth-dependent soil properties over six
standard intervals to 200 cm, based on profiles/covariates and machine learning.
Prediction intervals are model uncertainty, not exposed-surface classification.
No single current observation epoch is implied. CC BY 4.0 for current products;
older release terms differ. WebDAV/COG and documented services; service uptime
was not tested. Relevant as separate substrate evidence, not as proof of visible
soil or a reason to implement subsurface Atlas now.
[Definitions](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html),
[uncertainty](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html),
[rights/access](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html).

NASA mission data rights are governed by the
[Earthdata use policy](https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy);
non-NASA inputs can have their own restrictions. CLMS products use their
[free/full/open data policy](https://land.copernicus.eu/en/data-policy), with source
credit; this does not open every upstream commercial image.

## Europe

All CLMS entries below require source credit under the
[CLMS data policy](https://land.copernicus.eu/en/data-policy). Access generally uses
CLMS/CDSE/WEkEO downloads and documented services. Check the specific coverage
and generation: “Europe” is not proof of identical UK inclusion in every release.

### CORINE Land Cover

EEA/CLMS European status series 1990, 2000, 2006, 2012 and 2018; six-year cadence,
44 hierarchical classes mixing cover and use. Status MMU 25 ha, minimum width
100 m; vector and 100 m raster. Change mapping uses 5 ha MMU. Satellite-image
interpretation and national inputs vary. Validation is product/class-level, not
per-pixel probability. Useful broad land patterns, not small canopy gaps or
instantaneous water boundaries. Do not claim a newer released epoch from a
planned cycle.
[Product family](https://land.copernicus.eu/en/products/corine-land-cover),
[official 2018 service metadata](https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer).

### High Resolution Layers: forests and tree cover

CLMS European crown-projection density, leaf type and forest-related layers.
Annual 2018–2023 tree-cover products at 10/100 m; older 2012/2015 generations use
20 m. Sentinel-1/2 classification/estimation and confidence layers are documented.
Tree-cover percentage is not forest inventory membership; individual releases
have validation/status and definition differences. Forest-type epochs need not
match every annual density layer. Useful independent type/fraction properties,
not species, understorey or full vertical structure.
[Technical summary](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover?tab=technical_summary),
[2021 density](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2021-raster-10-m-100-m-europe-yearly).

### High Resolution Layer: imperviousness density 2021

CLMS 10/100 m sealed-surface percentage derived from Sentinel-2, with associated
confidence information. Epoch and processing date are distinct. The current
record's validation status must be read as published; no completed numerical
accuracy is inferred from the programme's targets. Imperviousness is not all
built area, land use or every artificial structure. Useful continuous property
with method/threshold scope, not a calibrated local runoff model.
[Product and technical documents](https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/imperviousness-density-2021).

### Water and Wetness 2018

CLMS 10/100 m product summarising 2012–2018 occurrence, using Sentinel-1/2.
Permanent/temporary water and wetness distinctions describe a period rather than
one instantaneous flood or soil-moisture value. The record is labelled not
validated while linking validation material; preserve that distinction instead
of quoting target accuracy as achieved. Masks/confidence require the manual's
meaning. It adds wetness history beyond a binary land-cover water class, but
neither a complete hydrographic network nor water-surface elevation.
[Product](https://land.copernicus.eu/en/products/high-resolution-layer-water-and-wetness/water-and-wetness-status-2018).

### Fractional Snow Cover

CLMS 20 m European fractional snow service, nominally daily/as Sentinel-2
observations permit, archive from 2016. Cloud/quality support matters; no clear
observation every day is guaranteed. Current documentation describes processing
changes and 2026 archive reprocessing; schedule is not verified completion.
A fraction is a physically scoped estimate, not class confidence or snow depth.
Documented catalogue/download APIs permit later bounded retrieval. Validation
and algorithm generation must accompany the specific asset.
[Family, coverage and delivery notices](https://land.copernicus.eu/en/products/snow/fractional-snow-cover).

### Riparian Zones

EEA/CLMS selected European river-buffer land-cover/use mapping, 2012/2018,
55 classes, vector MMU 0.5 ha and 10 m minimum width, with product-specific
interpretation and validation documentation. Targeted detailed mapping adds
information around mapped rivers; it is not complete all-wetland coverage or an
ecological condition measurement. Do not treat polygon edges as exact changing
inundation limits. Later epochs and input rights must be checked individually.
[Product family](https://land.copernicus.eu/en/products/riparian-zones).

## Great Britain

### UKCEH Land Cover Map 2024

UKCEH: GB 10 m raster, 21 broad-habitat classes and class-probability band;
2024 observations, published July 2025. Random Forest uses seasonal reflectance
composites and contextual inputs. Parcel confusion matrices do not establish
pixel-level accuracy everywhere. The 25 m rasterised parcel product and 1 km
summaries have different grain and meaning. Access is through catalogue/download
or licensed supply. **Custom raster terms** restrict use/redistribution; evaluation
and personal/noncommercial use provisions are not an open public-delivery grant.
No restricted data acquired. Parcel/vector rights must be checked separately.
[10 m record](https://catalogue.ceh.ac.uk/documents/4dd9df19-8df5-41a0-9829-8f6114e28db1),
[actual raster licence](https://eidc.ac.uk/licences/lcm-raster/plain),
[product family](https://www.ceh.ac.uk/data/ukceh-land-cover-maps).

### Ordnance Survey: detailed themes versus open cartographic products

OS National Geographic Database separates land cover, land use, water features
and networks; detailed national mapping is subject to PSGA/commercial terms,
not universally open. OGC API Features supports documented spatial/attribute/time
queries; no paid/subscribed data used. Exact theme epochs and semantic accuracy
require product records. OS OpenMap–Local provides generalised buildings, woodland
and water under OS OpenData/OGL: small features/gaps may be omitted or filled.
OS Open Rivers supplies connected 2D centreline links/nodes, not wet extent or
flow volume. Useful feature evidence and scope contrast, not one semantic map.
[OS public task](https://www.ordnancesurvey.co.uk/governance/public-task),
[NGD API](https://www.ordnancesurvey.co.uk/products/os-ngd-api-features),
[OpenMap guide](https://www.ordnancesurvey.co.uk/documents/os-open-map-local-product-guide.pdf),
[Open Rivers](https://docs.os.uk/os-downloads/products/water-portfolio/os-open-rivers/os-open-rivers-overview).

### National Forest Inventory

Forestry Commission/Forest Research GB inventory: woodland mapping and statistical
field samples, updated map series with five-year survey cycles. Definition includes
at least 0.5 ha, 20 m width and 20% canopy or potential canopy, with temporarily
unstocked areas. Thus forest membership is not current crown fraction. Aerial
interpretation, remote imagery and administrative inputs; inventory sampling and
mapped boundary accuracy are distinct. Vector/open downloads under OGL/Crown
attribution with release year. Trees Outside Woodland is a separate product;
small/individual trees cannot be inferred absent from the woodland map.
[Definition/method](https://www.forestresearch.gov.uk/tools-and-resources/national-forest-inventory/about-the-nfi/),
[open access](https://www.forestresearch.gov.uk/tools-and-resources/fthr/open-data/),
[rights](https://www.forestresearch.gov.uk/crown-copyright/).

### NRW terrestrial Phase 1 habitat survey

Natural Resources Wales field-based vector habitat survey, begun in 1979;
lowland/upland survey traditions and heterogeneous local dates/legends. A portal
publication date is not a current observation epoch. Habitat polygons/mosaics
include interpreted ecology; Voronoi subdivisions used for some mosaics are not
surveyed physical edges. Survey error work is documented, but no universal local
accuracy is inferred. DataMapWales downloads/services, OGL with NRW and applicable
OS notices. Useful source-native comparison at Tryfan only after checking actual
local survey date, support and definitions.
[Authoritative catalogue](https://datamap.gov.wales/layergroups/geonode%3Anrw_terrestrial_phase_1_habitat_survey).

### NatureScot habitat/land-cover maps

NatureScot/Space Intelligence 2024 EUNIS L1/L2 maps and associated predictions
are listed in June 2026. The 2024 product is 10 m; preceding 2019/2020/2022 maps
were 20 m. Do not transfer old legends, validation or licence automatically.
The inspected 2024 licence field does not establish reuse terms: **unknown until
verified**. Older 2022 documentation describes Sentinel/ALOS AI inputs and OGL.
HabMoS combines habitat surveys and classifications and is a different product.
Download links/catalogue metadata exist; update series is not guaranteed annual
current-state coverage.
[2024 catalogue](https://www.data.gov.uk/dataset/417c8f75-2c53-4e64-9aad-613a0fe015e0/scotland-habitat-and-land-cover-map-2024-eunis-level-1),
[downloads](https://gis-downloads.nature.scot/),
[2022 method context](https://www.nature.scot/doc/naturescot-research-report-1382-understanding-need-and-value-land-cover-and-habitat-data),
[HabMoS](https://www.nature.scot/landscapes-and-habitats/habitat-data-and-habitat-map-scotland).

### Environment Agency National LiDAR Programme — structural evidence

EA England survey catalogue, 1 m DTM/DSM and related return/intensity products.
Tile-specific acquisition date/survey identity matters; programme/mosaic date
is not uniform observation time. Point returns/DSM–DTM differences can inform
above-ground structure, but cannot alone establish vegetation type. Accuracy and
processing are survey/product-specific. Data.gov.uk and EA catalogue/services;
OGL with the record's EA copyright/database notice. No data acquired here.
Not a GB-wide cover map and not a reason to reopen terrain acquisition.
[Product catalogue](https://www.data.gov.uk/dataset/f0db0249-f17b-4036-9e65-309148c97ce4/national-lidar-programme),
[official survey metadata service](https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/National_LIDAR_Programme_Catalogues/FeatureServer/0).

## Switzerland

### swissTLM3D 2.4

swisstopo 2026 model for Switzerland/Liechtenstein, annual releases with
heterogeneous object/source epochs. LV95/LN02 vector objects separate cover,
use areas, buildings and hydrographic network. Specified cover classes can overlap;
rock/loose-rock classes have percentage and minimum-area definitions. Typical
geometric accuracy varies by object, not class probability. Vector formats include
GeoPackage/Geodatabase/Shapefile/INTERLIS. Free swisstopo geodata terms with
© swisstopo credit; no automatic licence for unrelated inputs. Valuable regional
semantic detail, not a complete vertically layered model or current state map.
[Product](https://www.swisstopo.admin.ch/de/landschaftsmodell-swisstlm3d),
[2.4 object catalogue, especially pp. 48–50](https://www.swisstopo.admin.ch/dam/de/sd-web/A3kQ2dAgenqG/2026-02%20swissTLM3D%202.4%20OK-DE.pdf),
[rights](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices).

### Federal Statistical Office land-use statistics

FSO aerial-photo interpretation at approximately 4.1 million points on a 100 m
lattice. This is a statistical sample, not a wall-to-wall hectare cover map.
Separate nomenclatures include 27 cover and 46 use classes, alongside a combined
72-class scheme. Epochs span acquisition ranges (1979–1985 through the listed
2020–2025 period); publication does not prove uniform recent coverage. Sampling
error matters for small areas; no local pixel confidence. Statistical tables and
geodata are distinct access products. Credit FSO; exact geodata redistribution
terms remain **unverified**, not inferred from public statistics access.
[Cover/use definitions](https://dam-api.bfs.admin.ch/hub/api/dam/assets/32376295/master),
[sampling description](https://www.swissstats.bfs.admin.ch/data/webviewer/appId/ch.admin.bfs.swissstat/article/issue21020021801-03/package),
[epoch table](https://www.pxweb-r.bfs.admin.ch/pxweb/en/px-x-0202020000_101/-/px-x-0202020000_101.px/).

### LFI vegetation-height model

Swiss National Forest Inventory/WSL/FOEN catalogue describes ADS80/100 stereo
surface models normalized against swissALTI3D, a vegetation-height field rather
than plant type. Inspected catalogue describes 1 m processing; do not assign a
different resolution or combine generations without asset lineage. Actual local
epoch, generation, validation and reuse terms are **not
established** by the inspected metadata (licence field blank). Documented WMS/WMTS,
STAC/API and product pages allow later bounded verification. Geometry dependency
is essential; residual objects/model errors are not automatically canopy.
[Official catalogue](https://opendata.swiss/en/dataset/vegetationshohenmodell-lfi),
[NFI product page](https://lfi.ch/de/karten/vegetationshoehe-oberflaechenmodell).

### GLAMOS Swiss Glacier Inventory 2016, release 2020

GLAMOS: glacier outlines, ice divides and debris information derived from
2013–2018 aerial/swissTLM observations and glaciological revision. Nominal 2016
inventory epoch differs from each actual source date. Vector shapes/points,
CC BY 4.0 with dataset citation; individually documented release/download.
No uniform pixel resolution or current-boundary accuracy is implied by a vector
inventory. Glacier identity can coexist with debris cover or seasonal snow;
outline changes require temporal/geometric evidence, not subtraction of unrelated
land-cover maps.
[Release identity, methodology and licence](https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html).

### SLF snow observations and products

WSL Institute for Snow and Avalanche Research: snow measurements and map products.
IMIS stations (roughly 180-plus) are point/timeseries evidence, often near treeline,
not wall-to-wall snow extent. Historical timestamps, station support and measurement
quality remain distinct from model/map generation. Data service documents access
and institutional attribution; full use conditions must accompany an eventual
specific record. Snow-map aggregation/model resolution and validity are **not
established here** and cannot be assigned from a station catalogue. No current
snow field is acquired or inferred.
[Data service](https://www.slf.ch/en/services-and-products/slf-data-service/),
[measurements](https://www.slf.ch/en/avalanche-bulletin-and-snow-situation/measured-values/),
[map overview](https://www.slf.ch/en/services-and-products/snow-maps/).

### GeoCover — scope contrast

swisstopo geological vector model v3, largely based on 1:25,000 geological
mapping with heterogeneous survey histories and local knowledge. Geological
units/superficial deposits describe geology, not necessarily today's exposed
surface under snow, grass or infrastructure. Geometry/generalisation and
interpretation uncertainty differ from cover classification quality. Free
swisstopo geodata terms/credit; documented vector downloads. Appropriate future
substrate evidence, not a reason to import a geological ontology into this
physical-cover foundation.
[Authoritative product](https://www.swisstopo.admin.ch/en/geological-model-2d-geocover).

## Interpretation and validation notes

The survey is deliberately broad enough to expose incompatible meanings, but not
a catalogue of every available national habitat, flood, coastal or geology service.
Dataset versions and dates above are source facts as reviewed; statements about
Atlas ownership are in the companion report. No producer's accuracy target,
service schedule or metadata publication date is converted into demonstrated
local accuracy, completed delivery or current physical state.

Particular unresolved checks before any subsequent use:

- NatureScot 2024 reuse licence; older generation terms do not settle it.
- Exact LFI asset generation, local dates, validation and licence.
- FSO geodata terms versus public statistical tables.
- SLF specific product/model semantics and complete use conditions.
- CLMS release-level validation and actual completion of scheduled reprocessing.
- UKCEH format-specific restrictions; no public redistribution assumed.

This inventory requires no external-data dependency in normal startup or CI.
Primary URLs were inspected for the facts cited; no bulk link crawl, account
access, paid licence or data download was performed. References are retained as
reproduction starting points rather than silently cached as current product truth.


## 2026-10-06 — verified bounded comparison access

The [comparison](source-native-semantic-comparison.md) adds these specific facts;
other inventory products remain unacquired:

- WorldCover v200 producer AWS native COG range reads work. Two native windows
  total 9,964 bytes after lossless extraction; authoritative PUM v2.0 is also
  available under the producer AWS `v200/2021/docs` path. Parent hashes/wire bytes
  remain unknown; subset definitions and hashes are pinned.
- NRW WFS vegetation Voronoi returns 193 complete intersecting features in the
  fixed Tryfan window; survey-area layer returns two date-context polygons.
  Native mosaics retain composition percentages and parent identifiers. JNCC's
  Welsh legend includes NA (not accessed), `?` (illegible original code) and a
  D.5 wet/dry naming conflict; none is silently normalized. Survey-area dates
  do not prove each upland component's epoch. OGL/NRW/OS notices still apply.
- The GeoCover [August 2026 restructuring](https://www.geo.admin.ch/en/new-structure-of-the-swissgeocover2d-datasets-on-mapgeoadminch)
  exposes separate `ch.swisstopo.geologie-swissgeocover2d_bedrock` and
  `_unconsolidated` layers through small geo.admin.ch identify-envelope queries.
  Retained 23/8 features carry native lithology/chronology and sheet links.
  Catalogue dataStatus 20260901 is not local survey time. No exposure class is
  inferred from geological units. Standard swisstopo terms/source credit apply.
- GLAMOS SGI2016 r2020 smallest published ZIP is 9,787,779 bytes. One glacier and
  six debris records intersect Riffelhorn. Published debris `sgi-id` identifies
  the underlying glacier; local acquisition fields are 2015 (glacier), 2016
  (debris), release 2020. Nominal 2016 does not erase this difference.
- TLM 2026-02 national Shapefile archive is 3.59 GB; compressed WEST cover geometry
  alone is 420.78 MB. Bounded archive-directory metadata informed exclusion,
  not a local TLM cover acquisition or change to its documented semantics.

Exact queries, attribution requirements, retained identities and byte counts are
in [the receipt manifest](semantic-comparison-sources.json). No paid/restricted
UKCEH raster, canopy model, new imagery or new elevation was acquired.

## 2026-10-06 — water feature/state source check

The [upper-Exe empirical report](water-feature-state-check.md) retains five products
from four families, a 10.5km² BNG window and six pre-frozen 200m probes. New facts:

- [EA WFD Cycle3 classification2019 simplified](https://www.data.gov.uk/dataset/52fa8958-ea30-46fc-8ecb-f31ea8f89aa6/water-framework-directive-wfd-transitional-and-coastal-water-bodies-cycle-3-classification-20191)
  exposes named EXE `GB510804505600` and MHW/OS OpenMap Local/UWWTD-derived geometry.
  This is an assessment-unit/reference boundary, not current wet extent. OGL, EA2024
  and OS2024 attribution; classification2019/export2024 differs from later catalogue.
- [NE Priority Habitats Inventory](https://www.data.gov.uk/dataset/4b6ddab7-6c0f-4407-946e-d6499f19fcde/priority-habitats-inventory-england)
  supports small OGC Features BNG queries. All 280 local native features are `Sept_26`,
  although linked catalogue/spatial-document revisions are 2025. Main/additional
  habitats, UID and primary-source descriptions preserve mixed contributors and
  different vintages. Reedbed/saltmarsh co-membership is explicit, not an exclusive
  label or fraction. Local contributor-year strings do not establish acquisition
  dates. OGL plus contributor notices/CC-BY4; complete NE/OS/contributor notices
  retained in source metadata. No universal local MMU or probability established.
- [JRC GSW v1.5 access](https://global-surface-water.appspot.com/download) now links
  a public CloudFerro object listing: retained native occurrence1984–2024 and
  March/September2024 history windows. These files use 0.00025° grids (locally
  approximately 17.67×27.81m), distinct from nominal 30 m Landsat sampling. Monthly0
  is no observations,1 non-detection,2 detection; not a local confidence score or
  instantaneous tide/state. Later extensions do not inherit original validation
  automatically. Copernicus reuse requires EC JRC/Google/Pekel2016 acknowledgement.
- [EA Flood Zones](https://www.data.gov.uk/dataset/104434b0-5263-4c90-9b1e-e43b1d57c750/flood-map-for-planning-flood-zones1)
  current present-day product has mixed modelled/recorded/direct-rainfall origins.
  Annual-probability and ignored-defence convention are reference conditions, not
  observations of water now. OGL/EA2025; revision2026-05-20; sub-model vintage unknown.
- [EA Recorded Flood Outlines](https://www.data.gov.uk/dataset/16e32c53-35a6-4d54-a111-ca09031eaaaf/recorded-flood-outlines1)
  provides outline/group IDs, event intervals, boundary evidence and qualitative
  outline quality. Revision2026-09-16; OGL/EA2025. No record means no held record,
  not no past flood. Guidance6.2 documents unknown 2050 dates; no such sentinel in
  this local set. Historical defences/conditions can differ from today.

Receipts/hashes/exact queries and rights are in [water-check-sources.json](water-check-sources.json).
Raw source/document payloads remain external; no restricted source or national
archive, new terrain or imagery acquired. This updates source facts only; it does
not establish a water ontology, runtime, classifier or semantic evidence contract.
