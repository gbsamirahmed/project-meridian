import { useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import DetailWorkspace from "./DetailWorkspace";
import type { Place } from "../types/place";
import type { WeatherData, HourlyForecast } from "../types/weather";

interface Props { place: Place | null; weather: WeatherData; activeTime: string | null; onForecastTimeChange: (time: string) => void; onClose: () => void; }
type Key = Exclude<keyof HourlyForecast, "time" | "windDirection">;
const rows: Array<{ key: Key; label: string; unit: string; kind: "line" | "bar" }> = [
  { key: "temperature", label: "Temperature", unit: "°C", kind: "line" },
  { key: "precipitation", label: "Precipitation", unit: "mm", kind: "bar" },
  { key: "cloudCover", label: "Cloud", unit: "%", kind: "bar" },
  { key: "windSpeed", label: "Wind", unit: "km/h", kind: "line" },
  { key: "windGusts", label: "Gust", unit: "km/h", kind: "line" },
  { key: "visibility", label: "Visibility", unit: "km", kind: "line" },
  { key: "freezingLevel", label: "Freezing level", unit: "m", kind: "line" },
];
const dateKey = (time: string) => time.slice(0, 10);
const fmtDay = (date: string) => new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric" }).format(new Date(`${date}T12:00:00`));
const fmtDate = (date: string) => new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(new Date(`${date}T12:00:00`));
const fmtTime = (time: string) => time.slice(11, 16);
const direction = (degrees: number | null) => degrees == null ? "" : ["N","NE","E","SE","S","SW","W","NW"][Math.round(degrees / 45) % 8];

function localForecastInstant(time: string, utcOffsetSeconds: number): number {
  return Date.parse(`${time}Z`) - utcOffsetSeconds * 1000;
}

function closestHourlyIndex(hourly: HourlyForecast[], time: string | null, utcOffsetSeconds: number): number {
  if (!time || hourly.length === 0) return 0;
  const target = Date.parse(time);
  return hourly.reduce((best, item, index) => Math.abs(localForecastInstant(item.time, utcOffsetSeconds) - target) < Math.abs(localForecastInstant(hourly[best].time, utcOffsetSeconds) - target) ? index : best, 0);
}

export default function ForecastWorkspace({ place, weather, activeTime, onForecastTimeChange, onClose }: Props) {
  const days = useMemo(() => [...new Set(weather.hourly.map(item => dateKey(item.time)))], [weather]);
  const activeGlobalIndex = closestHourlyIndex(weather.hourly, activeTime, weather.utcOffsetSeconds);
  const globalDay = dateKey(weather.hourly[activeGlobalIndex]?.time ?? weather.hourly[0]?.time ?? "");
  const [day, setDay] = useState(globalDay || days[0]);
  const [hovered, setHovered] = useState<number | null>(null);
  const [pinned, setPinned] = useState(false);
  const visibleDay = pinned ? globalDay : day;
  const samples = weather.hourly.map((item, index) => ({ item, index })).filter(({ item }) => dateKey(item.time) === visibleDay);
  const active = pinned ? activeGlobalIndex : hovered ?? (globalDay === visibleDay ? activeGlobalIndex : samples[0]?.index ?? 0);
  const activeSample = weather.hourly[active];
  const selectFromPointer = (event: { currentTarget: HTMLDivElement; clientX: number }) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const labelWidth = Number.parseFloat(getComputedStyle(event.currentTarget).getPropertyValue("--forecast-label-width")) || 0;
    const plotLeft = bounds.left + labelWidth;
    const plotWidth = Math.max(1, bounds.width - labelWidth);
    const position = Math.max(0, Math.min(1, (event.clientX - plotLeft) / plotWidth));
    return samples[Math.round(position * Math.max(0, samples.length - 1))]?.index ?? 0;
  };
  const commit = (index: number) => {
    if (pinned && index === activeGlobalIndex) {
      setPinned(false);
      return;
    }
    setPinned(true);
    setDay(dateKey(weather.hourly[index].time));
    onForecastTimeChange(new Date(localForecastInstant(weather.hourly[index].time, weather.utcOffsetSeconds)).toISOString());
  };
  const keyboard = (event: KeyboardEvent<HTMLDivElement>) => {
    const current = samples.findIndex(sample => sample.index === active);
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); setHovered(samples[Math.max(0, Math.min(samples.length - 1, current + (event.key === "ArrowRight" ? 1 : -1)))]?.index ?? 0); }
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); commit(active); }
  };
  return <DetailWorkspace label="Forecast workspace" onClose={onClose}>
    <header className="forecast-workspace-header"><div><p>{place?.name ?? "Selected location"}</p><h2>Forecast</h2><span>{fmtDate(visibleDay)}</span></div>{pinned && <button type="button" onClick={() => setPinned(false)}>Unpin</button>}</header>
    <nav className="forecast-days" aria-label="Forecast day">{days.map(value => { const summary = weather.forecast.find(item => item.date === value); return <button key={value} type="button" aria-pressed={visibleDay === value} onClick={() => { setDay(value); setHovered(null); setPinned(false); }}><strong>{fmtDay(value)}</strong>{summary && <small>{Math.round(summary.maxTemperature)}° / {Math.round(summary.minTemperature)}°</small>}</button>; })}</nav>
    <div className="forecast-axis" aria-hidden="true">{samples.filter((_, index) => index % 3 === 0).map(({ item }) => <span key={item.time}>{fmtTime(item.time)}</span>)}</div>
    <div className="forecast-plot" role="slider" tabIndex={0} aria-label="Forecast time" aria-valuemin={0} aria-valuemax={Math.max(0, samples.length - 1)} aria-valuenow={Math.max(0, samples.findIndex(sample => sample.index === active))} aria-valuetext={activeSample ? fmtTime(activeSample.time) : "Unavailable"} onKeyDown={keyboard} onPointerMove={event => setHovered(selectFromPointer(event))} onPointerLeave={() => setHovered(null)} onClick={event => commit(selectFromPointer(event))}>
      <div className={`forecast-time-cursor${pinned ? " pinned" : ""}`} style={{ "--forecast-position": Math.max(0, samples.findIndex(sample => sample.index === active)) / Math.max(1, samples.length - 1) } as CSSProperties}><span>{activeSample ? fmtTime(activeSample.time) : ""}</span></div>
      {rows.map(row => <ForecastRow key={row.key} row={row} samples={samples.map(sample => sample.item)} active={activeSample} />)}
      <section className="forecast-row unavailable-row"><div><strong>Highest freezing level</strong><span>Unavailable</span></div><div className="forecast-gap">No hourly location series</div></section>
      <section className="forecast-row unavailable-row"><div><strong>Cloud ceiling</strong><span>Unavailable</span></div><div className="forecast-gap">No hourly location series</div></section>
    </div>
  </DetailWorkspace>;
}

