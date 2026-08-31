interface TimeSliderProps {
  forecastHour: number;
  forecastTimes: string[];
  forecastHours?: number[];
  sourceLabel?: string;
  onForecastHourChange: (hour: number) => void;
}

function formatForecastTime(time?: string): string {
  if (!time) return "Select a location";

  const hasExplicitTimeZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(time);
  const date = new Date(hasExplicitTimeZone ? time : `${time}Z`);

  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

export default function TimeSlider({
  forecastHour,
  forecastTimes,
  forecastHours,
  sourceLabel,
  onForecastHourChange,
}: TimeSliderProps) {
  const label = formatForecastTime(forecastTimes[forecastHour]);
  const maximumIndex = Math.max(0, forecastTimes.length - 1);
  const displayedForecastHour = forecastHours?.[forecastHour] ?? forecastHour;

  return (
    <section className="weather-card timeline-card">
      <div className="card-heading timeline-heading">
        <div>
          <p className="section-kicker">Forecast timeline</p>
          <h2>{label}</h2>
        </div>

        <span className="card-meta">+{displayedForecastHour}h</span>
      </div>

      <input
        className="time-slider"
        type="range"
        aria-label="Forecast hour"
        min="0"
        max={maximumIndex}
        step="1"
        value={forecastHour}
        onChange={(event) =>
          onForecastHourChange(Number(event.target.value))
        }
      />

      <div className="range-labels">
        <span>{forecastHours ? `+${forecastHours[0]}h` : "Now"}</span>
        <span>
          {forecastHours
            ? `+${forecastHours[forecastHours.length - 1]}h`
            : `+${maximumIndex} hours`}
        </span>
      </div>
      {sourceLabel && <p className="timeline-source">{sourceLabel}</p>}
    </section>
  );
}
