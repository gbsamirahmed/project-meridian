/** Atlas visual-terrain declarations. No selection, fusion or renderer execution. */
import type {
  AssetReference, EntityReference, Knowledge, ProcessingStep,
  RasterDemHeightfieldRepresentation, SpatialArea, SpatialSupport, TerrainProduct,
} from './terrainMetadata';

/** Reuse the current heightfield contract; other forms need their own adapter contract. */
export type TerrainRepresentation = RasterDemHeightfieldRepresentation | {
  kind: 'other'; product: EntityReference; context: string;
  form: string; adapterContract: AssetReference;
};

export interface TerrainValidationEvidence {
  category: 'preparation-fidelity' | 'terrain-accuracy' | 'source-preservation'
    | 'parent-child-consistency' | 'numerical-continuity' | 'morphology'
    | 'source-edge' | 'visual-continuity' | 'renderer-navigation' | 'provenance';
  state: 'not-assessed' | 'passed' | 'qualified' | 'failed';
  scope: string;
  evidence: readonly AssetReference[];
  limitations: string;
}

/** Prepared content and its recipe are separate identities. Neither is a mutable URL. */
export type TerrainProductIdentity = {
  kind: 'immutable-prepared'; revision: string;
  preparation: AssetReference;
  contentManifest: {
    sha256: string; hashScope: 'manifest-bytes' | 'canonical-inventory';
    /** Evidence of the hashed manifest/canonical inventory, not a hash of this reference file. */
    record: AssetReference;
  };
} | { kind: 'external-unpinned'; reason: string };

export interface TerrainProductBinding {
  product: TerrainProduct;
  identity: TerrainProductIdentity;
  origin: { kind: 'source-derived'; sourceFamily: string }
    | { kind: 'derived-transition'; sourceFamily: string; compositionPolicy: string }
    | { kind: 'unresolved'; reason: string };
  validation: readonly TerrainValidationEvidence[];
  limitations: readonly string[];
}

export interface TerrainLevelSupport {
  state: 'complete' | 'partial' | 'absent' | 'unknown';
  validSupport: Knowledge<SpatialSupport>;
  /** Required for partial support: labels/fractions distinguish complete/partial/absent. */
  partition?: AssetReference;
  interpretation: string;
}

export interface TerrainLevelReference { family: string; level: string }

export interface TerrainHierarchyLevel {
  id: string;
  /** Ordinal within this family's declared scheme, increasing with detail. Not camera zoom. */
  order: number;
  representation: TerrainRepresentation;
  derivation: 'source-sampled' | 'resampled' | 'generalized-parent'
    | 'regional-derived-parent' | 'overzoom';
  support: TerrainLevelSupport;
  /** A parent may be in another family, but then it is explicitly a source-family handoff. */
  parent?: TerrainLevelReference;
  parentOperation: Knowledge<ProcessingStep>;
  /** Delivery sample spacing scoped to location/CRS; not measurement resolution. */
  sampleSpacing: Knowledge<string>;
}

export interface TerrainFamily {
  id: string;
  /** Role is independent of source-derived/synthetic origin. */
  role: 'common' | 'regional' | 'transition';
  sourceFamily: string;
  levelScheme: string;
  levels: readonly TerrainHierarchyLevel[];
  informationCeiling: Knowledge<string>;
  overzoom: { allowed: boolean; description: string };
  limitations: readonly string[];
}

export interface RegionalTerrainPyramid extends TerrainFamily {
  role: 'regional';
  protectedInterior?: Knowledge<SpatialSupport>;
  /** Availability of overlap is not validation of a reconciliation method. */
  transitionSupport: Knowledge<SpatialSupport>;
}

export interface TerrainCompositionPolicy {
  id: string;
  products: readonly EntityReference[];
  operations: readonly ProcessingStep[];
  heightPolicy: {
    kind: 'no-numerical-combination' | 'preserve-native-heterogeneous'
      | 'declared-common-frame';
    rationale: string;
    /** Explicit permission/purpose, not inferred from compatible-looking metadata. */
    permittedUse: 'visual-representation-only' | 'declared-geodetic-product';
  };
  contribution: {
    mapping: 'product-lineage' | 'spatial-map';
    spatiallyVarying: boolean;
    map?: AssetReference;
    semantics: 'categorical-identity' | 'composition-weights' | 'signed-operator';
    reconstruction: AssetReference;
    interpretation: string;
  };
  support: Knowledge<SpatialSupport>;
  protectedInterior?: Knowledge<SpatialSupport>;
  validation: readonly TerrainValidationEvidence[];
  limitations: readonly string[];
}

export interface TerrainSelectionPolicy {
  /** Ordered tie-breaking only; eligibility still requires spatial AND scale support. */
  regionalOrder: readonly string[];
  eligibility: AssetReference;
  missingFineLevel: 'same-family-parent-then-common' | 'unavailable';
  unsupportedRegional: 'common' | 'unavailable';
  unavailableTransition: 'common' | 'unavailable';
  /** Crossing families is never an ordinary LOD fallback. */
  sourceFamilyHandoff: { policy: AssetReference; state: 'unresolved' | 'declared' };
}

export interface TerrainHierarchy {
  id: string;
  revision: string;
  purpose: 'visual-terrain';
  products: readonly TerrainProductBinding[];
  common: TerrainFamily & { role: 'common' };
  regional: readonly RegionalTerrainPyramid[];
  transitions: readonly (TerrainFamily & { role: 'transition' })[];
  compositionPolicies: readonly TerrainCompositionPolicy[];
  selection: TerrainSelectionPolicy;
  /** Renderer-owned portrayal mechanisms; no implication of data reconciliation. */
  renderOnlyContinuity: readonly { mechanism: string; contract: AssetReference }[];
  limitations: readonly string[];
}

/** Future resolver inputs, not a resolver API implementation or camera-zoom rule. */
export interface TerrainSelectionContext {
  location?: { coordinates: readonly [number, number]; crs: string };
  footprint?: SpatialArea;
  scale: { scheme: string; requestedLevel: string };
  provenanceRequirement: 'product-lineage' | 'spatial-contributors';
}

/** Classification of a declared relationship, not proof of numerical compatibility. */
export function classifyTerrainRefinement(parent: TerrainFamily, child: TerrainFamily):
  'within-family-lod' | 'source-family-handoff' {
  return parent.sourceFamily === child.sourceFamily
    ? 'within-family-lod' : 'source-family-handoff';
}
