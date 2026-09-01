interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const ratio = clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return ratio * ratio * (3 - 2 * ratio);
}

export function cloudCoverColor(value: number): Rgba {
  const cover = clamp(value, 0, 100);
  const darkness = Math.round(231 - cover * 0.42);
  const alpha = Math.round(
    255 * smoothstep(8, 100, cover) * (0.14 + cover / 190)
  );

  return {
    r: darkness - 5,
    g: darkness,
    b: Math.min(255, darkness + 5),
    a: alpha,
  };
}
