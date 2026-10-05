/** Opt-in second-region proof metadata. Never imported by production configuration. */
import record from './tryfanProductRecord.json';
import { known, unknown } from './terrainMetadata';
import type { SpatialArea, HeightReference, TerrainSource, TerrainProduct } from './terrainMetadata';
import type { TerrainHierarchy } from './terrainHierarchy';
import { PRODUCTION_TERRAIN_HIERARCHY, productionTerrainRegistry } from '../runtime/productionTerrainHierarchy';
import { registerTerrainHierarchy } from '../runtime/terrainRegistry';

const report = 'docs/atlas/tryfan-second-region-proof.md';
const upstream = 'https://datamap.gov.wales/maps/lidar-data-download/';
const native = { name: 'OSGB36 / British National Grid', identifier: 'EPSG:27700' };
const sourceArea: SpatialArea = { kind: 'native-rectangle', crs: native, bounds: [264900, 357800, 267900, 360800], axisOrder: 'xy' };
const rights = { licence: known('Open Government Licence v3.0'), references: [upstream, 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'], attribution: ['Contains Welsh Government information licensed under the Open Government Licence v3.0.'], limitations: 'Prepared research product; retain attribution and check source-specific notices before public delivery. Catalogue licence is unspecified; the official download page explicitly licenses the linked DTM.' };
const height = unknown<HeightReference>('Checked source GeoTIFF and official catalogue/download metadata do not establish the vertical datum. Prior local ODN convention is not authoritative evidence. Native values retained, no vertical transformation.');
export const TRYFAN_SOURCE: TerrainSource = {
  id: 'welsh-government-tryfan-dtm-selection', name: 'Welsh Government Tryfan 1m DTM retained selection', authority: known('Welsh Government'),
  dataset: 'National LiDAR DTM 2020–2023, 32-bit COG bounded subset', release: known('National 2020–2023 distribution; delivery 11 in this AOI'), revision: known(record.source.sha256),
  surface: { kind: 'dtm', description: 'Provider bare-earth DTM; filtering limitations remain, not a true 3D surface.' },
  horizontalReference: known(native), verticalReference: height, elevationUnit: known('metre'),
  resolution: { gridSpacing: { x: 1, y: 1, unit: 'metre', crs: native }, nominalResolution: known('Published 1m raster grid'), measurementResolution: unknown('Independent measurement resolution/point density and local accuracy not established by the checked metadata.'), limitations: 'Distributed postings are not a guarantee of independent observations or cliff/overhang geometry.' },
  acquisition: known({ description: 'All 16 intersecting catalogue items: delivery 11, 2021-03-02; mosaic cell epochs not independently mapped.', start: '2021-03-02', end: '2021-03-02' }),
  coverage: { scope: 'retained-input-selection', area: known(sourceArea) }, nodata: known('Source sentinel -9999; hash-verified subset contains 9,000,000 valid cells and zero nodata.'), rights,
  documentation: [upstream, 'https://datamap.gov.wales/layers/geonode:welsh_government_lidar_tile_catalogue_2020_2023/metadata_detail', report],
  assets: [{ href: 'meridian-data://'+record.source.path, sha256: record.source.sha256 }],
};
const source = { kind: 'source' as const, id: TRYFAN_SOURCE.id, revision: TRYFAN_SOURCE.revision };
const support = (area: SpatialArea) => known({ area, purpose: 'Complete deliverable Welsh regional tiles only', basis: 'Full source-pixel footprints, 2m interpolation guard, strict recursive nodata propagation and full-tile finite checks. '+report });
const finest = record.levels.find(l => l.zoom === 17)!;
export const TRYFAN_PRODUCT: TerrainProduct = {
  id: record.version, name: 'Meridian Tryfan Welsh regional pyramid', version: known('v2'), revision: known(record.identity), producer: known('Meridian'),
  surface: TRYFAN_SOURCE.surface, vertical: { kind: 'preserved', from: source, reference: height }, elevationUnit: known('metre'),
  lineage: { contributors: [source], contributorList: 'complete', spatialMapping: 'uniform',
    processing: [{ method: '2D horizontal EPSG:27700 → EPSG:3857 reprojection, bilinear at z17, strict support; recursive unencoded 2x2 equal-Mercator-area means with float64 accumulation/float32 storage; independently encode each complete tile.', record: { href: report }, parameters: { finestLevel: 17, parentDeliveryMinimum: 14, sourceGuardMetres: 2, threads: 1 } }], limitations: 'No vertical/registration correction, sharpening, common padding or reconciliation. Partial tiles omitted; support contracts at coarse levels.' },
  delivery: { kind: 'raster-tiles', horizontalReference: known({ name: 'WGS84 / Pseudo-Mercator', identifier: 'EPSG:3857' }), scheme: 'xyz', tileSize: [256, 256], encoding: { name: 'Terrarium', description: 'RGB height encoding; native height reference unchanged.', quantizationIncrement: { value: 1/256, unit: 'metre' } }, format: 'RGB PNG', tileTemplate: 'http://127.0.0.1:4186/regional/{z}/{x}/{y}.png', zoom: { min: 14, max: known(17) }, availability: 'Opt-in local research endpoint; complete tiles only; not production or globally available.', resampling: known(record.delivery.parents) },
  sourceInformation: { description: record.delivery.sourceInformation, informationCeiling: known('1m distributed source grid. z17 samples approximately 0.72m near Tryfan and is resampled; no level asserts new independent measurements.') },
  spatial: { coverage: known(finest.validSupport as unknown as SpatialArea), validSupport: support(finest.validSupport as unknown as SpatialArea) },
  nodata: known('No nodata encoded. Full finite tiles delivered; partial and absent tiles retained in support inventory, then explicit common fallback.'), rights,
  generation: { timestamp: unknown('Generation wall-clock date is recorded in the proof, excluded from immutable deterministic content identity.'), buildRecord: { href: report } }, documentation: [report],
};

/** Same generic registry/selector/adapter as AWS; metadata changes terminate here. */
export function createTryfanTerrainProof() {
  const hierarchy: TerrainHierarchy = structuredClone(PRODUCTION_TERRAIN_HIERARCHY);
  hierarchy.id = 'tryfan-second-region-proof'; hierarchy.revision = '1';
  hierarchy.products = [...hierarchy.products, { product: TRYFAN_PRODUCT,
    identity: { kind: 'immutable-prepared', revision: record.identity, preparation: { href: 'scripts/atlas/tryfan_product.py', sha256: record.processing.scriptSha256 }, contentManifest: { sha256: record.manifestSha256, hashScope: 'manifest-bytes', record: { href: 'meridian-data://derived/atlas/tryfan/'+record.version+'/manifest.json' } } },
    origin: { kind: 'source-derived', sourceFamily: 'welsh-2021-regional' }, validation: [
      { category: 'source-preservation', state: 'passed', scope: 'Retained DTM/catalogue hashes before and after preparation', evidence: [{ href: report }], limitations: 'Encoding and resampling change representation samples; upstream files remain immutable.' },
      { category: 'preparation-fidelity', state: 'qualified', scope: '59,392 finest-level source-transfer checks and Terrarium quantization', evidence: [{ href: 'docs/atlas/tryfan-second-region-proof.json' }], limitations: '0.01989m RMS and 0.42062m maximum transfer difference; not terrain accuracy.' },
      { category: 'parent-child-consistency', state: 'passed', scope: 'Unencoded 2x2 parent means at z14–16', evidence: [{ href: report }], limitations: 'Float32 rounding remains; cross-family handoff is not validated.' },
      { category: 'renderer-navigation', state: 'qualified', scope: 'Nine matched cameras and seven bounded navigation sequences', evidence: [{ href: report }], limitations: 'Hard support-edge relief and coarse handoff remain unresolved; no universal no-popping claim.' },
    ], limitations: ['Prepared-source fidelity is not real-world accuracy; native vertical datum remains unverified.'] }];
  const levels = record.levels.filter(l => l.completeTiles > 0).map((l, i, all) => ({ id: `z${l.zoom}`, order: l.zoom,
    representation: { kind: 'raster-dem-heightfield' as const, product: { kind: 'product' as const, id: TRYFAN_PRODUCT.id, revision: TRYFAN_PRODUCT.revision }, context: 'Opt-in real Welsh regional heightfield proof' },
    derivation: l.zoom < 17 ? 'regional-derived-parent' as const : 'resampled' as const,
    support: { state: 'complete' as const, validSupport: support(l.validSupport as unknown as SpatialArea), interpretation: 'Complete over the exact union of delivered full tiles, not the source rectangle. Partial tiles outside this support are withheld.' },
    ...(i ? { parent: { family: 'welsh-regional', level: `z${all[i-1].zoom}` } } : {}), parentOperation: known({ method: record.delivery.parents }), sampleSpacing: known(`${l.groundSampleMetresAtBenchmark.toFixed(3)}m near latitude 53.115°; delivery sampling, not measurement resolution`) }));
  hierarchy.regional = [{ id: 'welsh-regional', role: 'regional', sourceFamily: 'welsh-2021-regional', levelScheme: hierarchy.common.levelScheme, levels,
    informationCeiling: TRYFAN_PRODUCT.sourceInformation.informationCeiling, overzoom: { allowed: true, description: 'Renderer may overzoom z17; no additional source information.' }, transitionSupport: unknown('No transition or reconciliation assessed or generated.'), limitations: ['z13 has no full tile; source-family handoff to common is unresolved. No protected/transition geometry is inferred from validity.'] }];
  hierarchy.selection = { ...hierarchy.selection, regionalOrder: ['welsh-regional'], eligibility: { href: report } };
  hierarchy.limitations = ['Experimental second-source proof; production and analytical terrain unchanged. Hard family handoff permitted, not reconciled.'];
  const registry = registerTerrainHierarchy(hierarchy, { ...productionTerrainRegistry.options,
    scaleLevels: Array.from({ length: 19 }, (_, order) => ({ scheme: hierarchy.common.levelScheme, id: `z${order}`, order })),
    legacyCommon: { ...productionTerrainRegistry.options.legacyCommon!, addressingExtent: { kind: 'native-rectangle', crs: { name: 'OGC:CRS84', identifier: 'OGC:CRS84' }, axisOrder: 'xy', bounds: [-180, -85.0511287798066, 180, 85.0511287798066] } },
  });
  return registry;
}
