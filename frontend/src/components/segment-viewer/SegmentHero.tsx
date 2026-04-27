import { useNavigate } from "react-router-dom";
import type { SegmentStatus } from "../../api/types";
import { SEG_STATUS_CONFIG, DEFAULT_SEG_CFG } from "../../utils/segmentStatusConfig";
import { formatDate, formatOffset, formatDuration } from "../../utils/formatters";

interface Props {
  routeId: string;
  segIdx: number;
  segmentsLength: number;
  status: SegmentStatus;
  startSeconds: number;
  durationSeconds: number;
  frameCount: number | undefined;
  createdAt: string;
}

export function SegmentHero({ routeId, segIdx, segmentsLength, status, startSeconds, durationSeconds, frameCount, createdAt }: Props) {
  const navigate = useNavigate();
  const cfg = SEG_STATUS_CONFIG[status] ?? DEFAULT_SEG_CFG;

  return (
    <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-5) var(--space-8)" }}>

      {/* Breadcrumb */}
      <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", marginBottom: "var(--space-4)", fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        <button
          onClick={() => navigate("/routes")}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--text-on-inverse-muted)" }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-on-inverse-secondary)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-on-inverse-muted)")}
        >
          Routes
        </button>
        <span style={{ color: "var(--text-on-inverse-dim)" }}>/</span>
        <button
          onClick={() => navigate(`/routes/${encodeURIComponent(routeId)}`)}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--text-on-inverse-muted)" }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-on-inverse-secondary)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-on-inverse-muted)")}
        >
          {routeId}
        </button>
        <span style={{ color: "var(--text-on-inverse-dim)" }}>/</span>
        <span style={{ color: "var(--text-on-inverse-secondary)" }}>Segment {String(segIdx).padStart(2, "0")}</span>
      </div>

      {/* Title row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "var(--space-3)", marginBottom: "var(--space-3)" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-3xl)", fontWeight: 700, color: "var(--text-on-inverse)", lineHeight: 1, letterSpacing: "-0.03em" }}>
            {String(segIdx).padStart(2, "0")}
          </span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-on-inverse-muted)" }}>
            / {String(segmentsLength - 1).padStart(2, "0")}
          </span>
        </div>

        <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "3px var(--space-3)", border: `1px solid ${cfg.borderColor}` }}>
          {status === "uploaded" && <span style={{ color: cfg.borderColor, fontSize: "9px", fontWeight: 800 }}>✓</span>}
          {status === "failed"   && <span style={{ color: cfg.borderColor, fontSize: "9px", fontWeight: 800 }}>✕</span>}
          <span style={{ fontSize: "9px", fontWeight: 700, color: cfg.borderColor, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Meta */}
      <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-muted)" }}>
        <span>{formatDate(createdAt)}</span>
        <span style={{ color: "var(--text-on-inverse-dim)" }}>·</span>
        <span>offset {formatOffset(startSeconds)}</span>
        <span style={{ color: "var(--text-on-inverse-dim)" }}>·</span>
        <span>{formatDuration(durationSeconds)}</span>
        <span style={{ color: "var(--text-on-inverse-dim)" }}>·</span>
        <span>{(frameCount ?? 0).toLocaleString()} frames</span>
      </div>
    </div>
  );
}
