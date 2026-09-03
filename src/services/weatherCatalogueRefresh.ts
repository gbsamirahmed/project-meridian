import type {
  GlobalWeatherCatalog,
  GlobalWeatherSourceRegistry,
  GlobalWeatherStatusRegistry,
} from "../types/globalWeather";
import {
  fetchGlobalWeatherCatalog,
  GLOBAL_WEATHER_FIELD_IDS,
  loadGlobalWeatherSources,
} from "./globalWeatherService";

export const WEATHER_CATALOGUE_POLL_MS = 5 * 60 * 1000;
export const WEATHER_CATALOGUE_TIMEOUT_MS = 20 * 1000;

const FIELD_PATHS: Record<string, string> = {
  precipitation: "",
  cloud_cover: "cloud-cover",
  wind_10m: "wind-10m",
  temperature_2m: "temperature-2m",
  gust_surface: "gust-surface",
  visibility_surface: "visibility-surface",
  freezing_level: "freezing-level",
  highest_freezing_level: "highest-freezing-level",
  cloud_ceiling: "cloud-ceiling",
};

export interface CompleteGlobalWeatherLoad {
  catalog: GlobalWeatherCatalog;
  sources: GlobalWeatherSourceRegistry;
  statuses: GlobalWeatherStatusRegistry;
}

export type CatalogueRefreshResult =
  | { kind: "adopted"; value: CompleteGlobalWeatherLoad }
  | { kind: "identical" | "older"; catalog: GlobalWeatherCatalog };

function exactIsoTime(value: string): number {
  const time = Date.parse(value);
  if (
    !Number.isFinite(time) ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.000)?Z$/.test(value)
  ) {
    throw new Error("Weather catalogue time is not canonical UTC");
  }
  return time;
}

export function completeCatalogueRunTime(catalog: GlobalWeatherCatalog): number {
  if (catalog.model !== "NOAA GFS" || catalog.product !== "pgrb2.0p25") {
    throw new Error("Weather catalogue model/product is unsupported");
  }
  const fields = Object.keys(catalog.fields);
  if (
    fields.length !== GLOBAL_WEATHER_FIELD_IDS.length ||
    !GLOBAL_WEATHER_FIELD_IDS.every((fieldId) => catalog.fields[fieldId])
  ) {
    throw new Error("Weather catalogue does not contain all nine fields");
  }
  let runTime: number | null = null;
  for (const fieldId of GLOBAL_WEATHER_FIELD_IDS) {
    const entry = catalog.fields[fieldId]!;
    const fieldRun = exactIsoTime(entry.runTime);
    const run = new Date(fieldRun);
    if (
      run.getUTCMinutes() !== 0 ||
      run.getUTCSeconds() !== 0 ||
      ![0, 6, 12, 18].includes(run.getUTCHours())
    ) {
      throw new Error("Weather catalogue run is not a GFS cycle");
    }
    if (runTime === null) runTime = fieldRun;
    if (fieldRun !== runTime) throw new Error("Weather catalogue mixes GFS runs");
    if (
      entry.timestepCount !== 24 ||
      exactIsoTime(entry.firstValidTime) !== fieldRun + 60 * 60 * 1000 ||
      exactIsoTime(entry.lastValidTime) !== fieldRun + 24 * 60 * 60 * 1000
    ) {
      throw new Error("Weather catalogue is not a complete +24 h run");
    }
    const name = `${run.getUTCFullYear()}${String(run.getUTCMonth() + 1).padStart(2, "0")}${String(run.getUTCDate()).padStart(2, "0")}T${String(run.getUTCHours()).padStart(2, "0")}Z`;
    const subdir = FIELD_PATHS[fieldId];
    const expected = [name, subdir, "manifest.json"].filter(Boolean).join("/");
    if (entry.manifest !== expected) {
      throw new Error("Weather catalogue manifest is not in its immutable run");
    }
  }
  if (runTime === null) throw new Error("Weather catalogue is empty");
  return runTime;
}

