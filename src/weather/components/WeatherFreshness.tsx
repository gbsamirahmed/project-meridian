import { useEffect, useState } from "react";
import type { GlobalWeatherCatalog } from "../types/globalWeather";
import type { ForecastCoverageWindow } from "../types/forecastCoverage";
import type { CatalogueCheckState } from "../data/weatherCatalogueRefresh";
import {
  weatherDataSummaryPresentation,
  weatherFreshnessPresentation,
} from "../presentation/weatherFreshness";

interface WeatherFreshnessProps {
  catalog: GlobalWeatherCatalog | null;
  check: CatalogueCheckState;
  coverage: ForecastCoverageWindow | null;
  compact?: boolean;
  resolutionDegrees?: number | null;
}

export default function WeatherFreshness({ catalog, check, coverage, compact = false, resolutionDegrees = null }: WeatherFreshnessProps) {
  const [clockTime, setClockTime] = useState<number | null>(null);
  useEffect(() => {
    const timer = window.setInterval(() => setClockTime(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);
  const checkedTime = check.lastSuccessfulCheck
    ? Date.parse(check.lastSuccessfulCheck)
    : Number.NaN;
  const generatedTime = catalog ? Date.parse(catalog.generatedAt) : Number.NaN;
  const now = clockTime ??
    (Number.isFinite(checkedTime) ? checkedTime : generatedTime);
  if (compact) {
    const summary = weatherDataSummaryPresentation(
      catalog,
      check,
      coverage,
      resolutionDegrees,
      now,
    );
    return (
      <section className={`forecast-data-summary forecast-data-summary-${summary.tone}`} title={summary.detail}>
        <span aria-hidden="true" />
        <div>
          <strong>{summary.primary}</strong>
          <small>{summary.secondary}</small>
        </div>
      </section>
    );
  }
  const presentation = weatherFreshnessPresentation(catalog, check, coverage, now);
  return (
    <section className={`weather-freshness weather-freshness-${presentation.tone}`} title={presentation.detail}>
      <span aria-hidden="true" />
      <div>
        <strong>{presentation.label}</strong>
        <small>{presentation.detail}</small>
      </div>
    </section>
  );
}
