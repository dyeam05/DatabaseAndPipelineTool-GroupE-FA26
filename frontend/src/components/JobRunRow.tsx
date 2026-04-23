import { useQuery } from "@tanstack/react-query";
import type { JobRun } from "../api/types";
import { formatRelativeTime } from "../utils/formatters";
import { listJobDefinitions } from "../api/job_definitions";

const JOB_STATUS_COLORS: Record<string, string> = {
  queued:    "var(--text-secondary)",
  running:   "var(--accent-caution)",
  succeeded: "var(--accent-go)",
  failed:    "var(--accent-alert)",
  cancelled: "var(--text-muted)",
};

const JOB_STATUS_LABELS: Record<string, string> = {
  queued: "Queued", running: "Running", succeeded: "Succeeded",
  failed: "Failed", cancelled: "Cancelled",
};

export function JobRunRow({ jobRun }: { jobRun: JobRun }) {
  const color = JOB_STATUS_COLORS[jobRun.status] ?? "var(--text-secondary)";
  const label = JOB_STATUS_LABELS[jobRun.status] ?? jobRun.status;
  const isActive = jobRun.status === "queued" || jobRun.status === "running";

  const { data: jobDefs = [] } = useQuery({
    queryKey: ["job-definitions"],
    queryFn: listJobDefinitions,
  });
  const defName = jobDefs.find((d) => d.id === jobRun.jobDefId)?.name ?? `def ${jobRun.jobDefId}`;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", padding: "calc(var(--space-2) + 1px) var(--space-3)", backgroundColor: "var(--bg-on-inverse-subtle)", border: "1px solid var(--border-on-inverse-faint)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px", minWidth: "100px" }}>
        {isActive && <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: color, flexShrink: 0 }} />}
        <span style={{ fontSize: "10px", fontWeight: 700, color, letterSpacing: "0.07em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
          {label}
        </span>
      </div>
      <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-muted)" }}>
        job #{jobRun.jobRunNum} · {defName}
      </span>
      <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-on-inverse-dim)", marginLeft: "auto" }}>
        {isActive ? `queued ${formatRelativeTime(jobRun.queuedAt)}` : formatRelativeTime(jobRun.finishedAt)}
      </span>
      {jobRun.error && (
        <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--accent-alert)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={jobRun.error}>
          {jobRun.error}
        </span>
      )}
    </div>
  );
}
