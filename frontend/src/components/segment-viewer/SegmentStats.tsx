import type { Segment } from "../../api/types";
import { formatDate, formatOffset, formatDuration } from "../../utils/formatters";
import { routeIdWithBreakHints } from "../../utils/routeId";

interface Props {
  segIdx: number;
  segmentsLength: number;
  segment: Segment;
  frameCount: number | undefined;
  createdAt: string;
}

export function SegmentStats({ segIdx, segmentsLength, segment, frameCount, createdAt }: Props) {
  const rows = [
    { label: "Segment",      value: `#${String(segIdx).padStart(2, "0")} of ${segmentsLength}` },
    { label: "Start offset", value: formatOffset(segment.startSeconds) },
    { label: "Duration",     value: formatDuration(segment.durationSeconds) },
    { label: "Frame count",  value: (frameCount ?? 0).toLocaleString() },
    { label: "Created",      value: formatDate(createdAt) },
    { label: "Route",        value: routeIdWithBreakHints(segment.routeId) },
  ];

  return (
    <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)" }}>
      {rows.map(({ label, value }, i) => (
        <div
          key={label}
          style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "var(--space-3)", padding: "var(--space-3) var(--space-4)", borderBottom: i < rows.length - 1 ? "1px solid var(--border-subtle)" : "none" }}
        >
          <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)", fontWeight: 600, flexShrink: 0 }}>{label}</span>
          <span style={{ fontSize: "var(--text-xs)", fontFamily: "var(--font-mono)", color: "var(--text-primary)", textAlign: "right" }} title={label === "Route" ? segment.routeId : undefined}>{value}</span>
        </div>
      ))}
    </div>
  );
}
