import type { HourlyForecast } from "../types/weather";

export interface LocalTimeParts {
  date: string;
  hour: number;
  minute: number;
}

const partsFormatter = (timeZone: string) => new Intl.DateTimeFormat("en-GB", {
  timeZone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

export function localTimeParts(instant: string | number, timeZone: string): LocalTimeParts {
  const parts = Object.fromEntries(partsFormatter(timeZone).formatToParts(new Date(instant)).map(part => [part.type, part.value]));
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    hour: Number(parts.hour),
    minute: Number(parts.minute),
  };
}

export function addCalendarDays(date: string, amount: number): string {
  const value = new Date(`${date}T12:00:00Z`);
  value.setUTCDate(value.getUTCDate() + amount);
  return value.toISOString().slice(0, 10);
}

export function availableLocalDays(hourly: HourlyForecast[], timeZone: string): string[] {
  return [...new Set(hourly.map(item => localTimeParts(item.time, timeZone).date))];
}

export function rollingForecastWindow(
  hourly: HourlyForecast[],
  timeZone: string,
  selectedDate: string,
  anchorHour: number,
): Array<{ item: HourlyForecast; index: number }> {
  const start = hourly.findIndex(item => {
    const local = localTimeParts(item.time, timeZone);
    return local.date === selectedDate && local.hour === anchorHour;
  });
  if (start < 0) return [];
  const endDate = addCalendarDays(selectedDate, 1);
  const end = hourly.findIndex((item, index) => {
    if (index <= start) return false;
    const local = localTimeParts(item.time, timeZone);
    return local.date === endDate && local.hour === anchorHour;
  });
  const final = end >= 0 ? end : hourly.length - 1;
  return hourly.slice(start, final + 1).map((item, offset) => ({ item, index: start + offset }));
}

export function forecastMarkerIndexes(sampleCount: number): number[] {
  if (sampleCount <= 0) return [];
  const markers = new Set([0, sampleCount - 1]);
  for (let index = 3; index < sampleCount - 1; index += 3) markers.add(index);
  return [...markers].sort((a, b) => a - b);
}

export function windTravelToDegrees(fromDegrees: number): number {
  return (fromDegrees + 180) % 360;
}

export function forecastDescription(samples: HourlyForecast[]): string {
  const precipitation = samples.map(item => item.precipitation).filter((value): value is number => value !== null);
  const clouds = samples.map(item => item.cloudCover).filter((value): value is number => value !== null);
  const peakRain = precipitation.length ? Math.max(...precipitation) : 0;
  const meanCloud = clouds.length ? clouds.reduce((sum, value) => sum + value, 0) / clouds.length : null;
  if (peakRain >= 2.5) return "Periods of heavy rain";
  if (peakRain >= 0.2) return "Rain at times";
  if (meanCloud === null) return "Conditions unavailable";
  if (meanCloud >= 80) return "Mostly overcast";
  if (meanCloud >= 45) return "Variable cloud";
  return "Mostly clear";
}

export function precipitationBarHeight(value: number | null, maximum: number): number | null {
  if (value === null) return null;
  if (value <= 0) return 0;
  return Math.max(1, value / Math.max(maximum, 0.1) * 26);
}
