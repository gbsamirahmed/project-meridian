# Tryfan historic LiDAR reconnaissance

Reconnaissance date: 2026-10-01. This is an open-data inventory, not a new Lab,
numbered phase, reconstruction or data migration. The
[machine-readable inventory](tryfan-lidar-reconnaissance.json) preserves all eight
matching archive records, raw footprints, acquisition metadata, download URLs,
query URLs, evidence hashes and coverage calculations.

**BEST OPEN TRYFAN DTM:** existing Welsh Government national LiDAR, delivery 11,
1 m, acquired 2021-03-02; complete canonical AOI coverage.

**BEST OPEN TRYFAN DSM:** the matching national 1 m DSM, acquired 2021-03-02;
complete canonical AOI coverage.

**0.25 M COVERAGE:** no intersecting record in the official published historic
catalogue, including its original layer and NRW-linked ArcGIS catalogue.

**0.5 M COVERAGE:** no intersecting record in those catalogues.

**CURRENT 1 M SOURCE SUPERSEDED?** No. No finer historic product is identified;
the existing national source is newer and has verified full AOI valid-cell coverage
in its retained canonical metadata. This recommendation compares the queried NRW
archive with the current national source, not every possible unpublished dataset.

**NEXT DATA ACTION:** retain the existing 2021 DTM/DSM; do not download historic
rasters for a resolution upgrade. Any later historic comparison should first
establish actual valid-data masks. No next action is implemented here.

## Canonical extent

The [promoted Tryfan catalogue](tryfan-data-catalog.json) and retained source
manifest agree on British National Grid **EPSG:27700**, bounds
`[264900, 357800, 267900, 360800]` in easting/northing metres. This is a
**3000 × 3000 m, 9,000,000 m²** reference area, from `SH6490057800` to
`SH6790060800`, spanning OS 10 km squares `SH65` and `SH66`.

Current source rasters are **3000 × 3000 pixels at 1 m**. The canonical manifest
records 9,000,000 valid cells and zero nodata cells in each DTM/DSM. Source metadata
lives beneath `${MERIDIAN_DATA_ROOT}/sources/atlas/tryfan/welsh-lidar-1m/metadata/`.
It was read, not modified; no raster payload was downloaded or rehashed.

The Lab 009 reconstruction has **3025 × 3025 vertices**, spacing
`3000 / 3024 = 0.9920634920634921 m`, over this same vertex domain. Its raster
representation adds a half-cell border, with bounds
`[264899.50396825396, 357799.50396825396, 267900.49603174604, 360800.49603174604]`.
That interpolation is not sub-metre LiDAR acquisition. A second archive hit query
using the padded bounds still finds eight records.

## Official evidence and completeness

