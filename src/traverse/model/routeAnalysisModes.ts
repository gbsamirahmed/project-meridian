import type { RouteConditionMode } from "../types/routeConditions";

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
