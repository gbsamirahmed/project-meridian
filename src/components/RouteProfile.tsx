import { useEffect, useId, useMemo, useRef, useState, type MouseEvent, type PointerEvent } from "react";
import { freezingProfileSeries } from "../services/derivedRouteConditions";
import { atmosphericHeightLabel } from "../services/atmosphericFormatting";
import {
  nearestRouteSampleForFraction,
  nextPinnedRouteSample,
  profilePointerFraction,
} from "../services/routeProfileInteraction";
import type { JourneySchedule, TerrainRoute } from "../types/route";
import { routeConditionColour } from "../services/routeConditionStyle";
import type { RouteConditionMode, RouteConditions } from "../types/routeConditions";

interface RouteProfileProps {
  route: TerrainRoute;
  schedule: JourneySchedule | null;
  conditions: RouteConditions | null;
  conditionMode: RouteConditionMode;
  focusedIndex: number | null;
  onFocusChange: (index: number | null) => void;
  wide?: boolean;
  pinnedIndex?: number | null;
  onPreviewChange?: (index: number | null) => void;
  onPinnedChange?: (index: number | null) => void;
}

const COMPACT_WIDTH = 300;
const COMPACT_HEIGHT = 126;
const WIDE_WIDTH = 760;
const WIDE_HEIGHT = 104;
const LEFT = 12;
const RIGHT = 8;
const TOP = 8;
const BOTTOM = 20;

function minutesLabel(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remainder = Math.round(minutes % 60);
  return hours ? `${hours}h ${remainder ? `${remainder}m` : ""}`.trim() : `${remainder}m`;
}

