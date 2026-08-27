import { interpolateGridValue } from "./interpolation";

import type { WeatherGridBounds } from "../types/weatherGrid";

export interface ContourProperties {
  level: number;
  label: string;
  emphasized: boolean;
}

export type ContourFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.LineString | GeoJSON.Point,
  ContourProperties
>;

interface Segment {
  start: [number, number];
  end: [number, number];
}

interface BuildContourOptions {
  matrix: number[][];
  bounds: WeatherGridBounds;
  levels: number[];
  formatLabel: (level: number) => string;
  isEmphasized?: (level: number) => boolean;
}

function upsampleMatrix(matrix: number[][], factor: number): number[][] {
  const rows = matrix.length;
  const columns = matrix[0]?.length ?? 0;

  if (rows < 2 || columns < 2 || factor <= 1) return matrix;

  const targetRows = (rows - 1) * factor + 1;
  const targetColumns = (columns - 1) * factor + 1;

  return Array.from({ length: targetRows }, (_, row) =>
    Array.from({ length: targetColumns }, (_, column) =>
      interpolateGridValue(matrix, column / factor, row / factor)
    )
  );
}

const CASE_SEGMENTS: Record<number, [number, number][]> = {
  1: [[3, 0]],
  2: [[0, 1]],
  3: [[3, 1]],
  4: [[1, 2]],
  6: [[0, 2]],
  7: [[3, 2]],
  8: [[2, 3]],
  9: [[0, 2]],
  11: [[1, 2]],
  12: [[1, 3]],
  13: [[0, 1]],
  14: [[3, 0]],
};

function coordinateKey(coordinate: [number, number]): string {
  return `${coordinate[0].toFixed(7)}:${coordinate[1].toFixed(7)}`;
}

function interpolateEdge(
  start: [number, number],
  end: [number, number],
  startValue: number,
  endValue: number,
  level: number
): [number, number] {
  const ratio =
    startValue === endValue
      ? 0.5
      : Math.max(0, Math.min(1, (level - startValue) / (endValue - startValue)));

  return [
    start[0] + (end[0] - start[0]) * ratio,
    start[1] + (end[1] - start[1]) * ratio,
  ];
}

function getCasePairs(
  caseIndex: number,
  centerValue: number,
  level: number
): [number, number][] {
  if (caseIndex === 5) {
    return centerValue >= level
      ? [[0, 1], [2, 3]]
      : [[3, 0], [1, 2]];
  }

  if (caseIndex === 10) {
    return centerValue >= level
      ? [[3, 0], [1, 2]]
      : [[0, 1], [2, 3]];
  }

  return CASE_SEGMENTS[caseIndex] ?? [];
}

function stitchSegments(segments: Segment[]): [number, number][][] {
  const remaining = [...segments];
  const lines: [number, number][][] = [];

  while (remaining.length > 0) {
    const segment = remaining.pop();

    if (!segment) break;

    const line: [number, number][] = [segment.start, segment.end];
    let extended = true;

    while (extended) {
      extended = false;

      for (let index = remaining.length - 1; index >= 0; index--) {
        const candidate = remaining[index];
        const startKey = coordinateKey(line[0]);
        const endKey = coordinateKey(line[line.length - 1]);
        const candidateStartKey = coordinateKey(candidate.start);
        const candidateEndKey = coordinateKey(candidate.end);

        if (candidateStartKey === endKey) {
          line.push(candidate.end);
        } else if (candidateEndKey === endKey) {
          line.push(candidate.start);
        } else if (candidateEndKey === startKey) {
          line.unshift(candidate.start);
        } else if (candidateStartKey === startKey) {
          line.unshift(candidate.end);
        } else {
          continue;
        }

        remaining.splice(index, 1);
        extended = true;
        break;
      }
    }

    lines.push(line);
  }

  return lines;
}

export function buildContourGeoJson({
  matrix,
  bounds,
  levels,
  formatLabel,
  isEmphasized = () => false,
}: BuildContourOptions): ContourFeatureCollection {
  // March over a bilinearly upsampled version of the same coarse field. This
  // produces stable, smooth isolines without inventing new model samples.
  const contourMatrix = upsampleMatrix(matrix, 4);
  const rows = contourMatrix.length;
  const columns = contourMatrix[0]?.length ?? 0;
  const features: ContourFeatureCollection["features"] = [];

  if (rows < 2 || columns < 2) {
    return { type: "FeatureCollection", features };
  }

  const longitudeStep = (bounds.east - bounds.west) / (columns - 1);
  const latitudeStep = (bounds.north - bounds.south) / (rows - 1);

  for (const level of levels) {
    const segments: Segment[] = [];

    for (let row = 0; row < rows - 1; row++) {
      for (let column = 0; column < columns - 1; column++) {
        const corners: [number, number][] = [
          [bounds.west + column * longitudeStep, bounds.north - row * latitudeStep],
          [bounds.west + (column + 1) * longitudeStep, bounds.north - row * latitudeStep],
          [bounds.west + (column + 1) * longitudeStep, bounds.north - (row + 1) * latitudeStep],
          [bounds.west + column * longitudeStep, bounds.north - (row + 1) * latitudeStep],
        ];
        const values = [
          contourMatrix[row][column],
          contourMatrix[row][column + 1],
          contourMatrix[row + 1][column + 1],
          contourMatrix[row + 1][column],
        ];
        const caseIndex = values.reduce(
          (result, value, index) => result | (value >= level ? 1 << index : 0),
          0
        );

        if (caseIndex === 0 || caseIndex === 15) continue;

        const edgeCornerIndexes: [number, number][] = [
          [0, 1],
          [1, 2],
          [2, 3],
          [3, 0],
        ];
        const intersections = edgeCornerIndexes.map(
          ([startIndex, endIndex]) => {

            return interpolateEdge(
              corners[startIndex],
              corners[endIndex],
              values[startIndex],
              values[endIndex],
              level
            );
          }
        );
        const centerValue = values.reduce((sum, value) => sum + value, 0) / 4;

        for (const [startEdge, endEdge] of getCasePairs(
          caseIndex,
          centerValue,
          level
        )) {
          segments.push({
            start: intersections[startEdge],
            end: intersections[endEdge],
          });
        }
      }
    }

    const lines = stitchSegments(segments);
    const properties: ContourProperties = {
      level,
      label: formatLabel(level),
      emphasized: isEmphasized(level),
    };

    for (const coordinates of lines) {
      features.push({
        type: "Feature",
        geometry: { type: "LineString", coordinates },
        properties,
      });
    }

    const labelLine = lines.reduce<[number, number][] | null>(
      (longest, line) => (!longest || line.length > longest.length ? line : longest),
      null
    );

    if (labelLine && labelLine.length >= 2) {
      features.push({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: labelLine[Math.floor(labelLine.length / 2)],
        },
        properties,
      });
    }
  }

  return { type: "FeatureCollection", features };
}
