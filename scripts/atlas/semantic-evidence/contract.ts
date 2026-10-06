/** ATLAS SEMANTIC EVIDENCE CONTRACT v1. Declarations only; no production consumer.
 * Existing generic primitives stay at their canonical location. Type-only reuse
 * does not make semantic evidence terrain metadata.
 */
import type { AssetReference, EntityReference, Knowledge, ProcessingStep,
  ReferenceSystem, RightsInformation, SpatialArea } from '../../../src/atlas/terrain/metadata/terrainMetadata';

export interface DefinitionRef { readonly id: string; readonly revision: string }
export type NativeScalar = string | number | boolean | null;
export type NativeFields = Readonly<Record<string, NativeScalar>>;
export type ValueKind = SemanticValue['kind'];
/** Stable, revisioned definitions; source-native namespaces and common concepts coexist.
 * Definitions are retained summaries plus source references, not copied ontologies. */
export interface SemanticDefinition extends DefinitionRef {
  readonly kind: 'property' | 'value' | 'condition';
  readonly vocabulary: { readonly id: string; readonly version: Knowledge<string> };
  readonly label: string;
  readonly meaning: string;
  readonly reference: AssetReference;
  readonly valueKinds?: readonly ValueKind[]; // Required only for property definitions.
  /** Optional definition-specific qualifications preventing known source misuse. */
  readonly requiredModes?: readonly EvidenceMode[];
  readonly requiredConditions?: readonly DefinitionRef[];
}
export interface FeatureRef {
  readonly namespace: EntityReference; // Source/product-scoped; NOT a global equivalence.
  readonly id: string;
  readonly kind: 'feature' | 'inventory-object' | 'event';
}
export type EvidenceGeometry = SpatialArea
  | { readonly kind: 'native-point'; readonly crs: ReferenceSystem; readonly coordinates: readonly [number, number] }
  | { readonly kind: 'native-line'; readonly crs: ReferenceSystem; readonly coordinates: readonly (readonly [number, number])[] };
export interface ClaimSupport {
  readonly geometry: EvidenceGeometry;
  readonly meaning: string; // Cell assignment, original mosaic, inventory outline, etc.
  readonly grain: Knowledge<string>; // Grid/MMU/generalisation; never positional accuracy.
}
export type TimeExtent =
  | { readonly kind: 'instant' | 'epoch'; readonly value: string; readonly precision: 'year' | 'month' | 'day' | 'second'; readonly basis: string }
  | { readonly kind: 'interval'; readonly start: string; readonly end: string; readonly precision: 'year' | 'month' | 'day' | 'second'; readonly basis: string }
  | { readonly kind: 'unknown'; readonly reason: string };
export interface ClaimTime {
  readonly role: 'observation' | 'survey' | 'event' | 'nominal-epoch' | 'asserted-validity';
  readonly extent: TimeExtent;
}
export interface ReferenceCondition {
  readonly definition: DefinitionRef;
  readonly native: NativeFields;
  readonly qualification: string; // Unknown numeric level/model vintage can be declared here.
}
export type EvidenceMode = 'observation' | 'detection' | 'classification' | 'survey-inventory'
  | 'interpreted-mapping' | 'derived' | 'model' | 'scenario' | 'event-record';
export type LineageInput =
  | { readonly kind: 'resource'; readonly ref: EntityReference; readonly role: string }
  | { readonly kind: 'claim'; readonly ref: DefinitionRef; readonly role: string };
export interface EvidenceBasis {
  /** Nonempty set: mixed origins are explicit, not collapsed to one mode. */
  readonly modes: readonly EvidenceMode[];
  readonly description: string;
  readonly inputs: readonly LineageInput[];
  readonly completeness: 'complete' | 'partial' | 'unknown';
  readonly limitations: string;
  readonly processing: readonly (ProcessingStep & { readonly revision: Knowledge<string> })[];
}
/** All numeric semantics are discriminated. No generic confidence number. */
export type SemanticValue =
  | { readonly kind: 'category'; readonly term: DefinitionRef }
  | { readonly kind: 'descriptor'; readonly text: string }
  | { readonly kind: 'quantity'; readonly value: number; readonly unit: string }
  | { readonly kind: 'fraction'; readonly value: number; readonly denominator: string; readonly support: ClaimSupport }
  | { readonly kind: 'probability'; readonly value: number; readonly event: string; readonly basis: string }
  | { readonly kind: 'occurrence'; readonly value: number; readonly denominator: string; readonly period: TimeExtent }
  | { readonly kind: 'detection'; readonly outcome: 'detected' | 'not-detected'; readonly target: string }
  | { readonly kind: 'membership'; readonly feature: FeatureRef }
  | { readonly kind: 'composition'; readonly components: readonly {
      readonly term: Knowledge<DefinitionRef>; readonly fraction: number;
    }[]; readonly denominator: string; readonly support: ClaimSupport };
