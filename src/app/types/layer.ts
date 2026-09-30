export type { Basemap } from "../../atlas/map/mapTypes";

export interface MapOverlayState {
  elevation: boolean;
  precipitation: boolean;
  clouds: boolean;
  temperatureContours: boolean;
  pressureIsobars: boolean;
  windFlow: boolean;
}
