import { useState } from "react";
import type { Route, Segment, JobRun } from "../api/types";
import { formatDate } from "../utils/formatDate";
import { RouteThumbnail } from "./RouteThumbnail";
import { StatusBadge } from "./StatusBadge";
import { UploadBar } from "./UploadBar";

export function RouteCard({
  route,
  segments,
  jobRuns,
  onClick,
}: {
  route: Route;
  segments: Segment[];
  jobRuns: JobRun[];
  onClick: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const [copied, setCopied] = useState(false);

  function handleCopy(e: React.MouseEvent) {
    e.stopPropagation();
    navigator.clipboard.writeText(route.id).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  const activeJobCount = jobRuns.filter((r) => r.status === "queued" || r.status === "running").length;

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        outline: hovered ? "2px solid var(--border-black)" : "2px solid transparent",
        outlineOffset: "-1px",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Thumbnail */}
      <div style={{ position: "relative", height: "140px", overflow: "hidden", flexShrink: 0 }}>
        <RouteThumbnail route={route} hovered={hovered} />
        <div style={{ position: "absolute", bottom: "var(--space-2)", left: "var(--space-2)" }}>
          <StatusBadge status={route.status} />
        </div>
        <div style={{ position: "absolute", bottom: "var(--space-2)", right: "var(--space-2)", backgroundColor: "var(--bg-inverse)", backdropFilter: "blur(4px)", padding: "2px var(--space-2)", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          {activeJobCount > 0 && (
            <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: "var(--accent-caution)", flexShrink: 0 }} title={`${activeJobCount} annotation job${activeJobCount > 1 ? "s" : ""} running`} />
          )}
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", fontWeight: 700, color: "var(--text-on-inverse)", letterSpacing: "0.04em" }}>
            {segments.length} seg
          </span>
        </div>
      </div>

      {/* Card body */}
      <div style={{ padding: "var(--space-3) var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {route.id}
            </span>
            <button
              onClick={handleCopy}
              title="Copy route ID"
              style={{ background: "none", border: "none", cursor: "pointer", padding: "0 3px", color: copied ? "var(--accent-go)" : "var(--text-muted)", fontSize: "var(--text-xs)", fontFamily: "var(--font-mono)", flexShrink: 0, lineHeight: 1 }}
            >
              {copied ? "✓" : "⎘"}
            </button>
          </div>

          <div style={{ marginTop: "4px", fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            {formatDate(route.createdAt)}
          </div>
        </div>

        <div style={{ height: "1px", backgroundColor: "var(--border-subtle)" }} />
        <UploadBar segments={segments} jobRuns={jobRuns} />
      </div>
    </div>
  );
}
