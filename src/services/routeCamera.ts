export const DEFAULT_WORKSPACE_GUTTER_PX = 12;
export const ROUTE_FIT_EDGE_PADDING_PX = 48;
export const ROUTE_FIT_RIGHT_FURNITURE_PX = 48;

interface RouteFitLayout {
  mapLeftPx: number;
  workspaceRightPx: number | null;
  workspaceGutterPx?: number;
  edgePaddingPx?: number;
  rightFurniturePx?: number;
}

export interface RouteFitPadding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export function calculateRouteFitPadding({
  mapLeftPx,
  workspaceRightPx,
  workspaceGutterPx = DEFAULT_WORKSPACE_GUTTER_PX,
  edgePaddingPx = ROUTE_FIT_EDGE_PADDING_PX,
  rightFurniturePx = ROUTE_FIT_RIGHT_FURNITURE_PX,
}: RouteFitLayout): RouteFitPadding {
  const obstructionRight = workspaceRightPx === null
    ? mapLeftPx
    : Math.max(mapLeftPx, workspaceRightPx + workspaceGutterPx);

  return {
    top: edgePaddingPx,
    right: rightFurniturePx + edgePaddingPx,
    bottom: edgePaddingPx,
    left: obstructionRight - mapLeftPx + edgePaddingPx,
  };
}
