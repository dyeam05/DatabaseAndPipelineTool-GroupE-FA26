import { useState } from "react";
import type { Segment } from "../api/types";
import { SEG_STATUS_CONFIG, DEFAULT_SEG_CFG } from "../utils/segmentStatusConfig";
import { formatOffset } from "../utils/formatters";

export function SegmentTimeline({ segments }: { segments: Segment[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  return (
    <div>
      <div style={{ display: "flex", gap: "2px", flexWrap: "wrap" }}>
        {segments.map((seg) => {
          const cfg = SEG_STATUS_CONFIG[seg.status] ?? DEFAULT_SEG_CFG;
          const isHovered = hoveredIdx === seg.index;
          return (
            <div
              key={seg.index}
              onMouseEnter={() => setHoveredIdx(seg.index)}
              onMouseLeave={() => setHoveredIdx(null)}
              title={`#${String(seg.index).padStart(2, "0")} · ${cfg.label} · ${formatOffset(seg.startSeconds)}`}
              style={{ width: "16px", height: "8px", backgroundColor: isHovered ? "var(--text-on-inverse)" : cfg.timelineColor, flexShrink: 0, cursor: "default", transition: "background-color 80ms ease" }}
            />
          );
        })}
      </div>
      {hoveredIdx !== null && segments[hoveredIdx] && (
        <div style={{ marginTop: "6px", fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-secondary)", letterSpacing: "0.04em" }}>
          seg{" "}
          <span style={{ color: "var(--text-on-inverse)", fontWeight: 700 }}>#{String(hoveredIdx).padStart(2, "0")}</span>
          {" · "}
          <span style={{ color: (SEG_STATUS_CONFIG[segments[hoveredIdx].status] ?? DEFAULT_SEG_CFG).timelineColor }}>
            {(SEG_STATUS_CONFIG[segments[hoveredIdx].status] ?? DEFAULT_SEG_CFG).label}
          </span>
          {" · "}
          {formatOffset(segments[hoveredIdx].startSeconds)}
        </div>
      )}
    </div>
  );
}
