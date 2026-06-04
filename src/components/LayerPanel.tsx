import type { WeatherLayer } from "../types/layer";

interface LayerPanelProps {
  selectedLayer: WeatherLayer;
  onLayerChange: (layer: WeatherLayer) => void;
}

export default function LayerPanel({
  selectedLayer,
  onLayerChange,
}: LayerPanelProps) {
  const layers: WeatherLayer[] = [
    "none",
    "temperature",
    "clouds",
    "precipitation",
    "elevation",
    "hillshade",
    "wind",
    "pressure",
  ];

  return (
    <div className="weather-card">
      <h2>Layers</h2>

      {layers.map((layer) => (
        <label key={layer} className="layer-option">
          <input
            type="radio"
            checked={selectedLayer === layer}
            onChange={() => onLayerChange(layer)}
          />

          {layer}
        </label>
      ))}
    </div>
  );
}