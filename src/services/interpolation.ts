export function interpolateGridValue(
  matrix: number[][],
  x: number,
  y: number
): number {
  const rowCount = matrix.length;
  const columnCount = matrix[0].length;

  const x0 = Math.floor(x);
  const y0 = Math.floor(y);

  const x1 = Math.min(x0 + 1, columnCount - 1);
  const y1 = Math.min(y0 + 1, rowCount - 1);

  const dx = x - x0;
  const dy = y - y0;

  const topLeft = matrix[y0][x0];
  const topRight = matrix[y0][x1];
  const bottomLeft = matrix[y1][x0];
  const bottomRight = matrix[y1][x1];

  const top = topLeft * (1 - dx) + topRight * dx;
  const bottom = bottomLeft * (1 - dx) + bottomRight * dx;

  return top * (1 - dy) + bottom * dy;
}