import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";

// ─── Mock thumbnails (served from public/mock_images/) ───────────────────────

const MOCK_IMAGES = [
  "/mock_images/00a05dec30654b82ba555e641cb9d486.png",
  "/mock_images/00a56e44dfff4c6fa8215ded1fb91dbf.png",
  "/mock_images/00bb829c9bc142f696491b040b18b6b6.png",
  "/mock_images/00bcea58ac984cf5bfb3de6982da313b.png",
  "/mock_images/00c2a80295774757b4494e014ca54d33.png",
  "/mock_images/00d60e52ddc340a78aeec290358286bf.png",
  "/mock_images/00e0a16f0b594d92a76e7d5fac05f098.png",
  "/mock_images/00e595c4cd24453ba6e72712911b3276.png",
  "/mock_images/00ed2361fe004f2c9fb04b97ad15e6c0.png",
  "/mock_images/00ef1795960d49448bc5924119624051.png",
  "/mock_images/00f52b1f66564c6797d12a72f135ddff.png",
  "/mock_images/00fe1eef2df44ce085ce4553f8dd2487.png",
];

// ─── Types ────────────────────────────────────────────────────────────────────

type AnnotationStatus =
  | "recorded"
  | "segmented"
  | "annotating"
  | "annotated"
  | "reviewed"
  | "failed";

