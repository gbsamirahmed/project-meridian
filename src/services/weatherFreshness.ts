import type { GlobalWeatherCatalog } from "../types/globalWeather";
import type { JourneySchedule } from "../types/route";
import type { CatalogueCheckState } from "./weatherCatalogueRefresh";

export type WeatherFreshnessTone = "current" | "ending" | "expired" | "unavailable";

export interface WeatherFreshnessPresentation {
  label: string;
  detail: string;
  tone: WeatherFreshnessTone;
}

function compactDuration(milliseconds: number): string {
  const hours = Math.max(0, milliseconds / 3_600_000);
  if (hours < 1) return `${Math.max(1, Math.ceil(hours * 60))} min`;
  return `${Math.ceil(hours)} h`;
}

function checkedLabel(value: string | null): string | null {
  if (!value || !Number.isFinite(Date.parse(value))) return null;
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function weatherFreshnessPresentation(
  catalog: GlobalWeatherCatalog | null,
  check: CatalogueCheckState,
  journey: JourneySchedule | null,
  now = Date.now()
): WeatherFreshnessPresentation {
  const entry = catalog?.fields.precipitation ?? Object.values(catalog?.fields ?? {})[0];
  if (!entry) {
    return {
      label: "GFS weather unavailable",
      detail: check.lastCheckFailed
        ? "The catalogue check failed; Meridian will retry without clearing the map."
        : "Waiting for a complete local weather catalogue.",
      tone: "unavailable",
    };
  }
  const run = new Date(entry.runTime);
  const runDate = new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  }).format(run);
  const checked = checkedLabel(check.lastSuccessfulCheck);
  const label = `GFS ${runDate} ${String(run.getUTCHours()).padStart(2, "0")}Z${checked ? ` · checked ${checked}` : ""}`;
  const first = Date.parse(entry.firstValidTime);
  const last = Date.parse(entry.lastValidTime);
  const journeyStart = journey ? Date.parse(journey.departureTime) : null;
  const journeyFinish = journey ? Date.parse(journey.expectedFinishTime) : null;
  const failure = check.lastCheckFailed ? " Latest update check failed; the active run was retained." : "";
  if (!Number.isFinite(first) || !Number.isFinite(last)) {
    return { label, detail: `Forecast coverage metadata is unavailable.${failure}`, tone: "unavailable" };
  }
  if (now > last) {
    return {
      label,
      detail: `Forecast coverage ended ${compactDuration(now - last)} ago.${failure}`,
      tone: "expired",
    };
  }
  if (
    (journeyStart !== null && Number.isFinite(journeyStart) && journeyStart < first) ||
    (journeyFinish !== null && Number.isFinite(journeyFinish) && journeyFinish > last)
  ) {
    return {
      label,
      detail: `Journey extends beyond forecast coverage, which ends ${new Date(last).toLocaleString()}.${failure}`,
      tone: "ending",
    };
  }
  if (now < first) {
    return {
      label,
      detail: `Coverage begins in ${compactDuration(first - now)}.${failure}`,
      tone: "ending",
    };
  }
  if (last - now <= 3 * 3_600_000) {
    return {
      label,
      detail: `Forecast coverage ends in ${compactDuration(last - now)}.${failure}`,
      tone: "ending",
    };
  }
  return {
    label,
    detail: `Forecast coverage is valid through ${new Date(last).toLocaleString()}.${failure}`,
    tone: "current",
  };
}
