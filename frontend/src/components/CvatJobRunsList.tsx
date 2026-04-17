import type { CSSProperties, ReactNode } from "react";
import { useQuery, useQueries, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getJobSegmentRunsForSegment,
  importToCvat,
  getCvatImportForRun,
} from "../api/job_segment_run";
import type { CvatImport, JobSegmentRun, JobSegmentRunStatus } from "../api/types";
import { CVAT_IN_PROGRESS_STATUSES } from "../api/types";

// ─── Constants & helpers ──────────────────────────────────────────────────────

const JOB_STATUS_COLOR: Record<JobSegmentRunStatus, string> = {
  queued:    "var(--text-secondary)",
  running:   "var(--accent-caution)",
  succeeded: "var(--accent-go)",
  failed:    "var(--accent-alert)",
  cancelled: "var(--text-muted)",
};

const ACTIVE_JOB_STATUSES: JobSegmentRunStatus[] = ["queued", "running"];

type RunKeyFields = Pick<JobSegmentRun, "jobDefId" | "jobRunNum" | "segmentId" | "camera">;

const runKey = (r: RunKeyFields) => `${r.jobDefId}-${r.jobRunNum}-${r.segmentId}-${r.camera}`;

type CvatActionState = "unavailable" | "load" | "in_progress" | "open";

interface CvatAction {
  state: CvatActionState;
  label: string;
}

function resolveAction(run: JobSegmentRun, imp: CvatImport | null, isPending: boolean): CvatAction {
  if (isPending)                    return { state: "in_progress", label: "Loading…" };
  if (run.status !== "succeeded")   return { state: "unavailable", label: "Not Available" };
  if (!imp || imp.status === "removed" || imp.status === "failed") {
    return { state: "load", label: "Load into CVAT" };
  }
  if (imp.status === "loaded")      return { state: "open", label: "Open in CVAT ↗" };
  return { state: "in_progress", label: "In Progress" };
}

