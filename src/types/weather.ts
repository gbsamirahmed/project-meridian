export interface ForecastDay {
  date: string;
  maxTemperature: number;
  minTemperature: number;
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windGusts: number;
  cloudCover: number;
  precipitation: number;
  visibility: number;
  dewPoint: number;
  forecastTimes: string[];
  forecast: ForecastDay[];
}