export default function TemperatureLegend() {
  return (
    <div className="weather-card">
      <h2>Temperature Scale</h2>

      <div className="legend-bar">
        <div
          className="legend-gradient"
          style={{
            background:
              "linear-gradient(to right, " +
              "#1e40af, " +
              "#2563eb, " +
              "#06b6d4, " +
              "#22c55e, " +
              "#facc15, " +
              "#ef4444, " +
              "#7e22ce" +
              ")",
          }}
        />

        <div className="legend-labels">
          <span>-20°</span>
          <span>-10°</span>
          <span>0°</span>
          <span>10°</span>
          <span>20°</span>
          <span>30°</span>
          <span>40°</span>
        </div>
      </div>
    </div>
  );
}