import type { TerrainRouteSample } from "../types/route";

export interface ProfilePlotGeometry {
  boundsLeft: number;
  boundsWidth: number;
  viewBoxWidth: number;
  plotLeft: number;
  plotRight: number;
}

export function profilePointerFraction(
  clientX: number,
  geometry: ProfilePlotGeometry
): number {
  const renderedFraction = (clientX - geometry.boundsLeft) /
    Math.max(1, geometry.boundsWidth);
  const viewBoxX = renderedFraction * geometry.viewBoxWidth;
  const drawableWidth = Math.max(
    1,
    geometry.viewBoxWidth - geometry.plotLeft - geometry.plotRight
  );
  return Math.max(
    0,
    Math.min(1, (viewBoxX - geometry.plotLeft) / drawableWidth)
  );
}

export function nearestRouteSampleForFraction(
  samples: Pick<TerrainRouteSample, "cumulativeDistanceM">[],
  totalDistanceM: number,
  fraction: number
): number {
  const targetDistance = Math.max(0, Math.min(1, fraction)) * totalDistanceM;
  let nearestIndex = 0;
  let nearestDifference = Number.POSITIVE_INFINITY;
  samples.forEach((sample, index) => {
    const difference = Math.abs(sample.cumulativeDistanceM - targetDistance);
    if (difference < nearestDifference) {
      nearestDifference = difference;
      nearestIndex = index;
    }
  });
  return nearestIndex;
}

export function nextPinnedRouteSample(
  currentPinnedIndex: number | null,
  candidateIndex: number
): number | null {
  return currentPinnedIndex === candidateIndex ? null : candidateIndex;
}
export function activeRouteSampleIndex(
  previewIndex: number | null,
  pinnedIndex: number | null
): number | null {
  return pinnedIndex ?? previewIndex;
}
