import * as maplibregl from "maplibre-gl";
import { getFirstSymbolLayerId } from "../../atlas/map/mapLayerAnchors";
import { getRouteBounds } from "../model/routeGeometry";
import {
  ROUTE_CASING_LAYER_ID,
  ROUTE_CONDITION_LAYER_ID,
  ROUTE_LINE_LAYER_ID,
  removeRouteLayer,
  updateRouteLayer,
} from "./routeLayer";
import type { RouteCoordinate } from "../types/route";
import type { RouteConditionMode, RouteConditions } from "../types/routeConditions";

const ROUTE_LAYER_ORDER = [
  "planned-route-casing",
  "planned-route-line",
  "planned-route-conditions",
  "planned-route-endpoints",
  "planned-route-focus",
] as const;

export interface TraverseMapState {
  coordinates: RouteCoordinate[];
  focusedSampleIndex: number | null;
  conditions: RouteConditions | null;
  conditionMode: RouteConditionMode;
}

export class TraverseMapController {
  private readonly map: maplibregl.Map;
  private state: TraverseMapState = {
    coordinates: [],
    focusedSampleIndex: null,
    conditions: null,
    conditionMode: "none",
  };

  constructor(map: maplibregl.Map) {
    this.map = map;
  }

  update(state: TraverseMapState): void {
    this.state = state;
    if (!this.map.isStyleLoaded()) return;
    updateRouteLayer(
      this.map,
      state.coordinates,
      state.focusedSampleIndex,
      state.conditions,
      state.conditionMode
    );
    this.placeAboveWeather();
  }

  styleChanged(): void {
    this.update(this.state);
  }

  placeAboveWeather(): void {
    const beforeId = getFirstSymbolLayerId(this.map);
    for (const layerId of ROUTE_LAYER_ORDER) {
      if (this.map.getLayer(layerId)) this.map.moveLayer(layerId, beforeId);
    }
  }

  nearestSample(point: maplibregl.PointLike, maximumPixels = 14): number | null {
    const target = maplibregl.Point.convert(point);
    let nearest: number | null = null;
    let bestDistance = maximumPixels;
    this.state.coordinates.forEach((coordinate, index) => {
      const projected = this.map.project([coordinate.longitude, coordinate.latitude]);
      const distance = Math.hypot(projected.x - target.x, projected.y - target.y);
      if (distance <= bestDistance) {
        bestDistance = distance;
        nearest = index;
      }
    });
    return nearest;
  }

  isRouteHit(point: maplibregl.PointLike): boolean {
    const layers = [ROUTE_CASING_LAYER_ID, ROUTE_LINE_LAYER_ID, ROUTE_CONDITION_LAYER_ID]
      .filter((layerId) => this.map.getLayer(layerId));
    return layers.length > 0 &&
      this.map.queryRenderedFeatures(point, { layers }).length > 0;
  }

  fitRoute(
    coordinates: RouteCoordinate[],
    padding: maplibregl.PaddingOptions
  ): void {
    const bounds = getRouteBounds(coordinates);
    const center = this.map.getCenter();
    const routeCenter = (bounds.west + bounds.east) / 2;
    const longitudeDelta = Math.abs(
      ((routeCenter - center.lng + 540) % 360) - 180
    );
    this.map.fitBounds(
      [[bounds.west, bounds.south], [bounds.east, bounds.north]],
      {
        padding,
        maxZoom: 14,
        bearing: this.map.getBearing(),
        pitch: this.map.getPitch(),
        duration: longitudeDelta > 70 ? 0 : 750,
        essential: true,
      }
    );
  }

  destroy(): void {
    removeRouteLayer(this.map);
  }
}
