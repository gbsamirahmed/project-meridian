/** Evidence snapshots, not a production registry. See the architecture decision
 * for scopes and links. External-service facts were checked on 2026-10-03 in
 * the retained evaluation, not refreshed or adopted by this module. */
import { known, unknown } from './terrainMetadata';
import { AWS_VISUAL_PRODUCT } from './awsVisualTerrainProduct';
export { AWS_VISUAL_PRODUCT } from './awsVisualTerrainProduct';
import type { EntityReference, SpatialArea, TerrainProduct, TerrainSource } from './terrainMetadata';

const lv95 = { name: 'CH1903+ / LV95', identifier: 'EPSG:2056' };
const ln02 = { name: 'LN02 height', identifier: 'EPSG:5728' };
const mercator = { name: 'WGS 84 / Pseudo-Mercator', identifier: 'EPSG:3857' };
const regionalRecord = 'docs/atlas/riffelhorn-regional-product.json';
const productRoot = '${MERIDIAN_DATA_ROOT}/derived/atlas/riffelhorn/riffelhorn-regional-terrain-v1';
const sourceRoot = '${MERIDIAN_DATA_ROOT}/sources/atlas/riffelhorn/swisstopo-2021-2024/originals/swissalti3d';
const awsUnknown = 'Exact hosted AWS vertical reference and complete measurement lineage are not established.';
const terrarium = { name: 'terrarium', description: 'Metres = R*256 + G + B/256 - 32768.', quantizationIncrement: { value: 1 / 256, unit: 'metre' } };

export const SWISS_SELECTION_AREA: SpatialArea = {
  kind: 'native-rectangle', crs: lv95, axisOrder: 'xy', bounds: [2624000, 1091000, 2626000, 1093000],
};

const swissFiles = [
  ['2624-1091', 'c68c305e4a142da416b46b555a80916ecc52f8fa50bf1efd5cd2c3f24f9cd4bc'],
  ['2624-1092', '9fa4a4391e2e1bfd650f2f31c7d38ed9a5a94494a967011468e6c44559bbcb2c'],
  ['2625-1091', '0d2ebc6d0b4fd06ab2191cbf2a2f5ab77728249fa8c835075040bce4dc4899de'],
  ['2625-1092', '4dffaad9efb82d3bf327a86b4f82d55762165ea5f825c386c23380a9320ff875'],
];

export const RIFFELHORN_SWISS_SOURCE: TerrainSource = {
  id: 'swissalti3d-riffelhorn-input-selection', name: 'swissALTI3D 2024 — retained Riffelhorn selection',
  authority: known('Swiss Federal Office of Topography (swisstopo)'), dataset: 'swissALTI3D',
  release: known('2024; regional provenance: 2024-2 Valais'), revision: known('2024; four immutable asset hashes below'),
  surface: { kind: 'dtm', description: 'Official bare-earth terrain model; retained four-file selection, not national coverage.' },
  horizontalReference: known(lv95), verticalReference: known(ln02), elevationUnit: known('metre'),
  resolution: {
    gridSpacing: { x: 0.5, y: 0.5, unit: 'metre', crs: lv95 },
    nominalResolution: known('Distributed 0.5 m grid.'),
    measurementResolution: unknown('A 0.5 m grid is not independent 0.5 m measurement resolution; variable LiDAR/photogrammetric support.'),
    limitations: 'Cell-specific measurement density, accuracy and update lineage are not available in the retained product.',
  },
  acquisition: known({ description: 'Valais basis: 2021/2022 LiDAR with 2023 photogrammetric updates; per-cell epoch unknown. Release and download dates are separate.' }),
  coverage: { scope: 'retained-input-selection', area: known(SWISS_SELECTION_AREA) },
  nodata: known('TIFF sentinel -9999; retained four tiles were measured fully valid.'),
  quality: unknown('No spatially resolved accuracy/quality mask established for these retained inputs.'),
  rights: {
    licence: known('swisstopo custom Open Government Data terms (1 March 2021)'),
    references: ['https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices'],
    attribution: ['©swisstopo'], limitations: 'Official STAC licence label proprietary is recorded; reuse terms, not that label alone, govern reuse.',
  },
  documentation: [regionalRecord, 'docs/atlas/riffelhorn-regional-terrain-prototype.md', 'docs/atlas/riffelhorn-data-catalog.json'],
  assets: swissFiles.map(([tile, sha256]) => ({ href: `${sourceRoot}/swissalti3d_2024_${tile}_0.5_2056_5728.tif`, sha256 })),
};

