import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getJobSegmentRunsForSegment, getCvatImportsForRoute, importToCvat, getCvatImportsForSegment } from "../api/job_segment_run";
import type { JobSegmentRun, CvatImport } from "../api/types";
import { CVAT_IN_PROGRESS_STATUSES } from "../api/types";

const JOB_STATUS_COLOR: Record<string, string> = {
  queued:    "var(--text-secondary)",
  running:   "var(--accent-caution)",
  succeeded: "var(--accent-go)",
  failed:    "var(--accent-alert)",
  cancelled: "var(--text-muted)",
};

type CvatButtonState = "load" | "in_progress" | "open";

function getCvatState(imports: CvatImport[], run: JobSegmentRun): CvatButtonState {
  const imp = imports.find(
    (i) =>
      i.jobRunNum === run.jobRunNum &&
      i.jobDefId  === run.jobDefId  &&
      i.segmentId === run.segmentId &&
      i.camera    === run.camera
  ) ?? null;

  if (!imp || imp.status === "removed" || imp.status === "failed") return "load";
  if (imp.status === "loaded") return "open";
  return "in_progress";
}

function getImport(imports: CvatImport[], run: JobSegmentRun): CvatImport | null {
  return imports.find(
    (i) =>
      i.jobRunNum === run.jobRunNum &&
      i.jobDefId  === run.jobDefId  &&
      i.segmentId === run.segmentId &&
      i.camera    === run.camera
  ) ?? null;
}

interface Props {
  routeId: string;
  segmentId: number;
}

