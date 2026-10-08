export class AtlasError extends Error {
  readonly code: string
  constructor(code: string, message: string) { super(message); this.code = code }
}
export function requireAtlas(ok: unknown, code: string, message: string): asserts ok {
  if (!ok) throw new AtlasError(code, message)
}
export function diagnostic(error: unknown): { code: string; message: string } {
  if (error instanceof AtlasError) return { code: error.code, message: error.message }
  return { code: 'authoritative-unavailable', message: 'Cannot validate required authoritative files. Check explicit data/publication paths and retained artifacts; no evidence was repaired.' }
}
