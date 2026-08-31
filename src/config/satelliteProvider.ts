export interface SatelliteProviderConfig {
  id: string;
  name: string;
  tileJsonUrl: string | null;
  tileSize: number;
  logoUrl: string;
  providerUrl: string;
}

const mapTilerKey = import.meta.env.VITE_MAPTILER_KEY?.trim() ?? "";

// Keep provider-specific details at this boundary so a later imagery source can
// replace MapTiler without changing Meridian's primary-view or map lifecycle.
export const SATELLITE_PROVIDER: SatelliteProviderConfig = {
  id: "maptiler-satellite-v2",
  name: "MapTiler Satellite",
  tileJsonUrl: mapTilerKey
    ? `https://api.maptiler.com/tiles/satellite-v2/tiles.json?key=${encodeURIComponent(mapTilerKey)}`
    : null,
  tileSize: 512,
  logoUrl: "https://api.maptiler.com/resources/logo.svg",
  providerUrl: "https://www.maptiler.com/",
};

export const IS_SATELLITE_CONFIGURED =
  SATELLITE_PROVIDER.tileJsonUrl !== null;