export function CvatJobRunsList({ routeId, segmentId }: Props) {
  const queryClient = useQueryClient();

  const { data: segmentRuns = [], isLoading: runsLoading } = useQuery({
    queryKey: ["job-segment-runs", routeId, segmentId],
    queryFn: () => getJobSegmentRunsForSegment(routeId, segmentId),
    enabled: !!routeId,
    refetchInterval: (q) => {
      const runs = q.state.data ?? [];
      return runs.some((r) => r.status === "queued" || r.status === "running") ? 5000 : false;
    },
  });

  const { data: cvatImports = [], isLoading: importsLoading } = useQuery({
    queryKey: ["cvat-imports", routeId],
    queryFn: () => getCvatImportsForSegment(routeId, segmentId),
    enabled: !!routeId,
    refetchInterval: (q) => {
      const imps = q.state.data ?? [];
      return imps.some((i) => CVAT_IN_PROGRESS_STATUSES.includes(i.status)) ? 3000 : false;
    },
  });

  const loadMutation = useMutation({
    mutationFn: (run: JobSegmentRun) =>
      importToCvat({
        routeId,
        jobDefId:  run.jobDefId,
        jobRunNum: run.jobRunNum,
        segmentId: run.segmentId,
        camera:    run.camera,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cvat-imports", routeId] });
    },
  });

  const loading = runsLoading || importsLoading;

  return (
    <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", padding: "var(--space-5)" }}>
      <div style={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.09em", color: "var(--text-muted)", fontWeight: 600, marginBottom: "var(--space-4)" }}>
        Job Runs
      </div>

      {loading && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", padding: "var(--space-3) 0" }}>
          Loading…
        </div>
      )}

      {!loading && segmentRuns.length === 0 && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", padding: "var(--space-3) 0" }}>
          No job runs for this segment.
        </div>
      )}

      {!loading && segmentRuns.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {segmentRuns.map((run) => {
            const imp       = getImport(cvatImports, run);
            const state     = getCvatState(cvatImports, run);
            const statusColor = JOB_STATUS_COLOR[run.status] ?? "var(--text-secondary)";
            const isActive  = run.status === "queued" || run.status === "running";
            const isPending =
              loadMutation.isPending &&
              loadMutation.variables?.jobRunNum === run.jobRunNum &&
              loadMutation.variables?.jobDefId  === run.jobDefId  &&
              loadMutation.variables?.camera    === run.camera;

            return (
              <div
                key={`${run.jobDefId}-${run.jobRunNum}-${run.camera}`}
                style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", padding: "var(--space-3) var(--space-4)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-elevated)" }}
              >
                {/* Run identity */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "2px" }}>
                    {isActive && (
                      <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: statusColor, flexShrink: 0, display: "inline-block" }} />
                    )}
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700, color: statusColor, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                      {run.status}
                    </span>
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-secondary)" }}>
                    run #{run.jobRunNum} · def {run.jobDefId}
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-muted)", marginTop: "1px" }}>
                    {run.camera}
                  </div>
                  {imp?.status === "failed" && imp.errorMessage && (
                    <div
                      title={imp.errorMessage}
                      style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent-alert)", marginTop: "2px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    >
                      {imp.errorMessage}
                    </div>
                  )}
                </div>

                {/* Job not yet finished — CVAT locked */}
                {isActive && (
                  <button
                    disabled
                    style={{
                      flexShrink: 0, display: "flex", alignItems: "center", gap: "6px",
                      padding: "var(--space-2) var(--space-3)",
                      backgroundColor: "var(--bg-elevated)", color: "var(--text-muted)",
                      border: "1px solid var(--border-subtle)", cursor: "not-allowed",
                      fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700,
                      textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap", opacity: 0.5,
                    }}
                  >
                    <CvatIcon size={12} />
                    Job Running…
                  </button>
                )}

                {/* Stage 1: job done, not yet imported */}
                {!isActive && state === "load" && (
                  <button
                    onClick={() => loadMutation.mutate(run)}
                    disabled={isPending}
                    style={{
                      flexShrink: 0, display: "flex", alignItems: "center", gap: "6px",
                      padding: "var(--space-2) var(--space-3)",
                      backgroundColor: isPending ? "var(--bg-elevated)" : "var(--bg-inverse)",
                      color: isPending ? "var(--text-muted)" : "var(--text-on-inverse)",
                      border: "1px solid var(--border-strong)",
                      cursor: isPending ? "not-allowed" : "pointer",
                      fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700,
                      textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap",
                    }}
                  >
                    <CvatIcon size={12} />
                    {isPending ? "Loading…" : "Load into CVAT"}
                  </button>
                )}

                {/* Stage 2: CVAT import in progress */}
                {!isActive && state === "in_progress" && (
                  <button
                    disabled
                    style={{
                      flexShrink: 0, display: "flex", alignItems: "center", gap: "6px",
                      padding: "var(--space-2) var(--space-3)",
                      backgroundColor: "var(--bg-elevated)", color: "var(--accent-caution)",
                      border: "1px solid var(--accent-caution)", cursor: "not-allowed",
                      fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700,
                      textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap", opacity: 0.7,
                    }}
                  >
                    <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: "var(--accent-caution)", display: "inline-block" }} />
                    In Progress
                  </button>
                )}

                {/* Stage 3: loaded, ready to open */}
                {!isActive && state === "open" && imp?.taskUrl && (
                  <a href={imp.taskUrl} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none", flexShrink: 0 }}>
                    <button
                      style={{
                        display: "flex", alignItems: "center", gap: "6px",
                        padding: "var(--space-2) var(--space-3)",
                        backgroundColor: "var(--bg-inverse)", color: "var(--accent-cvat)",
                        border: "1px solid var(--accent-cvat)", cursor: "pointer",
                        fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700,
                        textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap",
                      }}
                    >
                      <CvatIcon size={12} />
                      Open in CVAT ↗
                    </button>
                  </a>
                )}

                {!isActive && state === "open" && !imp?.taskUrl && (
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent-go)", flexShrink: 0 }}>
                    Loaded (no URL)
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CvatIcon({ size }: { size: number }) {
  return (
    <div style={{ width: size, height: size, backgroundColor: "var(--accent-cvat)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: `${Math.floor(size * 0.55)}px`, color: "var(--text-on-inverse)", letterSpacing: "0.03em", lineHeight: 1 }}>CV</span>
    </div>
  );
}