// ─── Main component ───────────────────────────────────────────────────────────

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
    refetchInterval: (q) =>
      (q.state.data ?? []).some((r) => ACTIVE_JOB_STATUSES.includes(r.status)) ? 5000 : false,
  });

  const importQueryKey = (r: RunKeyFields) =>
    ["cvat-import", routeId, r.jobDefId, r.jobRunNum, r.segmentId, r.camera] as const;

  const importQueries = useQueries({
    queries: segmentRuns.map((run) => ({
      queryKey: importQueryKey(run),
      queryFn: () =>
        getCvatImportForRun({
          routeId,
          jobDefId:  run.jobDefId,
          jobRunNum: run.jobRunNum,
          segmentId: run.segmentId,
          camera:    run.camera,
        }),
      enabled: !!routeId,
      refetchInterval: (q: { state: { data?: CvatImport | null } }) =>
        q.state.data && CVAT_IN_PROGRESS_STATUSES.includes(q.state.data.status) ? 3000 : false,
    })),
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
    onSuccess: (newImport) => {
      const key = importQueryKey(newImport);
      queryClient.setQueryData<CvatImport | null>(key, newImport);
      return queryClient.invalidateQueries({ queryKey: key });
    },
  });

  const pendingKey = loadMutation.isPending && loadMutation.variables
    ? runKey(loadMutation.variables)
    : null;

  const importsByKey = new Map<string, CvatImport | null>();
  segmentRuns.forEach((run, i) => {
    importsByKey.set(runKey(run), importQueries[i]?.data ?? null);
  });
  const importsLoading = importQueries.some((q) => q.isLoading);
  const loading = runsLoading || importsLoading;

  return (
    <div style={CONTAINER_STYLE}>
      <div style={HEADING_STYLE}>Job Runs</div>

      {loading ? (
        <EmptyRow>Loading…</EmptyRow>
      ) : segmentRuns.length === 0 ? (
        <EmptyRow>No job runs for this segment.</EmptyRow>
      ) : (
        <div style={LIST_STYLE}>
          {segmentRuns.map((run) => {
            const key = runKey(run);
            const imp = importsByKey.get(key) ?? null;
            const action = resolveAction(run, imp, key === pendingKey);
            return (
              <JobRunRow
                key={key}
                run={run}
                imp={imp}
                action={action}
                onLoad={() => loadMutation.mutate(run)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Row ──────────────────────────────────────────────────────────────────────

interface RowProps {
  run: JobSegmentRun;
  imp: CvatImport | null;
  action: CvatAction;
  onLoad: () => void;
}

function JobRunRow({ run, imp, action, onLoad }: RowProps) {
  const statusColor = JOB_STATUS_COLOR[run.status];
  const isActive    = ACTIVE_JOB_STATUSES.includes(run.status);
  const showError   = imp?.status === "failed" && imp.errorMessage;

  return (
    <div style={ROW_STYLE}>
      <div style={ROW_INFO_STYLE}>
        <div style={ROW_STATUS_LINE_STYLE}>
          {isActive && <StatusDot color={statusColor} />}
          <span style={{ ...MONO_LABEL, color: statusColor }}>{run.status}</span>
        </div>
        <div style={ROW_META_STYLE}>
          run #{run.jobRunNum} · def {run.jobDefId}
        </div>
        <div style={ROW_CAMERA_STYLE}>{run.camera}</div>
        {showError && (
          <div title={imp.errorMessage ?? undefined} style={ROW_ERROR_STYLE}>
            {imp.errorMessage}
          </div>
        )}
      </div>

      <CvatActionButton action={action} taskUrl={imp?.taskUrl ?? null} onLoad={onLoad} />
    </div>
  );
}

// ─── Action button ────────────────────────────────────────────────────────────

interface ActionButtonProps {
  action: CvatAction;
  taskUrl: string | null;
  onLoad: () => void;
}

function CvatActionButton({ action, taskUrl, onLoad }: ActionButtonProps) {
  const style = { ...BUTTON_BASE, ...VARIANT_STYLE[action.state] };
  const leading = action.state === "in_progress"
    ? <StatusDot color="var(--accent-caution)" />
    : <CvatIcon size={12} />;

  if (action.state === "open" && taskUrl) {
    return (
      <a href={taskUrl} target="_blank" rel="noopener noreferrer" style={style}>
        {leading}{action.label}
      </a>
    );
  }

  const canClick = action.state === "load";
  return (
    <button type="button" disabled={!canClick} onClick={canClick ? onLoad : undefined} style={style}>
      {leading}{action.label}
    </button>
  );
}

// ─── Tiny visuals ─────────────────────────────────────────────────────────────

function EmptyRow({ children }: { children: ReactNode }) {
  return <div style={EMPTY_ROW_STYLE}>{children}</div>;
}

function StatusDot({ color }: { color: string }) {
  return <span style={{ ...STATUS_DOT_STYLE, backgroundColor: color }} />;
}

function CvatIcon({ size }: { size: number }) {
  return (
    <div style={{ ...CVAT_ICON_STYLE, width: size, height: size }}>
      <span style={{ ...CVAT_ICON_TEXT_STYLE, fontSize: `${Math.floor(size * 0.55)}px` }}>
        CV
      </span>
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const CONTAINER_STYLE: CSSProperties = {
  border: "1px solid var(--border-subtle)",
  backgroundColor: "var(--bg-surface)",
  padding: "var(--space-5)",
};

const HEADING_STYLE: CSSProperties = {
  fontSize: "10px",
  fontFamily: "var(--font-mono)",
  textTransform: "uppercase",
  letterSpacing: "0.09em",
  color: "var(--text-muted)",
  fontWeight: 600,
  marginBottom: "var(--space-4)",
};

const LIST_STYLE: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-2)",
};

const ROW_STYLE: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "var(--space-3)",
  padding: "var(--space-3) var(--space-4)",
  border: "1px solid var(--border-subtle)",
  backgroundColor: "var(--bg-elevated)",
};

const ROW_INFO_STYLE: CSSProperties = { flex: 1, minWidth: 0 };

const ROW_STATUS_LINE_STYLE: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "6px",
  marginBottom: "2px",
};

const ROW_META_STYLE: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "10px",
  color: "var(--text-secondary)",
};

const ROW_CAMERA_STYLE: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "9px",
  color: "var(--text-muted)",
  marginTop: "1px",
};

const ROW_ERROR_STYLE: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "9px",
  color: "var(--accent-alert)",
  marginTop: "2px",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const MONO_LABEL: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "9px",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.07em",
};

const BUTTON_BASE: CSSProperties = {
  flexShrink: 0,
  display: "flex",
  alignItems: "center",
  gap: "6px",
  padding: "var(--space-2) var(--space-3)",
  fontFamily: "var(--font-mono)",
  fontSize: "9px",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.07em",
  whiteSpace: "nowrap",
  textDecoration: "none",
};

const VARIANT_STYLE: Record<CvatActionState, CSSProperties> = {
  unavailable: {
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-muted)",
    border: "1px solid var(--border-subtle)",
    cursor: "not-allowed",
    opacity: 0.5,
  },
  load: {
    backgroundColor: "var(--bg-inverse)",
    color: "var(--text-on-inverse)",
    border: "1px solid var(--border-strong)",
    cursor: "pointer",
  },
  in_progress: {
    backgroundColor: "var(--bg-elevated)",
    color: "var(--accent-caution)",
    border: "1px solid var(--accent-caution)",
    cursor: "not-allowed",
    opacity: 0.7,
  },
  open: {
    backgroundColor: "var(--bg-inverse)",
    color: "var(--accent-cvat)",
    border: "1px solid var(--accent-cvat)",
    cursor: "pointer",
  },
};

const EMPTY_ROW_STYLE: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "11px",
  color: "var(--text-muted)",
  padding: "var(--space-3) 0",
};

const STATUS_DOT_STYLE: CSSProperties = {
  width: "5px",
  height: "5px",
  borderRadius: "50%",
  flexShrink: 0,
  display: "inline-block",
};

const CVAT_ICON_STYLE: CSSProperties = {
  backgroundColor: "var(--accent-cvat)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
};

const CVAT_ICON_TEXT_STYLE: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontWeight: 700,
  color: "var(--text-on-inverse)",
  letterSpacing: "0.03em",
  lineHeight: 1,
};
