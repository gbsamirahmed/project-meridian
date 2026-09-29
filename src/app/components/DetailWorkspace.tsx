import type { ReactNode } from "react";

interface Props { label: string; onClose: () => void; children: ReactNode; }

export default function DetailWorkspace({ label, onClose, children }: Props) {
  return <aside className="detail-workspace desktop-surface" aria-label={label}>
    <button className="detail-workspace-close" type="button" aria-label={`Close ${label}`} onClick={onClose}>×</button>
    {children}
  </aside>;
}
