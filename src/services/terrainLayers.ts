import maplibregl from "maplibre-gl";

import {
  ELEVATION_COLOR_STOPS,
  HILLSHADE_ZOOM_STOPS,
  LAYER_VISUAL_STRENGTHS,
} from "../config/layerVisuals";
import { TERRAIN_ATTRIBUTION } from "../config/dataAttribution";
import {
  placeGeographicContextAboveOverlays,
} from "./mapLayerOrder";

import type { Basemap } from "../types/layer";

export const TERRAIN_SOURCE_ID = "terrain-dem";
export const TERRAIN_ANALYSIS_SOURCE_ID = "terrain-analysis-dem";
export const ELEVATION_RELIEF_LAYER_ID = "terrain-elevation-relief";
export const HILLSHADE_LAYER_ID = "terrain-hillshade";
const TERRAIN_STACK_BOUNDARY_SOURCE_ID = "terrain-stack-boundary-source";
const TERRAIN_STACK_BOUNDARY_LAYER_ID = "terrain-stack-boundary-layer";
const terrainModeByMap = new WeakMap<maplibregl.Map, "globe" | "terrain">();

const TERRARIUM_TILES =
  "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png";
export const TERRAIN_DEM_NATIVE_MAX_ZOOM = 15;
// OpenFreeMap's vector tiles top out at z14. Keeping the terrain mesh at the
// same canonical ceiling avoids a MapLibre terrain fallback warning while the
// separate analysis source can still use Terrarium's final native z15 tiles
// for hillshade and color relief.
const TERRAIN_GEOMETRY_MAX_ZOOM = 14;
// MapLibre's detailed terrain renderer does not yet support every globe/fog
// calculation. At this zoom the globe and Mercator projections are visually
// close, so switch to Mercator before enabling terrain to avoid that unsupported
// overlap while keeping the planetary view genuinely spherical at world scale.
export const TERRAIN_MIN_ZOOM = 5.5;
export const TERRAIN_EXAGGERATION = 1.45;

function buildElevationExpression(): maplibregl.ExpressionSpecification {
  return [
    "interpolate",
    ["linear"],
    ["elevation"],
    ...ELEVATION_COLOR_STOPS.flatMap((stop) => [
      stop.value,
      stop.color,
    ]),
  ];
}

function buildHillshadeExpression(
  strengthScale = 1
): maplibregl.ExpressionSpecification {
  return [
    "interpolate",
    ["linear"],
    ["zoom"],
    ...HILLSHADE_ZOOM_STOPS.flatMap((stop) => [
      stop.zoom,
      stop.strength * strengthScale,
    ]),
  ];
}

