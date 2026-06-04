export interface GridPoint {
  latitude: number;
  longitude: number;

  elevation: number;

  temperature: number[];
  cloudCover: number[];
  precipitation: number[];
  pressure: number[];

  windSpeed: number[];
  windDirection: number[];
}