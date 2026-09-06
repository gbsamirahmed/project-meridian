import type { WeatherData, ForecastDay } from "../types/weather";

export async function getWeather(
  latitude: number,
  longitude: number
): Promise<WeatherData> {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m,visibility,dew_point_2m&hourly=temperature_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,freezing_level_height&daily=temperature_2m_max,temperature_2m_min&forecast_days=7&timezone=auto`
  );

  if (!response.ok) {
    throw new Error(`Weather API error: ${response.status}`);
  }

  const data = await response.json();

  if (!data.current || !data.daily || !data.hourly) {
    throw new Error(
      "Weather API response is missing current, hourly or daily data"
    );
  }

  const forecast: ForecastDay[] = data.daily.time.map(
    (date: string, index: number) => ({
      date,
      maxTemperature: data.daily.temperature_2m_max[index],
      minTemperature: data.daily.temperature_2m_min[index],
    })
  );
  const utcOffsetSeconds = data.utc_offset_seconds ?? 0;

  return {
    utcOffsetSeconds,
    temperature: data.current.temperature_2m,
    humidity: data.current.relative_humidity_2m,
    pressure: data.current.pressure_msl,
    windSpeed: data.current.wind_speed_10m,
    windGusts: data.current.wind_gusts_10m,
    cloudCover: data.current.cloud_cover,
    precipitation: data.current.precipitation,
    visibility: data.current.visibility / 1000,
    dewPoint: data.current.dew_point_2m,
    hourly: data.hourly.time.map((time: string, index: number) => ({
      time,
      temperature: data.hourly.temperature_2m?.[index] ?? null,
      precipitation: data.hourly.precipitation?.[index] ?? null,
      cloudCover: data.hourly.cloud_cover?.[index] ?? null,
      windSpeed: data.hourly.wind_speed_10m?.[index] ?? null,
      windDirection: data.hourly.wind_direction_10m?.[index] ?? null,
      windGusts: data.hourly.wind_gusts_10m?.[index] ?? null,
      visibility: data.hourly.visibility?.[index] == null ? null : data.hourly.visibility[index] / 1000,
      freezingLevel: data.hourly.freezing_level_height?.[index] ?? null,
    })),
    forecastTimes: data.hourly.time.map((time: string) =>
      new Date(Date.parse(`${time}Z`) - utcOffsetSeconds * 1000).toISOString()
    ),
    forecast,
  };
}
