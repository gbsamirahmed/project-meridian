import { spawn } from 'node:child_process'
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'
import type { Json } from './types.ts'
import { AtlasError } from './errors.ts'

/** Session-owned native/catalogue process; bounded JSON requests, no daemon. */
export class NativeWorker {
  private child
  private next = 0
  private pending = new Map<number, { resolve: (v: Json) => void; reject: (e: Error) => void }>()
  private closed = false
  constructor(python: string) {
    this.child = spawn(python, [fileURLToPath(new URL('./worker.py', import.meta.url))], { stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONDONTWRITEBYTECODE: '1', PROJ_NETWORK: 'OFF' } })
    // Internal traceback/stderr is deliberately not a normal CLI diagnostic.
    this.child.stderr.resume()
    createInterface({ input: this.child.stdout }).on('line', line => {
      try {
        const v = JSON.parse(line), entry = this.pending.get(v.id)
        if (!entry) return
        this.pending.delete(v.id)
        if (v.error) entry.reject(new AtlasError(v.error.code, v.error.message))
        else entry.resolve(v.result)
      } catch { this.fail('Invalid native worker response.') }
    })
    this.child.on('error', () => this.fail('Cannot start configured Python; check the retained GIS environment.'))
    this.child.on('exit', () => this.fail('Native worker exited; reopen the pinned context.'))
    this.child.stdin.on('error', () => this.fail('Native worker pipe unavailable.'))
  }
  private fail(message: string) {
    this.closed = true
    for (const p of this.pending.values()) p.reject(new AtlasError('worker-unavailable', message))
    this.pending.clear()
  }
  call(operation: string, args: Json): Promise<Json> {
    if (this.closed) return Promise.reject(new AtlasError('session-closed', 'Open a new pinned context.'))
    const id = this.next++
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      this.child.stdin.write(JSON.stringify({ id, operation, args }) + '\n')
    })
  }
  async close(): Promise<void> {
    if (this.closed) return
    this.child.stdin.end()
    await new Promise<void>(resolve => { this.child.once('exit', () => resolve()) })
  }
}
