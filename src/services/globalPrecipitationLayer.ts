import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { createGlobalScalarSurface } from "./globalScalarSurface";
import { precipitationColor } from "./precipitationStyle";

const precipitationSurface = createGlobalScalarSurface({
  id: "precipitation",
  opacity: LAYER_VISUAL_STRENGTHS.precipitation,
  colour: precipitationColor,
});

export const updateGlobalPrecipitationLayer = precipitationSurface.update;
export const setGlobalPrecipitationEnabled = precipitationSurface.setEnabled;
export const removeGlobalPrecipitationLayer = precipitationSurface.remove;
