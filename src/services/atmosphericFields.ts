import type { ScalarFieldManifest } from "../types/globalWeather";

/** Physical contracts only; these fields deliberately have no map-layer controls. */
export const ATMOSPHERIC_FIELDS = {
  gust_surface: { sourceParameter: "GUST", sourceLevel: "surface", units: "m/s", verticalReference: "surface" },
  visibility_surface: { sourceParameter: "VIS", sourceLevel: "surface", units: "m", verticalReference: "surface" },
  freezing_level: { sourceParameter: "HGT", sourceLevel: "0C isotherm", units: "gpm", verticalReference: "mean-sea-level" },
  highest_freezing_level: { sourceParameter: "HGT", sourceLevel: "highest tropospheric freezing level", units: "gpm", verticalReference: "mean-sea-level" },
  cloud_ceiling: { sourceParameter: "HGT", sourceLevel: "cloud ceiling", units: "gpm", verticalReference: "model-surface" },
} as const;

export type AtmosphericFieldId = keyof typeof ATMOSPHERIC_FIELDS;

export function validateAtmosphericManifest(manifest: ScalarFieldManifest): void {
  if (!(manifest.field.id in ATMOSPHERIC_FIELDS)) return;
  const contract = ATMOSPHERIC_FIELDS[manifest.field.id as AtmosphericFieldId];
  if (
    Object.entries(contract).some(([key, value]) => manifest.field[key as keyof typeof contract] !== value) ||
    manifest.field.timeSemantics !== "instantaneous" ||
    manifest.tiles.encoding !== "uint16-rg" ||
    !Number.isFinite(manifest.tiles.scale) || manifest.tiles.scale <= 0 ||
    !Number.isFinite(manifest.tiles.offset) || manifest.tiles.noData !== 65535 ||
    !Array.isArray(manifest.field.validRange) || manifest.field.validRange.length !== 2 ||
    !manifest.field.validRange.every(Number.isFinite) ||
    manifest.field.validRange[0] > manifest.field.validRange[1] ||
    (manifest.field.validRange[0] - manifest.tiles.offset) / manifest.tiles.scale < 0 ||
    (manifest.field.validRange[1] - manifest.tiles.offset) / manifest.tiles.scale >= 65535 ||
    manifest.field.nativeResolution?.longitudeDegrees !== 0.25 ||
    manifest.field.nativeResolution?.latitudeDegrees !== 0.25 ||
    (manifest.field.id === "cloud_ceiling" && manifest.field.noDataMeaning !== "missing-or-no-diagnosed-ceiling")
  ) throw new Error(`Invalid ${manifest.field.id} physical/encoding contract`);
  const run = Date.parse(manifest.runTime);
  let previousHour = 0;
  for (const step of manifest.timesteps) {
    if (!Number.isFinite(run) || !Number.isInteger(step.forecastHour) ||
      step.forecastHour <= previousHour || step.forecastHour > 24 ||
      Date.parse(step.validTime) !== run + step.forecastHour * 3600000 ||
      !Number.isFinite(step.minimum) || !Number.isFinite(step.maximum) ||
      step.minimum > step.maximum || step.minimum < manifest.field.validRange[0] ||
      step.maximum > manifest.field.validRange[1]) {
      throw new Error(`Invalid ${manifest.field.id} forecast time/range`);
    }
    previousHour = step.forecastHour;
  }
}
