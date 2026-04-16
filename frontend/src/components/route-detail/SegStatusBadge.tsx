import type { SegmentStatus } from "../../api/types";
import { SEG_STATUS_CONFIG, DEFAULT_SEG_CFG } from "../../utils/segmentStatusConfig";

export function SegStatusBadge({ status }: { status: SegmentStatus }) {
  const cfg = SEG_STATUS_CONFIG[status] ?? DEFAULT_SEG_CFG;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "3px", paddingLeft: "var(--space-2)", paddingRight: "var(--space-2)", paddingTop: "2px", paddingBottom: "2px", borderLeft: `3px solid ${cfg.borderColor}`, backgroundColor: cfg.bg, backdropFilter: "blur(4px)" }}>
      {status === "uploaded" && <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✓</span>}
      {status === "failed" && <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✕</span>}
      <span style={{ fontSize: "8px", fontWeight: 700, color: cfg.textColor, letterSpacing: "0.07em", textTransform: "uppercase" }}>{cfg.label}</span>
    </div>
  );
}
