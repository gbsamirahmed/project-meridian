interface TimeSliderProps {
  forecastHour: number;
  onForecastHourChange: (hour: number) => void;
}

export default function TimeSlider({
  forecastHour,
  onForecastHourChange,
}: TimeSliderProps) {
  return (
    <div className="weather-card">
      <h2>Forecast Time</h2>

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

      <p>
        {forecastHour === 0
          ? "Now"
          : `+${forecastHour} hour${forecastHour === 1 ? "" : "s"}`}
      </p>
    </div>
  );
}