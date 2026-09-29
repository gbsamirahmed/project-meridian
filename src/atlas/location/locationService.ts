import { requestNominatimJson } from "./nominatimClient";

interface NominatimReverseResult {
  display_name?: string;
}

export async function getLocationName(
  latitude: number,
  longitude: number,
  signal?: AbortSignal
): Promise<string> {
  const roundedLatitude = latitude.toFixed(5);
  const roundedLongitude = longitude.toFixed(5);
  const data = await requestNominatimJson<NominatimReverseResult>(
    `https://nominatim.openstreetmap.org/reverse?lat=${roundedLatitude}&lon=${roundedLongitude}&format=jsonv2`,
    `reverse:${roundedLatitude}:${roundedLongitude}`,
    signal
  );

  return data.display_name ?? "Unknown location";
}
