import {
  PRECIPITATION_DRY_THRESHOLD_MM,
  PRECIPITATION_INTENSITY_LEVELS,
} from "../config/layerVisuals";

export interface RgbaColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

function parseHexColor(color: string) {
  const value = color.replace("#", "");
  return {
    r: Number.parseInt(value.slice(0, 2), 16),
    g: Number.parseInt(value.slice(2, 4), 16),
    b: Number.parseInt(value.slice(4, 6), 16),
  };
}

export function precipitationColor(value: number): RgbaColor {
  if (value < PRECIPITATION_DRY_THRESHOLD_MM) return { r: 0, g: 0, b: 0, a: 0 };

  const stops = PRECIPITATION_INTENSITY_LEVELS;
  let start = stops[0];
  let end = stops[stops.length - 1];
  for (let index = 0; index < stops.length - 1; index++) {
    if (value >= stops[index].value && value <= stops[index + 1].value) {
      start = stops[index];
      end = stops[index + 1];
      break;
    }
    if (value > stops[index + 1].value) start = end = stops[index + 1];
  }

  const ratio = start === end ? 0 : (value - start.value) / (end.value - start.value);
  const startColor = parseHexColor(start.color);
  const endColor = parseHexColor(end.color);
  const opacity = start.opacity + (end.opacity - start.opacity) * ratio;
  return {
    r: Math.round(startColor.r + (endColor.r - startColor.r) * ratio),
    g: Math.round(startColor.g + (endColor.g - startColor.g) * ratio),
    b: Math.round(startColor.b + (endColor.b - startColor.b) * ratio),
    a: Math.round(255 * opacity),
  };
}
