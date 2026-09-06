export const DEFAULT_WORKSPACE_GUTTER_PX = 12;
export const ROUTE_FIT_EDGE_PADDING_PX = 48;

interface RouteFitLayout {
  mapLeftPx: number;
  workspaceRightPx: number | null;
  workspaceGutterPx?: number;
  edgePaddingPx?: number;
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
}: RouteFitLayout): RouteFitPadding {
  const obstructionRight = workspaceRightPx === null
    ? mapLeftPx
    : Math.max(mapLeftPx, workspaceRightPx + workspaceGutterPx);

  return {
    top: edgePaddingPx,
    right: edgePaddingPx,
    bottom: edgePaddingPx,
    left: obstructionRight - mapLeftPx + edgePaddingPx,
  };
}