function ForecastRow({ row, samples, active }: { row: typeof rows[number]; samples: HourlyForecast[]; active: HourlyForecast | undefined }) {
  const values = samples.map(item => item[row.key]).filter((value): value is number => value !== null);
  const min = values.length ? Math.min(...values) : 0, max = values.length ? Math.max(...values) : 1, range = Math.max(1, max - min);
  const segments: string[] = [];
  let points: string[] = [];
  samples.forEach((item, index) => {
    const value = item[row.key];
    if (value == null) {
      if (points.length) segments.push(points.join(" "));
      points = [];
      return;
    }
    points.push(`${index / Math.max(1, samples.length - 1) * 100},${30 - (value - min) / range * 24}`);
  });
  if (points.length) segments.push(points.join(" "));
  const value = active?.[row.key];
  return <section className={`forecast-row ${row.kind}`}><div><strong>{row.label}</strong><span>{value == null ? "Unavailable" : `${row.key === "windSpeed" ? `${direction(active?.windDirection ?? null)} ` : ""}${value.toFixed(value < 10 ? 1 : 0)} ${row.unit}`}</span></div>{values.length ? <svg viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true">{row.kind === "bar" ? samples.map((item, index) => item[row.key] == null ? null : <rect key={index} x={index / samples.length * 100 + 0.25} y={30 - (item[row.key]! - min) / range * 24} width={Math.max(0.8, 100 / samples.length - 0.5)} height={4 + (item[row.key]! - min) / range * 24} />) : segments.map((segment, index) => <polyline key={index} points={segment} />)}</svg> : <div className="forecast-gap">Unavailable</div>}</section>;
}
