const MINIMUM_REQUEST_INTERVAL_MS = 1_000;
const MAXIMUM_CACHE_ENTRIES = 48;

const responseCache = new Map<string, unknown>();
let requestQueue = Promise.resolve();
let lastRequestStartedAt = 0;

function abortError(): DOMException {
  return new DOMException("The request was cancelled", "AbortError");
}

function waitFor(milliseconds: number, signal?: AbortSignal): Promise<void> {
  if (milliseconds <= 0) return Promise.resolve();

  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortError());
      return;
    }

    const timeout = window.setTimeout(() => {
      signal?.removeEventListener("abort", handleAbort);
      resolve();
    }, milliseconds);

    const handleAbort = () => {
      window.clearTimeout(timeout);
      reject(abortError());
    };

    signal?.addEventListener("abort", handleAbort, { once: true });
  });
}

function readCached<T>(key: string): T | undefined {
  if (!responseCache.has(key)) return undefined;

  const value = responseCache.get(key) as T;
  responseCache.delete(key);
  responseCache.set(key, value);
  return value;
}

function cacheResponse(key: string, value: unknown): void {
  responseCache.delete(key);
  responseCache.set(key, value);

  while (responseCache.size > MAXIMUM_CACHE_ENTRIES) {
    const oldestKey = responseCache.keys().next().value;
    if (oldestKey === undefined) break;
    responseCache.delete(oldestKey);
  }
}

export async function requestNominatimJson<T>(
  url: string,
  cacheKey: string,
  signal?: AbortSignal
): Promise<T> {
  const cached = readCached<T>(cacheKey);
  if (cached !== undefined) return cached;

  const queuedRequest = requestQueue.then(async () => {
    if (signal?.aborted) throw abortError();

    await waitFor(
      Math.max(0, lastRequestStartedAt + MINIMUM_REQUEST_INTERVAL_MS - Date.now()),
      signal
    );

    if (signal?.aborted) throw abortError();
    lastRequestStartedAt = Date.now();

    const response = await fetch(url, {
      signal,
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Nominatim returned HTTP ${response.status}`);
    }

    const value = (await response.json()) as T;
    cacheResponse(cacheKey, value);
    return value;
  });

  requestQueue = queuedRequest.then(
    () => undefined,
    () => undefined
  );

  return queuedRequest;
}
