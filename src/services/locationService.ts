export async function getLocationName(
  latitude: number,
  longitude: number
): Promise<string> {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=jsonv2`
  );

  const data = await response.json();

  return data.display_name ?? "Unknown location";
}