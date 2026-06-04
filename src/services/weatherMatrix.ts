import { GRID_SIZE } from "../config/gridConfig";

import type { GridPoint } from "../types/gridPoint";

export function buildWeatherMatrix(
  gridPoints: GridPoint[],
  forecastHour: number,
  selector: (
    point: GridPoint,
    forecastHour: number
  ) => number
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < GRID_SIZE; row++) {
    const rowValues: number[] = [];

    for (
      let column = 0;
      column < GRID_SIZE;
      column++
    ) {
      const index =
        row * GRID_SIZE + column;

      rowValues.push(
        selector(
          gridPoints[index],
          forecastHour
        )
      );
    }

    matrix.push(rowValues);
  }

  return matrix;
}