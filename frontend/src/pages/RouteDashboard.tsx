import { useState, useMemo } from "react";
import { ImportRouteButton } from "../components/ImportRouteButton";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listRoutes, getThumbnailUrl } from "../api/routes";
import { listSegments } from "../api/segments";
import { listJobRuns } from "../api/job_runs";
import type { Route, Segment, JobRun } from "../api/types";
import { ROUTE_TERMINAL_STATUSES, SEGMENT_TERMINAL_STATUSES, JOB_TERMINAL_STATUSES } from "../api/types";

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { label: string; barColor: string; textColor: string; bg: string }
> = {
  "download queue": { label: "Queued",       barColor: "var(--text-primary)",   textColor: "var(--text-secondary)",      bg: "var(--status-recorded-bg)" },
  downloading:      { label: "Downloading",  barColor: "var(--accent-caution)", textColor: "var(--status-caution-text)", bg: "var(--status-caution-bg)"  },
  "upload queue":   { label: "Upload Queue", barColor: "var(--text-primary)",   textColor: "var(--text-secondary)",      bg: "var(--status-recorded-bg)" },
  uploading:        { label: "Uploading",    barColor: "var(--accent-caution)", textColor: "var(--status-caution-text)", bg: "var(--status-caution-bg)"  },
  uploaded:         { label: "Uploaded",     barColor: "var(--accent-go)",      textColor: "var(--status-go-text)",      bg: "var(--status-go-bg)"       },
  failed:           { label: "Failed",       barColor: "var(--accent-alert)",   textColor: "var(--status-alert-text)",   bg: "var(--status-alert-bg)"    },
};

const DEFAULT_STATUS_CFG = {
  label: "Unknown",
  barColor: "var(--border-strong)",
  textColor: "var(--text-secondary)",
  bg: "var(--status-recorded-bg)",
};

function getStatusCfg(status: string) {
  return STATUS_CONFIG[status] ?? DEFAULT_STATUS_CFG;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─── Thumbnail ────────────────────────────────────────────────────────────────

function RouteThumbnail({ route, hovered }: { route: Route; hovered: boolean }) {
  const [errored, setErrored] = useState(false);
  const src = getThumbnailUrl(route.id, 0);

  return errored ? (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "var(--bg-elevated)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        No preview
      </span>
    </div>
  ) : (
    <img
      src={src}
      alt="Route thumbnail"
      onError={() => setErrored(true)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: "center",
        display: "block",
        filter: hovered ? "brightness(1.05)" : "brightness(0.95)",
      }}
    />
  );
}

// ─── StatusBadge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cfg = getStatusCfg(status);
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        paddingLeft: "var(--space-2)",
        paddingRight: "var(--space-3)",
        paddingTop: "3px",
        paddingBottom: "3px",
        borderLeft: `3px solid ${cfg.barColor}`,
        backgroundColor: cfg.bg,
        backdropFilter: "blur(4px)",
      }}
    >
      {status === "uploaded" && (
        <span style={{ color: cfg.textColor, fontSize: "9px", fontWeight: 800 }}>✓</span>
      )}
      <span
        style={{
          fontSize: "9px",
          fontWeight: 700,
          color: cfg.textColor,
          letterSpacing: "0.07em",
          textTransform: "uppercase",
        }}
      >
        {cfg.label}
      </span>
    </div>
  );
}

// ─── LiveDot ──────────────────────────────────────────────────────────────────

function LiveDot() {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 6px",
        backgroundColor: "var(--status-caution-bg)",
        border: "1px solid var(--accent-caution)",
      }}
    >
      <span
        style={{
          width: "5px",
          height: "5px",
          borderRadius: "50%",
          backgroundColor: "var(--accent-caution)",
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontSize: "9px",
          fontWeight: 700,
          color: "var(--status-caution-text)",
          letterSpacing: "0.07em",
          textTransform: "uppercase",
          fontFamily: "var(--font-mono)",
        }}
      >
        Live
      </span>
    </span>
  );
}

// ─── Pip ──────────────────────────────────────────────────────────────────────

