import type {
  ScalarWeatherFieldSource,
  ScalarWeatherTimestep,
  WeatherLatestPointer,
  WeatherRunManifest,
} from "../types/globalWeather";

const LATEST_DATASET_URL = "/weather/gfs/latest.json";

function isManifest(value: unknown): value is WeatherRunManifest {
  if (!value || typeof value !== "object") return false;
  const manifest = value as Partial<WeatherRunManifest>;

  return (
    manifest.schemaVersion === 1 &&
    typeof manifest.id === "string" &&
    typeof manifest.runTime === "string" &&
    manifest.variable?.id === "precipitation" &&
    manifest.variable?.units === "mm" &&
    manifest.tiles?.encoding === "uint16-rg" &&
    Array.isArray(manifest.timesteps) &&
    manifest.timesteps.length > 0
  );
}

function isLatestPointer(value: unknown): value is WeatherLatestPointer {
  if (!value || typeof value !== "object") return false;
  const pointer = value as Partial<WeatherLatestPointer>;
  return (
    pointer.schemaVersion === 1 &&
    pointer.variable === "precipitation" &&
    typeof pointer.model === "string" &&
    typeof pointer.product === "string" &&
    typeof pointer.runTime === "string" &&
    typeof pointer.generatedAt === "string" &&
    typeof pointer.firstValidTime === "string" &&
    typeof pointer.lastValidTime === "string" &&
    typeof pointer.timestepCount === "number" &&
    typeof pointer.manifest === "string"
  );
}

async function fetchJson<T>(url: string, cache: RequestCache): Promise<T> {
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`Global weather metadata returned HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function loadGlobalPrecipitationSource(): Promise<ScalarWeatherFieldSource> {
  const latestUrl = new URL(LATEST_DATASET_URL, window.location.href);
  const pointerValue = await fetchJson<unknown>(latestUrl.href, "no-cache");
  if (!isLatestPointer(pointerValue)) {
    throw new Error("Global weather dataset pointer is invalid");
  }
  const pointer = pointerValue;

  const manifestUrl = new URL(pointer.manifest, latestUrl).href;
  const manifest = await fetchJson<unknown>(manifestUrl, "force-cache");
  if (!isManifest(manifest)) {
    throw new Error("Global weather manifest is unsupported or incomplete");
  }
  if (
    manifest.runTime !== pointer.runTime ||
    manifest.product !== pointer.product ||
    manifest.timesteps.length !== pointer.timestepCount ||
    manifest.timesteps[0]?.validTime !== pointer.firstValidTime ||
    manifest.timesteps.at(-1)?.validTime !== pointer.lastValidTime
  ) {
    throw new Error("Global weather pointer does not match its immutable manifest");
  }

  return {
    manifest,
    manifestUrl,
    baseUrl: new URL(".", manifestUrl).href,
  };
}

export function getScalarTimestep(
  source: ScalarWeatherFieldSource,
  index: number
): ScalarWeatherTimestep {
  return (
    source.manifest.timesteps[Math.max(0, Math.min(index, source.manifest.timesteps.length - 1))]
  );
}

export function resolveScalarTileUrl(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): string {
  const relativeUrl = timestep.tileTemplate
    .replace("{z}", String(zoom))
    .replace("{x}", String(x))
    .replace("{y}", String(y));
  return new URL(relativeUrl, source.baseUrl).href;
}
