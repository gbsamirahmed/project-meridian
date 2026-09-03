import type {
  GlobalWeatherCatalog,
  GlobalWeatherCatalogEntry,
  GlobalWeatherFieldId,
  GlobalWeatherSourceRegistry,
  GlobalWeatherStatusRegistry,
  GlobalWeatherFieldSource,
  ScalarFieldManifest,
  ScalarFieldTimestep,
  ScalarWeatherFieldSource,
  VectorFieldManifest,
  VectorFieldTimestep,
  VectorWeatherFieldSource,
} from "../types/globalWeather";

import { ATMOSPHERIC_FIELDS, validateAtmosphericManifest } from "./atmosphericFields";

const LATEST_DATASET_URL = "/weather/gfs/latest.json";
const FIELD_IDS: GlobalWeatherFieldId[] = [
  "precipitation",
  "cloud_cover",
  "wind_10m",
  "temperature_2m",
  ...Object.keys(ATMOSPHERIC_FIELDS) as Array<keyof typeof ATMOSPHERIC_FIELDS>,
];

interface LegacyPrecipitationManifest {
  schemaVersion: 1;
  id: string;
  model: string;
  product: string;
  runTime: string;
  variable: {
    id: "precipitation";
    sourceParameter: string;
    displayName: string;
    units: "mm";
    nativeResolutionDegrees: number;
    accumulationSemantics: "interval-total";
  };
  coverage: ScalarFieldManifest["coverage"];
  tiles: Omit<ScalarFieldManifest["tiles"], "encoding"> & {
    encoding: "uint16-rg";
  };
  timesteps: ScalarFieldTimestep[];
  attribution: ScalarFieldManifest["attribution"];
  generatedAt: string;
}

interface LegacyLatestPointer extends GlobalWeatherCatalogEntry {
  schemaVersion: 1;
  model: string;
  product: string;
  variable: "precipitation";
  generatedAt: string;
}

export interface GlobalWeatherLoadResult {
  catalog: GlobalWeatherCatalog | null;
  sources: GlobalWeatherSourceRegistry;
  statuses: GlobalWeatherStatusRegistry;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}

function isCatalogEntry(value: unknown): value is GlobalWeatherCatalogEntry {
  if (!isRecord(value)) return false;
  return (
    typeof value.runTime === "string" &&
    typeof value.firstValidTime === "string" &&
    typeof value.lastValidTime === "string" &&
    typeof value.timestepCount === "number" &&
    typeof value.manifest === "string"
  );
}

function normaliseCatalog(value: unknown): GlobalWeatherCatalog {
  if (!isRecord(value)) throw new Error("Global weather dataset pointer is invalid");

  if (
    value.schemaVersion === 1 &&
    value.variable === "precipitation" &&
    typeof value.model === "string" &&
    typeof value.product === "string" &&
    typeof value.generatedAt === "string" &&
    isCatalogEntry(value)
  ) {
    const pointer = value as unknown as LegacyLatestPointer;
    return {
      schemaVersion: 2,
      model: pointer.model,
      product: pointer.product,
      generatedAt: pointer.generatedAt,
      fields: { precipitation: pointer },
    };
  }

  if (
    value.schemaVersion !== 2 ||
    typeof value.model !== "string" ||
    typeof value.product !== "string" ||
    typeof value.generatedAt !== "string" ||
    !isRecord(value.fields)
  ) {
    throw new Error("Global weather field catalogue is invalid");
  }

  const fields: GlobalWeatherCatalog["fields"] = {};
  for (const fieldId of FIELD_IDS) {
    const entry = value.fields[fieldId];
    if (entry !== undefined) {
      if (!isCatalogEntry(entry)) {
        // An invalid independently published field must not hide healthy fields.
        continue;
      }
      fields[fieldId] = entry;
    }
  }

  return {
    schemaVersion: 2,
    model: value.model,
    product: value.product,
    generatedAt: value.generatedAt,
    fields,
  };
}

function isTimestep(value: unknown): value is ScalarFieldTimestep {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.forecastHour === "number" &&
    typeof value.validTime === "string" &&
    typeof value.minimum === "number" &&
    typeof value.maximum === "number" &&
    typeof value.tileTemplate === "string"
  );
}

