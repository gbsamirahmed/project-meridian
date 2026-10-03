/**
 * Atlas/MapLibre's visual DEM policy. This does not configure route elevation.
 * The AWS URL is intentionally independent of analyticalElevationConfig.ts,
 * even while both policies select the same dataset.
 */
export const VISUAL_TERRAIN_DEM = {
  tileTemplate:
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
  encoding: "terrarium",
  tileSize: 256,
  // Preserve the current OpenFreeMap/terrain delivery compatibility ceiling.
  geometryMaxZoom: 14,
  // Separate visual hillshade/color-relief source; not native survey resolution.
  reliefMaxZoom: 15,
  attribution:
    '<a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">Terrain data credits</a>',
} as const;
