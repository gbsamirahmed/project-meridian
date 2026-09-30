import type { MapOverlayState } from "./mapOverlayState";

export const MAP_OVERLAY_TOOLS: ReadonlyArray<{
  key: keyof MapOverlayState;
  label: string;
  shortLabel: string;
}> = [
  { key: "elevation", label: "Elevation", shortLabel: "Elev" },
  { key: "precipitation", label: "Precipitation", shortLabel: "Rain" },
  { key: "clouds", label: "Cloud cover", shortLabel: "Cloud" },
  { key: "temperatureContours", label: "Temperature contours", shortLabel: "Temp" },
  { key: "pressureIsobars", label: "Pressure isobars", shortLabel: "Pres" },
  { key: "windFlow", label: "Wind flow", shortLabel: "Wind" },
];