interface Route {
  id: string;
  vehicleId: string;
  recordedAt: string;
  durationSeconds: number;
  segmentCount: number;
  annotatedSegmentCount: number;
  annotatingSegmentCount: number;
  failedSegmentCount: number;
  status: AnnotationStatus;
  thumbnailIndex: number;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_ROUTES: Route[] = [
  {
    id: "2f4b8c1d|2024-03-15|09:42:18",
    vehicleId: "comma-3x-001",
    recordedAt: "2024-03-15T09:42:18Z",
    durationSeconds: 1847,
    segmentCount: 24,
    annotatedSegmentCount: 24,
    annotatingSegmentCount: 0,
    failedSegmentCount: 0,
    status: "reviewed",
    thumbnailIndex: 0,
  },
  {
    id: "7a9e3f2c|2024-03-15|14:22:05",
    vehicleId: "comma-3x-002",
    recordedAt: "2024-03-15T14:22:05Z",
    durationSeconds: 923,
    segmentCount: 12,
    annotatedSegmentCount: 9,
    annotatingSegmentCount: 2,
    failedSegmentCount: 0,
    status: "annotating",
    thumbnailIndex: 1,
  },
  {
    id: "b1c5d8e9|2024-03-14|11:05:33",
    vehicleId: "comma-3x-001",
    recordedAt: "2024-03-14T11:05:33Z",
    durationSeconds: 3201,
    segmentCount: 42,
    annotatedSegmentCount: 42,
    annotatingSegmentCount: 0,
    failedSegmentCount: 0,
    status: "annotated",
    thumbnailIndex: 2,
  },
  {
    id: "c3d7f0a2|2024-03-14|08:15:44",
    vehicleId: "comma-3x-003",
    recordedAt: "2024-03-14T08:15:44Z",
    durationSeconds: 512,
    segmentCount: 7,
    annotatedSegmentCount: 0,
    annotatingSegmentCount: 0,
    failedSegmentCount: 7,
    status: "failed",
    thumbnailIndex: 3,
  },
  {
    id: "e5f2a1b3|2024-03-13|16:30:00",
    vehicleId: "comma-3x-002",
    recordedAt: "2024-03-13T16:30:00Z",
    durationSeconds: 2104,
    segmentCount: 28,
    annotatedSegmentCount: 0,
    annotatingSegmentCount: 0,
    failedSegmentCount: 0,
    status: "segmented",
    thumbnailIndex: 4,
  },
  {
    id: "f8g4h2i1|2024-03-13|09:00:00",
    vehicleId: "comma-3x-004",
    recordedAt: "2024-03-13T09:00:00Z",
    durationSeconds: 741,
    segmentCount: 10,
    annotatedSegmentCount: 0,
    annotatingSegmentCount: 0,
    failedSegmentCount: 0,
    status: "recorded",
    thumbnailIndex: 5,
  },
  {
    id: "a2b9c6d4|2024-03-12|13:45:22",
    vehicleId: "comma-3x-001",
    recordedAt: "2024-03-12T13:45:22Z",
    durationSeconds: 1655,
    segmentCount: 22,
    annotatedSegmentCount: 15,
    annotatingSegmentCount: 4,
    failedSegmentCount: 1,
    status: "annotating",
    thumbnailIndex: 6,
  },
  {
    id: "d6e3f9g1|2024-03-12|07:20:11",
    vehicleId: "comma-3x-003",
    recordedAt: "2024-03-12T07:20:11Z",
    durationSeconds: 2980,
    segmentCount: 39,
    annotatedSegmentCount: 39,
    annotatingSegmentCount: 0,
    failedSegmentCount: 0,
    status: "reviewed",
    thumbnailIndex: 7,
  },
];

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  AnnotationStatus,
  { label: string; barColor: string; textColor: string; bg: string }
> = {
  recorded:   { label: "Recorded",   barColor: "var(--border-strong)",   textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)" },
  segmented:  { label: "Segmented",  barColor: "var(--text-primary)",    textColor: "var(--text-secondary)",       bg: "var(--status-recorded-bg)" },
  annotating: { label: "Annotating", barColor: "var(--accent-caution)",  textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  annotated:  { label: "Annotated",  barColor: "var(--accent-go)",       textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  reviewed:   { label: "Reviewed",   barColor: "var(--accent-go)",       textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  failed:     { label: "Failed",     barColor: "var(--accent-alert)",    textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)"    },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDuration(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${String(s % 60).padStart(2, "0")}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// function truncateId(id: string, len = 20): string {
//   return id.length > len ? id.substring(0, len) + "…" : id;
// }

// ─── StatusBadge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: AnnotationStatus }) {
  const cfg = STATUS_CONFIG[status];
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

function CompletionBar({ route }: { route: Route }) {
  const { segmentCount, annotatedSegmentCount, annotatingSegmentCount, failedSegmentCount } = route;
  const pct = segmentCount > 0 ? Math.round((annotatedSegmentCount / segmentCount) * 100) : 0;
  const isComplete = pct === 100;
  const hasMultipleStates =
    annotatingSegmentCount > 0 || failedSegmentCount > 0;

  return (
    <div>
      {/* Label row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "6px",
        }}
      >
        <span
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--text-secondary)",
            fontFamily: "var(--font-mono)",
          }}
        >
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

      {/* Progress track */}
      <div
        style={{
          height: "5px",
          backgroundColor: "var(--bg-elevated)",
          border: "1px solid var(--border-subtle)",
          overflow: "hidden",
          display: "flex",
        }}
      >
        {annotatedSegmentCount > 0 && (
          <div
            style={{
              width: `${(annotatedSegmentCount / segmentCount) * 100}%`,
              backgroundColor: "var(--accent-go)",
              flexShrink: 0,
            }}
          />
        )}
        {annotatingSegmentCount > 0 && (
          <div
            style={{
              width: `${(annotatingSegmentCount / segmentCount) * 100}%`,
              backgroundColor: "var(--accent-caution)",
              flexShrink: 0,
            }}
          />
        )}
        {failedSegmentCount > 0 && (
          <div
            style={{
              width: `${(failedSegmentCount / segmentCount) * 100}%`,
              backgroundColor: "var(--accent-alert)",
              flexShrink: 0,
            }}
          />
        )}
      </div>

      {/* Inline legend — only when multiple states coexist */}
      {hasMultipleStates && (
        <div
          style={{
            display: "flex",
            gap: "var(--space-4)",
            marginTop: "6px",
            flexWrap: "wrap",
          }}
        >
          {annotatedSegmentCount > 0 && (
            <Pip color="var(--accent-go)" label={`${annotatedSegmentCount} done`} />
          )}
          {annotatingSegmentCount > 0 && (
            <Pip color="var(--accent-caution)" label={`${annotatingSegmentCount} in progress`} />
          )}
          {failedSegmentCount > 0 && (
            <Pip color="var(--accent-alert)" label={`${failedSegmentCount} failed`} />
          )}
        </div>
      )}
    </div>
  );
}

function Pip({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <div style={{ width: "6px", height: "6px", backgroundColor: color, flexShrink: 0 }} />
      <span
        style={{
          fontSize: "10px",
          color: "var(--text-muted)",
          fontFamily: "var(--font-mono)",
        }}
      >
        {label}
      </span>
    </div>
  );
}

// ─── StatCard ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  accentColor,
}: {
  label: string;
  value: number | string;
  accentColor?: string;
}) {
  return (
    <div
      style={{
        padding: "var(--space-3) var(--space-4)",
        backgroundColor: "var(--bg-surface)",
      }}
    >
      <div
        style={{
          fontSize: "var(--text-xl)",
          fontWeight: 700,
          fontFamily: "var(--font-mono)",
          color: accentColor ?? "var(--text-primary)",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: "10px",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.09em",
          marginTop: "var(--space-1)",
          fontWeight: 600,
        }}
      >
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

  const thumbnail = MOCK_IMAGES[route.thumbnailIndex % MOCK_IMAGES.length];

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
      {/* ── Thumbnail with overlaid status badge ── */}
      <div
        style={{
          position: "relative",
          height: "140px",
          overflow: "hidden",
          flexShrink: 0,
        }}
      >
        <img
          src={thumbnail}
          alt="Route thumbnail"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center",
            display: "block",
            filter: hovered ? "brightness(1.05)" : "brightness(0.95)",
          }}
        />
        {/* Status badge — bottom-left of image */}
        <div
          style={{
            position: "absolute",
            bottom: "var(--space-2)",
            left: "var(--space-2)",
          }}
        >
          <StatusBadge status={route.status} />
        </div>
        {/* Segment count chip — bottom-right */}
        <div
          style={{
            position: "absolute",
            bottom: "var(--space-2)",
            right: "var(--space-2)",
            backgroundColor: "rgba(17,17,17,0.75)",
            backdropFilter: "blur(4px)",
            padding: "2px var(--space-2)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              fontWeight: 700,
              color: "var(--text-on-inverse)",
              letterSpacing: "0.04em",
            }}
          >
            {route.segmentCount} seg
          </span>
        </div>
      </div>

      {/* ── Card body ── */}
      <div
        style={{
          padding: "var(--space-3) var(--space-4)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-3)",
        }}
      >
        {/* Route ID + copy */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-xs)",
                fontWeight: 700,
                color: "var(--text-primary)",
                letterSpacing: "-0.01em",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {(route.id)}
            </span>
            <button
              onClick={handleCopy}
              title="Copy route ID"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "0 3px",
                color: copied ? "var(--accent-go)" : "var(--text-muted)",
                fontSize: "var(--text-xs)",
                fontFamily: "var(--font-mono)",
                flexShrink: 0,
                lineHeight: 1,
              }}
            >
              {copied ? "✓" : "⎘"}
            </button>
          </div>
          {/* Single compact meta row */}
          <div
            style={{
              display: "flex",
              gap: "var(--space-2)",
              marginTop: "4px",
              fontSize: "10px",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <span>{route.vehicleId}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span>{formatDate(route.recordedAt)}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span>{formatDuration(route.durationSeconds)}</span>
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: "1px", backgroundColor: "var(--border-subtle)" }} />

