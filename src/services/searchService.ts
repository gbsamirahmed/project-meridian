import type { SelectedLocation } from "../types/location";
import { requestNominatimJson } from "./nominatimClient";

interface NominatimSearchResult {
  lat: string;
  lon: string;
}

export async function searchLocation(
  query: string,
  signal?: AbortSignal
): Promise<SelectedLocation | null> {
  const normalisedQuery = query.trim().toLocaleLowerCase();
  const results = await requestNominatimJson<NominatimSearchResult[]>(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=jsonv2&limit=1`,
    `search:${normalisedQuery}`,
    signal
  );

  if (!results.length) {
    return null;
  }

  return {
    latitude: Number(results[0].lat),
    longitude: Number(results[0].lon),
  };
}
