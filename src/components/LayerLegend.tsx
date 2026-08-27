import {
  ELEVATION_COLOR_STOPS,
  PRECIPITATION_INTENSITY_LEVELS,
} from "../config/layerVisuals";

import type { VisualColorStop } from "../config/layerVisuals";
import type { PrimaryView, WeatherOverlayState } from "../types/layer";

interface LayerLegendProps {
  primaryView: PrimaryView;
  weatherOverlays: WeatherOverlayState;
}

function buildGradient(
  stops: VisualColorStop[],
  minimum: number,
  maximum: number,
  prefix = ""
): string {
  const colors = stops.map((stop) => {
    const position = ((stop.value - minimum) / (maximum - minimum)) * 100;

    return `${stop.color} ${Math.max(0, Math.min(100, position))}%`;
  });

  return `linear-gradient(to right, ${prefix}${colors.join(", ")})`;
}

function GradientKey({
  title,
  gradient,
  labels,
}: {
  title: string;
  gradient: string;
  labels: string[];
}) {
  return (
    <div className="legend-section">
      <strong>{title}</strong>
      <div className="legend-bar">
        <div className="legend-gradient" style={{ background: gradient }} />
        <div className="legend-labels">
          {labels.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function PrecipitationKey() {
  return (
    <div className="legend-section">
      <GradientKey
        title="Precipitation in previous hour (mm)"
        gradient={buildGradient(
          PRECIPITATION_INTENSITY_LEVELS,
          0,
          15,
          "transparent 0%, transparent 0.6%, "
        )}
        labels={["Dry", "0.1", "1", "3", "8", "15+"]}
      />
      <div className="precipitation-symbol-key" aria-label="Precipitation intensity symbols">
        {[
          { count: 1, label: "Light" },
          { count: 2, label: "Moderate" },
          { count: 3, label: "Heavy" },
          { count: 4, label: "Very heavy" },
        ].map((item) => (
          <span key={item.count} className="precipitation-symbol-key-item">
            <span className="legend-drops" aria-hidden="true">
              {Array.from({ length: item.count }, (_, index) => (
                <i key={index} />
              ))}
            </span>
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function LayerLegend({
  primaryView,
  weatherOverlays,
}: LayerLegendProps) {
  const hasLegend =
    primaryView !== "terrain" ||
    weatherOverlays.temperatureContours ||
    weatherOverlays.pressureIsobars ||
    weatherOverlays.windFlow;

  if (!hasLegend) return null;

  return (
    <section className="weather-card legend-card">
      <p className="section-kicker">Visible information</p>

      {primaryView === "elevation" && (
        <GradientKey
          title="DEM elevation"
          gradient={buildGradient(ELEVATION_COLOR_STOPS, -500, 8000)}
          labels={["Below 0", "0 m", "600", "1,500", "3,000", "8,000 m"]}
        />
      )}

      {primaryView === "precipitation" && <PrecipitationKey />}

      {primaryView === "clouds" && (
        <GradientKey
          title="Model cloud cover"
          gradient="linear-gradient(to right, rgba(226, 231, 236, 0.05), rgba(205, 213, 218, 0.35), rgba(184, 192, 197, 0.72))"
          labels={["0%", "50%", "100%"]}
        />
      )}

      {weatherOverlays.temperatureContours && (
        <div className="legend-inline-key">
          <span className="temperature-contour-key" aria-hidden="true" />
          <p>
            Temperature contours use 1°, 2° or 5° intervals; 0° is emphasized.
          </p>
        </div>
      )}

      {weatherOverlays.pressureIsobars && (
        <div className="legend-inline-key">
          <span className="pressure-contour-key" aria-hidden="true" />
          <p>Mean sea-level pressure isobars are labelled in hPa.</p>
        </div>
      )}

      {weatherOverlays.windFlow && (
        <div className="legend-inline-key">
          <span className="wind-sample" aria-hidden="true">→</span>
          <p>Arrows show flow direction; warmer colours indicate faster wind.</p>
        </div>
      )}
    </section>
  );
}
