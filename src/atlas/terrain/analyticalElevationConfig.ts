/**
 * Numeric elevation policy for terrainElevationSampler and route analysis.
 * Fixed contract: Terrarium RGB heights in metres, 256-pixel XYZ Web Mercator
 * tiles sampled at z15. The sampler implements that encoding/addressing; this
 * is not a generic provider interface or a claim of native survey resolution.
 *
 * Independent of visualTerrainConfig.ts. A source change must explicitly assess
 * route profiles, gradients, timing and derived route conditions.
 */
export const ANALYTICAL_ELEVATION = {
  tileTemplate:
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
  tileSize: 256,
  samplingZoom: 15,
} as const;