function Pip({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <div style={{ width: "6px", height: "6px", backgroundColor: color, flexShrink: 0 }} />
      <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {label}
      </span>
    </div>
  );
}

// ─── UploadBar ────────────────────────────────────────────────────────────────

function UploadBar({ segments, jobRuns }: { segments: Segment[]; jobRuns: JobRun[] }) {
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

// ─── StatCard ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, accentColor }: { label: string; value: number | string; accentColor?: string }) {
  return (
    <div style={{ padding: "var(--space-3) var(--space-4)", backgroundColor: "var(--bg-surface)" }}>
      <div style={{ fontSize: "var(--text-xl)", fontWeight: 700, fontFamily: "var(--font-mono)", color: accentColor ?? "var(--text-primary)", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.09em", marginTop: "var(--space-1)", fontWeight: 600 }}>
        {label}
      </div>
    </div>
  );
}

// ─── RouteCard ────────────────────────────────────────────────────────────────

function RouteCard({
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

// ─── RouteDashboard ───────────────────────────────────────────────────────────

type SortKey = "date" | "status" | "segments";

export default function RouteDashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortKey>("date");

  // ── Queries with live polling ───────────────────────────────────────────────

  const routesQuery = useQuery({
    queryKey: ["routes"],
    queryFn: listRoutes,
    refetchInterval: (query) => {
      const routes = query.state.data ?? [];
      // Active routes poll every 5s; fall back to 30s so newly created routes are detected
      return routes.some((r) => !ROUTE_TERMINAL_STATUSES.includes(r.status)) ? 5000 : 30000;
    },
  });

  const segmentsQuery = useQuery({
    queryKey: ["segments"],
    queryFn: listSegments,
    refetchInterval: (query) => {
      const segs = query.state.data ?? [];
      return segs.some((s) => !SEGMENT_TERMINAL_STATUSES.includes(s.status)) ? 5000 : false;
    },
  });

  const jobRunsQuery = useQuery({
    queryKey: ["jobRuns"],
    queryFn: listJobRuns,
    refetchInterval: (query) => {
      const runs = query.state.data ?? [];
      if (runs.length === 0) return 10000;
      return runs.some((r) => !JOB_TERMINAL_STATUSES.includes(r.status)) ? 3000 : false;
    },
  });

  const routes = routesQuery.data ?? [];
  const segments = segmentsQuery.data ?? [];
  const jobRuns = jobRunsQuery.data ?? [];
  const loading = routesQuery.isLoading;
  const error = routesQuery.error ? (routesQuery.error as Error).message ?? "Failed to load routes" : null;
  const isPolling = routesQuery.isFetching || segmentsQuery.isFetching || jobRunsQuery.isFetching;

  // ── Computed per-route maps ─────────────────────────────────────────────────

  const segmentsByRoute = useMemo(() => {
    const map: Record<string, Segment[]> = {};
    for (const s of segments) {
      if (!map[s.routeId]) map[s.routeId] = [];
      map[s.routeId].push(s);
    }
    return map;
  }, [segments]);

  const jobRunsByRoute = useMemo(() => {
    const map: Record<string, JobRun[]> = {};
    for (const j of jobRuns) {
      if (!map[j.routeId]) map[j.routeId] = [];
      map[j.routeId].push(j);
    }
    return map;
  }, [jobRuns]);

  // ── Stats ───────────────────────────────────────────────────────────────────

  const stats = useMemo(() => {
    const totalSegments = segments.length;
    const totalUploaded = segments.filter((s) => s.status === "uploaded").length;
    return {
      total: routes.length,
      totalSegments,
      overallPct: totalSegments > 0 ? Math.round((totalUploaded / totalSegments) * 100) : 0,
      pending: routes.filter((r) => r.status === "download queue" || r.status === "upload queue").length,
      inProgress: routes.filter((r) => {
        const routeActive = r.status === "downloading" || r.status === "uploading";
        const jobActive = (jobRunsByRoute[r.id] ?? []).some((j) => j.status === "queued" || j.status === "running");
        return routeActive || jobActive;
      }).length,
      completed: routes.filter((r) => {
        if (r.status !== "uploaded") return false;
        const runs = jobRunsByRoute[r.id] ?? [];
        return runs.length === 0 || runs.every((j) => JOB_TERMINAL_STATUSES.includes(j.status));
      }).length,
      failed: routes.filter((r) => r.status === "failed").length,
    };
  }, [routes, segments, jobRunsByRoute]);

  // ── Filter + sort ───────────────────────────────────────────────────────────

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let list = routes.filter((r) => {
      if (q && !r.id.toLowerCase().includes(q)) return false;
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      return true;
    });

    list.sort((a, b) => {
      switch (sortBy) {
        case "date":    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case "status":  return a.status.localeCompare(b.status);
        case "segments": return (segmentsByRoute[b.id]?.length ?? 0) - (segmentsByRoute[a.id]?.length ?? 0);
      }
    });
    return list;
  }, [routes, search, statusFilter, sortBy, segmentsByRoute]);

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>
      {/* Header */}
      <div style={{ marginBottom: "var(--space-5)", display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontFamily: "var(--font-sans)", fontSize: "var(--text-2xl)", fontWeight: 600, color: "var(--text-primary)" }}>
            Routes
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: "2px" }}>
            Annotation pipeline overview
          </p>
        </div>
        {isPolling && <LiveDot />}
        <ImportRouteButton onImport={(_id) => {}} />
      </div>

      {/* Stat strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "1px", backgroundColor: "var(--border-subtle)", border: "1px solid var(--border-subtle)", marginBottom: "var(--space-5)" }}>
        <StatCard label="Total Routes"  value={loading ? "…" : stats.total} />
        <StatCard label="Segments"      value={loading ? "…" : stats.totalSegments} />
        <StatCard label="Uploaded"      value={loading ? "…" : `${stats.overallPct}%`} />
        <StatCard label="Pending"       value={loading ? "…" : stats.pending} />
        <StatCard label="In Progress"   value={loading ? "…" : stats.inProgress}  accentColor={stats.inProgress  > 0 ? "var(--accent-caution)" : undefined} />
        <StatCard label="Completed"     value={loading ? "…" : stats.completed}   accentColor={stats.completed   > 0 ? "var(--accent-go)"      : undefined} />
        <StatCard label="Failed"        value={loading ? "…" : stats.failed}      accentColor={stats.failed      > 0 ? "var(--accent-alert)"   : undefined} />
      </div>

      {/* Filter bar */}
      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-4)", flexWrap: "wrap" }}>
        <input
          type="search"
          placeholder="Search route ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: "200px", padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none" }}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="all">All Statuses</option>
          <option value="download queue">Queued</option>
          <option value="downloading">Downloading</option>
          <option value="upload queue">Upload Queue</option>
          <option value="uploading">Uploading</option>
          <option value="uploaded">Uploaded</option>
          <option value="failed">Failed</option>
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortKey)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="date">Sort: Date</option>
          <option value="status">Sort: Status</option>
          <option value="segments">Sort: Segments</option>
        </select>
      </div>

      {/* Count */}
      <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.09em", fontWeight: 600, marginBottom: "var(--space-4)" }}>
        {loading ? "Loading…" : `${filtered.length} route${filtered.length !== 1 ? "s" : ""}${statusFilter !== "all" ? ` · ${getStatusCfg(statusFilter).label}` : ""}`}
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: "var(--space-4)", border: "1px solid var(--accent-alert)", backgroundColor: "var(--status-alert-bg)", color: "var(--status-alert-text)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", marginBottom: "var(--space-4)" }}>
          Error: {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !error && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "var(--space-4)" }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", height: "240px", opacity: 0.4 }} />
          ))}
        </div>
      )}

      {/* Grid */}
      {!loading && !error && (
        filtered.length === 0 ? (
          <div style={{ padding: "var(--space-12)", textAlign: "center", color: "var(--text-muted)", border: "1px dashed var(--border-subtle)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>
            No routes match your filters.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "var(--space-4)" }}>
            {filtered.map((route) => (
              <RouteCard
                key={route.id}
                route={route}
                segments={segmentsByRoute[route.id] ?? []}
                jobRuns={jobRunsByRoute[route.id] ?? []}
                onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}`)}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}
