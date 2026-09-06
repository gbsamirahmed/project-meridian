import { useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import DetailWorkspace from "./DetailWorkspace";
import {
  availableLocalDays,
  forecastDescription,
  forecastMarkerIndexes,
  localTimeParts,
  precipitationBarHeight,
  rollingForecastWindow,
  windTravelToDegrees,
} from "../services/forecastWorkspaceModel";
import type { MapOverlayState } from "../types/layer";
import type { Place } from "../types/place";
import type { WeatherData, HourlyForecast } from "../types/weather";

interface Props {
  place: Place | null;
  weather: WeatherData;
  activeTime: string | null;
  onForecastTimeChange: (time: string) => void;
  onMapLayerChange: (key: keyof MapOverlayState, enabled: boolean) => void;
  onClose: () => void;
}
type Key = Exclude<keyof HourlyForecast, "time" | "windDirection">;
type Row = { key: Key; label: string; unit: string; kind: "line" | "bar" | "wind"; colour: "orange" | "blue" | "grey"; layer?: keyof MapOverlayState };
const coreRows: Row[] = [
  { key: "temperature", label: "Temperature", unit: "°C", kind: "line", colour: "orange", layer: "temperatureContours" },
  { key: "precipitation", label: "Precipitation", unit: "mm / h", kind: "bar", colour: "blue", layer: "precipitation" },
  { key: "cloudCover", label: "Cloud", unit: "%", kind: "bar", colour: "grey", layer: "clouds" },
  { key: "windSpeed", label: "Wind", unit: "km/h", kind: "wind", colour: "orange", layer: "windFlow" },
];
const optionalRows: Row[] = [
  { key: "windGusts", label: "Gust", unit: "km/h", kind: "line", colour: "orange" },
  { key: "visibility", label: "Visibility", unit: "km", kind: "line", colour: "orange" },
  { key: "freezingLevel", label: "Freezing level", unit: "m", kind: "line", colour: "orange" },
];
const direction = (degrees: number | null) => degrees == null ? "" : ["N","NE","E","SE","S","SW","W","NW"][Math.round(degrees / 45) % 8];
const localLabel = (instant: string, timezone: string) => new Intl.DateTimeFormat("en-GB", { timeZone: timezone, hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(instant));
const fmtDay = (date: string) => new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric" }).format(new Date(`${date}T12:00:00Z`));
const fmtDate = (date: string) => new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(new Date(`${date}T12:00:00Z`));
const closestIndex = (hourly: HourlyForecast[], time: string | null) => {
  if (!time || !hourly.length) return 0;
  const target = Date.parse(time);
  return hourly.reduce((best, item, index) => Math.abs(Date.parse(item.time) - target) < Math.abs(Date.parse(hourly[best].time) - target) ? index : best, 0);
};

export default function ForecastWorkspace({ place, weather, activeTime, onForecastTimeChange, onMapLayerChange, onClose }: Props) {
  const timezone = weather.timezone || "UTC";
  const [openedAt] = useState(() => Date.now());
  const now = localTimeParts(openedAt, timezone);
  const days = useMemo(() => availableLocalDays(weather.hourly, timezone).filter(date => rollingForecastWindow(weather.hourly, timezone, date, now.hour).length > 1), [weather.hourly, timezone, now.hour]);
  const globalIndex = closestIndex(weather.hourly, activeTime);
  const activeDate = localTimeParts(weather.hourly[globalIndex]?.time ?? openedAt, timezone).date;
  const [day, setDay] = useState(days.includes(now.date) ? now.date : days.includes(activeDate) ? activeDate : days[0]);
  const [hovered, setHovered] = useState<number | null>(null);
  const [pinnedIndex, setPinnedIndex] = useState<number | null>(null);
  const [expanded, setExpanded] = useState(false);
  const pinned = pinnedIndex !== null;
  const selectedDay = day;
  const samples = rollingForecastWindow(weather.hourly, timezone, selectedDay, now.hour);
  const localActivePosition = samples.findIndex(sample => sample.index === (pinned ? pinnedIndex : hovered));
  const position = localActivePosition >= 0 ? localActivePosition : 0;
  const active = samples[position]?.item;
  const markers = forecastMarkerIndexes(samples.length);
  const daySamples = weather.hourly.filter(item => localTimeParts(item.time, timezone).date === selectedDay);
  const temperatures = daySamples.map(item => item.temperature).filter((value): value is number => value !== null);
  const peak = (key: "precipitation" | "windSpeed" | "windGusts") => {
    const values = daySamples.map(item => item[key]).filter((value): value is number => value !== null);
    return values.length ? Math.max(...values) : null;
  };
  const selectFromPointer = (event: { currentTarget: HTMLDivElement; clientX: number }) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const labelWidth = Number.parseFloat(getComputedStyle(event.currentTarget).getPropertyValue("--forecast-label-width")) || 0;
    const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left - labelWidth) / Math.max(1, bounds.width - labelWidth)));
    return Math.round(ratio * Math.max(0, samples.length - 1));
  };
  const commit = (samplePosition: number) => {
    const chosen = samples[samplePosition];
    if (!chosen) return;
    if (pinnedIndex === chosen.index) { setPinnedIndex(null); return; }
    setPinnedIndex(chosen.index);
    onForecastTimeChange(chosen.item.time);
  };
  const keyboard = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      setHovered(Math.max(0, Math.min(samples.length - 1, position + (event.key === "ArrowRight" ? 1 : -1))));
    }
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); commit(position); }
  };
  const rows = expanded ? [...coreRows, ...optionalRows] : coreRows;
  return <DetailWorkspace label="Forecast workspace" onClose={onClose}>
    <header className="forecast-workspace-header"><div><p>{place?.name ?? "Selected location"}</p><h2>Forecast</h2><span>{fmtDate(selectedDay)} · {localLabel(samples[0]?.item.time ?? "", timezone)}–{localLabel(samples.at(-1)?.item.time ?? "", timezone)}</span></div>{pinned && <button type="button" onClick={() => setPinnedIndex(null)}>Unpin</button>}</header>
    <nav className="forecast-days" aria-label="Forecast day">{days.map(value => {
      const localSamples = weather.hourly.filter(item => localTimeParts(item.time, timezone).date === value);
      const temps = localSamples.map(item => item.temperature).filter((entry): entry is number => entry !== null);
      return <button key={value} type="button" aria-pressed={selectedDay === value} onClick={() => { setDay(value); setHovered(null); setPinnedIndex(null); }}>
        <strong>{fmtDay(value)}</strong><small>{temps.length ? `${Math.round(Math.max(...temps))}° / ${Math.round(Math.min(...temps))}°` : "Unavailable"}</small>
      </button>;
    })}</nav>
    <section className="forecast-daily-summary"><div><span>Outlook</span><strong>{forecastDescription(daySamples)}</strong></div><div><span>Temperature</span><strong>{temperatures.length ? `${Math.round(Math.min(...temperatures))}–${Math.round(Math.max(...temperatures))} °C` : "Unavailable"}</strong></div><div><span>Peak rain</span><strong>{peak("precipitation") == null ? "Unavailable" : `${peak("precipitation")!.toFixed(1)} mm/h`}</strong></div><div><span>Wind / gust</span><strong>{peak("windSpeed") == null ? "Unavailable" : `${Math.round(peak("windSpeed")!)} / ${Math.round(peak("windGusts") ?? peak("windSpeed")!)} km/h`}</strong></div></section>
    <div className="forecast-axis" aria-hidden="true">{markers.map(index => <span key={index} style={{ "--marker-position": index / Math.max(1, samples.length - 1) } as CSSProperties}>{localLabel(samples[index].item.time, timezone)}</span>)}</div>
    <div className="forecast-plot" role="slider" tabIndex={0} aria-label="Forecast time" aria-valuemin={0} aria-valuemax={Math.max(0, samples.length - 1)} aria-valuenow={position} aria-valuetext={active ? localLabel(active.time, timezone) : "Unavailable"} onKeyDown={keyboard} onPointerMove={event => setHovered(selectFromPointer(event))} onPointerLeave={() => !pinned && setHovered(null)} onClick={event => commit(selectFromPointer(event))}>
      {(hovered !== null || pinned) && <div className={`forecast-time-cursor${pinned ? " pinned" : ""}`} style={{ "--forecast-position": position / Math.max(1, samples.length - 1) } as CSSProperties}><span>{active ? localLabel(active.time, timezone) : ""}</span></div>}
      {rows.map(row => <ForecastRow key={row.key} row={row} samples={samples.map(sample => sample.item)} active={active} markers={markers} onMap={() => { if (row.layer) { onMapLayerChange(row.layer, true); onClose(); } }} />)}
    </div>
    <footer className="forecast-workspace-options"><button type="button" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? "Fewer variables" : "More variables"}</button><span>Highest freezing level and cloud ceiling are not available as location time series.</span></footer>
  </DetailWorkspace>;
}

