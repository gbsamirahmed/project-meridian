export const WEATHER_GRID_ROWS = 9;
export const WEATHER_GRID_COLUMNS = 9;

// Sampling extends well beyond the current camera footprint. A refresh begins
// while the viewport is still inside the safe interior, leaving the outer band
// solely as a buffer for requests and crossfades rather than a visible frame.
export const WEATHER_GRID_PADDING_RATIO = 0.65;
export const WEATHER_GRID_REFRESH_INSET_RATIO = 0.22;
export const WEATHER_GRID_VISIBLE_INSET_RATIO = 0.14;
export const WEATHER_GRID_MIN_ZOOM = 4.75;
// A UK-scale view needs more than ten degrees once the camera footprint is
// padded. The sample count remains 9 by 9, so broader views are deliberately
// coarser rather than generating more requests or suggesting more detail.
export const WEATHER_GRID_MAX_SPAN_DEGREES = 24;
export const WEATHER_GRID_REQUEST_DELAY_MS = 550;
export const WEATHER_GRID_CACHE_SIZE = 12;
export const WEATHER_GRID_CACHE_MAX_AGE_MS = 30 * 60 * 1000;
