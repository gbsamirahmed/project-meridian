import type { MapOverlayState } from "../types/layer";
import type { RouteConditionMode } from "../types/routeConditions";

export const MAP_OVERLAY_TOOLS: ReadonlyArray<{
  key: keyof MapOverlayState;
  label: string;
  shortLabel: string;
}> = [
  { key: "elevation", label: "Elevation", shortLabel: "Elev" },
  { key: "precipitation", label: "Precipitation", shortLabel: "Rain" },
  { key: "clouds", label: "Cloud cover", shortLabel: "Cloud" },
  { key: "temperatureContours", label: "Temperature contours", shortLabel: "Temp" },
  { key: "pressureIsobars", label: "Pressure isobars", shortLabel: "Press" },
  { key: "windFlow", label: "Wind flow", shortLabel: "Wind" },
];

export const ANALYSIS_MODES: ReadonlyArray<{
  mode: RouteConditionMode;
  label: string;
}> = [
  { mode: "none", label: "Elevation" },
  { mode: "temperature", label: "Temperature" },
  { mode: "precipitation", label: "Rain" },
  { mode: "wind", label: "Wind" },
  { mode: "gradient", label: "Gradient" },
];