function ForecastRow({ row, samples, active, markers, onMap }: { row: Row; samples: HourlyForecast[]; active: HourlyForecast | undefined; markers: number[]; onMap: () => void }) {
  const values = samples.map(item => item[row.key]).filter((value): value is number => value !== null);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const range = Math.max(0.1, max - min);
  const segments: string[] = [];
  let points: string[] = [];
  samples.forEach((item, index) => {
    const value = item[row.key];
    if (value == null) { if (points.length) segments.push(points.join(" ")); points = []; return; }
    points.push(`${index / Math.max(1, samples.length - 1) * 100},${29 - (value - min) / range * 23}`);
  });
  if (points.length) segments.push(points.join(" "));
  const value = active?.[row.key];
  return <section className={`forecast-row ${row.kind} forecast-${row.colour}`}>
    <div><strong>{row.label}</strong><span>{value == null ? "Unavailable" : `${row.key === "windSpeed" ? `${direction(active?.windDirection ?? null)} ` : ""}${value.toFixed(value < 10 ? 1 : 0)} ${row.unit}`}</span>{row.layer && <button type="button" onClick={event => { event.stopPropagation(); onMap(); }}>Map</button>}</div>
    {values.length ? <div className="forecast-row-visual">
      <svg viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true">
        {row.kind === "bar" ? samples.map((item, index) => {
          const height = row.key === "precipitation" ? precipitationBarHeight(item[row.key], max) : item[row.key] == null ? null : Math.max(1, item[row.key]! / Math.max(max, 1) * 26);
          return height == null ? null : <rect key={index} x={index / Math.max(1, samples.length - 1) * 100 - .8} y={30 - height} width="1.6" height={height} />;
        }) : row.kind === "line" ? segments.map((segment, index) => <polyline key={index} points={segment} />) : null}
      </svg>
      {row.kind === "wind" && <div className="forecast-wind-vectors">{markers.map(index => {
        const degrees = samples[index]?.windDirection;
        return <span key={index} style={{ "--wind-position": index / Math.max(1, samples.length - 1), "--wind-rotation": `${degrees == null ? 0 : windTravelToDegrees(degrees)}deg` } as CSSProperties} title={degrees == null ? "Direction unavailable" : `Wind from ${direction(degrees)}`}>↑</span>;
      })}</div>}
      <div className="forecast-sparse-values" aria-hidden="true">{markers.map(index => <span key={index} style={{ "--marker-position": index / Math.max(1, samples.length - 1) } as CSSProperties}>{samples[index]?.[row.key] == null ? "–" : Math.round(samples[index][row.key]!)}</span>)}</div>
    </div> : <div className="forecast-gap">Unavailable</div>}
  </section>;
}
