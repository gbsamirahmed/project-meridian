export interface MutableWindVector {
  eastwardFlow: number;
  northwardFlow: number;
  speed: number;
  flowBearing: number;
  fromDirection: number;
}

export function formatWindDirection(direction: number): string {
  const labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return labels[Math.round(direction / 45) % 8];
}
