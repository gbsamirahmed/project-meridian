export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }
export interface RuntimeConfig {
  dataRoot: string
  publicationRoot: string
  catalogueRoot: string
  python: string
  generation?: string
}
export interface Query {
  region?: 'tryfan' | 'riffelhorn'
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
