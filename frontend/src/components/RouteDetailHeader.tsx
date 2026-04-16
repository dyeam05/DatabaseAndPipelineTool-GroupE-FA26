import type { Route, Segment, JobRun } from "../api/types";
import { formatDate } from "../utils/formatters";
import { isAnnotationInProgress } from "../hooks/useJobRunsForRoute";
import { DarkStatCell } from "./DarkStatCell";
import { HeroUploadBar } from "./HeroUploadBar";
import { JobRunRow } from "./JobRunRow";
import { SegmentTimeline } from "./SegmentTimeline";

const ROUTE_STATUS_COLORS: Record<string, string> = {
  "download queue": "var(--text-secondary)",
  downloading:      "var(--accent-caution)",
  "upload queue":   "var(--text-secondary)",
  uploading:        "var(--accent-caution)",
  uploaded:         "var(--accent-go)",
  failed:           "var(--accent-alert)",
};

const ROUTE_STATUS_LABELS: Record<string, string> = {
  "download queue": "Queued",
  downloading:      "Downloading",
  "upload queue":   "Upload Queue",
  uploading:        "Uploading",
  uploaded:         "Uploaded",
  failed:           "Failed",
};

export function RouteDetailHeader({
  route,
  segments,
  jobRuns,
  isPolling,
  onBack,
}: {
  route: Route;
  segments: Segment[];
  jobRuns: JobRun[];
  isPolling: boolean;
  onBack: () => void;
}) {
  const uploadedSegs  = segments.filter((s) => s.status === "uploaded").length;
  const uploadingSegs = segments.filter((s) => s.status === "uploading" || s.status === "downloading").length;
  const failedSegs    = segments.filter((s) => s.status === "failed").length;
  const queuedSegs    = segments.filter((s) => s.status === "download queue" || s.status === "upload queue").length;
  const annotationActive = isAnnotationInProgress(jobRuns);

  const routeStatusColor = ROUTE_STATUS_COLORS[route.status] ?? "var(--text-secondary)";
  const routeStatusLabel = ROUTE_STATUS_LABELS[route.status] ?? route.status;

  return (
    <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-6) var(--space-8) var(--space-5)" }}>
      <button
        onClick={onBack}
        style={{ background: "none", border: "none", cursor: "pointer", padding: 0, display: "inline-flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-on-inverse-dim)", fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "var(--space-4)" }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.color = "var(--text-on-inverse-secondary)")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.color = "var(--text-on-inverse-dim)")}
      >
        ← Routes
      </button>

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-4)", flexWrap: "wrap", marginBottom: "var(--space-2)" }}>
        <h1 style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-lg)", fontWeight: 700, color: "var(--text-on-inverse)", letterSpacing: "-0.01em", margin: 0 }}>
          {route.id}
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          {isPolling && (
            <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "2px 6px", border: "1px solid var(--border-on-inverse)" }}>
              <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: "var(--accent-caution)", flexShrink: 0 }} />
              <span style={{ fontSize: "9px", fontWeight: 700, color: "var(--text-on-inverse-muted)", letterSpacing: "0.07em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>Live</span>
            </span>
          )}
          <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "3px var(--space-3)", border: `1px solid ${routeStatusColor}` }}>
            {route.status === "uploaded" && <span style={{ color: routeStatusColor, fontSize: "9px", fontWeight: 800 }}>✓</span>}
            <span style={{ fontSize: "9px", fontWeight: 700, color: routeStatusColor, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
              {routeStatusLabel}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap", marginBottom: "var(--space-4)", fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-secondary)" }}>
        <span>{formatDate(route.createdAt)}</span>
        <span style={{ color: "var(--border-on-inverse-subtle)" }}>·</span>
        <span>{segments.length} segments</span>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", border: "1px solid var(--border-on-inverse-faint)", marginBottom: "var(--space-4)" }}>
        <DarkStatCell label="Segments"  value={segments.length} />
        <DarkStatCell label="Uploaded"  value={uploadedSegs}  valueColor={uploadedSegs  > 0 ? "var(--accent-go)"      : undefined} />
        <DarkStatCell label="Uploading" value={uploadingSegs} valueColor={uploadingSegs > 0 ? "var(--accent-caution)" : undefined} />
        <DarkStatCell label="Failed"    value={failedSegs}    valueColor={failedSegs    > 0 ? "var(--accent-alert)"   : undefined} />
        <DarkStatCell label="Queued"    value={queuedSegs} />
      </div>

      <div style={{ marginBottom: "var(--space-4)" }}>
        <HeroUploadBar segments={segments} />
      </div>

      {jobRuns.length > 0 && (
        <div style={{ marginBottom: "var(--space-4)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
            <span style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-dim)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Annotation Jobs
            </span>
            {annotationActive && <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: "var(--accent-caution)" }} />}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {jobRuns.map((jr) => (
              <JobRunRow key={`${jr.jobRunNum}-${jr.jobDefId}`} jobRun={jr} />
            ))}
          </div>
        </div>
      )}

      {segments.length > 0 && (
        <div>
          <div style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-dim)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "var(--space-2)" }}>
            Segment timeline
          </div>
          <SegmentTimeline segments={segments} />
        </div>
      )}
    </div>
  );
}