const swiss: EntityReference = { kind: 'source', id: RIFFELHORN_SWISS_SOURCE.id, revision: RIFFELHORN_SWISS_SOURCE.revision };
const aws: EntityReference = { kind: 'product', id: 'aws-terrarium', revision: unknown('Mutable public hosted tiles; no complete immutable product revision established.') };

export const RIFFELHORN_REGIONAL_PRODUCT: TerrainProduct = {
  id: 'riffelhorn-regional-terrain', name: 'Riffelhorn regional terrain v1 — experimental Swiss/AWS composition',
  version: known('riffelhorn-regional-terrain-v1'), revision: known('4fc837f299271c7238591865a393f98facc6fa7b93d9cc75305160df900b1fe5'),
  producer: known('Meridian'),
  surface: { kind: 'heterogeneous', description: 'Swiss bare earth at centre-in-AOI pixels; AWS mosaic elsewhere in intersecting prepared tiles.' },
  vertical: { kind: 'heterogeneous', parts: [{ contributor: swiss, reference: known(ln02) }, { contributor: aws, reference: unknown(awsUnknown) }], description: 'Source heights preserved; no datum shift, vertical transformation or accepted reconciliation.' },
  elevationUnit: known('metre'),
  lineage: {
    contributors: [swiss, aws], contributorList: 'complete', spatialMapping: 'mask',
    contributionMask: {
      asset: { href: `${productRoot}/masks/{z}/{x}/{y}.png` },
      interpretation: '0=AWS, 255=Swiss input. Binary input selection, not measurement confidence; file hashes in build manifest.', contributors: [swiss, aws],
    },
    processing: [
      { method: 'Two-dimensional LV95 to Web Mercator reprojection; preserve LN02 numbers.', software: { GDAL: '3.9.3', pyproj: '3.7.2', rasterio: '1.4.3' }, parameters: { statedHorizontalOperationAccuracyMetres: 1, verticalTransform: 'none' }, record: { href: regionalRecord, selector: 'processing.horizontalOperation' } },
      { method: 'Resample Swiss average z5–17, bilinear z18; pixel-centre AOI selection; AWS fill.', parameters: { swissGridSpacingMetres: 0.5, awsFrozenInputCount: 37, boundary: 'hard substitution' } },
      { method: 'Terrarium encode; AWS bilinear z15 overzoom above z15.', parameters: { incrementMetres: 1 / 256, maxRoundingErrorMetres: 1 / 512 }, record: { href: regionalRecord, selector: 'delivery' } },
    ],
    limitations: 'Complete immediate contributors for prepared tiles only. Swiss acquisition lineage per cell and underlying AWS source lineage remain incomplete. Build record freezes 37 AWS inputs; endpoint fallthrough is mutable.',
  },
  delivery: { kind: 'raster-tiles', horizontalReference: known(mercator), scheme: 'xyz', tileSize: [256, 256], encoding: terrarium, format: 'lossless RGB PNG', tileTemplate: `${productRoot}/tiles/{z}/{x}/{y}.png`, zoom: { min: 5, max: known(18) }, availability: '547 prepared tiles; Swiss sample centres exist only at z7–18. Evaluation endpoint falls through to AWS outside inventory.', resampling: known('Swiss average z5–17/bilinear z18; AWS original ≤z15, cross-tile bilinear z15 overzoom above.') },
  sourceInformation: { description: 'Swiss 0.5 m distributed grid; transformed/resampled delivery. 1/256 m encoding precision is not accuracy. AWS overzoom adds no information.', informationCeiling: unknown('Useful rendered detail depends on location, source support and MapLibre mesh; z18 does not prove 0.5 m measurements.') },
  spatial: {
    coverage: known({ kind: 'asset', asset: { href: `${productRoot}/manifest.json`, sha256: '778745c36f2208e72a28a99923d00d81fcd0bd7f90e8759ba3f03362ccfc4627', selector: 'files entries with path prefix tiles/' }, crs: known(mercator), interpretation: 'Union of prepared tile footprints; not the Swiss source AOI or global endpoint footprint.' }),
    validSupport: unknown('Interior detail demonstrated, but no accepted support polygon: hard west/south joins failed. The whole AOI is not production-valid support.'),
    protectedInterior: unknown('No protected interior selected by the completed prototype/investigation.'),
    transitionSupport: unknown('2 km crop is insufficient for inferred kilometre-scale transition; no accepted overlap collar.'),
  },
  nodata: known('Swiss nodata excluded; AWS fill. Never encode -9999 or transparent DEM; underlying AWS semantics remain unknown.'),
  fallback: { product: aws, when: 'Outside prepared tile inventory or outside Swiss sample support', behavior: 'Evaluation server AWS original ≤z15, bilinear z15 overzoom above; this relationship does not expand Swiss coverage.' },
  rights: { licence: unknown('Combined rights inherit Swiss custom OGD and source-specific AWS terms.'), references: [...RIFFELHORN_SWISS_SOURCE.rights.references, ...AWS_VISUAL_PRODUCT.rights.references], attribution: ['©swisstopo', 'AWS terrain data credits'] },
  generation: { timestamp: unknown('Generation date 2026-10-03 recorded; exact timestamp not retained in repository summary.'), buildRecord: { href: regionalRecord, selector: 'identity, manifestSha256, processing, source.inputs, paths' } },
  documentation: [regionalRecord, 'docs/atlas/riffelhorn-regional-terrain-prototype.md', 'docs/atlas/riffelhorn-terrain-reconciliation.md'],
};