/** A non-detection is an asserted detection outcome, never an evidence gap or absence proof. */
export type ClaimResult =
  | { readonly kind: 'assertion'; readonly value: SemanticValue }
  | { readonly kind: 'gap'; readonly reason: 'outside-support' | 'no-observation' | 'not-classified'
      | 'missing-inventory' | 'unsupported' | 'unknown' | 'not-applicable'; readonly explanation: string };
export interface QualityStatement {
  readonly kind: 'validation' | 'confidence' | 'probability' | 'survey' | 'unspecified';
  readonly scope: { readonly kind: 'product' | 'class' | 'claim' | 'spatial'; readonly description: string };
  readonly metric: string;
  readonly meaning: string;
  readonly value?: { readonly kind: 'numeric'; readonly value: number; readonly unit: string }
    | { readonly kind: 'label'; readonly label: string };
  readonly reference: AssetReference;
}
export interface SemanticResource {
  readonly ref: EntityReference;
  readonly domain: 'semantics' | 'observation' | 'survey' | 'model' | 'terrain' | 'appearance';
  readonly name: string;
  readonly definition: AssetReference;
  readonly rights: RightsInformation;
  readonly coverage?: Knowledge<SpatialArea>;
  readonly dates?: readonly { readonly role: 'processing' | 'publication' | 'retrieval'; readonly extent: TimeExtent }[];
  readonly inputs: readonly EntityReference[];
}
/** Relation direction is native extension relative to target extension:
 * broader = native includes cases outside target; narrower = native subset of target.
 * Compatible is usable with stated qualification, NEVER an equivalence proof. */
export interface SemanticMapping extends DefinitionRef {
  readonly from: DefinitionRef;
  readonly target: DefinitionRef; // Candidate target, even if rejected.
  readonly relationship: 'compatible' | 'broader' | 'narrower' | 'partial' | 'ambiguous' | 'incompatible' | 'unmappable';
  readonly method: ProcessingStep;
  readonly loss: readonly string[]; // Explicit [] means no identified loss under qualification.
  readonly qualification: string;
}
export interface Interpretation {
  readonly mapping: DefinitionRef;
  readonly disposition: 'qualified' | 'unresolved' | 'rejected';
}
export interface ClaimContext {
  readonly support: ClaimSupport;
  readonly time: readonly ClaimTime[];
  readonly evidence: EvidenceBasis;
  readonly conditions?: readonly ReferenceCondition[];
  readonly quality?: readonly QualityStatement[];
}
export interface SemanticClaim extends DefinitionRef {
  readonly native: { readonly property: DefinitionRef; readonly term?: DefinitionRef; readonly fields: NativeFields };
  readonly result: ClaimResult;
  readonly feature?: FeatureRef;
  readonly associations?: readonly FeatureRef[]; // Event/inventory associations do not change feature identity.
  readonly interpretation?: Interpretation;
  /** Whole-field replacement, never automatic merging. Resolve against collection context. */
  readonly context?: Partial<ClaimContext>;
  readonly record: AssetReference;
}
export interface ClaimCollection extends DefinitionRef {
  readonly product: EntityReference;
  readonly context: ClaimContext;
  readonly representation: 'raster' | 'vector' | 'records' | 'time-series';
  readonly claims: readonly SemanticClaim[];
  /** Optional metadata binding only; no pixel reader, GIS adapter or temporal engine. */
  readonly binding?: {
    readonly asset: AssetReference;
    readonly assignment: string; // Declares cell/feature/time to template support, not blanket assertion.
    readonly codes: readonly { readonly code: string | number; readonly claim: DefinitionRef }[];
  };
}
export interface SemanticEvidenceBundle {
  readonly contract: 'atlas-semantic-evidence/v1';
  readonly resources: readonly SemanticResource[];
  readonly definitions: readonly SemanticDefinition[];
  readonly mappings: readonly SemanticMapping[];
  readonly collections: readonly ClaimCollection[];
}
