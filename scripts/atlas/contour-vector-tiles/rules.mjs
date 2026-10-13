/* Provisional MapLibre zoom rules, not source accuracy or worldwide coverage policy. */
export const policy = { first: 11, fifty: 12, twenty: 13.5, ten: 15.5,
  strictStart: 14.75, strictEnd: 15.25, nativeStart: 17.25, nativeEnd: 17.75, fade: 0.25 };
// Automatic index prominence only; manual comparisons retain their original opacity.
export const indexStops = [[11, 0], [11.5, 0.08], [12, 0.22], [13, 0.6],
  [14, 1], [16, 0.6], [18, 0.4], [21, 0.3]];
export function indexOpacity(z) {
  if (z <= indexStops[0][0]) return 0;
  for (let i = 1; i < indexStops.length; i++) {
    const [end, value] = indexStops[i], [start, previous] = indexStops[i - 1];
    if (z <= end) return previous + (value - previous) * (z - start) / (end - start);
  }
  return indexStops.at(-1)[1];
}
const ramp = (z, from, to) => Math.max(0, Math.min(1, (z - from) / (to - from)));
export function sourceWeight(product, z) {
  const strict = ramp(z, policy.strictStart, policy.strictEnd), native = ramp(z, policy.nativeStart, policy.nativeEnd);
  return product === 'swiss-smoothed' ? 1 - strict : product === 'swiss-2m' ? strict * (1 - native) : native;
}
export function intervalWeight(level, z) {
  if (level % 100 === 0) return indexOpacity(z);
  if (level % 50 === 0) return Math.max(ramp(z, policy.fifty, policy.fifty + policy.fade)
    * (1 - ramp(z, policy.twenty, policy.twenty + policy.fade)), ramp(z, policy.ten, policy.ten + policy.fade));
  return level % 20 === 0 ? ramp(z, policy.twenty, policy.twenty + policy.fade) : ramp(z, policy.ten, policy.ten + policy.fade);
}
export function opacity(product, mode = 'auto', interval = 20) {
  if (mode !== 'auto') return mode === product ? ['case', ['==', ['%', ['get', 'elevation_m'], interval], 0], 1, 0] : 0;
  const stops = [...new Set([0, ...indexStops.map(([z]) => z), policy.first, policy.first + policy.fade, policy.fifty, policy.fifty + policy.fade,
    policy.twenty, policy.twenty + policy.fade, policy.ten, policy.ten + policy.fade,
    policy.strictStart, policy.strictEnd, policy.nativeStart, policy.nativeEnd, 22])].sort((a, b) => a - b);
  const expression = ['interpolate', ['linear'], ['zoom']];
  for (const z of stops) {
    const value = level => intervalWeight(level, z) * sourceWeight(product, z);
    expression.push(z, ['case', ['==', ['%', ['get', 'elevation_m'], 100], 0], value(2500),
      ['==', ['%', ['get', 'elevation_m'], 50], 0], value(2550),
      ['==', ['%', ['get', 'elevation_m'], 20], 0], value(2520), value(2510)]);
  }
  return expression;
}
