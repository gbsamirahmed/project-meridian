export interface ForecastDay {
  date: string;
  maxTemperature: number;
  minTemperature: number;
}

export interface HourlyForecast {
  time: string;
  temperature: number | null;
  precipitation: number | null;
  cloudCover: number | null;
  windSpeed: number | null;
  windDirection: number | null;
  windGusts: number | null;
  visibility: number | null;
  freezingLevel: number | null;
}

export interface WeatherData {
  timezone: string;
  utcOffsetSeconds: number;
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windGusts: number;
  cloudCover: number;
  precipitation: number;
  visibility: number;
  dewPoint: number;
  hourly: HourlyForecast[];
  forecastTimes: string[];
  forecast: ForecastDay[];
}
