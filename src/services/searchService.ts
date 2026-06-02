import type { SelectedLocation } from "../types/location";

export async function searchLocation(
  query: string
): Promise<SelectedLocation | null> {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
      query
    )}&format=jsonv2&limit=1`
  );

  const results = await response.json();

  if (!results.length) {
    return null;
  }

  return {
    latitude: Number(results[0].lat),
    longitude: Number(results[0].lon),
  };
}