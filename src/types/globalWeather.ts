import type { AtmosphericFieldId } from "../services/atmosphericFields";

export type GlobalWeatherFieldId =
  | AtmosphericFieldId
  | "precipitation"
  | "cloud_cover"
  | "wind_10m"
  | "temperature_2m";
export type GlobalWeatherFieldStatus =
  | "loading"
  | "ready"
  | "unavailable"
  | "error";

export interface ScalarFieldTimestep {
  id: string;
  forecastHour: number;
  validTime: string;
  minimum: number;
  maximum: number;
  tileTemplate: string;
  accumulationStart?: string;
  accumulationEnd?: string;
  accumulationHours?: number;
}

export interface VectorFieldTimestep {
  id: string;
  forecastHour: number;
  validTime: string;
  minimumU: number;
  maximumU: number;
  minimumV: number;
  maximumV: number;
  minimumSpeed: number;
  maximumSpeed: number;
  tileTemplate: string;
}

export interface WeatherFieldManifestBase {
  schemaVersion: 2;
  id: string;
  model: string;
  product: string;
  runTime: string;
  coverage: {
    bounds: [number, number, number, number];
    worldWrap: boolean;
    polarLimit: string;
  };
  attribution: {
    label: string;
    url: string;
    source: string;
  };
  generatedAt: string;
}

export interface ScalarFieldManifest extends WeatherFieldManifestBase {
  field: {
    id: Exclude<GlobalWeatherFieldId, "wind_10m">;
    kind: "scalar";
    sourceParameter: string;
    sourceLevel: string;
    displayName: string;
    units: "mm" | "percent" | "celsius" | "m/s" | "m" | "gpm";
    verticalReference?: "surface" | "mean-sea-level" | "model-surface";
    noDataMeaning?: string;
    interpretation?: string;
    validRange: [number, number];
    timeSemantics: "instantaneous" | "interval-total";
    nativeResolution: {
      longitudeDegrees: number;
      latitudeDegrees: number;
    };
  };
  tiles: {
    format: "png";
    encoding: "uint16-rg" | "uint8-r";
    tileSize: number;
    minZoom: number;
    maxZoom: number;
    scale: number;
    offset: number;
    noData: number;
    resampling: string;
    overzoom: boolean;
  };
  timesteps: ScalarFieldTimestep[];
}

export interface VectorFieldManifest extends WeatherFieldManifestBase {
  field: {
    id: "wind_10m";
    kind: "vector";
    sourceLevel: string;
    displayName: string;
    units: "m/s";
    timeSemantics: "instantaneous";
    vectorConvention: "earth-relative-eastward-northward";
    nativeResolution: {
      longitudeDegrees: number;
      latitudeDegrees: number;
    };
    components: [
      {
        id: "u";
        sourceParameter: "UGRD";
        role: "eastward";
      },
      {
        id: "v";
        sourceParameter: "VGRD";
        role: "northward";
      },
    ];
  };
  tiles: {
    format: "png";
    encoding: "packed-uv10-rgb";
    tileSize: number;
    minZoom: number;
    maxZoom: number;
    componentScale: number;
    componentBias: number;
    componentBits: 10;
    noDataCode: 0;
    noDataRgb: [0, 0, 0];
    resampling: string;
    overzoom: boolean;
  };
  timesteps: VectorFieldTimestep[];
}

export interface GlobalWeatherCatalogEntry {
  runTime: string;
  firstValidTime: string;
  lastValidTime: string;
  timestepCount: number;
  manifest: string;
}

export interface GlobalWeatherCatalog {
  schemaVersion: 2;
  model: string;
  product: string;
  generatedAt: string;
  fields: Partial<Record<GlobalWeatherFieldId, GlobalWeatherCatalogEntry>>;
}

export interface ScalarWeatherFieldSource {
  manifest: ScalarFieldManifest;
  manifestUrl: string;
  baseUrl: string;
}

export interface VectorWeatherFieldSource {
  manifest: VectorFieldManifest;
  manifestUrl: string;
  baseUrl: string;
}

export type GlobalWeatherFieldSource =
  | ScalarWeatherFieldSource
  | VectorWeatherFieldSource;

export interface GlobalWeatherSourceRegistry extends Partial<Record<AtmosphericFieldId, ScalarWeatherFieldSource>> {
  precipitation?: ScalarWeatherFieldSource;
  cloud_cover?: ScalarWeatherFieldSource;
  wind_10m?: VectorWeatherFieldSource;
  temperature_2m?: ScalarWeatherFieldSource;
}

export type GlobalWeatherStatusRegistry = Record<
  GlobalWeatherFieldId,
  GlobalWeatherFieldStatus
>;

export type ScalarWeatherTimestep = ScalarFieldTimestep;
export type VectorWeatherTimestep = VectorFieldTimestep;
export type WeatherRunManifest = ScalarFieldManifest;