export const MAPTERHORN_EVALUATION_PRODUCT: TerrainProduct = {
  id: 'mapterhorn-public-terrain', name: 'Mapterhorn public terrain — 2026-10-03 evaluation snapshot',
  version: unknown('Public tiles do not expose an immutable dataset build version.'), revision: unknown('Inspected software commit is not an immutable hosted tile revision.'), producer: known('Mapterhorn'),
  surface: { kind: 'heterogeneous', description: 'Copernicus GLO-30 DSM global fallback and regional elevation datasets including DTMs.' },
  vertical: { kind: 'unknown', reason: 'Common output vertical normalization is not established; do not inherit a datum from one contributor.' }, elevationUnit: known('metre'),
  lineage: {
    contributors: [
      { kind: 'source', id: 'copernicus-glo30', revision: unknown('Hosted contributing release not fully established.') },
      { kind: 'source', id: 'swissalti3d', revision: known('Catalogue Riffelhorn inputs: four official 2024 0.5 m tiles.') },
      { kind: 'source', id: 'wales-1m-dtm', revision: unknown('Catalogue LiDAR 2020–2023; immutable hosted contribution revision not established.') },
    ], contributorList: 'partial', spatialMapping: 'catalogue-only',
    processing: [{ method: 'Catalogue-priority mosaic; cubic-spline warp, nodata fill, Gaussian blending and coarse-level averaging.', record: { href: 'docs/atlas/global-terrain-foundation-evaluation.md', selector: 'Dataset architecture / resolution findings' } }],
    limitations: 'Three relevant contributors shown, not all 151 catalogue sources. Footprints indicate candidate support, not exact per-pixel winner or contribution. Pinned software commit 077e6530bf410ce756fba8817eedfcea0ab0e806 does not pin hosted content.',
  },
  delivery: { kind: 'raster-tiles', horizontalReference: known(mercator), scheme: 'xyz', tileSize: [512, 512], encoding: terrarium, format: 'lossless RGB WebP', tileTemplate: 'https://tiles.mapterhorn.com/{z}/{x}/{y}.webp', zoom: { min: 0, max: unknown('Live TileJSON omitted zoom limits; catalogue shards up to z18 do not establish universal availability.') }, availability: 'Planet z0–12; sparse regional children z13+. Observed Swiss z17 present/z18 missing, Wales z16 present/z18 missing. Missing children 404; MapLibre parent search, not server substitution.', resampling: known('Cubic-spline reprojection, Gaussian source blending, 2×2 averaging at coarser levels; version-dependent rounding.') },
  sourceInformation: { description: 'Global GLO-30 nominal 30 m/1 arcsecond; Swiss 0.5 m distributed grid, Wales 1 m DTM. Neither tile dimensions nor zoom guarantee local source information.', informationCeiling: unknown('Region-dependent sparse information; no uniform global high-resolution ceiling.') },
  spatial: {
    coverage: known({ kind: 'asset', asset: { href: 'docs/atlas/global-terrain-foundation-evaluation.md', selector: 'Dataset architecture and verified catalogue coverage' }, crs: known(mercator), interpretation: 'Documented nominal global coarse product; regional fine coverage is heterogeneous, not global.' }),
    validSupport: unknown('No Meridian-accepted global support/quality mask; catalogue support is not a suitability assessment.'),
  },
  nodata: known('Processing sentinel -9999; remaining nodata encoded as zero without exported validity mask; water/missing semantics incompletely established.'),
  rights: { licence: unknown('Source-specific rights and public-service commitments remain incomplete; BSD-3 software does not license all data.'), references: ['https://mapterhorn.com/attribution/', 'docs/atlas/global-terrain-foundation-evaluation.md'], attribution: ['Mapterhorn and contributing terrain authorities; source-specific notices required'], limitations: 'Evaluation passed; production adoption did not. This record is not legal clearance.' },
  generation: { timestamp: unknown('Hosted generation time not established.') },
  documentation: ['docs/atlas/global-terrain-foundation-evaluation.md'],
};
