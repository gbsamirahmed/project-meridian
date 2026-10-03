/** Atlas data semantics, independent of rendering and analytical sampling policy.
 * These owned metadata records are not a resolver or an external JSON schema.
 */
export type Knowledge<T> =
  | { status: 'known'; value: T }
  | { status: 'unknown'; reason: string };

export const known = <T>(value: T): Knowledge<T> => ({ status: 'known', value });
export const unknown = <T>(reason: string): Knowledge<T> => ({ status: 'unknown', reason });

export interface ReferenceSystem {
  name: string;
  /** Authority identifier where established, e.g. EPSG:2056 or EPSG:5728. */
  identifier?: string;
  documentation?: string;
}

export interface AssetReference {
  /** URL, repository path or documented external-root-relative URI/template. */
  href: string;
  sha256?: string;
  /** Describes a subset/field when the asset is a manifest or catalogue. */
  selector?: string;
}

export interface EntityReference {
  kind: 'source' | 'product';
  id: string;
  revision: Knowledge<string>;
}

export type TerrainSurface =
  | { kind: 'dtm' | 'dsm' | 'heterogeneous'; description: string }
  | { kind: 'other'; description: string }
  | { kind: 'unknown'; reason: string };

type Position2D = readonly [number, number];
type Ring = readonly Position2D[];
/** GeoJSON footprints are 2D OGC:CRS84 lon/lat; never LV95 or LN02 z values. */
export type FootprintGeometry =
  | { type: 'Polygon'; coordinates: readonly Ring[] }
  | { type: 'MultiPolygon'; coordinates: readonly (readonly Ring[])[] };

export type SpatialArea =
  | { kind: 'geojson'; geometry: FootprintGeometry }
  | { kind: 'native-rectangle'; crs: ReferenceSystem; bounds: readonly [number, number, number, number]; axisOrder: 'xy' }
  | { kind: 'asset'; asset: AssetReference; crs: Knowledge<ReferenceSystem>; interpretation: string };

export interface SpatialSupport {
  area: SpatialArea;
  purpose: string;
  /** An assessment/reference, not a declaration that the footprint proves quality. */
  basis: string;
}

export interface ResolutionInformation {
  /** Distributed grid, not independent observation/measurement resolution. */
  gridSpacing?: { x: number; y: number; unit: string; crs: ReferenceSystem };
  nominalResolution: Knowledge<string>;
  measurementResolution: Knowledge<string>;
  limitations: string;
}

export interface RightsInformation {
  /** Source-specific terms or unknown; software licence is not data permission. */
  licence: Knowledge<string>;
  references: readonly string[];
  attribution: readonly string[];
  limitations?: string;
}

export interface TerrainSource {
  id: string;
  name: string;
  authority: Knowledge<string>;
  dataset: string;
  release: Knowledge<string>;
  revision: Knowledge<string>;
  surface: TerrainSurface;
  horizontalReference: Knowledge<ReferenceSystem>;
  verticalReference: Knowledge<ReferenceSystem>;
  elevationUnit: Knowledge<string>;
  resolution: ResolutionInformation;
  /** Acquisition period/basis, independent of release, download and build dates. */
  acquisition: Knowledge<{ description: string; start?: string; end?: string }>;
  coverage: { scope: 'dataset' | 'retained-input-selection'; area: Knowledge<SpatialArea> };
  nodata: Knowledge<string>;
  quality?: Knowledge<string>;
  rights: RightsInformation;
  documentation: readonly string[];
  assets?: readonly AssetReference[];
}

export interface VerticalTransformation {
  from: ReferenceSystem;
  to: ReferenceSystem;
  method: string;
  accuracy: Knowledge<string>;
  limitations: string;
}

export type ProductVerticalSemantics =
  | { kind: 'known'; reference: ReferenceSystem }
  | { kind: 'preserved'; from: EntityReference; reference: Knowledge<ReferenceSystem> }
  | { kind: 'transformed'; transformation: VerticalTransformation }
  | { kind: 'heterogeneous'; parts: readonly { contributor: EntityReference; reference: Knowledge<ReferenceSystem> }[]; description: string }
  | { kind: 'unknown'; reason: string };

export interface ProcessingStep {
  method: string;
  software?: Readonly<Record<string, string>>;
  parameters?: Readonly<Record<string, string | number | boolean>>;
  record?: AssetReference;
  verticalTransformation?: VerticalTransformation;
}

export interface ContributionMask {
  asset: AssetReference;
  /** A label mask, weights or other representation; weights are not confidence. */
  interpretation: string;
  contributors: readonly EntityReference[];
}

export interface TerrainLineage {
  contributors: readonly EntityReference[];
  contributorList: 'complete' | 'partial' | 'unknown';
  spatialMapping: 'mask' | 'catalogue-only' | 'unavailable';
  contributionMask?: ContributionMask;
  processing: readonly ProcessingStep[];
  limitations: string;
}

export type TerrainDelivery =
  | {
      kind: 'raster-tiles'; horizontalReference: Knowledge<ReferenceSystem>;
      scheme: 'xyz' | 'tms'; tileSize: readonly [number, number];
      encoding: { name: string; description: string; quantizationIncrement?: { value: number; unit: string } };
      format: string; tileTemplate: string;
      zoom: { min: number; max: Knowledge<number> };
      availability: string; resampling: Knowledge<string>;
    }
  | { kind: 'raster-file'; horizontalReference: Knowledge<ReferenceSystem>; format: string; assets: readonly AssetReference[] }
  | { kind: 'other'; description: string; assets: readonly AssetReference[] }
  | { kind: 'unknown'; reason: string };

export interface TerrainProduct {
  id: string;
  name: string;
  version: Knowledge<string>;
  /** Immutable build identity if known; a mutable URL is not a revision. */
  revision: Knowledge<string>;
  producer: Knowledge<string>;
  surface: TerrainSurface;
  vertical: ProductVerticalSemantics;
  elevationUnit: Knowledge<string>;
  lineage: TerrainLineage;
  delivery: TerrainDelivery;
  sourceInformation: {
    description: string;
    /** Scoped statement about genuine information; independent of delivery zoom. */
    informationCeiling: Knowledge<string>;
  };
  spatial: {
    /** Coverage of this delivered/prepared product, not necessarily source coverage. */
    coverage: Knowledge<SpatialArea>;
    validSupport: Knowledge<SpatialSupport>;
    protectedInterior?: Knowledge<SpatialSupport>;
    transitionSupport?: Knowledge<SpatialSupport>;
  };
  nodata: Knowledge<string>;
  /** Descriptive relationship only; no priority or source-selection execution. */
  fallback?: { product: EntityReference; when: string; behavior: string };
  rights: RightsInformation;
  generation: { timestamp: Knowledge<string>; buildRecord?: AssetReference };
  documentation: readonly string[];
}

/** Current representation form, distinct from data provenance and style policy. */
export interface RasterDemHeightfieldRepresentation {
  kind: 'raster-dem-heightfield';
  product: EntityReference;
  context: string;
}
