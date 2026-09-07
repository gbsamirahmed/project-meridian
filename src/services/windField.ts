import type { MutableWindVector } from "./windVector";
import type { GeographicBounds } from "../types/globalWeather";
import type maplibregl from "maplibre-gl";

export interface WindVectorField {
  bounds: GeographicBounds;
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
