import type { MutableWindVector } from "./weatherInterpolation";
import type { WeatherGridBounds } from "../types/weatherGrid";
import type maplibregl from "maplibre-gl";

export interface WindVectorField {
  bounds: WeatherGridBounds;
  signature: string;
  isGlobal?: boolean;
  sample(
    latitude: number,
    longitude: number,
    target: MutableWindVector
  ): boolean;
  prepareCoverage?(map: maplibregl.Map): Promise<boolean>;
  scheduleCoverage?(map: maplibregl.Map): void;
  dispose?(): void;
}