        {/* Completion */}
        <CompletionBar route={route} />
      </div>
    </div>
  );
}

// ─── RouteDashboard ───────────────────────────────────────────────────────────

type SortKey = "date" | "status" | "segments" | "completion";

export default function RouteDashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<AnnotationStatus | "all">("all");
  const [sortBy, setSortBy] = useState<SortKey>("date");

  const stats = useMemo(() => {
    const totalSegments = MOCK_ROUTES.reduce((s, r) => s + r.segmentCount, 0);
    const totalAnnotated = MOCK_ROUTES.reduce((s, r) => s + r.annotatedSegmentCount, 0);
    return {
      total: MOCK_ROUTES.length,
      totalSegments,
      overallPct: totalSegments > 0 ? Math.round((totalAnnotated / totalSegments) * 100) : 0,
      pending: MOCK_ROUTES.filter((r) => r.status === "recorded" || r.status === "segmented").length,
      inProgress: MOCK_ROUTES.filter((r) => r.status === "annotating").length,
      completed: MOCK_ROUTES.filter((r) => r.status === "annotated" || r.status === "reviewed").length,
      failed: MOCK_ROUTES.filter((r) => r.status === "failed").length,
    };
  }, []);

  const routes = useMemo(() => {
    const q = search.trim().toLowerCase();
    let filtered = MOCK_ROUTES.filter((r) => {
      if (q && !r.id.toLowerCase().includes(q) && !r.vehicleId.toLowerCase().includes(q))
        return false;
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      return true;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "date":
          return new Date(b.recordedAt).getTime() - new Date(a.recordedAt).getTime();
        case "status":
          return a.status.localeCompare(b.status);
        case "segments":
          return b.segmentCount - a.segmentCount;
        case "completion": {
          const pA = a.segmentCount > 0 ? a.annotatedSegmentCount / a.segmentCount : 0;
          const pB = b.segmentCount > 0 ? b.annotatedSegmentCount / b.segmentCount : 0;
          return pB - pA;
        }
      }
    });

    return filtered;
  }, [search, statusFilter, sortBy]);

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>
      {/* Header */}
      <div style={{ marginBottom: "var(--space-5)" }}>
        <h1
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "var(--text-2xl)",
            fontWeight: 600,
            color: "var(--text-primary)",
          }}
        >
          Routes
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: "2px" }}>
          Annotation pipeline overview
        </p>
      </div>

      {/* Stat strip */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))",
          gap: "1px",
          backgroundColor: "var(--border-subtle)",
          border: "1px solid var(--border-subtle)",
          marginBottom: "var(--space-5)",
        }}
      >
        <StatCard label="Total Routes" value={stats.total} />
        <StatCard label="Segments" value={stats.totalSegments} />
        <StatCard label="Overall" value={`${stats.overallPct}%`} />
        <StatCard label="Pending" value={stats.pending} />
        <StatCard
          label="In Progress"
          value={stats.inProgress}
          accentColor={stats.inProgress > 0 ? "var(--accent-caution)" : undefined}
        />
        <StatCard
          label="Completed"
          value={stats.completed}
          accentColor={stats.completed > 0 ? "var(--accent-go)" : undefined}
        />
        <StatCard
          label="Failed"
          value={stats.failed}
          accentColor={stats.failed > 0 ? "var(--accent-alert)" : undefined}
        />
      </div>

      {/* Filter bar */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          marginBottom: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <input
          type="search"
          placeholder="Search route ID or vehicle…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            minWidth: "200px",
            padding: "var(--space-2) var(--space-3)",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-sm)",
            color: "var(--text-primary)",
            outline: "none",
          }}
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as AnnotationStatus | "all")}
          style={{
            padding: "var(--space-2) var(--space-3)",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            fontSize: "var(--text-sm)",
            color: "var(--text-primary)",
            outline: "none",
            cursor: "pointer",
          }}
        >
          <option value="all">All Statuses</option>
          <option value="recorded">Recorded</option>
          <option value="segmented">Segmented</option>
          <option value="annotating">Annotating</option>
          <option value="annotated">Annotated</option>
          <option value="reviewed">Reviewed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortKey)}
          style={{
            padding: "var(--space-2) var(--space-3)",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            fontSize: "var(--text-sm)",
            color: "var(--text-primary)",
            outline: "none",
            cursor: "pointer",
          }}
        >
          <option value="date">Sort: Date</option>
          <option value="status">Sort: Status</option>
          <option value="segments">Sort: Segments</option>
          <option value="completion">Sort: Completion %</option>
        </select>
      </div>

      {/* Count */}
      <div
        style={{
          fontSize: "10px",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.09em",
          fontWeight: 600,
          marginBottom: "var(--space-4)",
        }}
      >
        {routes.length} route{routes.length !== 1 ? "s" : ""}
        {statusFilter !== "all" ? ` · ${STATUS_CONFIG[statusFilter].label}` : ""}
      </div>

      {/* Grid */}
      {routes.length === 0 ? (
        <div
          style={{
            padding: "var(--space-12)",
            textAlign: "center",
            color: "var(--text-muted)",
            border: "1px dashed var(--border-subtle)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-sm)",
          }}
        >
          No routes match your filters.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "var(--space-4)",
          }}
        >
          {routes.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
