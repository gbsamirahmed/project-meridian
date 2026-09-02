import type { PointerEvent } from "react";
import type { JourneySchedule, TerrainRoute } from "../types/route";

interface RouteProfileProps {
  route: TerrainRoute;
  schedule: JourneySchedule | null;
  focusedIndex: number | null;
  onFocusChange: (index: number | null) => void;
}

const WIDTH = 300;
const HEIGHT = 126;
const LEFT = 12;
const RIGHT = 8;
const TOP = 12;
const BOTTOM = 24;

function minutesLabel(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remainder = Math.round(minutes % 60);
  return hours ? `${hours}h ${remainder ? `${remainder}m` : ""}`.trim() : `${remainder}m`;
}

export default function RouteProfile({
  route,
  schedule,
  focusedIndex,
  onFocusChange,
}: RouteProfileProps) {
  const validElevations = route.samples
    .map((sample) => sample.smoothedElevationM)
    .filter((value): value is number => value !== null);
  if (validElevations.length < 2) return null;
  const minimum = Math.floor(Math.min(...validElevations) / 50) * 50;
  const maximum = Math.ceil(Math.max(...validElevations) / 50) * 50;
  const range = Math.max(50, maximum - minimum);
  const innerWidth = WIDTH - LEFT - RIGHT;
  const innerHeight = HEIGHT - TOP - BOTTOM;
  const xFor = (distance: number) =>
    LEFT + (distance / Math.max(1, route.totalDistanceM)) * innerWidth;
  const yFor = (elevation: number) =>
    TOP + (1 - (elevation - minimum) / range) * innerHeight;
  let path = "";
  let open = false;
  for (const sample of route.samples) {
    if (sample.smoothedElevationM === null) {
      open = false;
      continue;
    }
    path += `${open ? "L" : "M"}${xFor(sample.cumulativeDistanceM).toFixed(2)},${yFor(sample.smoothedElevationM).toFixed(2)} `;
    open = true;
  }
  const focusSample =
    focusedIndex === null
      ? null
      : route.samples[Math.max(0, Math.min(route.samples.length - 1, focusedIndex))];
  const focusSchedule =
    focusSample && schedule ? schedule.samples[focusSample.index] : null;

  const focusFromPointer = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = Math.max(
      0,
      Math.min(1, (event.clientX - bounds.left) / Math.max(1, bounds.width))
    );
    const target = fraction * route.totalDistanceM;
    let nearest = 0;
    let difference = Number.POSITIVE_INFINITY;
    route.samples.forEach((sample, index) => {
      const candidate = Math.abs(sample.cumulativeDistanceM - target);
      if (candidate < difference) {
        difference = candidate;
        nearest = index;
      }
    });
    onFocusChange(nearest);
  };

  return (
    <div className="route-profile">
      <div className="route-profile-heading">
        <span>Elevation & journey</span>
        {focusSample && (
          <strong>
            {(focusSample.cumulativeDistanceM / 1000).toFixed(1)} km · {Math.round(focusSample.smoothedElevationM ?? 0)} m
            {focusSchedule ? ` · ${minutesLabel(focusSchedule.elapsedMinutes)}` : ""}
          </strong>
        )}
      </div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="slider"
        aria-label="Route elevation and expected journey profile"
        aria-valuemin={0}
        aria-valuemax={Math.round(route.totalDistanceM)}
        aria-valuenow={Math.round(focusSample?.cumulativeDistanceM ?? 0)}
        tabIndex={0}
        onPointerDown={focusFromPointer}
        onPointerMove={(event) => {
          if (event.pointerType === "mouse" || event.buttons > 0) focusFromPointer(event);
        }}
        onKeyDown={(event) => {
          if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
          event.preventDefault();
          const direction = event.key === "ArrowRight" ? 1 : -1;
          onFocusChange(
            Math.max(
              0,
              Math.min(route.samples.length - 1, (focusedIndex ?? 0) + direction)
            )
          );
        }}
      >
        <line x1={LEFT} y1={TOP + innerHeight} x2={WIDTH - RIGHT} y2={TOP + innerHeight} className="route-profile-axis" />
        <path d={path.trim()} className="route-profile-line" />
        {focusSample && focusSample.smoothedElevationM !== null && (
          <>
            <line
              x1={xFor(focusSample.cumulativeDistanceM)}
              y1={TOP}
              x2={xFor(focusSample.cumulativeDistanceM)}
              y2={TOP + innerHeight}
              className="route-profile-focus-line"
            />
            <circle
              cx={xFor(focusSample.cumulativeDistanceM)}
              cy={yFor(focusSample.smoothedElevationM!)}
              r="3.8"
              className="route-profile-focus-point"
            />
          </>
        )}
        <text x={LEFT} y={HEIGHT - 5}>0</text>
        <text x={WIDTH / 2} y={HEIGHT - 5} textAnchor="middle">
          {(route.totalDistanceM / 2000).toFixed(1)} km
        </text>
        <text x={WIDTH - RIGHT} y={HEIGHT - 5} textAnchor="end">
          {(route.totalDistanceM / 1000).toFixed(1)} km
        </text>
        <text x={LEFT + 2} y={TOP + 9}>{maximum} m</text>
      </svg>
      <p>Move, tap, or use arrow keys to locate a point on the map.</p>
    </div>
  );
}
