/** Small conservative containment checks; no reprojection, inventory fetching or GIS engine. */
import type { SpatialArea } from '../metadata/terrainMetadata';
import type { TerrainSelectionContext } from '../metadata/terrainHierarchy';

type Point = readonly [number, number];
type Ring = readonly Point[];
type Polygon = readonly Ring[];
const cross = (a: Point, b: Point, p: Point) => (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]);
const onEdge = (p: Point, a: Point, b: Point) => Math.abs(cross(a, b, p)) < 1e-9
  && p[0] >= Math.min(a[0], b[0]) && p[0] <= Math.max(a[0], b[0])
  && p[1] >= Math.min(a[1], b[1]) && p[1] <= Math.max(a[1], b[1]);
function inRing(p: Point, ring: Ring): boolean {
  let inside = false;
  for (let i = 1; i < ring.length; i++) {
    const a = ring[i - 1], b = ring[i];
    if (onEdge(p, a, b)) return true;
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}
const inPolygon = (p: Point, polygon: Polygon) => inRing(p, polygon[0]) && !polygon.slice(1).some(hole => inRing(p, hole));
function polygons(area: SpatialArea): { crs: string; values: readonly Polygon[] } | undefined {
  if (area.kind === 'asset') return undefined;
  if (area.kind === 'geojson') return { crs: 'OGC:CRS84', values: area.geometry.type === 'Polygon' ? [area.geometry.coordinates] : area.geometry.coordinates };
  const [x0, y0, x1, y1] = area.bounds;
  return { crs: area.crs.identifier ?? area.crs.name, values: [[[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]] };
}
/** Split an edge at support-boundary crossings, then test every intervening segment. */
function edgeInside(a: Point, b: Point, polygon: Polygon): boolean {
  const cuts = [0, 1], dx = b[0] - a[0], dy = b[1] - a[1];
  for (const ring of polygon) for (let i = 1; i < ring.length; i++) {
    const c = ring[i - 1], d = ring[i], ex = d[0] - c[0], ey = d[1] - c[1];
    const den = dx * ey - dy * ex;
    if (Math.abs(den) < 1e-12) continue;
    const t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den;
    const u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den;
    if (t >= 0 && t <= 1 && u >= 0 && u <= 1) cuts.push(t);
  }
  cuts.sort((x, y) => x - y);
  return cuts.slice(1).every((t, i) => {
    const middle = (t + cuts[i]) / 2;
    return inPolygon([a[0] + dx * middle, a[1] + dy * middle], polygon);
  });
}
export function containsTerrainQuery(area: SpatialArea, query: TerrainSelectionContext): 'inside' | 'outside' | 'unknown' {
  const support = polygons(area);
  if (!support) return 'unknown';
  if (query.footprint) {
    const footprint = polygons(query.footprint);
    if (!footprint || footprint.crs !== support.crs) return 'unknown';
    // Each requested polygon must fit one support component. No union stitching or dateline inference.
    return footprint.values.every(part => support.values.some(target =>
      part.every(ring => ring.every(p => inPolygon(p, target)) && ring.slice(1).every((p, i) => edgeInside(ring[i], p, target)))
      && !target.slice(1).some(hole => hole.some(p => inPolygon(p, part))))) ? 'inside' : 'outside';
  }
  if (!query.location || query.location.crs !== support.crs) return 'unknown';
  return support.values.some(polygon => inPolygon(query.location!.coordinates, polygon)) ? 'inside' : 'outside';
}
