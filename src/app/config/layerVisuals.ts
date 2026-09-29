export interface VisualColorStop {
  value: number;
  color: string;
  label?: string;
}

export interface PrecipitationIntensityLevel extends VisualColorStop {
  drops: 1 | 2 | 3 | 4;
  opacity: number;
  category: "light" | "moderate" | "heavy" | "very-heavy";
}

// Product-level visual choices, deliberately kept out of user controls.
export const LAYER_VISUAL_STRENGTHS = {
  clouds: 0.56,
  precipitation: 0.86,
  elevation: 0.7,
  temperatureContour: 0.86,
  temperatureHalo: 0.26,
  pressureLine: 0.58,
  pressureLabel: 0.74,
  windParticle: 0.94,
} as const;

export const HILLSHADE_ZOOM_STOPS = [
  { zoom: 5.5, strength: 0 },
  { zoom: 7, strength: 0.06 },
  { zoom: 9, strength: 0.2 },
  { zoom: 11, strength: 0.36 },
  { zoom: 12, strength: 0.3 },
  { zoom: 13, strength: 0.24 },
  { zoom: 14, strength: 0.22 },
  { zoom: 15, strength: 0.2 },
  { zoom: 16, strength: 0.2 },
] as const;

export const WEATHER_SURFACE_CROSSFADE_MS = 260;

// GFS precipitation is a one-hour interval total, in millimetres. These
// nonlinear stops preserve ordinary rain without saturating extremes; positive
// trace amounts below the first stop fade continuously from zero.
export const PRECIPITATION_INTENSITY_LEVELS: PrecipitationIntensityLevel[] = [
  {
    value: 0.1,
    color: "#58bfd3",
    label: "0.1 light",
    drops: 1,
    opacity: 0.46,
    category: "light",
  },
  {
    value: 0.5,
    color: "#2497c8",
    label: "0.5",
    drops: 1,
    opacity: 0.62,
    category: "light",
  },
  {
    value: 1,
    color: "#386fd0",
    label: "1 moderate",
    drops: 2,
    opacity: 0.72,
    category: "moderate",
  },
  {
    value: 3,
    color: "#6548c7",
    label: "3 heavy",
    drops: 3,
    opacity: 0.82,
    category: "heavy",
  },
  {
    value: 8,
    color: "#b63c91",
    label: "8 very heavy",
    drops: 4,
    opacity: 0.92,
    category: "very-heavy",
  },
  {
    value: 15,
    color: "#e64f45",
    label: "15+ mm",
    drops: 4,
    opacity: 1,
    category: "very-heavy",
  },
];

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
