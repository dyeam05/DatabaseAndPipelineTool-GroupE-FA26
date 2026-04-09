import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listRoutes } from "../api/routes";
import { getThumbnailUrl } from "../api/routes";
import type { Route, AnnotationStatus } from "../api/types";
import { listSegments } from "../api/segments";
// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { label: string; barColor: string; textColor: string; bg: string }
> = {
  recorded:        { label: "Recorded",        barColor: "var(--border-strong)",   textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)" },
  downloaded:      { label: "Downloaded",      barColor: "var(--text-primary)",    textColor: "var(--text-secondary)",       bg: "var(--status-recorded-bg)" },
  download_queue:  { label: "Queued",          barColor: "var(--text-primary)",    textColor: "var(--text-secondary)",       bg: "var(--status-recorded-bg)" },
  downloading:     { label: "Downloading",     barColor: "var(--accent-caution)",  textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  download_failed: { label: "Download Failed", barColor: "var(--accent-alert)",    textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)"    },
  segmented:       { label: "Segmented",       barColor: "var(--text-primary)",    textColor: "var(--text-secondary)",       bg: "var(--status-recorded-bg)" },
  annotating:      { label: "Annotating",      barColor: "var(--accent-caution)",  textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  annotated:       { label: "Annotated",       barColor: "var(--accent-go)",       textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  reviewed:        { label: "Reviewed",        barColor: "var(--accent-go)",       textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  failed:          { label: "Failed",          barColor: "var(--accent-alert)",    textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)"    },
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

function formatDuration(s: number): string {
  if (!s) return "—";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${String(s % 60).padStart(2, "0")}s`;
}

function formatDate(iso: string): string {
  if (!iso || iso === new Date(0).toISOString()) return "—";
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
  // Use the first segment (index 0) as the route thumbnail
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
      {status === "reviewed" && (
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

// ─── CompletionBar ────────────────────────────────────────────────────────────

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

function CompletionBar({ route }: { route: Route }) {
  const { segmentCount, annotatedSegmentCount, annotatingSegmentCount, failedSegmentCount } = route;
  const pct = segmentCount > 0 ? Math.round((annotatedSegmentCount / segmentCount) * 100) : 0;
  const isComplete = pct === 100;
  const hasMultipleStates = annotatingSegmentCount > 0 || failedSegmentCount > 0;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
          {annotatedSegmentCount} / {segmentCount} segments
        </span>
        <span
          style={{
            fontSize: "var(--text-sm)",
            fontWeight: 700,
            fontFamily: "var(--font-mono)",
            color: isComplete
              ? "var(--accent-go)"
              : failedSegmentCount === segmentCount
              ? "var(--accent-alert)"
              : "var(--text-primary)",
          }}
        >
          {pct}%
        </span>
      </div>

      <div style={{ height: "5px", backgroundColor: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", overflow: "hidden", display: "flex" }}>
        {annotatedSegmentCount > 0 && (
          <div style={{ width: `${(annotatedSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-go)", flexShrink: 0 }} />
        )}
        {annotatingSegmentCount > 0 && (
          <div style={{ width: `${(annotatingSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-caution)", flexShrink: 0 }} />
        )}
        {failedSegmentCount > 0 && (
          <div style={{ width: `${(failedSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-alert)", flexShrink: 0 }} />
        )}
      </div>

      {hasMultipleStates && (
        <div style={{ display: "flex", gap: "var(--space-4)", marginTop: "6px", flexWrap: "wrap" }}>
          {annotatedSegmentCount > 0 && <Pip color="var(--accent-go)" label={`${annotatedSegmentCount} done`} />}
          {annotatingSegmentCount > 0 && <Pip color="var(--accent-caution)" label={`${annotatingSegmentCount} in progress`} />}
          {failedSegmentCount > 0 && <Pip color="var(--accent-alert)" label={`${failedSegmentCount} failed`} />}
        </div>
      )}
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

function RouteCard({ route, onClick }: { route: Route; onClick: () => void }) {
  const [hovered, setHovered] = useState(false);
  const [copied, setCopied] = useState(false);

  function handleCopy(e: React.MouseEvent) {
    e.stopPropagation();
    navigator.clipboard.writeText(route.id).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

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
        <div style={{ position: "absolute", bottom: "var(--space-2)", right: "var(--space-2)", backgroundColor: "rgba(17,17,17,0.75)", backdropFilter: "blur(4px)", padding: "2px var(--space-2)" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", fontWeight: 700, color: "var(--text-on-inverse)", letterSpacing: "0.04em" }}>
            {route.segmentCount} seg
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

          <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "4px", fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", alignItems: "center", flexWrap: "wrap" }}>
            <span>{route.vehicleId}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span>{formatDate(route.recordedAt)}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span>{formatDuration(route.durationSeconds)}</span>
          </div>
        </div>

        <div style={{ height: "1px", backgroundColor: "var(--border-subtle)" }} />
        <CompletionBar route={route} />
      </div>
    </div>
  );
}

// ─── RouteDashboard ───────────────────────────────────────────────────────────

type SortKey = "date" | "status" | "segments" | "completion";

export default function RouteDashboard() {
  const navigate = useNavigate();
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortKey>("date");

  useEffect(() => {
  let cancelled = false;
  setLoading(true);
  setError(null);

  Promise.all([listRoutes(), listSegments()])
    .then(([routesData, segmentsData]) => {
      if (cancelled) return;

      const counts: Record<string, number> = {};

      for (const s of segmentsData) {
        counts[s.routeId] = (counts[s.routeId] || 0) + 1;
      }

      const enriched = routesData.map((r) => ({
        ...r,
        segmentCount: counts[r.id] || 0,
      }));

      setRoutes(enriched);
      setLoading(false);
    })
    .catch((err) => {
      if (!cancelled) {
        setError(err.message ?? "Failed to load routes");
        setLoading(false);
      }
    });

  return () => {
    cancelled = true;
  };
}, []);

  const stats = useMemo(() => {
    const totalSegments = routes.reduce((s, r) => s + r.segmentCount, 0);
    const totalAnnotated = routes.reduce((s, r) => s + r.annotatedSegmentCount, 0);
    return {
      total: routes.length,
      totalSegments,
      overallPct: totalSegments > 0 ? Math.round((totalAnnotated / totalSegments) * 100) : 0,
      pending: routes.filter((r) => r.status === "recorded" || r.status === "segmented" || r.status === "downloaded").length,
      inProgress: routes.filter((r) => r.status === "annotating" || r.status === "downloading").length,
      completed: routes.filter((r) => r.status === "annotated" || r.status === "reviewed").length,
      failed: routes.filter((r) => r.status === "failed" || r.status === "download_failed").length,
    };
  }, [routes]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let list = routes.filter((r) => {
      if (q && !r.id.toLowerCase().includes(q) && !r.vehicleId.toLowerCase().includes(q)) return false;
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      return true;
    });

    list.sort((a, b) => {
      switch (sortBy) {
        case "date": return new Date(b.recordedAt).getTime() - new Date(a.recordedAt).getTime();
        case "status": return a.status.localeCompare(b.status);
        case "segments": return b.segmentCount - a.segmentCount;
        case "completion": {
          const pA = a.segmentCount > 0 ? a.annotatedSegmentCount / a.segmentCount : 0;
          const pB = b.segmentCount > 0 ? b.annotatedSegmentCount / b.segmentCount : 0;
          return pB - pA;
        }
      }
    });
    return list;
  }, [routes, search, statusFilter, sortBy]);

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>
      {/* Header */}
      <div style={{ marginBottom: "var(--space-5)" }}>
        <h1 style={{ fontFamily: "var(--font-sans)", fontSize: "var(--text-2xl)", fontWeight: 600, color: "var(--text-primary)" }}>
          Routes
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: "2px" }}>
          Annotation pipeline overview
        </p>
      </div>

      {/* Stat strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "1px", backgroundColor: "var(--border-subtle)", border: "1px solid var(--border-subtle)", marginBottom: "var(--space-5)" }}>
        <StatCard label="Total Routes" value={loading ? "…" : stats.total} />
        <StatCard label="Segments" value={loading ? "…" : stats.totalSegments} />
        <StatCard label="Overall" value={loading ? "…" : `${stats.overallPct}%`} />
        <StatCard label="Pending" value={loading ? "…" : stats.pending} />
        <StatCard label="In Progress" value={loading ? "…" : stats.inProgress} accentColor={stats.inProgress > 0 ? "var(--accent-caution)" : undefined} />
        <StatCard label="Completed" value={loading ? "…" : stats.completed} accentColor={stats.completed > 0 ? "var(--accent-go)" : undefined} />
        <StatCard label="Failed" value={loading ? "…" : stats.failed} accentColor={stats.failed > 0 ? "var(--accent-alert)" : undefined} />
      </div>

      {/* Filter bar */}
      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-4)", flexWrap: "wrap" }}>
        <input
          type="search"
          placeholder="Search route ID or vehicle…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: "200px", padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none" }}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="all">All Statuses</option>
          <option value="download_queue">Queued</option>
          <option value="downloading">Downloading</option>
          <option value="downloaded">Downloaded</option>
          <option value="download_failed">Download Failed</option>
          <option value="segmented">Segmented</option>
          <option value="annotating">Annotating</option>
          <option value="annotated">Annotated</option>
          <option value="reviewed">Reviewed</option>
          <option value="failed">Failed</option>
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortKey)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="date">Sort: Date</option>
          <option value="status">Sort: Status</option>
          <option value="segments">Sort: Segments</option>
          <option value="completion">Sort: Completion %</option>
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
              <RouteCard key={route.id} route={route} onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}`)} />
            ))}
          </div>
        )
      )}
    </div>
  );
}
