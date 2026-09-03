import { useEffect, useState } from "react";
import type { GlobalWeatherCatalog } from "../types/globalWeather";
import type { JourneySchedule } from "../types/route";
import type { CatalogueCheckState } from "../services/weatherCatalogueRefresh";
import { weatherFreshnessPresentation } from "../services/weatherFreshness";

interface WeatherFreshnessProps {
  catalog: GlobalWeatherCatalog | null;
  check: CatalogueCheckState;
  journey: JourneySchedule | null;
}

export default function WeatherFreshness({ catalog, check, journey }: WeatherFreshnessProps) {
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
  const presentation = weatherFreshnessPresentation(catalog, check, journey, now);
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
