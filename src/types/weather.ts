export interface ForecastDay {
  date: string;
  maxTemperature: number;
  minTemperature: number;
}

export interface WeatherData {
  temperature: number;
  windSpeed: number;
  windGusts: number;
  cloudCover: number;
  humidity: number;
  pressure: number;
  precipitation: number;
  forecast: ForecastDay[];
}