export default function RouteProfile({
  route,
  schedule,
  conditions,
  conditionMode,
  focusedIndex,
  onFocusChange,
  wide = false,
  pinnedIndex = null,
  onPreviewChange,
  onPinnedChange,
}: RouteProfileProps) {
  const clipId = useId();
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [wideSize, setWideSize] = useState({ width: WIDE_WIDTH, height: WIDE_HEIGHT });
  const WIDTH = wide ? wideSize.width : COMPACT_WIDTH;
  const HEIGHT = wide ? wideSize.height : COMPACT_HEIGHT;

  useEffect(() => {
    if (!wide || !svgRef.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.max(320, Math.round(entry.contentRect.width));
      const height = Math.max(80, Math.round(entry.contentRect.height));
      setWideSize((current) => current.width === width && current.height === height
        ? current
        : { width, height });
    });
    observer.observe(svgRef.current);
    return () => observer.disconnect();
  }, [wide]);

  const freezingSeries = useMemo(
    () => conditions?.derived && conditions.routeId === route.id && conditions.samples.length === route.samples.length
      ? freezingProfileSeries(conditions.samples, conditions.derived)
      : [],
    [conditions, route.id, route.samples.length]
  );
  const validElevations = route.samples
    .map((sample) => sample.smoothedElevationM)
    .filter((value): value is number => value !== null);
  const minimum = Math.floor(Math.min(...validElevations) / 50) * 50;
  const maximum = Math.ceil(Math.max(...validElevations) / 50) * 50;
  const range = Math.max(50, maximum - minimum);
  const innerWidth = WIDTH - LEFT - RIGHT;
  const innerHeight = HEIGHT - TOP - BOTTOM;
  const atmosphere = useMemo(() => {
    let path = "", open = false;
    let low = Infinity, high = -Infinity, visible = false;
    for (const point of freezingSeries) {
      if (point.altitudeM === null) { open = false; continue; }
      low = Math.min(low, point.altitudeM);
      high = Math.max(high, point.altitudeM);
      if (point.altitudeM >= minimum && point.altitudeM <= minimum + range) visible = true;
      const x = LEFT + point.distanceM / Math.max(1, route.totalDistanceM) * innerWidth;
      const y = TOP + (1 - (point.altitudeM - minimum) / range) * innerHeight;
      path += `${open ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)} `;
      open = true;
    }
    return { path, low, high, visible };
  }, [freezingSeries, innerHeight, innerWidth, minimum, range, route.totalDistanceM]);
  if (validElevations.length < 2) return null;

  const xFor = (distance: number) => LEFT + distance / Math.max(1, route.totalDistanceM) * innerWidth;
  const yFor = (elevation: number) => TOP + (1 - (elevation - minimum) / range) * innerHeight;
  let path = "";
  let open = false;
  for (const sample of route.samples) {
    if (sample.smoothedElevationM === null) { open = false; continue; }
    path += `${open ? "L" : "M"}${xFor(sample.cumulativeDistanceM).toFixed(2)},${yFor(sample.smoothedElevationM).toFixed(2)} `;
    open = true;
  }

  const focusSample = focusedIndex === null
    ? null
    : route.samples[Math.max(0, Math.min(route.samples.length - 1, focusedIndex))];
  const focusSchedule = focusSample && schedule ? schedule.samples[focusSample.index] : null;
  const conditionStrip = conditionMode !== "none" && conditions?.routeId === route.id && conditions.samples.length === route.samples.length
    ? conditions.samples
    : null;
  const stripStep = conditionStrip ? Math.max(1, Math.ceil((conditionStrip.length - 1) / 160)) : 1;

  const indexFromPointer = (event: PointerEvent<SVGSVGElement> | MouseEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const fraction = profilePointerFraction(event.clientX, {
      boundsLeft: bounds.left,
      boundsWidth: bounds.width,
      viewBoxWidth: WIDTH,
      plotLeft: LEFT,
      plotRight: RIGHT,
    });
    return nearestRouteSampleForFraction(route.samples, route.totalDistanceM, fraction);
  };

  const preview = (index: number | null) => {
    (onPreviewChange ?? onFocusChange)(index);
  };

  return (
    <div className={`route-profile${pinnedIndex !== null ? " route-profile-pinned" : ""}`}>
      <div className="route-profile-heading">
        <span>{pinnedIndex === null ? "Hover to preview · click to pin" : "Pinned journey point"}</span>
        {focusSample && <strong>{(focusSample.cumulativeDistanceM / 1000).toFixed(1)} km · {Math.round(focusSample.smoothedElevationM ?? 0)} m{focusSchedule ? ` · ${minutesLabel(focusSchedule.elapsedMinutes)}` : ""}</strong>}
        {pinnedIndex !== null && onPinnedChange && <button type="button" className="route-profile-pin-button" onClick={() => { onPinnedChange(null); preview(null); }}>Unpin</button>}
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        role="slider"
        aria-label="Route elevation and expected journey profile"
        aria-description={pinnedIndex === null ? "Move to preview a point and click to pin it." : "The selected journey point is pinned."}
        aria-valuemin={0}
        aria-valuemax={Math.round(route.totalDistanceM)}
        aria-valuenow={Math.round(focusSample?.cumulativeDistanceM ?? 0)}
        tabIndex={0}
        onPointerMove={(event) => {
          if (pinnedIndex === null) preview(indexFromPointer(event));
        }}
        onPointerLeave={() => {
          if (pinnedIndex === null) preview(null);
        }}
        onClick={(event) => {
          const index = indexFromPointer(event);
          if (onPinnedChange) {
            const next = nextPinnedRouteSample(pinnedIndex, index);
            onPinnedChange(next);
            if (next === null) preview(index);
          } else {
            onFocusChange(index);
          }
        }}
        onKeyDown={(event) => {
          if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
          event.preventDefault();
          const direction = event.key === "ArrowRight" ? 1 : -1;
          const next = Math.max(0, Math.min(route.samples.length - 1, (focusedIndex ?? 0) + direction));
          if (onPinnedChange) onPinnedChange(next);
          else onFocusChange(next);
        }}
      >
        <line x1={LEFT} y1={TOP + innerHeight} x2={WIDTH - RIGHT} y2={TOP + innerHeight} className="route-profile-axis" />
        <path d={path.trim()} className="route-profile-line" />
        <defs><clipPath id={clipId}><rect x={LEFT} y={TOP} width={innerWidth} height={innerHeight} /></clipPath></defs>
        <path d={atmosphere.path.trim()} className="route-profile-freezing-line" clipPath={`url(#${clipId})`} />
        {conditionStrip && Array.from({ length: Math.ceil((conditionStrip.length - 1) / stripStep) }, (_, segmentIndex) => {
          const startIndex = segmentIndex * stripStep;
          const endIndex = Math.min(conditionStrip.length - 1, startIndex + stripStep);
          return <line key={startIndex} x1={xFor(conditionStrip[startIndex].cumulativeDistanceM)} x2={xFor(conditionStrip[endIndex].cumulativeDistanceM)} y1={TOP + innerHeight + 4} y2={TOP + innerHeight + 4} stroke={routeConditionColour(conditionStrip[startIndex], conditionMode)} className="route-profile-condition-segment" />;
        })}
        {focusSample && focusSample.smoothedElevationM !== null && <>
          <line x1={xFor(focusSample.cumulativeDistanceM)} y1={TOP} x2={xFor(focusSample.cumulativeDistanceM)} y2={TOP + innerHeight} className="route-profile-focus-line" />
          <circle cx={xFor(focusSample.cumulativeDistanceM)} cy={yFor(focusSample.smoothedElevationM)} r="3.5" className="route-profile-focus-point" />
        </>}
        <text x={LEFT} y={HEIGHT - 4}>0</text>
        <text x={WIDTH / 2} y={HEIGHT - 4} textAnchor="middle">{(route.totalDistanceM / 2000).toFixed(1)} km</text>
        <text x={WIDTH - RIGHT} y={HEIGHT - 4} textAnchor="end">{(route.totalDistanceM / 1000).toFixed(1)} km</text>
        <text x={LEFT + 2} y={TOP + 8}>{maximum} m</text>
      </svg>
      {Number.isFinite(atmosphere.low) && <p className="route-profile-freezing-key">Dashed: GFS 0.25° forecast 0°C level {atmosphericHeightLabel(atmosphere.low)}–{atmosphericHeightLabel(atmosphere.high)}{!atmosphere.visible ? " (outside elevation scale)" : ""}. Gaps mean unavailable.</p>}
    </div>
  );
}