function isVectorTimestep(value: unknown): value is VectorFieldTimestep {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.forecastHour === "number" &&
    typeof value.validTime === "string" &&
    typeof value.minimumU === "number" &&
    typeof value.maximumU === "number" &&
    typeof value.minimumV === "number" &&
    typeof value.maximumV === "number" &&
    typeof value.minimumSpeed === "number" &&
    typeof value.maximumSpeed === "number" &&
    typeof value.tileTemplate === "string"
  );
}

function normaliseManifest(
  value: unknown
): ScalarFieldManifest | VectorFieldManifest {
  if (!isRecord(value)) throw new Error("Global weather manifest is invalid");

  if (
    value.schemaVersion === 2 &&
    typeof value.id === "string" &&
    typeof value.model === "string" &&
    typeof value.product === "string" &&
    typeof value.runTime === "string" &&
    isRecord(value.field) &&
    value.field.id === "wind_10m" &&
    value.field.kind === "vector" &&
    value.field.units === "m/s" &&
    value.field.sourceLevel === "10 m above ground" &&
    value.field.timeSemantics === "instantaneous" &&
    value.field.vectorConvention ===
      "earth-relative-eastward-northward" &&
    Array.isArray(value.field.components) &&
    value.field.components.length === 2 &&
    isRecord(value.tiles) &&
    value.tiles.encoding === "packed-uv10-rgb" &&
    value.tiles.componentBits === 10 &&
    typeof value.tiles.componentScale === "number" &&
    typeof value.tiles.componentBias === "number" &&
    value.tiles.noDataCode === 0 &&
    Array.isArray(value.timesteps) &&
    value.timesteps.length > 0 &&
    value.timesteps.every(isVectorTimestep)
  ) {
    const manifest = value as unknown as VectorFieldManifest;
    const [u, v] = manifest.field.components;
    if (
      u.id !== "u" ||
      u.sourceParameter !== "UGRD" ||
      u.role !== "eastward" ||
      v.id !== "v" ||
      v.sourceParameter !== "VGRD" ||
      v.role !== "northward"
    ) {
      throw new Error("Global wind component semantics are invalid");
    }
    return manifest;
  }

  if (
    value.schemaVersion === 1 &&
    isRecord(value.variable) &&
    value.variable.id === "precipitation" &&
    value.variable.units === "mm" &&
    isRecord(value.tiles) &&
    value.tiles.encoding === "uint16-rg" &&
    Array.isArray(value.timesteps)
  ) {
    const legacy = value as unknown as LegacyPrecipitationManifest;
    return {
      schemaVersion: 2,
      id: legacy.id,
      model: legacy.model,
      product: legacy.product,
      runTime: legacy.runTime,
      field: {
        id: "precipitation",
        kind: "scalar",
        sourceParameter: legacy.variable.sourceParameter,
        sourceLevel: "surface",
        displayName: legacy.variable.displayName,
        units: "mm",
        validRange: [0, 655.34],
        timeSemantics: "interval-total",
        nativeResolution: {
          longitudeDegrees: legacy.variable.nativeResolutionDegrees,
          latitudeDegrees: legacy.variable.nativeResolutionDegrees,
        },
      },
      coverage: legacy.coverage,
      tiles: legacy.tiles,
      timesteps: legacy.timesteps,
      attribution: legacy.attribution,
      generatedAt: legacy.generatedAt,
    };
  }

  if (
    value.schemaVersion !== 2 ||
    typeof value.id !== "string" ||
    typeof value.model !== "string" ||
    typeof value.product !== "string" ||
    typeof value.runTime !== "string" ||
    !isRecord(value.field) ||
    !FIELD_IDS.includes(value.field.id as GlobalWeatherFieldId) ||
    value.field.kind !== "scalar" ||
    !isRecord(value.tiles) ||
    !["uint16-rg", "uint8-r"].includes(String(value.tiles.encoding)) ||
    !Array.isArray(value.timesteps) ||
    value.timesteps.length === 0 ||
    !value.timesteps.every(isTimestep)
  ) {
    throw new Error("Global weather scalar manifest is unsupported or incomplete");
  }

  const manifest = value as unknown as ScalarFieldManifest;
  validateAtmosphericManifest(manifest);
  if (
    manifest.field.id === "cloud_cover" &&
    (manifest.field.sourceParameter !== "TCDC" ||
      manifest.field.sourceLevel !== "entire atmosphere" ||
      manifest.field.units !== "percent" ||
      manifest.field.timeSemantics !== "instantaneous" ||
      manifest.field.validRange[0] !== 0 ||
      manifest.field.validRange[1] !== 100 ||
      manifest.tiles.encoding !== "uint8-r" ||
      manifest.tiles.noData !== 255)
  ) {
    throw new Error("Global cloud manifest semantics are invalid");
  }
  if (
    manifest.field.id === "precipitation" &&
    (manifest.field.units !== "mm" ||
      manifest.field.timeSemantics !== "interval-total" ||
      manifest.tiles.encoding !== "uint16-rg")
  ) {
    throw new Error("Global precipitation manifest semantics are invalid");
  }
  if (
    manifest.field.id === "temperature_2m" &&
    (manifest.field.sourceParameter !== "TMP" ||
      manifest.field.sourceLevel !== "2 m above ground" ||
      manifest.field.units !== "celsius" ||
      manifest.field.timeSemantics !== "instantaneous" ||
      manifest.field.validRange[0] !== -150 ||
      manifest.field.validRange[1] !== 100 ||
      manifest.tiles.encoding !== "uint16-rg" ||
      manifest.tiles.scale !== 0.1 ||
      manifest.tiles.offset !== -150 ||
      manifest.tiles.noData !== 65535)
  ) {
    throw new Error("Global temperature manifest semantics are invalid");
  }
  return manifest;
}

