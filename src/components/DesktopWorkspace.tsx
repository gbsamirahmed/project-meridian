import type { ReactNode } from "react";
import type { WorkspaceMode } from "../services/desktopWorkspaceState";

interface DesktopWorkspaceProps {
  mode: WorkspaceMode;
  onModeChange: (mode: WorkspaceMode) => void;
  onClose: () => void;
  onSettings: () => void;
  onClearMap: () => void;
  children: ReactNode;
}

export function MeridianMark({ label }: { label?: string }) {
  return (
    <span className="meridian-mark" aria-label={label} role={label ? "img" : undefined}>
      <span /><span />
    </span>
  );
}

export default function DesktopWorkspace({
  mode,
  onModeChange,
  onClose,
  onSettings,
  onClearMap,
  children,
}: DesktopWorkspaceProps) {
  return (
    <aside className="desktop-workspace desktop-surface" aria-label="Meridian workspace">
      <header className="desktop-workspace-header">
        <div className="desktop-brand"><MeridianMark /><div><p>Terrain weather</p><h1>Meridian</h1></div></div>
        <div className="surface-actions">
          <button type="button" aria-label="Global settings" title="Settings" onClick={onSettings}>⚙</button>
          <button type="button" aria-label="Focus map" title="Focus map" onClick={onClearMap}>Focus</button>
          <button type="button" aria-label="Hide workspace" title="Hide workspace" onClick={onClose}>×</button>
        </div>
      </header>
      <div className="workspace-tabs" role="tablist" aria-label="Workspace context">
        <button type="button" role="tab" aria-selected={mode === "location"} onClick={() => onModeChange("location")}>Location</button>
        <button type="button" role="tab" aria-selected={mode === "journey"} onClick={() => onModeChange("journey")}>Journey</button>
      </div>
      <div className="desktop-workspace-content">{children}</div>
    </aside>
  );
}
