export type WorkspaceMode = "location" | "journey";

export interface DesktopWorkspaceState {
  workspaceMode: WorkspaceMode;
  leftOpen: boolean;
  mapControlsOpen: boolean;
  routeAnalysisOpen: boolean;
  settingsOpen: boolean;
  journeySettingsOpen: boolean;
  clearMap: boolean;
  mapInspectorEnabled: boolean;
  mapInspectorSession: number;
}

export type DesktopWorkspaceAction =
  | { type: "set-workspace"; mode: WorkspaceMode }
  | { type: "set-left"; open: boolean }
  | { type: "set-map-controls"; open: boolean }
  | { type: "set-route-analysis"; open: boolean }
  | { type: "set-settings"; open: boolean }
  | { type: "set-journey-settings"; open: boolean }
  | { type: "set-clear-map"; active: boolean }
  | { type: "set-map-inspector"; enabled: boolean };

export const INITIAL_DESKTOP_WORKSPACE_STATE: DesktopWorkspaceState = {
  workspaceMode: "location",
  leftOpen: true,
  mapControlsOpen: true,
  routeAnalysisOpen: true,
  settingsOpen: false,
  journeySettingsOpen: false,
  clearMap: false,
  mapInspectorEnabled: false,
  mapInspectorSession: 0,
};

export function desktopWorkspaceReducer(
  state: DesktopWorkspaceState,
  action: DesktopWorkspaceAction
): DesktopWorkspaceState {
  switch (action.type) {
    case "set-workspace":
      return { ...state, workspaceMode: action.mode };
    case "set-left":
      return { ...state, leftOpen: action.open };
    case "set-map-controls":
      return { ...state, mapControlsOpen: action.open };
    case "set-route-analysis":
      return { ...state, routeAnalysisOpen: action.open };
    case "set-settings":
      return { ...state, settingsOpen: action.open };
    case "set-journey-settings":
      return { ...state, journeySettingsOpen: action.open };
    case "set-clear-map":
      return {
        ...state,
        clearMap: action.active,
        settingsOpen: action.active ? false : state.settingsOpen,
        journeySettingsOpen: action.active ? false : state.journeySettingsOpen,
      };
    case "set-map-inspector":
      return {
        ...state,
        mapInspectorEnabled: action.enabled,
        mapInspectorSession: state.mapInspectorSession + 1,
      };
  }
}
