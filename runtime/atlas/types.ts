export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }
export interface RuntimeConfig {
  dataRoot: string
  publicationRoot: string
  catalogueRoot: string
  python: string
  generation?: string
}
export interface Query {
  region?: 'tryfan' | 'riffelhorn' | 'exe'
  identity?: string
  feature?: string
  families?: string[]
  representation?: 'vector' | 'raster' | 'source-product-metadata'
  product?: string
  point?: [number, number]
  area?: [number, number, number, number]
  crs?: 'EPSG:2056' | 'EPSG:27700' | 'EPSG:4326' | 'OGC:CRS84'
  time?: { role: 'evidence-epoch' | 'product-reference'; start: number; end: number } |
    { role: 'evidence-epoch' | 'product-reference'; unknown: true }
}
export interface QualifiedResult {
  identity: string
  region: string
  componentIdentity: string
  evidence: Json
  support: Json
  temporal: Json
  provenance: Json
  rights: Json
  registration?: Json
}
export interface QueryAnswer {
  schema: 'atlas-local-query/v1'
  generation: string
  members: Record<string, string>
  results: QualifiedResult[]
  gap: Json
  metrics: Record<string, number>
}
export interface ValidationMetrics {
  milliseconds: number
  metadataRecords: number
  metadataBytes: number
  payloadHashOperations: number
  payloadBytesHashed: number
  ancestryTraversals: number
  parentRssBytes: number
}
/** Versioned finite lifecycle DTO; scientific qualifications remain canonical metadata. */
export interface DerivationStage {
  schema: 'atlas-runtime-lifecycle-stage/v1'
  generation: string
  predecessor: string
  status: 'no-op' | 'staged-unpublished' | 'full-oracle-only'
  affected: string[]
  recomputed: string[]
  reused: number
  active: Record<string, string>
  policy: import('./lifecycle-model.ts').Policy
  environment: Json
  metrics: Record<string, Json>
  validation: ValidationMetrics
}
export interface DerivedQuery { identity?: string; property?: 'slope' | 'area-ratio' }
export interface DerivedAnswer {
  generation: string
  regionalRegistration: { componentIdentity: string; evidence: Json; knowledgeRegistration?: Json }
  status: 'no-runtime-derived-state' | 'current-in-pinned-context'
  results: Array<{ [key: string]: Json }>
  metrics?: Record<string, number>
}
/** A finite qualified query; publication selection belongs to RuntimeConfig. */
export interface EvidenceQuery extends Omit<Query, 'representation'> {
  waterTime?: { role: 'observation' | 'event' | 'reference'; start: string; end: string } | { role: 'observation' | 'event' | 'reference'; unknown: true }
  evidenceClass?: 'source' | 'derived'
  representation?: Query['representation'] | 'local-scalar' | 'native-cell-summary'
  revision?: string
  spatialSupport?: 'location' | 'consumed'
  knowledge?: { revision: string } | { start: string; end: string } | { unknown: true }
  relatedTo?: { identity: string; direction: 'inputs' | 'dependents'; depth: 'direct' | 'transitive' }
}
export interface EvidenceRecord {
  key: string
  identity: string
  revision: string
  evidenceClass: 'source' | 'derived'
  region: string
  family: string
  representation: string
  componentIdentity: string
  evidenceRef: string
  qualificationRef: string
  provenanceRef: string
  rightsRef: string
  support: Json
  temporal: Json
  knowledgeRef: string | null
  relationshipRefs: string[]
}
export interface EvidenceRelationship {
  identity: string
  from: string
  to: string
  kind: 'consumes-qualified-source' | 'derived-input'
  fromRevision: string
  toRevision: string
  via: Json
}
export interface EvidenceAnswer {
  schema: 'atlas-qualified-retrieval/v1'
  generation: string
  members: Record<string, string>
  results: EvidenceRecord[]
  relationships: EvidenceRelationship[]
  documents: Record<string, Json>
  regions: Record<string, { nativeRef: string; knowledgeRef: string | null }>
  traversal: { selection: EvidenceQuery['relatedTo']; relationshipRefs: string[] } | null
  gap: Json
  metrics: Record<string, number>
}
