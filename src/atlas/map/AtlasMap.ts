import * as maplibregl from "maplibre-gl";
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

// Vite must bundle the v6 worker together with its shared ESM dependencies.
maplibregl.setWorkerUrl(maplibreWorkerUrl);

import {
  applySatelliteLayerState,
  captureSatelliteBasemapLayers,
  ensureSatelliteLayer,

  SATELLITE_SOURCE_ID,
  type SatelliteLayerStatus,
} from "./satelliteLayer";
import { IS_SATELLITE_CONFIGURED } from "./satelliteProvider";
import {
  applyTerrainLayerState,
  configurePlanetAndTerrain,
  updateTerrainActivation,
} from "./terrainLayers";
import type { Basemap } from "./mapTypes";

export interface AtlasMapOptions {
  attributions: string[];
  onStyleReady: (map: maplibregl.Map) => void;
  onRenderable: (map: maplibregl.Map) => void;
  onSatelliteStatus: (status: SatelliteLayerStatus) => void;
}

/** Owns the MapLibre instance and Atlas-specific geographic lifecycle. */
export class AtlasMap {
  readonly map: maplibregl.Map;
  private basemap: Basemap = "terrain";
  private elevationEnabled = false;
  private readonly options: AtlasMapOptions;
  private destroyed = false;

  constructor(container: HTMLElement, options: AtlasMapOptions) {
    this.options = options;
    this.map = new maplibregl.Map({
      container,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [-4.0762, 53.0685],
      zoom: 11.4,
      minZoom: 1.4,
      pitch: 0,
      bearing: 0,
      maxPitch: 72,
      renderWorldCopies: false,
      // Keep v5 vector-tile overscaling and feature-query behaviour.
      zoomLevelsToOverscale: undefined,
      cancelPendingTileRequestsWhileZooming: false,
      attributionControl: { compact: true, customAttribution: options.attributions },
    });
    this.map.addControl(
      new maplibregl.NavigationControl({ visualizePitch: true }),
      "top-right"
    );
    this.map.on("style.load", this.handleStyleReady);
    this.map.on("idle", this.handleRenderable);
    this.map.on("zoomend", this.handleZoomEnd);
    this.map.on("sourcedata", this.handleSourceData);
    this.map.on("error", this.handleError);
  }

  setPresentation(basemap: Basemap, elevationEnabled: boolean): void {
    const basemapChanged = this.basemap !== basemap;
    this.basemap = basemap;
    this.elevationEnabled = elevationEnabled;
    if (!this.map.isStyleLoaded()) return;
    applyTerrainLayerState(this.map, basemap, elevationEnabled);
    if (basemapChanged) {
      this.syncSatellite();
    } else {
      applySatelliteLayerState(this.map, basemap === "satellite");
    }
  }

  resize(): void {
    this.map.resize();
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.map.remove();
  }

  private readonly handleStyleReady = (): void => {
    captureSatelliteBasemapLayers(this.map);
    configurePlanetAndTerrain(this.map);
    this.options.onStyleReady(this.map);
    applyTerrainLayerState(this.map, this.basemap, this.elevationEnabled);
    this.syncSatellite();
  };

  private readonly handleRenderable = (): void => {
    this.options.onRenderable(this.map);
  };

  private readonly handleZoomEnd = (): void => {
    updateTerrainActivation(this.map);
  };

  private readonly handleSourceData = (event: maplibregl.MapSourceDataEvent): void => {
    if (
      event.sourceId === SATELLITE_SOURCE_ID &&
      this.map.getSource(SATELLITE_SOURCE_ID) &&
      this.map.isSourceLoaded(SATELLITE_SOURCE_ID)
    ) {
      this.options.onSatelliteStatus("ready");
    }
  };

  private readonly handleError = (event: maplibregl.ErrorEvent): void => {
    const sourceId = (event as typeof event & { sourceId?: string }).sourceId;
    if (sourceId === SATELLITE_SOURCE_ID) {
      this.options.onSatelliteStatus("degraded");
      return;
    }
    console.error(event.error);
  };

  private syncSatellite(): void {
    const enabled = this.basemap === "satellite";
    applySatelliteLayerState(this.map, enabled);
    if (!enabled) return;
    if (!IS_SATELLITE_CONFIGURED) {
      this.options.onSatelliteStatus("unavailable");
      return;
    }
    this.options.onSatelliteStatus("loading");
    void ensureSatelliteLayer(this.map).then((status) => {
      if (this.destroyed) return;
      applySatelliteLayerState(this.map, this.basemap === "satellite" && status === "ready");
      this.options.onSatelliteStatus(status === "ready" ? "loading" : status);
      if (
        status === "ready" &&
        this.map.getSource(SATELLITE_SOURCE_ID) &&
        this.map.isSourceLoaded(SATELLITE_SOURCE_ID)
      ) {
        this.options.onSatelliteStatus("ready");
      }
      this.options.onRenderable(this.map);
    });
  }
}
