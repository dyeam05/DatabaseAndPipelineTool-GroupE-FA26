import React, { useState, useMemo, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getRoute, getThumbnailUrl } from "../api/routes";
import { listSegmentsForRoute } from "../api/segments";
import type { Route, Segment, SegmentStatus } from "../api/types";

// ─── Status config ────────────────────────────────────────────────────────────

const SEG_STATUS_CONFIG: Record<
  SegmentStatus,
  { label: string; timelineColor: string; textColor: string; bg: string; borderColor: string }
> = {
  recorded:   { label: "Recorded",   timelineColor: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)", borderColor: "var(--border-strong)"  },
  annotating: { label: "Annotating", timelineColor: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)",  borderColor: "var(--accent-caution)" },
  annotated:  { label: "Annotated",  timelineColor: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)",       borderColor: "var(--accent-go)"      },
  reviewed:   { label: "Reviewed",   timelineColor: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)",       borderColor: "var(--accent-go)"      },
  failed:     { label: "Failed",     timelineColor: "var(--accent-alert)",   textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)",    borderColor: "var(--accent-alert)"   },
};

const ROUTE_STATUS_COLORS: Record<string, string> = {
  recorded:        "var(--status-recorded-text)",
  downloaded:      "var(--text-secondary)",
  download_queue:  "var(--text-secondary)",
  downloading:     "var(--accent-caution)",
  download_failed: "var(--accent-alert)",
  segmented:       "var(--text-secondary)",
  annotating:      "var(--accent-caution)",
  annotated:       "var(--accent-go)",
  reviewed:        "var(--accent-go)",
  failed:          "var(--accent-alert)",
};

