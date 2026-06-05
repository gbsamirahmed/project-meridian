interface TimeSliderProps {
  forecastHour: number;
  forecastTimes?: string[];
  onForecastHourChange: (hour: number) => void;
}

function formatForecastTime(time?: string): string {
  if (!time) return "Select a location";

  const date = new Date(time);

  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function TimeSlider({
  forecastHour,
  forecastTimes,
  onForecastHourChange,
}: TimeSliderProps) {
  const label = formatForecastTime(
    forecastTimes?.[forecastHour]
  );

  return (
    <div className="weather-card">
      <h2>Forecast Time</h2>

      <p>{label}</p>

      <input
        className="time-slider"
        type="range"
        min="0"
        max="24"
        step="1"
        value={forecastHour}
        onChange={(event) =>
          onForecastHourChange(Number(event.target.value))
        }
      />
    </div>
  );
}