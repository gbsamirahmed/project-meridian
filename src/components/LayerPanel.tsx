import type { PrimaryView, WeatherOverlayState } from "../types/layer";

interface LayerPanelProps {
  primaryView: PrimaryView;
  weatherOverlays: WeatherOverlayState;
  onPrimaryViewChange: (view: PrimaryView) => void;
  onOverlayChange: (
    overlay: keyof WeatherOverlayState,
    enabled: boolean
  ) => void;
}

const PRIMARY_VIEW_LABELS: Record<PrimaryView, string> = {
  terrain: "Terrain",
  elevation: "Elevation",
  precipitation: "Precipitation",
  clouds: "Cloud cover",
};

const OVERLAY_OPTIONS: Array<{
  key: keyof WeatherOverlayState;
  label: string;
}> = [
  { key: "temperatureContours", label: "Temperature contours" },
  { key: "pressureIsobars", label: "Pressure isobars" },
  { key: "windFlow", label: "Wind flow" },
];

export default function LayerPanel({
  primaryView,
  weatherOverlays,
  onPrimaryViewChange,
  onOverlayChange,
}: LayerPanelProps) {
  const primaryViews = Object.keys(PRIMARY_VIEW_LABELS) as PrimaryView[];

  return (
    <section className="weather-card layer-card">
      <div className="card-heading">
        <div>
          <p className="section-kicker">Map display</p>
          <h2>Weather view</h2>
        </div>

        <span className="card-meta">{PRIMARY_VIEW_LABELS[primaryView]}</span>
      </div>

      <fieldset className="layer-control-group">
        <legend>View</legend>
        <div className="layer-grid layer-grid-primary">
          {primaryViews.map((view) => (
            <label key={view} className="layer-option">
              <input
                type="radio"
                name="primary-map-view"
                checked={primaryView === view}
                onChange={() => onPrimaryViewChange(view)}
              />
              <span>{PRIMARY_VIEW_LABELS[view]}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="layer-control-group layer-overlay-group">
        <legend>Overlays</legend>
        <div className="layer-grid layer-grid-overlays">
          {OVERLAY_OPTIONS.map((option) => (
            <label key={option.key} className="layer-option layer-toggle-option">
              <input
                type="checkbox"
                checked={weatherOverlays[option.key]}
                onChange={(event) =>
                  onOverlayChange(option.key, event.target.checked)
                }
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </section>
  );
}
