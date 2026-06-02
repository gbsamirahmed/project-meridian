export interface ForecastDay {
  date: string;
  maxTemperature: number;
  minTemperature: number;
}

export interface WeatherData {
  temperature: number;
  windSpeed: number;
  cloudCover: number;
  forecast: ForecastDay[];
}