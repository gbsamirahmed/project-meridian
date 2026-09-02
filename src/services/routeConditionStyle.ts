import type {
  RouteConditionMode,
  RouteConditionSample,
} from "../types/routeConditions";

interface ColourStop {
  value: number;
  colour: string;
}

const COLOUR_STOPS: Record<Exclude<RouteConditionMode, "none">, ColourStop[]> = {
  temperature: [
    { value: -20, colour: "#766bd8" },
    { value: 0, colour: "#5bc2d1" },
    { value: 10, colour: "#8ed08a" },
    { value: 20, colour: "#efc45e" },
    { value: 30, colour: "#e5684d" },
  ],
  precipitation: [
    { value: 0, colour: "#d8dedb" },
    { value: 0.1, colour: "#55bad1" },
    { value: 1, colour: "#6366cf" },
    { value: 3, colour: "#a84db6" },
    { value: 8, colour: "#dc4c71" },
    { value: 15, colour: "#ee554e" },
  ],
  wind: [
    { value: 0, colour: "#d8e4df" },
    { value: 5, colour: "#80cfa2" },
    { value: 10, colour: "#e7c45f" },
    { value: 20, colour: "#ef7852" },
    { value: 30, colour: "#bd68d7" },
  ],
  gradient: [
    { value: -0.3, colour: "#7185d8" },
    { value: -0.1, colour: "#6ab7c4" },
    { value: 0, colour: "#9bcf9d" },
    { value: 0.1, colour: "#e4b85f" },
    { value: 0.3, colour: "#e26952" },
  ],
};

export const ROUTE_CONDITION_LEGENDS: Record<
  Exclude<RouteConditionMode, "none">,
  { label: string; units: string; values: string[]; gradient: string }
> = {
  temperature: {
    label: "Encountered temperature",
    units: "°C",
    values: ["−20", "0", "10", "20", "30+"],
    gradient: "linear-gradient(90deg, #766bd8, #5bc2d1, #8ed08a, #efc45e, #e5684d)",
  },
  precipitation: {
    label: "Encountered 1 h precipitation",
    units: "mm",
    values: ["Dry", "0.1", "1", "3", "8", "15+"],
    gradient: "linear-gradient(90deg, #d8dedb, #55bad1, #6366cf, #a84db6, #dc4c71, #ee554e)",
  },
  wind: {
    label: "Encountered wind speed",
    units: "m/s",
    values: ["0", "5", "10", "20", "30+"],
    gradient: "linear-gradient(90deg, #d8e4df, #80cfa2, #e7c45f, #ef7852, #bd68d7)",
  },
  gradient: {
    label: "Route gradient",
    units: "%",
    values: ["−30", "−10", "0", "10", "30+"],
    gradient: "linear-gradient(90deg, #7185d8, #6ab7c4, #9bcf9d, #e4b85f, #e26952)",
  },
};

function parseHex(colour: string): [number, number, number] {
  return [
    Number.parseInt(colour.slice(1, 3), 16),
    Number.parseInt(colour.slice(3, 5), 16),
    Number.parseInt(colour.slice(5, 7), 16),
  ];
}

function interpolateColour(stops: ColourStop[], value: number): string {
  if (value <= stops[0].value) return stops[0].colour;
  if (value >= stops[stops.length - 1].value) return stops[stops.length - 1].colour;
  const endIndex = stops.findIndex((stop) => stop.value >= value);
  const start = stops[endIndex - 1];
  const end = stops[endIndex];
  const ratio = (value - start.value) / (end.value - start.value);
  const first = parseHex(start.colour);
  const second = parseHex(end.colour);
  const component = (index: number) =>
    Math.round(first[index] + (second[index] - first[index]) * ratio)
      .toString(16)
      .padStart(2, "0");
  return `#${component(0)}${component(1)}${component(2)}`;
}

export function routeConditionValue(
  sample: RouteConditionSample,
  mode: RouteConditionMode
): number | null {
  if (mode === "none") return null;
  if (mode === "gradient") return sample.terrain.gradient;
  if (mode === "temperature") {
    return sample.weather.temperature.state === "available"
      ? sample.weather.temperature.value
      : null;
  }
  if (mode === "precipitation") {
    return sample.weather.precipitation.state === "available"
      ? sample.weather.precipitation.value
      : null;
  }
  return sample.weather.wind.state === "available"
    ? sample.weather.wind.speedMs
    : null;
}

export function routeConditionColour(
  sample: RouteConditionSample,
  mode: RouteConditionMode
): string {
  const value = routeConditionValue(sample, mode);
  if (value === null) return "#7b8581";
  return interpolateColour(COLOUR_STOPS[mode as Exclude<RouteConditionMode, "none">], value);
}
