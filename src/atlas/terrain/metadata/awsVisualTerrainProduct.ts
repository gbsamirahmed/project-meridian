/** Canonical metadata for the existing visual service. Unknown provenance/support remains unknown.
 * Kept separate from experimental examples so production imports no research fixtures. */
import { known, unknown } from './terrainMetadata';
import type { EntityReference, TerrainProduct } from './terrainMetadata';
const mercator = { name: 'WGS 84 / Pseudo-Mercator', identifier: 'EPSG:3857' };
const awsUnknown = 'Exact hosted AWS vertical reference and complete measurement lineage are not established.';
const terrarium = { name: 'terrarium', description: 'Metres = R*256 + G + B/256 - 32768.', quantizationIncrement: { value: 1 / 256, unit: 'metre' } };
const aws: EntityReference = { kind: 'product', id: 'aws-terrarium', revision: unknown('Mutable public hosted tiles; no complete immutable product revision established.') };

export const AWS_VISUAL_PRODUCT: TerrainProduct = {
  id: aws.id, name: 'AWS hosted Terrarium terrain used by production Atlas',
  version: unknown('No immutable hosted dataset version established.'), revision: aws.revision,
  producer: known('Tilezen/Mapzen terrain delivery on AWS'),
  surface: { kind: 'heterogeneous', description: 'Derived terrain mosaic; do not label all regions bare-earth. Riffelhorn cached tile headers identify EU-DEM input, not full ingestion lineage.' },
  vertical: { kind: 'unknown', reason: awsUnknown }, elevationUnit: known('metre'),
  lineage: {
    contributors: [], contributorList: 'unknown', spatialMapping: 'unavailable', processing: [],
    limitations: 'Local header eudem/eudem_dem_5deg_n45e005.tif is evidence of an input, not proof of hosted datum, exact preprocessing or global composition.',
  },
  delivery: {
    kind: 'raster-tiles', horizontalReference: known(mercator), scheme: 'xyz', tileSize: [256, 256],
    encoding: terrarium, format: 'RGB PNG', tileTemplate: 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
    zoom: { min: 0, max: unknown('Complete current hosted zoom availability is not established by these records; Atlas consumes through z15.') },
    availability: 'Global visual fallback; coverage is nominal delivery extent, not a per-pixel quality/validity claim.',
    resampling: unknown('Exact preprocessing of the currently hosted Riffelhorn tiles is incompletely established.'),
  },
  sourceInformation: { description: 'Region-dependent measurement lineage/resolution. EU-DEM source hint at Riffelhorn does not establish hosted native resolution.', informationCeiling: unknown('Neither Atlas geometry z14 nor relief z15 ceilings prove measurement resolution.') },
  spatial: {
    coverage: known({ kind: 'native-rectangle', crs: mercator, axisOrder: 'xy', bounds: [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244] }),
    validSupport: unknown('No global assessed quality/validity geometry; nominal Web Mercator delivery coverage only.'),
  },
  nodata: unknown('Complete hosted missing-data/water semantics are not established.'),
  rights: { licence: unknown('Source-specific data rights; attribution page is not a single universal licence.'), references: ['https://github.com/tilezen/joerd/blob/master/docs/attribution.md'], attribution: ['Terrain data credits (Tilezen/Joerd attribution link)'] },
  generation: { timestamp: unknown('Hosted build timestamp unknown.') },
  documentation: ['docs/atlas/riffelhorn-terrain-reconciliation.md', 'src/atlas/map/visualTerrainConfig.ts'],
};