export interface CatalogueRefreshDependencies {
  fetchCatalog: (signal: AbortSignal) => Promise<GlobalWeatherCatalog>;
  loadSources: (
    catalog: GlobalWeatherCatalog,
    signal: AbortSignal
  ) => Promise<CompleteGlobalWeatherLoad>;
}

const defaultDependencies: CatalogueRefreshDependencies = {
  fetchCatalog: fetchGlobalWeatherCatalog,
  async loadSources(catalog, signal) {
    const loaded = await loadGlobalWeatherSources({ catalog, signal });
    if (
      !loaded.catalog ||
      !GLOBAL_WEATHER_FIELD_IDS.every(
        (fieldId) => loaded.statuses[fieldId] === "ready" && loaded.sources[fieldId]
      )
    ) {
      throw new Error("New weather run did not load all nine validated manifests");
    }
    return { catalog: loaded.catalog, sources: loaded.sources, statuses: loaded.statuses };
  },
};

export async function refreshGlobalWeatherCatalogue(
  current: GlobalWeatherCatalog | null,
  signal: AbortSignal,
  dependencies: CatalogueRefreshDependencies = defaultDependencies
): Promise<CatalogueRefreshResult> {
  const candidate = await dependencies.fetchCatalog(signal);
  const candidateTime = completeCatalogueRunTime(candidate);
  let currentTime: number | null = null;
  if (current) {
    try {
      currentTime = completeCatalogueRunTime(current);
    } catch {
      // A legacy/partial initial catalogue may be replaced by the next complete run.
    }
  }
  if (currentTime !== null && candidateTime <= currentTime) {
    return { kind: candidateTime === currentTime ? "identical" : "older", catalog: candidate };
  }
  const loaded = await dependencies.loadSources(candidate, signal);
  if (completeCatalogueRunTime(loaded.catalog) !== candidateTime) {
    throw new Error("Loaded weather manifests do not match the candidate catalogue");
  }
  return { kind: "adopted", value: loaded };
}

export function catalogueForecastIndex(
  validTimes: string[],
  preferredValidTime: string | null,
  now = Date.now()
): number {
  const retained = preferredValidTime ? validTimes.indexOf(preferredValidTime) : -1;
  if (retained >= 0) return retained;
  const firstFuture = validTimes.findIndex((validTime) => Date.parse(validTime) >= now);
  return firstFuture >= 0 ? firstFuture : Math.max(0, validTimes.length - 1);
}

export interface CatalogueCheckState {
  lastSuccessfulCheck: string | null;
  lastCheckFailed: boolean;
}

interface VisibilitySource {
  visibilityState: string;
  addEventListener(type: "visibilitychange", listener: () => void): void;
  removeEventListener(type: "visibilitychange", listener: () => void): void;
}

interface WatcherOptions {
  intervalMs?: number;
  timeoutMs?: number;
  visibility?: VisibilitySource;
  dependencies?: CatalogueRefreshDependencies;
  now?: () => number;
  setTimer?: (callback: () => void, delay: number) => ReturnType<typeof setTimeout>;
  clearTimer?: (timer: ReturnType<typeof setTimeout>) => void;
}

export class GlobalWeatherCatalogueWatcher {
  private current: GlobalWeatherCatalog | null;
  private readonly onAdopt: (value: CompleteGlobalWeatherLoad) => void;
  private readonly onCheck: (state: CatalogueCheckState) => void;
  private readonly options: Required<Omit<WatcherOptions, "visibility" | "dependencies">> &
    Pick<WatcherOptions, "visibility" | "dependencies">;
  private pollTimer: ReturnType<typeof setTimeout> | null = null;
  private timeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private controller: AbortController | null = null;
  private pending: Promise<void> | null = null;
  private generation = 0;
  private started = false;

