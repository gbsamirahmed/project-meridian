import type { ForecastDay } from "../types/weather";

interface ForecastPanelProps {
  forecast: ForecastDay[];
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);

  return date.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export default function ForecastPanel({
  forecast,
}: ForecastPanelProps) {
  return (
    <div className="weather-card">
      <h2>7 Day Forecast</h2>

      {forecast.map((day) => (
        <div key={day.date} className="forecast-row">
          <span>{formatDate(day.date)}</span>

          <span>
            {Math.round(day.maxTemperature)}° /{" "}
            {Math.round(day.minTemperature)}°
          </span>
        </div>
      ))}
    </div>
  );
}