import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { cloudCoverColor } from "./cloudStyle";
import { createGlobalScalarSurface } from "./globalScalarSurface";

const cloudSurface = createGlobalScalarSurface({
  id: "cloud-cover",
  opacity: LAYER_VISUAL_STRENGTHS.clouds,
  colour: cloudCoverColor,
});

export const updateGlobalCloudLayer = cloudSurface.update;
export const setGlobalCloudEnabled = cloudSurface.setEnabled;
export const removeGlobalCloudLayer = cloudSurface.remove;
