export interface GfsPublicationOptions {
  publicationRoot?: string
}

export function resolveGfsPublicationRoot(options?: {
  repositoryRoot?: string
  environment?: Record<string, string | undefined>
  requireExists?: boolean
}): string

export function createGfsPublicationMiddleware(options?: GfsPublicationOptions): (
  request: import('node:http').IncomingMessage,
  response: import('node:http').ServerResponse,
  next: (error?: unknown) => void,
) => void

export function materializeGfsPublication(
  destination: string,
  options?: GfsPublicationOptions,
): { target: string; runName: string }