Authority: [NRW LiDAR tile catalogue archive on DataMapWales](https://datamap.gov.wales/layers/geonode:nrw_lidar_tile_catalogue_archive/metadata_detail),
with its [original Historic LiDAR Archive layer](https://datamap.gov.wales/layers/inspire-nrw:NRW_LIDAR_ARCHIVE_TILE_CATALOGUE/metadata_detail).
The archive is published under the
[Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
Attribution: Contains Natural Resources Wales information © Natural Resources
Wales and Database Right. All rights Reserved.

The live WFS endpoint is `https://datamap.gov.wales/geoserver/ows`. Queried types:
`geonode:nrw_lidar_tile_catalogue_archive` and
`inspire-nrw:NRW_LIDAR_ARCHIVE_TILE_CATALOGUE`. Each bounded GetFeature response
reports **8 matched / 8 returned**, below the requested maximum of 100. Independent
WFS 2.0 `resultType=hits` also reports eight. A combined spatial CQL filter with
`resolution < 1` reports zero. No resolution filter was used for the primary
inventory, so the absence of 2 m entries is also established by the complete result.

The service-wide capabilities request timed out. The official
[layer-specific capabilities](https://datamap.gov.wales/capabilities/layer/6988/?ows_service=wfs)
and DescribeFeatureType succeeded. A mixed KVP BBOX/CQL request returned HTTP 500;
combining both predicates in one CQL expression succeeded. These failures and
recoveries are retained in the inventory.

The [NRW-linked web map](https://nrw.maps.arcgis.com/apps/webappviewer/index.html?id=3f8007ca0b8847948ca47de0a27319e2)
points to the [official ArcGIS tile service](https://services.arcgis.com/hQoYDJEEJMaPw8Sy/arcgis/rest/services/NRW_Historic_LiDAR_Tile_Catalogue/FeatureServer/0).
Its bounded query independently returns the same eight LiDAR names and confirms
the resolution field's units as metres. The original WFS layer supplies survey
`POLYGON_ID`, acquisition interval and `PERCENT_CO`; these are preserved rather
than grouping unrelated records solely by resolution.

Primary geometry and AOI are both EPSG:27700: no transformation is needed.
ArcGIS's native service CRS is EPSG:3857, so its corroborating query explicitly
uses `inSR=27700` and `outSR=27700`; the response confirms that output CRS.
Coverage calculations use the native BNG WFS polygons, not ArcGIS-transformed
geometry or place-name inference.

## Historic records and spatial coverage

All eight records advertise **both DTM and DSM at 1 m**. All ten distinct archive
ZIP URLs returned HTTP 200 to HEAD requests. No ZIP body or source raster was
downloaded. URLs and header results are in the JSON inventory.

| Survey polygon | Acquisition | Intersecting tiles | Tile union inside AOI | AOI tile-overlap | Status |
| --- | --- | --- | ---: | ---: | --- |
| P_5024 | 2007-02-07–2007-04-02 | SH6458, SH6460, SH6658, SH6660 | 8,400,000 m² | 93.33% | Partial tile extent |
| P_6405 | 2009-03-18 | SH6660 | 1,520,000 m² | 16.89% | Partial tile extent |
| P_9378 | 2014-03-10 | SH6456, SH6656, SH6660 | 2,120,000 m² | 23.56% | Partial tile extent |

| LiDAR record | Survey | Tile | Nominal BNG tile bounds | AOI overlap | Reported whole-tile coverage |
| --- | --- | --- | --- | ---: | ---: |
| D0074612 | P_5024 | SH6458 | [264000, 358000, 266000, 360000] | 24.44% | 40.6% |
| D0074618 | P_5024 | SH6460 | [264000, 360000, 266000, 362000] | 9.78% | 80.05% |
| D0074613 | P_5024 | SH6658 | [266000, 358000, 268000, 360000] | 42.22% | 30.7% |
| D0074619 | P_5024 | SH6660 | [266000, 360000, 268000, 362000] | 16.89% | 51.975% |
| D0115900 | P_6405 | SH6660 | [266000, 360000, 268000, 362000] | 16.89% | 3.56% |
| D0170995 | P_9378 | SH6456 | [264000, 356000, 266000, 358000] | 2.44% | 41.77% |
| D0170997 | P_9378 | SH6656 | [266000, 356000, 268000, 358000] | 4.22% | 65.61% |
| D0170998 | P_9378 | SH6660 | [266000, 360000, 268000, 362000] | 16.89% | 6.1% |

**These AOI percentages describe catalogue tile rectangles, not measured-data
coverage.** The original catalogue/web map explicitly reports partial coverage
within each tile. It does not provide the spatial arrangement of those covered
cells. Multiplying a tile's AOI intersection by its whole-tile coverage percentage
would be unjustified. Actual historic AOI valid-data coverage remains `null` in
the inventory. Even the union of all historic tile rectangles reaching 100% does
not prove complete LiDAR coverage across acquisitions.

The JSON also records conditional upper bounds: if `PERCENT_CO` denotes surveyed
area of each nominal 4 km² tile, no more than approximately **58.36%, 1.58% and
9.38%** of the AOI can be covered by the 2007, 2009 and 2014 groups respectively.
These are bounds derived from tile totals, not measured AOI coverage. No historical
survey is presented as a full-reference replacement.

For tile-union calculation, raw polygons are retained and checked against their
OS tile identities. Sub-millimetre transformation noise is normalised to nominal
integer-metre rectangles only after verifying a maximum deviation below 1 mm
(observed below 0.00014 m). Rectangles are clipped to the canonical AOI and unioned
without double counting. This precision correction cannot turn a partial survey
into full coverage or create a high-resolution record.

## Current source and remaining limits

A live bounded query of
[the national 2020–2023 catalogue](https://datamap.gov.wales/layers/geonode:welsh_government_lidar_tile_catalogue_2020_2023/metadata_detail)
returns 16 tiles covering the whole AOI, all delivery 11, dated 2021-03-02. Their
identifiers, bounds and individual DTM/DSM URLs are retained in the JSON. The
existing national [DTM COG](https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif)
and [DSM COG](https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dsm_32bit_cog.tif)
both return HTTP 200 to HEAD requests. Canonical raster metadata establishes full
valid-cell coverage, stronger evidence than the historic tile envelopes alone.

No finer dataset covers the whole AOI or a part of it **in the queried official
historic catalogues**. That scoped finding does not rule out unpublished or
unindexed acquisitions. Exact historic swath/valid-cell overlap remains unresolved;
HEAD success does not validate ZIP contents. Metadata-only query evidence is
cached beneath `${MERIDIAN_DATA_ROOT}/cache/reconnaissance/tryfan-nrw-lidar/2026-10-01`.
Existing sources, derived products, Lab identities, renderer and application remain
unchanged.
