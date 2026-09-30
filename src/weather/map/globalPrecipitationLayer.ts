import { WEATHER_LAYER_VISUAL_STRENGTHS } from "./weatherVisuals";
import { createGlobalScalarSurface } from "./globalScalarSurface";
import { precipitationColor } from "../presentation/precipitationStyle";

const precipitationSurface = createGlobalScalarSurface({
  id: "precipitation",
  opacity: WEATHER_LAYER_VISUAL_STRENGTHS.precipitation,
  colour: precipitationColor,
});

export const updateGlobalPrecipitationLayer = precipitationSurface.update;
export const setGlobalPrecipitationEnabled = precipitationSurface.setEnabled;
export const removeGlobalPrecipitationLayer = precipitationSurface.remove;
