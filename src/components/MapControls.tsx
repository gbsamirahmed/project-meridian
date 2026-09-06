import type { Basemap, MapOverlayState } from "../types/layer";
import { MAP_OVERLAY_TOOLS } from "../services/desktopControlOptions";

interface MapControlsProps {
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  satelliteAvailable: boolean;
  onBasemapChange: (basemap: Basemap) => void;
  onOverlayChange: (overlay: keyof MapOverlayState, enabled: boolean) => void;
}

export default function MapControls({ basemap, mapOverlays, satelliteAvailable, onBasemapChange, onOverlayChange }: MapControlsProps) {
  return (
    <div className="map-controls-native" aria-label="Map controls">
      <aside className="map-tool-strip desktop-surface" aria-label="Map layers">
        <button type="button" className={`map-tool-button${basemap === "terrain" ? " active" : ""}`} aria-pressed={basemap === "terrain"} aria-label="Terrain basemap" title="Terrain basemap" onClick={() => onBasemapChange("terrain")}><span aria-hidden="true">◒</span><small>Ter</small></button>
        <button type="button" className={`map-tool-button${basemap === "satellite" ? " active" : ""}`} aria-pressed={basemap === "satellite"} aria-label="Satellite basemap" disabled={!satelliteAvailable} title={satelliteAvailable ? "Satellite basemap" : "Satellite requires a configured MapTiler key"} onClick={() => onBasemapChange("satellite")}><span aria-hidden="true">◉</span><small>Sat</small></button>
        <div className="map-tool-divider" />
        {MAP_OVERLAY_TOOLS.map((tool) => (
          <button key={tool.key} type="button" className={`map-tool-button${mapOverlays[tool.key] ? " active" : ""}`} aria-pressed={mapOverlays[tool.key]} aria-label={tool.label} title={tool.label} onClick={() => onOverlayChange(tool.key, !mapOverlays[tool.key])}>
            <span aria-hidden="true">{tool.key === "precipitation" ? "≋" : tool.key === "windFlow" ? "↝" : tool.key === "clouds" ? "☁" : tool.key === "temperatureContours" ? "°" : tool.key === "pressureIsobars" ? "P" : "△"}</span>
            <small>{tool.shortLabel}</small>
          </button>
        ))}
      </aside>
    </div>
  );
}