export interface PrecipitationIntensityLevel {
  value: number;
  color: string;
  label?: string;
  drops: 1 | 2 | 3 | 4;
  opacity: number;
  category: "light" | "moderate" | "heavy" | "very-heavy";
}

export const WEATHER_LAYER_VISUAL_STRENGTHS = {
  clouds: 0.56,
  precipitation: 0.86,
  temperatureContour: 0.86,
  temperatureHalo: 0.26,
  pressureLine: 0.58,
  pressureLabel: 0.74,
  windParticle: 0.94,
} as const;

export const WEATHER_SURFACE_CROSSFADE_MS = 260;

export const PRECIPITATION_INTENSITY_LEVELS: PrecipitationIntensityLevel[] = [
  { value: 0.1, color: "#58bfd3", label: "0.1 light", drops: 1, opacity: 0.46, category: "light" },
  { value: 0.5, color: "#2497c8", label: "0.5", drops: 1, opacity: 0.62, category: "light" },
  { value: 1, color: "#386fd0", label: "1 moderate", drops: 2, opacity: 0.72, category: "moderate" },
  { value: 3, color: "#6548c7", label: "3 heavy", drops: 3, opacity: 0.82, category: "heavy" },
  { value: 8, color: "#b63c91", label: "8 very heavy", drops: 4, opacity: 0.92, category: "very-heavy" },
  { value: 15, color: "#e64f45", label: "15+ mm", drops: 4, opacity: 1, category: "very-heavy" },
];
