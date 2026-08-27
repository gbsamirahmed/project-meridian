import type { GridPoint } from "../types/gridPoint";

export function buildWeatherMatrix(
  gridPoints: GridPoint[],
  rows: number,
  columns: number,
  forecastHour: number,
  selector: (
    point: GridPoint,
    forecastHour: number
  ) => number
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < rows; row++) {
    const rowValues: number[] = [];

    for (
      let column = 0;
      column < columns;
      column++
    ) {
      const index =
        row * columns + column;

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
