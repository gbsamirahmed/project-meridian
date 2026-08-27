export type PrimaryView =
  | "terrain"
  | "elevation"
  | "precipitation"
  | "clouds";

export interface WeatherOverlayState {
  temperatureContours: boolean;
  pressureIsobars: boolean;
  windFlow: boolean;
}
