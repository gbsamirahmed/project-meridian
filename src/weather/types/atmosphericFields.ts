/** Physical contracts only; these fields deliberately have no map-layer controls. */
export const ATMOSPHERIC_FIELDS = {
  gust_surface: { sourceParameter: "GUST", sourceLevel: "surface", units: "m/s", verticalReference: "surface" },
  visibility_surface: { sourceParameter: "VIS", sourceLevel: "surface", units: "m", verticalReference: "surface" },
  freezing_level: { sourceParameter: "HGT", sourceLevel: "0C isotherm", units: "gpm", verticalReference: "mean-sea-level" },
  highest_freezing_level: { sourceParameter: "HGT", sourceLevel: "highest tropospheric freezing level", units: "gpm", verticalReference: "mean-sea-level" },
  cloud_ceiling: { sourceParameter: "HGT", sourceLevel: "cloud ceiling", units: "gpm", verticalReference: "model-surface" },
} as const;

export type AtmosphericFieldId = keyof typeof ATMOSPHERIC_FIELDS;