  constructor(
    current: GlobalWeatherCatalog | null,
    onAdopt: (value: CompleteGlobalWeatherLoad) => void,
    onCheck: (state: CatalogueCheckState) => void,
    options: WatcherOptions = {}
  ) {
    this.current = current;
    this.onAdopt = onAdopt;
    this.onCheck = onCheck;
    this.options = {
      intervalMs: options.intervalMs ?? WEATHER_CATALOGUE_POLL_MS,
      timeoutMs: options.timeoutMs ?? WEATHER_CATALOGUE_TIMEOUT_MS,
      visibility: options.visibility,
      dependencies: options.dependencies,
      now: options.now ?? Date.now,
      setTimer: options.setTimer ?? setTimeout,
      clearTimer: options.clearTimer ?? clearTimeout,
    };
  }

  start(): void {
    if (this.started) return;
    this.started = true;
    this.options.visibility?.addEventListener("visibilitychange", this.handleVisibility);
    this.schedule();
  }

  setCurrent(catalog: GlobalWeatherCatalog): void {
    let currentTime = Number.NEGATIVE_INFINITY;
    try {
      if (this.current) currentTime = completeCatalogueRunTime(this.current);
    } catch {
      // A complete catalogue supersedes a partial initial catalogue.
    }
    if (completeCatalogueRunTime(catalog) > currentTime) this.current = catalog;
  }

  check(): Promise<void> {
    if (this.pending) return this.pending;
    if (this.pollTimer !== null) {
      this.options.clearTimer(this.pollTimer);
      this.pollTimer = null;
    }
    const generation = ++this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.timeoutTimer = this.options.setTimer(() => controller.abort(), this.options.timeoutMs);
    const dependencies = this.options.dependencies ?? defaultDependencies;
    this.pending = refreshGlobalWeatherCatalogue(this.current, controller.signal, dependencies)
      .then((result) => {
        if (!this.started || generation !== this.generation) return;
        this.onCheck({
          lastSuccessfulCheck: new Date(this.options.now()).toISOString(),
          lastCheckFailed: false,
        });
        if (result.kind !== "adopted") return;
        const candidateTime = completeCatalogueRunTime(result.value.catalog);
        let activeTime = Number.NEGATIVE_INFINITY;
        try {
          if (this.current) activeTime = completeCatalogueRunTime(this.current);
        } catch {
          // Replace a partial initial catalogue.
        }
        if (candidateTime <= activeTime) return;
        this.current = result.value.catalog;
        this.onAdopt(result.value);
      })
      .catch(() => {
        if (this.started && generation === this.generation) {
          this.onCheck({ lastSuccessfulCheck: null, lastCheckFailed: true });
        }
      })
      .finally(() => {
        if (this.timeoutTimer !== null) this.options.clearTimer(this.timeoutTimer);
        this.timeoutTimer = null;
        this.controller = null;
        this.pending = null;
        if (this.started) this.schedule();
      });
    return this.pending;
  }

  stop(): void {
    if (!this.started) return;
    this.started = false;
    this.generation += 1;
    this.controller?.abort();
    if (this.pollTimer !== null) this.options.clearTimer(this.pollTimer);
    if (this.timeoutTimer !== null) this.options.clearTimer(this.timeoutTimer);
    this.pollTimer = null;
    this.timeoutTimer = null;
    this.options.visibility?.removeEventListener("visibilitychange", this.handleVisibility);
  }

  private schedule(): void {
    if (!this.started || this.pollTimer !== null) return;
    this.pollTimer = this.options.setTimer(() => {
      this.pollTimer = null;
      if (!this.options.visibility || this.options.visibility.visibilityState === "visible") {
        void this.check();
      } else {
        this.schedule();
      }
    }, this.options.intervalMs);
  }

  private readonly handleVisibility = (): void => {
    if (this.options.visibility?.visibilityState === "visible") void this.check();
  };
}
