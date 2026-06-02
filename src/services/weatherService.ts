import type { WeatherData, ForecastDay } from "../types/weather";

export async function getWeather(
  latitude: number,
  longitude: number
): Promise<WeatherData> {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m,visibility,dew_point_2m&daily=temperature_2m_max,temperature_2m_min&forecast_days=7`
  );

  const data = await response.json();

  const forecast: ForecastDay[] = data.daily.time.map(
    (date: string, index: number) => ({
      date,
      maxTemperature: data.daily.temperature_2m_max[index],
      minTemperature: data.daily.temperature_2m_min[index],
    })
  );

  return {
    temperature: data.current.temperature_2m,
    humidity: data.current.relative_humidity_2m,
    pressure: data.current.pressure_msl,
    windSpeed: data.current.wind_speed_10m,
    windGusts: data.current.wind_gusts_10m,
    cloudCover: data.current.cloud_cover,
    precipitation: data.current.precipitation,
    visibility: data.current.visibility / 1000,
    dewPoint: data.current.dew_point_2m,
    forecast,
  };
}