async function fetchJson<T>(url: string, cache: RequestCache): Promise<T> {
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`Global weather metadata returned HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

async function loadField(
  latestUrl: URL,
  entry: GlobalWeatherCatalogEntry,
  expectedId: GlobalWeatherFieldId,
  expectedProduct: string
): Promise<GlobalWeatherFieldSource> {
  const manifestUrl = new URL(entry.manifest, latestUrl).href;
  const manifest = normaliseManifest(
    await fetchJson<unknown>(manifestUrl, "force-cache")
  );

  if (
    manifest.field.id !== expectedId ||
    manifest.runTime !== entry.runTime ||
    manifest.product !== expectedProduct ||
    manifest.timesteps.length !== entry.timestepCount ||
    manifest.timesteps[0]?.validTime !== entry.firstValidTime ||
    manifest.timesteps.at(-1)?.validTime !== entry.lastValidTime
  ) {
    throw new Error(`Global weather ${expectedId} entry does not match its manifest`);
  }

  const baseUrl = new URL(".", manifestUrl).href;
  if (manifest.field.kind === "vector") {
    return {
      manifest: manifest as VectorFieldManifest,
      manifestUrl,
      baseUrl,
    };
  }
  return {
    manifest: manifest as ScalarFieldManifest,
    manifestUrl,
    baseUrl,
  };
}

export async function loadGlobalWeatherSources(): Promise<GlobalWeatherLoadResult> {
  const latestUrl = new URL(LATEST_DATASET_URL, window.location.href);
  const emptyStatuses: GlobalWeatherStatusRegistry = {
    precipitation: "unavailable",
    cloud_cover: "unavailable",
    wind_10m: "unavailable",
    temperature_2m: "unavailable",
    gust_surface: "unavailable",
    visibility_surface: "unavailable",
    freezing_level: "unavailable",
    highest_freezing_level: "unavailable",
    cloud_ceiling: "unavailable",
  };
  let catalog: GlobalWeatherCatalog;

  try {
    catalog = normaliseCatalog(
      await fetchJson<unknown>(latestUrl.href, "no-cache")
    );
  } catch {
    return { catalog: null, sources: {}, statuses: emptyStatuses };
  }

  const sources: GlobalWeatherSourceRegistry = {};
  const statuses = { ...emptyStatuses };
  await Promise.all(
    FIELD_IDS.map(async (fieldId) => {
      const entry = catalog.fields[fieldId];
      if (!entry) return;
      try {
        const source = await loadField(
          latestUrl,
          entry,
          fieldId,
          catalog.product
        );
        if (fieldId === "wind_10m" && source.manifest.field.kind === "vector") {
          sources.wind_10m = source as VectorWeatherFieldSource;
        } else if (
          fieldId === "precipitation" &&
          source.manifest.field.kind === "scalar" &&
          source.manifest.field.id === "precipitation"
        ) {
          sources.precipitation = source as ScalarWeatherFieldSource;
        } else if (
          fieldId === "cloud_cover" &&
          source.manifest.field.kind === "scalar" &&
          source.manifest.field.id === "cloud_cover"
        ) {
          sources.cloud_cover = source as ScalarWeatherFieldSource;
        } else if (
          fieldId === "temperature_2m" &&
          source.manifest.field.kind === "scalar" &&
          source.manifest.field.id === "temperature_2m"
        ) {
          sources.temperature_2m = source as ScalarWeatherFieldSource;
        } else if (fieldId !== "wind_10m" && fieldId in ATMOSPHERIC_FIELDS && source.manifest.field.kind === "scalar") {
          sources[fieldId] = source as ScalarWeatherFieldSource;
        } else {
          throw new Error(`Global weather ${fieldId} manifest kind is invalid`);
        }
        statuses[fieldId] = "ready";
      } catch {
        statuses[fieldId] = "error";
      }
    })
  );

  return { catalog, sources, statuses };
}

export function getScalarTimestep(
  source: ScalarWeatherFieldSource,
  index: number
): ScalarFieldTimestep {
  return source.manifest.timesteps[
    Math.max(0, Math.min(index, source.manifest.timesteps.length - 1))
  ];
}

export function getVectorTimestepAtTime(
  source: VectorWeatherFieldSource,
  validTime: string | null | undefined
): VectorFieldTimestep | null {
  if (!validTime) return null;
  return (
    source.manifest.timesteps.find((step) => step.validTime === validTime) ??
    null
  );
}

export function getClosestVectorTimestep(
  source: VectorWeatherFieldSource,
  validTime: string | null | undefined
): VectorFieldTimestep {
  if (!validTime) return source.manifest.timesteps[0];
  const target = new Date(validTime).getTime();
  return source.manifest.timesteps.reduce((closest, candidate) =>
    Math.abs(new Date(candidate.validTime).getTime() - target) <
    Math.abs(new Date(closest.validTime).getTime() - target)
      ? candidate
      : closest
  );
}

export function getScalarTimestepAtTime(
  source: ScalarWeatherFieldSource,
  validTime: string | null | undefined
): ScalarFieldTimestep | null {
  if (!validTime) return null;
  return source.manifest.timesteps.find((step) => step.validTime === validTime) ?? null;
}

export function getClosestScalarTimestep(
  source: ScalarWeatherFieldSource,
  validTime: string | null | undefined
): ScalarFieldTimestep {
  if (!validTime) return source.manifest.timesteps[0];
  const target = new Date(validTime).getTime();
  return source.manifest.timesteps.reduce((closest, candidate) =>
    Math.abs(new Date(candidate.validTime).getTime() - target) <
    Math.abs(new Date(closest.validTime).getTime() - target)
      ? candidate
      : closest
  );
}

export function intersectScalarValidTimes(
  sources: GlobalWeatherFieldSource[]
): string[] {
  if (sources.length === 0) return [];
  const remaining = sources.slice(1).map(
    (source) => new Set(source.manifest.timesteps.map((step) => step.validTime))
  );
  return sources[0].manifest.timesteps
    .map((step) => step.validTime)
    .filter((validTime) => remaining.every((times) => times.has(validTime)));
}

export function resolveScalarTileUrl(
  source: ScalarWeatherFieldSource,
  timestep: ScalarFieldTimestep,
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

export function resolveVectorTileUrl(
  source: VectorWeatherFieldSource,
  timestep: VectorFieldTimestep,
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
