import type { SpatialArea, TerrainProduct, TerrainSource } from './terrainMetadata';

/** Focused checks on owned typed records, not a parser for untrusted JSON,
 * a GIS topology validator or proof of scientific/production suitability. */
function common(record: TerrainSource | TerrainProduct): string[] {
  const errors: string[] = [];
  if (!record.id.trim()) errors.push('id must be nonempty');
  if (!record.name.trim()) errors.push('name must be nonempty');
  function visit(value: unknown, path: string): void {
    if (!value || typeof value !== 'object') return;
    const object = value as Record<string, unknown>;
    if ((object.status === 'unknown' || object.kind === 'unknown') &&
        (typeof object.reason !== 'string' || !object.reason.trim())) {
      errors.push(`${path}: unknown requires a reason`);
    }
    if ('sha256' in object && (typeof object.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(object.sha256))) {
      errors.push(`${path}: invalid SHA-256`);
    }
    if ('href' in object && (typeof object.href !== 'string' || !object.href.trim())) errors.push(`${path}: empty asset reference`);
    for (const [key, child] of Object.entries(object)) visit(child, `${path}.${key}`);
  }
  visit(record, record.id);
  return errors;
}

function checkArea(area: SpatialArea, errors: string[], path: string): void {
  if (area.kind === 'native-rectangle') {
    const [x0, y0, x1, y1] = area.bounds;
    if (!area.bounds.every(Number.isFinite) || x0 >= x1 || y0 >= y1) errors.push(`${path}: invalid native rectangle`);
    if (!area.crs.name.trim()) errors.push(`${path}: missing rectangle CRS`);
  } else if (area.kind === 'geojson') {
    const polygons = area.geometry.type === 'Polygon' ? [area.geometry.coordinates] : area.geometry.coordinates;
    if (!polygons.length) errors.push(`${path}: empty footprint`);
    for (const rings of polygons) {
      if (!rings.length) errors.push(`${path}: polygon requires an exterior ring`);
      for (const ring of rings) {
        if (ring.length < 4 || ring[0]?.[0] !== ring.at(-1)?.[0] || ring[0]?.[1] !== ring.at(-1)?.[1]) {
          errors.push(`${path}: footprint rings must be closed and have at least four positions`);
        }
        if (ring.some(point => point.length !== 2 || !Number.isFinite(point[0]) || !Number.isFinite(point[1]) || Math.abs(point[0]) > 180 || Math.abs(point[1]) > 90)) {
          errors.push(`${path}: GeoJSON requires 2D longitude/latitude positions`);
        }
      }
    }
  }
}

export function validateTerrainSource(source: TerrainSource): string[] {
  const errors = common(source);
  const grid = source.resolution.gridSpacing;
  if (grid && (!Number.isFinite(grid.x) || !Number.isFinite(grid.y) || grid.x <= 0 || grid.y <= 0 || !grid.unit.trim())) {
    errors.push('grid spacing must be finite, positive and have units');
  }
  if (source.coverage.area.status === 'known') checkArea(source.coverage.area.value, errors, 'source coverage');
  return errors;
}

export function validateTerrainProduct(product: TerrainProduct): string[] {
  const errors = common(product);
  for (const [role, value] of Object.entries(product.spatial)) {
    if (value?.status === 'known') checkArea('area' in value.value ? value.value.area : value.value, errors, role);
  }
  const delivery = product.delivery;
  if (delivery.kind === 'raster-tiles') {
    if (delivery.tileSize.some(n => !Number.isInteger(n) || n <= 0)) errors.push('tile dimensions must be positive integers');
    if (!Number.isInteger(delivery.zoom.min) || delivery.zoom.min < 0 ||
        (delivery.zoom.max.status === 'known' && (!Number.isInteger(delivery.zoom.max.value) || delivery.zoom.max.value < delivery.zoom.min))) {
      errors.push('invalid delivery zoom range');
    }
    const increment = delivery.encoding.quantizationIncrement;
    if (increment && (!Number.isFinite(increment.value) || increment.value <= 0 || !increment.unit.trim())) errors.push('invalid encoding increment');
  }
  const lineage = product.lineage;
  if (lineage.contributorList === 'complete' && !lineage.contributors.length) errors.push('complete lineage requires contributors');
  if (lineage.spatialMapping === 'uniform' && (lineage.contributorList !== 'complete' || lineage.contributors.length !== 1)) errors.push('uniform contribution requires one complete immediate contributor');
  if (lineage.spatialMapping === 'mask' && !lineage.contributionMask) errors.push('mask mapping requires a mask reference');
  if (lineage.spatialMapping !== 'mask' && lineage.contributionMask) errors.push('mask reference requires mask mapping');
  if (lineage.contributionMask) {
    const keys = new Set(lineage.contributors.map(ref => `${ref.kind}:${ref.id}`));
    if (!lineage.contributionMask.contributors.length || lineage.contributionMask.contributors.some(ref => !keys.has(`${ref.kind}:${ref.id}`))) {
      errors.push('mask contributors must occur in lineage');
    }
  }
  if (product.vertical.kind === 'heterogeneous' && !product.vertical.parts.length) errors.push('heterogeneous vertical semantics require parts');
  const transforms = [...lineage.processing.flatMap(step => step.verticalTransformation ? [step.verticalTransformation] : []),
    ...(product.vertical.kind === 'transformed' ? [product.vertical.transformation] : [])];
  for (const transform of transforms) {
    if (!transform.from.name.trim() || !transform.to.name.trim() || !transform.method.trim() || !transform.limitations.trim()) errors.push('vertical transformation requires references, method and limitations');
  }
  return errors;
}
