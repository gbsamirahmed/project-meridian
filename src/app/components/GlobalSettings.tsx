interface GlobalSettingsProps {
  open: boolean;
  mapInspectorEnabled: boolean;
  onMapInspectorChange: (enabled: boolean) => void;
  onClose: () => void;
}

export default function GlobalSettings({ open, mapInspectorEnabled, onMapInspectorChange, onClose }: GlobalSettingsProps) {
  if (!open) return null;
  return (
    <div className="workspace-dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="workspace-dialog global-settings-dialog" role="dialog" aria-modal="true" aria-labelledby="global-settings-title">
        <div className="dialog-heading"><div><p className="section-kicker">Meridian</p><h2 id="global-settings-title">Settings</h2></div><button type="button" aria-label="Close settings" onClick={onClose}>×</button></div>
        <label className="settings-toggle"><span><strong>Map Inspector</strong><small>Show elevation and weather when hovering or tapping the map.</small></span><input type="checkbox" checked={mapInspectorEnabled} onChange={(event) => onMapInspectorChange(event.target.checked)} /></label>
      </section>
    </div>
  );
}
