import type { SelectedLocation } from "../types/location";
import type { WeatherGridRequest } from "../types/weatherGrid";

export function generateGrid(
  request: WeatherGridRequest
): SelectedLocation[] {
  const points: SelectedLocation[] = [];
  const { bounds, rows, columns } = request;

  const latitudeStep =
    rows > 1 ? (bounds.north - bounds.south) / (rows - 1) : 0;
  const longitudeStep =
    columns > 1 ? (bounds.east - bounds.west) / (columns - 1) : 0;

  // Canvas and matrix rows run from north to south, so the API coordinate
  // order deliberately follows that same convention.
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      points.push({
        latitude: bounds.north - row * latitudeStep,
        longitude: bounds.west + column * longitudeStep,
      });
    }
  }

  return points;
}
