export interface ScalarWeatherTimestep {
  id: string;
  forecastHour: number;
  validTime: string;
  accumulationStart: string;
  accumulationEnd: string;
  accumulationHours: number;
  minimum: number;
  maximum: number;
  tileTemplate: string;
}

export interface WeatherRunManifest {
  schemaVersion: 1;
  id: string;
  model: string;
  product: string;
  runTime: string;
  variable: {
    id: "precipitation";
    sourceParameter: string;
    displayName: string;
    units: "mm";
    nativeResolutionDegrees: number;
    accumulationSemantics: "interval-total";
  };
  coverage: {
    bounds: [number, number, number, number];
    worldWrap: boolean;
    polarLimit: string;
  };
  tiles: {
    format: "png";
    encoding: "uint16-rg";
    tileSize: number;
    minZoom: number;
    maxZoom: number;
    scale: number;
    offset: number;
    noData: number;
    resampling: string;
    overzoom: boolean;
  };
  timesteps: ScalarWeatherTimestep[];
  attribution: {
    label: string;
    url: string;
    source: string;
  };
  generatedAt: string;
}

export interface WeatherLatestPointer {
  schemaVersion: 1;
  model: string;
  product: string;
  variable: "precipitation";
  runTime: string;
  generatedAt: string;
  firstValidTime: string;
  lastValidTime: string;
  timestepCount: number;
  manifest: string;
}

export interface ScalarWeatherFieldSource {
  manifest: WeatherRunManifest;
  manifestUrl: string;
  baseUrl: string;
}

export type GlobalPrecipitationStatus =
  | "loading"
  | "ready"
  | "unavailable"
  | "error";
