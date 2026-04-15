import type { JobRun, Segment } from "../api/types";
import { Pip } from "./Pip";

export function UploadBar({ segments, jobRuns }: { segments: Segment[]; jobRuns: JobRun[] }) {
  const total = segments.length;
  const uploaded = segments.filter((s) => s.status === "uploaded").length;
  const uploading = segments.filter(
    (s) => s.status === "uploading" || s.status === "downloading"
  ).length;
  const failed = segments.filter((s) => s.status === "failed").length;
  const pct = total > 0 ? Math.round((uploaded / total) * 100) : 0;

  const activeJobs = jobRuns.filter((r) => r.status === "queued" || r.status === "running").length;
  const succeededJobs = jobRuns.filter((r) => r.status === "succeeded").length;
  const failedJobs = jobRuns.filter((r) => r.status === "failed").length;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
          {uploaded} / {total} uploaded
        </span>
        <span
          style={{
            fontSize: "var(--text-sm)",
            fontWeight: 700,
            fontFamily: "var(--font-mono)",
            color: pct === 100 ? "var(--accent-go)" : failed === total && total > 0 ? "var(--accent-alert)" : "var(--text-primary)",
          }}
        >
          {total > 0 ? `${pct}%` : "—"}
        </span>
      </div>

      <div style={{ height: "5px", backgroundColor: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", overflow: "hidden", display: "flex" }}>
        {uploaded > 0 && total > 0 && (
          <div style={{ width: `${(uploaded / total) * 100}%`, backgroundColor: "var(--accent-go)", flexShrink: 0 }} />
        )}
        {uploading > 0 && total > 0 && (
          <div style={{ width: `${(uploading / total) * 100}%`, backgroundColor: "var(--accent-caution)", flexShrink: 0 }} />
        )}
        {failed > 0 && total > 0 && (
          <div style={{ width: `${(failed / total) * 100}%`, backgroundColor: "var(--accent-alert)", flexShrink: 0 }} />
        )}
      </div>

      <div style={{ display: "flex", gap: "var(--space-4)", marginTop: "6px", flexWrap: "wrap" }}>
        {(uploading > 0 || failed > 0) && (
          <>
            {uploading > 0 && <Pip color="var(--accent-caution)" label={`${uploading} uploading`} />}
            {failed > 0 && <Pip color="var(--accent-alert)" label={`${failed} failed`} />}
          </>
        )}
        {jobRuns.length > 0 && (
          <>
            {activeJobs > 0 && <Pip color="var(--accent-caution)" label={`${activeJobs} job${activeJobs > 1 ? "s" : ""} running`} />}
            {succeededJobs > 0 && <Pip color="var(--accent-go)" label={`${succeededJobs} job${succeededJobs > 1 ? "s" : ""} done`} />}
            {failedJobs > 0 && <Pip color="var(--accent-alert)" label={`${failedJobs} job${failedJobs > 1 ? "s" : ""} failed`} />}
          </>
        )}
      </div>
    </div>
  );
}
