import type { Basemap, MapOverlayState } from "../types/layer";

interface LayerPanelProps {
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  satelliteAvailable: boolean;
  onBasemapChange: (basemap: Basemap) => void;
  onOverlayChange: (
    overlay: keyof MapOverlayState,
    enabled: boolean
  ) => void;
}

const BASEMAP_LABELS: Record<Basemap, string> = {
  terrain: "Terrain",
  satellite: "Satellite",
};

const BASEMAPS: Basemap[] = ["terrain", "satellite"];

const OVERLAY_OPTIONS: Array<{
  key: keyof MapOverlayState;
  label: string;
}> = [
  { key: "elevation", label: "Elevation" },
  { key: "precipitation", label: "Precipitation" },
  { key: "clouds", label: "Cloud cover" },
  { key: "temperatureContours", label: "Temperature contours" },
  { key: "pressureIsobars", label: "Pressure isobars" },
  { key: "windFlow", label: "Wind flow" },
];

export default function LayerPanel({
  basemap,
  mapOverlays,
  satelliteAvailable,
  onBasemapChange,
  onOverlayChange,
}: LayerPanelProps) {
  return (
    <section className="weather-card layer-card">
      <div className="card-heading">
        <div>
          <p className="section-kicker">Map display</p>
          <h2>Basemap & overlays</h2>
        </div>

        <span className="card-meta">{BASEMAP_LABELS[basemap]}</span>
      </div>

      <fieldset className="layer-control-group">
        <legend>Basemap</legend>
        <div className="layer-grid layer-grid-primary">
          {BASEMAPS.map((option) => {
            const disabled = option === "satellite" && !satelliteAvailable;

            return (
            <label
              key={option}
              className={`layer-option${disabled ? " layer-option-disabled" : ""}`}
              title={
                disabled
                  ? "Satellite is unavailable until a MapTiler key is configured."
                  : undefined
              }
            >
              <input
                type="radio"
                name="map-basemap"
                checked={basemap === option}
                disabled={disabled}
                onChange={() => onBasemapChange(option)}
              />
              <span>
                {BASEMAP_LABELS[option]}
                {disabled && <small>Setup</small>}
              </span>
            </label>
            );
          })}
        </div>
      </fieldset>

      <fieldset className="layer-control-group layer-overlay-group">
        <legend>Overlays</legend>
        <div className="layer-grid layer-grid-overlays">
          {OVERLAY_OPTIONS.map((option) => (
            <label key={option.key} className="layer-option layer-toggle-option">
              <input
                type="checkbox"
                checked={mapOverlays[option.key]}
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
