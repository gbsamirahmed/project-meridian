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
    <section className="weather-card forecast-card">
      <div className="card-heading">
        <div>
          <p className="section-kicker">Looking ahead</p>
          <h2>7 day forecast</h2>
        </div>
      </div>

      {forecast.map((day) => (
        <div key={day.date} className="forecast-row">
          <span>{formatDate(day.date)}</span>

          <span className="forecast-temperature">
            <strong>{Math.round(day.maxTemperature)}°</strong>
            <span>{Math.round(day.minTemperature)}°</span>
          </span>
        </div>
      ))}
    </section>
  );
}
