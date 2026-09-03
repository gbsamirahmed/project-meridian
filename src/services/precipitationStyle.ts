import { PRECIPITATION_INTENSITY_LEVELS } from "../config/layerVisuals";

export interface RgbaColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

export function precipitationAmountLabel(value: number): string {
  if (value === 0) return "Dry";
  return `${value < 0.01 ? "<0.01" : value.toFixed(2)} mm / 1 h`;
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
  if (!Number.isFinite(value) || value <= 0) return { r: 0, g: 0, b: 0, a: 0 };

  const stops = PRECIPITATION_INTENSITY_LEVELS;
  // Trace precipitation is valid data, not dry/no-data. Join continuously to
  // the existing light-rain stop instead of jumping from transparent at 0.1 mm.
  if (value < stops[0].value) {
    return {
      ...parseHexColor(stops[0].color),
      a: Math.round(255 * stops[0].opacity * value / stops[0].value),
    };
  }
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
