import type { WeatherData, ForecastDay } from "../types/weather";

export async function getWeather(
  latitude: number,
  longitude: number
): Promise<WeatherData & { forecast: ForecastDay[] }> {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m&daily=temperature_2m_max,temperature_2m_min&forecast_days=7`
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
    windSpeed: data.current.wind_speed_10m,
    windGusts: data.current.wind_gusts_10m,
    cloudCover: data.current.cloud_cover,
    humidity: data.current.relative_humidity_2m,
    pressure: data.current.pressure_msl,
    precipitation: data.current.precipitation,
    forecast,
  };
}