const ROUTE_STATUS_LABELS: Record<string, string> = {
  recorded: "Recorded", downloaded: "Downloaded", download_queue: "Queued",
  downloading: "Downloading", download_failed: "Download Failed",
  segmented: "Segmented", annotating: "Annotating", annotated: "Annotated",
  reviewed: "Reviewed", failed: "Failed",
};

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
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function formatOffset(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

// ─── SegmentThumbnail ─────────────────────────────────────────────────────────

function SegmentThumbnail({ segment, hovered }: { segment: Segment; hovered: boolean }) {
  const [errored, setErrored] = useState(false);
  const src = getThumbnailUrl(segment.routeId, segment.index);

  if (errored) {
    return (
      <div style={{ width: "100%", height: "100%", backgroundColor: "var(--bg-elevated)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          No preview
        </span>
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={`Segment ${segment.index}`}
      onError={() => setErrored(true)}
      style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", display: "block", filter: hovered ? "brightness(1.05)" : "brightness(0.9)", transition: "filter var(--transition-fast)" }}
    />
  );
}

// ─── SegmentTimeline ──────────────────────────────────────────────────────────

function SegmentTimeline({ segments }: { segments: Segment[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  return (
    <div>
      <div style={{ display: "flex", gap: "2px", flexWrap: "wrap" }}>
        {segments.map((seg) => {
          const cfg = SEG_STATUS_CONFIG[seg.status] ?? SEG_STATUS_CONFIG.recorded;
          const isHovered = hoveredIdx === seg.index;
          return (
            <div
              key={seg.index}
              onMouseEnter={() => setHoveredIdx(seg.index)}
              onMouseLeave={() => setHoveredIdx(null)}
              title={`#${String(seg.index).padStart(2, "0")} · ${cfg.label} · ${formatOffset(seg.startSeconds)}`}
              style={{ width: "16px", height: "8px", backgroundColor: isHovered ? "var(--text-on-inverse)" : cfg.timelineColor, flexShrink: 0, cursor: "default", transition: "background-color 80ms ease" }}
            />
          );
        })}
      </div>
      {hoveredIdx !== null && segments[hoveredIdx] && (
        <div style={{ marginTop: "6px", fontSize: "10px", fontFamily: "var(--font-mono)", color: "rgba(255,255,255,0.5)", letterSpacing: "0.04em" }}>
          seg{" "}
          <span style={{ color: "var(--text-on-inverse)", fontWeight: 700 }}>#{String(hoveredIdx).padStart(2, "0")}</span>
          {" · "}
          <span style={{ color: (SEG_STATUS_CONFIG[segments[hoveredIdx].status] ?? SEG_STATUS_CONFIG.recorded).timelineColor }}>
            {(SEG_STATUS_CONFIG[segments[hoveredIdx].status] ?? SEG_STATUS_CONFIG.recorded).label}
          </span>
          {" · "}
          {formatOffset(segments[hoveredIdx].startSeconds)}
        </div>
      )}
    </div>
  );
}

// ─── HeroCompletionBar ────────────────────────────────────────────────────────

function HeroCompletionBar({ route }: { route: Route }) {
  const { segmentCount, annotatedSegmentCount, annotatingSegmentCount, failedSegmentCount } = route;
  const pct = segmentCount > 0 ? Math.round((annotatedSegmentCount / segmentCount) * 100) : 0;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          {annotatedSegmentCount} / {segmentCount} segments annotated
        </span>
        <span style={{ fontSize: "var(--text-sm)", fontWeight: 700, fontFamily: "var(--font-mono)", color: pct === 100 ? "var(--accent-go)" : pct === 0 ? "rgba(255,255,255,0.3)" : "var(--accent-caution)" }}>
          {pct}%
        </span>
      </div>
      <div style={{ height: "4px", backgroundColor: "rgba(255,255,255,0.1)", display: "flex", overflow: "hidden" }}>
        {annotatedSegmentCount > 0 && <div style={{ width: `${(annotatedSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-go)", flexShrink: 0 }} />}
        {annotatingSegmentCount > 0 && <div style={{ width: `${(annotatingSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-caution)", flexShrink: 0 }} />}
        {failedSegmentCount > 0 && <div style={{ width: `${(failedSegmentCount / segmentCount) * 100}%`, backgroundColor: "var(--accent-alert)", flexShrink: 0 }} />}
      </div>
    </div>
  );
}

// ─── SegStatusBadge ───────────────────────────────────────────────────────────

function SegStatusBadge({ status }: { status: SegmentStatus }) {
  const cfg = SEG_STATUS_CONFIG[status] ?? SEG_STATUS_CONFIG.recorded;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "3px", paddingLeft: "var(--space-2)", paddingRight: "var(--space-2)", paddingTop: "2px", paddingBottom: "2px", borderLeft: `3px solid ${cfg.borderColor}`, backgroundColor: cfg.bg, backdropFilter: "blur(4px)" }}>
      {(status === "reviewed" || status === "annotated") && <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✓</span>}
      {status === "failed" && <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✕</span>}
      <span style={{ fontSize: "8px", fontWeight: 700, color: cfg.textColor, letterSpacing: "0.07em", textTransform: "uppercase" }}>{cfg.label}</span>
    </div>
  );
}

// ─── Annotation shapes + dots ─────────────────────────────────────────────────

type AnnotationKey = keyof Segment["annotations"];

const LABEL_META: Record<AnnotationKey, { color: string; title: string; shape: (color: string) => React.ReactNode }> = {
  person:       { color: "var(--class-pedestrian)",   title: "Person",        shape: (c) => <circle cx="6" cy="6" r="5" fill={c} /> },
  bicycle:      { color: "var(--class-cyclist)",      title: "Bicycle",       shape: (c) => <><circle cx="3" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" /><circle cx="9" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" /><polyline points="3,8 6,3 9,8" stroke={c} strokeWidth="1.2" fill="none" /></> },
  car:          { color: "var(--class-vehicle)",      title: "Car",           shape: (c) => <><rect x="1" y="6" width="10" height="4" fill={c} /><rect x="3" y="3" width="6" height="4" fill={c} /></> },
  motorbike:    { color: "var(--class-motorbike)",    title: "Motorbike",     shape: (c) => <><circle cx="6" cy="6" r="4.5" stroke={c} strokeWidth="1.5" fill="none" /><circle cx="6" cy="6" r="1.2" fill={c} /></> },
  bus:          { color: "var(--class-bus)",          title: "Bus",           shape: (c) => <><rect x="2" y="1" width="8" height="10" fill={c} /><rect x="3.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" /><rect x="6.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" /></> },
  train:        { color: "var(--class-train)",        title: "Train",         shape: (c) => <><rect x="1" y="1" width="10" height="9" fill={c} /><line x1="1" y1="4.5" x2="11" y2="4.5" stroke="white" strokeWidth="0.8" opacity="0.6" /><line x1="1" y1="7.5" x2="11" y2="7.5" stroke="white" strokeWidth="0.8" opacity="0.6" /></> },
  truck:        { color: "var(--class-truck)",        title: "Truck",         shape: (c) => <><rect x="0" y="4" width="9" height="5" fill={c} /><rect x="9" y="6" width="3" height="3" fill={c} /></> },
  trafficLight: { color: "var(--class-traffic-light)", title: "Traffic Light", shape: (c) => <><rect x="3.5" y="1" width="5" height="10" rx="2.5" fill={c} /><circle cx="6" cy="3" r="1" fill="white" opacity="0.9" /><circle cx="6" cy="6" r="1" fill="white" opacity="0.9" /><circle cx="6" cy="9" r="1" fill="white" opacity="0.9" /></> },
  stopSign:     { color: "var(--class-road-sign)",    title: "Stop Sign",     shape: (c) => <polygon points="8.6,2.5 10.5,5 10.5,7.5 8.6,10 5.9,10 4,7.5 4,5 5.9,2.5" fill={c} /> },
};

function AnnotationDots({ annotations }: { annotations: Segment["annotations"] }) {
  const items = (Object.keys(LABEL_META) as AnnotationKey[]).map((k) => ({ key: k, count: annotations[k], meta: LABEL_META[k] })).filter((x) => x.count > 0);
  if (items.length === 0) return null;
  return (
    <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
      {items.map(({ key, count, meta }) => (
        <div key={key} title={meta.title} style={{ display: "flex", alignItems: "center", gap: "3px" }}>
          <svg width="12" height="12" viewBox="0 0 12 12" style={{ flexShrink: 0, overflow: "visible" }}>{meta.shape(meta.color)}</svg>
          <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>{count}</span>
        </div>
      ))}
    </div>
  );
}

// ─── SegmentCard ──────────────────────────────────────────────────────────────

function SegmentCard({ segment, onClick }: { segment: Segment; onClick: () => void }) {
  const [hovered, setHovered] = useState(false);
  const isAnnotated = segment.status === "annotated" || segment.status === "reviewed";
  const totalAnnotations = Object.values(segment.annotations).reduce((a, b) => a + b, 0);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", outline: hovered ? "2px solid var(--border-black)" : "2px solid transparent", outlineOffset: "-1px", cursor: "pointer", display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <div style={{ position: "relative", height: "96px", overflow: "hidden", flexShrink: 0 }}>
        <SegmentThumbnail segment={segment} hovered={hovered} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, rgba(0,0,0,0.55) 0%, transparent 60%)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", top: "var(--space-2)", left: "var(--space-2)" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-lg)", fontWeight: 700, color: "var(--text-on-inverse)", lineHeight: 1, letterSpacing: "-0.02em", textShadow: "0 1px 4px rgba(0,0,0,0.6)" }}>
            {String(segment.index).padStart(2, "0")}
          </span>
        </div>
        <div style={{ position: "absolute", bottom: "var(--space-2)", left: "var(--space-2)" }}>
          <SegStatusBadge status={segment.status} />
        </div>
        <div style={{ position: "absolute", bottom: "var(--space-2)", right: "var(--space-2)", backgroundColor: "rgba(17,17,17,0.7)", backdropFilter: "blur(4px)", padding: "2px 5px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", fontWeight: 700, color: "var(--text-on-inverse)", letterSpacing: "0.04em" }}>
            {formatOffset(segment.startSeconds)}
          </span>
        </div>
      </div>

      <div style={{ padding: "var(--space-2) var(--space-3)", display: "flex", flexDirection: "column", gap: "var(--space-2)", flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-secondary)" }}>{formatDuration(segment.durationSeconds)}</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)" }}>{segment.frameCount.toLocaleString()} fr</span>
        </div>
        {isAnnotated ? (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "4px" }}>
              <span style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em" }}>annotations</span>
              <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-go)" }}>{totalAnnotations}</span>
            </div>
            <AnnotationDots annotations={segment.annotations} />
          </div>
        ) : (
          <div style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
            {segment.status === "failed" ? "— processing failed" : "— pending annotation"}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── DarkStatCell ─────────────────────────────────────────────────────────────

function DarkStatCell({ label, value, valueColor }: { label: string; value: number | string; valueColor?: string }) {
  return (
    <div style={{ padding: "var(--space-3) var(--space-4)", borderRight: "1px solid rgba(255,255,255,0.08)" }}>
      <div style={{ fontSize: "var(--text-xl)", fontWeight: 700, fontFamily: "var(--font-mono)", color: valueColor ?? "var(--text-on-inverse)", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.09em", marginTop: "var(--space-1)", fontWeight: 600 }}>{label}</div>
    </div>
  );
}

// ─── RouteDetail ──────────────────────────────────────────────────────────────

type SegFilterStatus = SegmentStatus | "all";
type SegSortKey = "index" | "status" | "annotations";

export default function RouteDetail() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const decodedRouteId = routeId ? decodeURIComponent(routeId) : "";

  const [route, setRoute] = useState<Route | null>(null);
  const [allSegments, setAllSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<SegFilterStatus>("all");
  const [sortBy, setSortBy] = useState<SegSortKey>("index");

  useEffect(() => {
    if (!decodedRouteId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
  getRoute(decodedRouteId),
  listSegmentsForRoute(decodedRouteId),
])
      .then(([r, segs]) => {
  if (!cancelled) {
    setRoute({
      ...r,
      segmentCount: segs.length,
    });
    setAllSegments(segs);
    setLoading(false);
  }
})
      .catch((err) => {
        if (!cancelled) {
          setError(err.message ?? "Failed to load route");
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [decodedRouteId]);

  const segments = useMemo(() => {
    let filtered = allSegments.filter((s) => statusFilter === "all" ? true : s.status === statusFilter);
    filtered.sort((a, b) => {
      if (sortBy === "index") return a.index - b.index;
      if (sortBy === "status") return a.status.localeCompare(b.status);
      if (sortBy === "annotations") {
        const sum = (s: Segment) => Object.values(s.annotations).reduce((x, y) => x + y, 0);
        return sum(b) - sum(a);
      }
      return 0;
    });
    return filtered;
  }, [allSegments, statusFilter, sortBy]);

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ paddingBottom: "var(--space-12)" }}>
        <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-6) var(--space-8) var(--space-5)", height: "220px", opacity: 0.4 }} />
        <div style={{ marginTop: "var(--space-5)", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "var(--space-3)" }}>
          {Array.from({ length: 8 }).map((_, i) => <div key={i} style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", height: "160px", opacity: 0.4 }} />)}
        </div>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (error || !route) {
    return (
      <div style={{ padding: "var(--space-12)", textAlign: "center" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          {error ?? `Route "${decodedRouteId}" not found.`}
        </div>
        <button onClick={() => navigate("/routes")} style={{ marginTop: "var(--space-4)", padding: "var(--space-2) var(--space-4)", backgroundColor: "var(--bg-inverse)", color: "var(--text-on-inverse)", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>
          ← Back to Routes
        </button>
      </div>
    );
  }

  const routeStatusColor = ROUTE_STATUS_COLORS[route.status] ?? "var(--text-secondary)";
  const routeStatusLabel = ROUTE_STATUS_LABELS[route.status] ?? route.status;
  const completedSegs = allSegments.filter((s) => s.status === "annotated" || s.status === "reviewed").length;
  const inProgressSegs = allSegments.filter((s) => s.status === "annotating").length;
  const failedSegs = allSegments.filter((s) => s.status === "failed").length;
  const pendingSegs = allSegments.filter((s) => s.status === "recorded").length;

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>

      {/* ── Dark hero header ────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-6) var(--space-8) var(--space-5)" }}>
        {/* Breadcrumb */}
        <button
          onClick={() => navigate("/routes")}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0, display: "inline-flex", alignItems: "center", gap: "var(--space-2)", color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "var(--space-4)" }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.8)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.4)")}
        >
          ← Routes
        </button>

        {/* Route ID + status */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-4)", flexWrap: "wrap", marginBottom: "var(--space-2)" }}>
          <h1 style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-lg)", fontWeight: 700, color: "var(--text-on-inverse)", letterSpacing: "-0.01em", margin: 0 }}>
            {route.id}
          </h1>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "3px var(--space-3)", border: `1px solid ${routeStatusColor}` }}>
            {route.status === "reviewed" && <span style={{ color: routeStatusColor, fontSize: "9px", fontWeight: 800 }}>✓</span>}
            <span style={{ fontSize: "9px", fontWeight: 700, color: routeStatusColor, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
              {routeStatusLabel}
            </span>
          </div>
        </div>

        {/* Meta row */}
        <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap", marginBottom: "var(--space-4)", fontSize: "11px", fontFamily: "var(--font-mono)", color: "rgba(255,255,255,0.45)" }}>
          <span>{route.vehicleId}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDate(route.recordedAt)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDuration(route.durationSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{route.segmentCount} segments</span>
        </div>

        {/* Stat cells */}
        <div style={{ display: "flex", flexWrap: "wrap", border: "1px solid rgba(255,255,255,0.08)", marginBottom: "var(--space-4)" }}>
          <DarkStatCell label="Segments" value={route.segmentCount} />
          <DarkStatCell label="Annotated" value={completedSegs} valueColor={completedSegs > 0 ? "var(--accent-go)" : undefined} />
          <DarkStatCell label="In Progress" value={inProgressSegs} valueColor={inProgressSegs > 0 ? "var(--accent-caution)" : undefined} />
          <DarkStatCell label="Failed" value={failedSegs} valueColor={failedSegs > 0 ? "var(--accent-alert)" : undefined} />
          <DarkStatCell label="Pending" value={pendingSegs} />
        </div>

        {/* Completion bar */}
        <div style={{ marginBottom: "var(--space-4)" }}>
          <HeroCompletionBar route={route} />
        </div>

        {/* Timeline strip */}
        {allSegments.length > 0 && (
          <div>
            <div style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: "rgba(255,255,255,0.25)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "var(--space-2)" }}>
              Segment timeline
            </div>
            <SegmentTimeline segments={allSegments} />
          </div>
        )}
      </div>

      {/* ── Filter bar ────────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-5)", marginBottom: "var(--space-4)", flexWrap: "wrap" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as SegFilterStatus)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="all">All Statuses</option>
          <option value="recorded">Recorded</option>
          <option value="annotating">Annotating</option>
          <option value="annotated">Annotated</option>
          <option value="reviewed">Reviewed</option>
          <option value="failed">Failed</option>
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SegSortKey)} style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}>
          <option value="index">Sort: Index</option>
          <option value="status">Sort: Status</option>
          <option value="annotations">Sort: Annotations</option>
        </select>
      </div>

      {/* Count */}
      <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.09em", fontWeight: 600, marginBottom: "var(--space-4)" }}>
        {segments.length} segment{segments.length !== 1 ? "s" : ""}
        {statusFilter !== "all" ? ` · ${(SEG_STATUS_CONFIG[statusFilter as SegmentStatus] ?? { label: statusFilter }).label}` : ""}
      </div>

      {/* Segment grid */}
      {segments.length === 0 ? (
        <div style={{ padding: "var(--space-12)", textAlign: "center", color: "var(--text-muted)", border: "1px dashed var(--border-subtle)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>
          No segments match your filter.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "var(--space-3)" }}>
          {segments.map((seg) => (
            <SegmentCard key={seg.index} segment={seg} onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}/segments/${seg.index}`)} />
          ))}
        </div>
      )}
    </div>
  );
}
