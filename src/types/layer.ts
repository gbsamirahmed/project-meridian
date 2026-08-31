export type Basemap = "terrain" | "satellite";

export interface MapOverlayState {
  elevation: boolean;
  precipitation: boolean;
  clouds: boolean;
  temperatureContours: boolean;
  pressureIsobars: boolean;
  windFlow: boolean;
}