export function configurePlanetAndTerrain(
  map: maplibregl.Map
): void {
  // A style reload invalidates MapLibre's terrain/projection resources, so the
  // transition guard must allow one fresh activation for the rebuilt style.
  terrainModeByMap.delete(map);
  map.getContainer().style.backgroundColor = "#03070d";

  map.setSky({
    "sky-color": "#07111e",
    "horizon-color": "#9eb4ba",
    "fog-color": "#bdc9c6",
    "fog-ground-blend": 0.42,
    "horizon-fog-blend": 0.72,
    "sky-horizon-blend": 0.82,
    "atmosphere-blend": [
      "interpolate",
      ["linear"],
      ["zoom"],
      0,
      1,
      4,
      0.9,
      7,
      0.25,
      9,
      0,
    ],
  });

  if (!map.getSource(TERRAIN_SOURCE_ID)) {
    map.addSource(TERRAIN_SOURCE_ID, {
      type: "raster-dem",
      tiles: [TERRARIUM_TILES],
      tileSize: 256,
      encoding: "terrarium",
      maxzoom: TERRAIN_GEOMETRY_MAX_ZOOM,
      attribution: TERRAIN_ATTRIBUTION,
    });
  }

  // MapLibre recommends separate internal sources when one DEM is used both
  // for 3D terrain and for analysis layers. Both sources reference the same
  // Terrarium tiles, so this does not add another dataset or provider.
  if (!map.getSource(TERRAIN_ANALYSIS_SOURCE_ID)) {
    map.addSource(TERRAIN_ANALYSIS_SOURCE_ID, {
      type: "raster-dem",
      tiles: [TERRARIUM_TILES],
      tileSize: 256,
      encoding: "terrarium",
      maxzoom: TERRAIN_DEM_NATIVE_MAX_ZOOM,
    });
  }

  if (!map.getLayer(ELEVATION_RELIEF_LAYER_ID)) {
    map.addLayer({
      id: ELEVATION_RELIEF_LAYER_ID,
      type: "color-relief",
      source: TERRAIN_ANALYSIS_SOURCE_ID,
      paint: {
        "color-relief-color": buildElevationExpression(),
        "color-relief-opacity": 0,
        resampling: "linear",
      },
    });
  }

  if (!map.getLayer(HILLSHADE_LAYER_ID)) {
    map.addLayer({
      id: HILLSHADE_LAYER_ID,
      type: "hillshade",
      source: TERRAIN_ANALYSIS_SOURCE_ID,
      paint: {
        "hillshade-method": "igor",
        "hillshade-exaggeration": buildHillshadeExpression(),
        "hillshade-shadow-color": "#17211f",
        "hillshade-highlight-color": "#f4efe0",
        "hillshade-accent-color": "#586b66",
        "hillshade-illumination-anchor": "map",
        "hillshade-illumination-direction": 315,
        "hillshade-illumination-altitude": 42,
        resampling: "linear",
      },
    });
  }

  // MapLibre 5.24 needs color-relief to finish a terrain render-to-texture
  // stack before later draped basemap layers. This empty symbol layer is an
  // intentional stack boundary, allowing water and linework to render above
  // relief without suppressing the relief itself.
  if (!map.getSource(TERRAIN_STACK_BOUNDARY_SOURCE_ID)) {
    map.addSource(TERRAIN_STACK_BOUNDARY_SOURCE_ID, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }

  if (!map.getLayer(TERRAIN_STACK_BOUNDARY_LAYER_ID)) {
    map.addLayer({
      id: TERRAIN_STACK_BOUNDARY_LAYER_ID,
      type: "symbol",
      source: TERRAIN_STACK_BOUNDARY_SOURCE_ID,
    });
  }

  // Terrain analysis sits above land styling but below water, roads,
  // boundaries and labels. This keeps below-sea-level land coloured while
  // allowing intentional basemap water polygons to cover DEM bathymetry.
  map.moveLayer(ELEVATION_RELIEF_LAYER_ID);
  map.moveLayer(HILLSHADE_LAYER_ID);
  map.moveLayer(TERRAIN_STACK_BOUNDARY_LAYER_ID);
  placeGeographicContextAboveOverlays(
    map,
    TERRAIN_STACK_BOUNDARY_LAYER_ID
  );
  updateTerrainActivation(map);
}

export function applyTerrainLayerState(
  map: maplibregl.Map,
  basemap: Basemap,
  elevationEnabled: boolean
): void {
  if (map.getLayer(ELEVATION_RELIEF_LAYER_ID)) {
    map.setPaintProperty(
      ELEVATION_RELIEF_LAYER_ID,
      "color-relief-opacity",
      elevationEnabled
        ? LAYER_VISUAL_STRENGTHS.elevation
        : 0
    );
  }

  if (map.getLayer(HILLSHADE_LAYER_ID)) {
    map.setPaintProperty(
      HILLSHADE_LAYER_ID,
      "hillshade-exaggeration",
      buildHillshadeExpression(basemap === "satellite" ? 0 : 1)
    );
  }
}

export function updateTerrainActivation(map: maplibregl.Map): void {
  const shouldUseTerrain = map.getZoom() >= TERRAIN_MIN_ZOOM;
  const desiredMode = shouldUseTerrain ? "terrain" : "globe";

  // Zoom emits many frames around the threshold. Repeating setProjection or
  // setTerrain while MapLibre is still applying the same transition can race
  // its tile requests, so apply each requested mode only once.
  if (terrainModeByMap.get(map) === desiredMode) return;
  terrainModeByMap.set(map, desiredMode);

  const hasTerrain = map.getTerrain() !== null;
  // Styles without an explicit projection report `undefined`, which is
  // MapLibre's default Mercator projection.
  const projectionType = map.getProjection()?.type ?? "mercator";

  if (!shouldUseTerrain) {
    // Remove terrain before entering globe projection. Reversing this order can
    // make MapLibre render one frame with an unsupported globe/terrain pairing.
    if (hasTerrain) map.setTerrain(null);
    if (projectionType !== "globe") map.setProjection({ type: "globe" });
    return;
  }

  if (projectionType !== "mercator") {
    if (hasTerrain) map.setTerrain(null);
    map.setProjection({ type: "mercator" });
  }

  if (map.getTerrain() === null) {
    map.setTerrain({
      source: TERRAIN_SOURCE_ID,
      exaggeration: TERRAIN_EXAGGERATION,
    });
  }
}
