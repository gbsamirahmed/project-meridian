export interface VisualColorStop {
  value: number;
  color: string;
  label?: string;
}

export const ELEVATION_LAYER_STRENGTH = 0.7;

// Native IGOR cartographic relief: 1.5 times the pre-evaluation strength curve.
// Keep the continuous planning-scale peak and close-view taper; this is not
// geometry exaggeration. Satellite suppression is applied in terrainLayers.
export const HILLSHADE_ZOOM_STOPS = [
  { zoom: 5.5, strength: 0 },
  { zoom: 7, strength: 0.09 },
  { zoom: 9, strength: 0.3 },
  { zoom: 11, strength: 0.54 },
  { zoom: 12, strength: 0.45 },
  { zoom: 13, strength: 0.36 },
  { zoom: 14, strength: 0.33 },
  { zoom: 15, strength: 0.3 },
  { zoom: 16, strength: 0.3 },
] as const;

export const ELEVATION_COLOR_STOPS: VisualColorStop[] = [
  { value: -11000, color: "#355f53" },
  { value: -500, color: "#3f725d", label: "Below sea level" },
  { value: 0, color: "#4c8267", label: "0 m" },
  { value: 20, color: "#568d6d" },
  { value: 100, color: "#6f9a6e" },
  { value: 300, color: "#a6a35c", label: "300" },
  { value: 600, color: "#bd854c", label: "600" },
  { value: 900, color: "#a45e49", label: "900" },
  { value: 1500, color: "#75615c", label: "1,500" },
  { value: 3000, color: "#b7afa5", label: "3,000" },
  { value: 5000, color: "#e4e1da", label: "5,000" },
  { value: 8000, color: "#fffdf8", label: "8,000 m" },
];
