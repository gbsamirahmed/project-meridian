import type { ReactNode } from "react";
import type { WorkspaceMode } from "../services/desktopWorkspaceState";

interface DesktopWorkspaceProps {
  mode: WorkspaceMode;
  analysisAvailable: boolean;
  onModeChange: (mode: WorkspaceMode) => void;
  onSettings: () => void;
  onFocusMode: () => void;
  children: ReactNode;
}

export function MeridianMark({ label }: { label?: string }) {
  return <img className="meridian-mark" src="/favicon.svg" alt={label ?? ""} />;
}

export default function DesktopWorkspace({
  mode,
  analysisAvailable,
  onModeChange,
  onSettings,
  onFocusMode,
  children,
}: DesktopWorkspaceProps) {
  return (
    <aside className="desktop-workspace desktop-surface" aria-label="Meridian workspace">
      <header className="desktop-workspace-header">
        <button type="button" className="desktop-brand" aria-label="Enter focus mode" title="Enter focus mode" onClick={onFocusMode}>
          <MeridianMark />
          <div><p>Terrain weather</p><h1>Meridian</h1></div>
        </button>
        <div className="surface-actions">
          <button type="button" aria-label="Global settings" title="Settings" onClick={onSettings}>⚙</button>
        </div>
      </header>
      <div className={`workspace-tabs${analysisAvailable ? " workspace-tabs-three" : ""}`} role="tablist" aria-label="Workspace context">
        <button type="button" role="tab" aria-selected={mode === "location"} onClick={() => onModeChange("location")}>Location</button>
        <button type="button" role="tab" aria-selected={mode === "journey"} onClick={() => onModeChange("journey")}>Journey</button>
        {analysisAvailable && <button type="button" role="tab" aria-selected={mode === "analysis"} onClick={() => onModeChange("analysis")}>Analysis</button>}
      </div>
      <div className="desktop-workspace-content">{children}</div>
    </aside>
  );
}
