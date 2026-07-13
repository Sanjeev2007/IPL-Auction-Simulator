/**
 * Precision Terminal — rating heat encoding.
 * Maps a numeric value within a domain to the cool → warm → hot ramp,
 * the core visual language for ratings/odds across every page.
 */

const COOL = [0x5b, 0x8d, 0xef]; // #5B8DEF
const WARM = [0xf5, 0xb8, 0x41]; // #F5B841
const HOT = [0xff, 0x6b, 0x5a]; // #FF6B5A

function lerp(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * t);
}

function mix(from: number[], to: number[], t: number) {
  return `rgb(${lerp(from[0], to[0], t)}, ${lerp(from[1], to[1], t)}, ${lerp(from[2], to[2], t)})`;
}

/**
 * heatColor(value, min, max) → an rgb() string on the cool→hot ramp.
 * Values at/below min read cool; at/above max read hot.
 */
export function heatColor(value: number, min: number, max: number): string {
  const span = max - min || 1;
  const t = Math.min(1, Math.max(0, (value - min) / span));
  return t < 0.5 ? mix(COOL, WARM, t * 2) : mix(WARM, HOT, (t - 0.5) * 2);
}
