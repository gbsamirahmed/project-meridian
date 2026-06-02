import type { WeatherData, ForecastDay } from "../types/weather";

export async function getWeather(
  latitude: number,
  longitude: number
): Promise<WeatherData> {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,wind_speed_10m,cloud_cover&daily=temperature_2m_max,temperature_2m_min&forecast_days=7`
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
    cloudCover: data.current.cloud_cover,
    forecast,
  };
}