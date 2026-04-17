import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getThumbnailUrl } from "../api/routes";
import { listSegmentsForRoute } from "../api/segments";
import type { Segment, SegmentStatus } from "../api/types";
import { SEGMENT_TERMINAL_STATUSES } from "../api/types";
import { useRouteStatus } from "../hooks/useRouteStatus";
import { CvatJobRunsList } from "../components/CvatJobRunsList";

// ─── Status config ────────────────────────────────────────────────────────────

const SEG_STATUS_CONFIG: Record<
  SegmentStatus,
  { label: string; color: string; textColor: string; bg: string }
> = {
  "download queue": { label: "Queued",       color: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)" },
  downloading:      { label: "Downloading",  color: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  "upload queue":   { label: "Upload Queue", color: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)" },
  uploading:        { label: "Uploading",    color: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  uploaded:         { label: "Uploaded",     color: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  failed:           { label: "Failed",       color: "var(--accent-alert)",   textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)"    },
};

const DEFAULT_SEG_CFG = SEG_STATUS_CONFIG["download queue"];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDuration(s: number): string {
  if (!s) return "—";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${String(s % 60).padStart(2, "0")}s`;
}

function formatOffset(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function formatDate(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

// ─── SegmentViewer ────────────────────────────────────────────────────────────

export default function SegmentViewer() {
  const { routeId, segmentId } = useParams<{ routeId: string; segmentId: string }>();
  const navigate = useNavigate();
  const decodedRouteId = routeId ? decodeURIComponent(routeId) : "";
  const segIdx = segmentId !== undefined ? parseInt(segmentId, 10) : NaN;

  const [imgErrored, setImgErrored] = useState(false);

  // ── Live polling queries ──────────────────────────────────────────────────
  const { data: route, isLoading: routeLoading, error: routeError } = useRouteStatus(decodedRouteId || undefined);

  const { data: segments = [], isLoading: segsLoading } = useQuery({
    queryKey: ["segments", decodedRouteId],
    queryFn: () => listSegmentsForRoute(decodedRouteId),
    enabled: !!decodedRouteId,
    refetchInterval: (query) => {
      const segs = query.state.data ?? [];
      return segs.some((s) => !SEGMENT_TERMINAL_STATUSES.includes(s.status)) ? 3000 : false;
    },
  });

  const loading = routeLoading || segsLoading;
  const error = routeError ? (routeError as Error).message ?? "Failed to load segment" : null;

  // Reset image error state when navigating between segments
  useEffect(() => { setImgErrored(false); }, [segIdx]);

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ paddingBottom: "var(--space-12)" }}>
        <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-5) var(--space-8)", height: "140px", opacity: 0.4 }} />
        <div style={{ marginTop: "var(--space-6)", height: "300px", backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", opacity: 0.4 }} />
      </div>
    );
  }

  // ── Error / not found ────────────────────────────────────────────────────
  const segment: Segment | null =
    !isNaN(segIdx) && segIdx >= 0 && segIdx < segments.length
      ? segments[segIdx]
      : null;

  if (error || !route || !segment) {
    return (
      <div style={{ padding: "var(--space-12)", textAlign: "center" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          {error ?? "Segment not found."}
        </div>
        <button
          onClick={() => navigate(`/routes/${encodeURIComponent(decodedRouteId)}`)}
          style={{ marginTop: "var(--space-4)", padding: "var(--space-2) var(--space-4)", backgroundColor: "var(--bg-inverse)", color: "var(--text-on-inverse)", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}
        >
          ← Back to Route
        </button>
      </div>
    );
  }

  const cfg = SEG_STATUS_CONFIG[segment.status] ?? DEFAULT_SEG_CFG;
  const isUploaded = segment.status === "uploaded";
  const totalAnnotations = Object.values(segment.annotations).reduce((a, b) => a + b, 0);
  const prevSeg = segIdx > 0 ? segments[segIdx - 1] : null;
  const nextSeg = segIdx < segments.length - 1 ? segments[segIdx + 1] : null;
  const thumbnailSrc = getThumbnailUrl(route.id, segment.index);

  const annotationClasses: {
    label: string; count: number; color: string; shape: (c: string) => React.ReactNode;
  }[] = [
    { label: "Person",        count: segment.annotations.person,       color: "var(--class-pedestrian)",    shape: (c) => <circle cx="6" cy="6" r="5" fill={c} /> },
    { label: "Bicycle",       count: segment.annotations.bicycle,      color: "var(--class-cyclist)",       shape: (c) => <><circle cx="3" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" /><circle cx="9" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" /><polyline points="3,8 6,3 9,8" stroke={c} strokeWidth="1.2" fill="none" /></> },
    { label: "Car",           count: segment.annotations.car,          color: "var(--class-vehicle)",       shape: (c) => <><rect x="1" y="6" width="10" height="4" fill={c} /><rect x="3" y="3" width="6" height="4" fill={c} /></> },
    { label: "Motorbike",     count: segment.annotations.motorbike,    color: "var(--class-motorbike)",     shape: (c) => <><circle cx="6" cy="6" r="4.5" stroke={c} strokeWidth="1.5" fill="none" /><circle cx="6" cy="6" r="1.2" fill={c} /></> },
    { label: "Bus",           count: segment.annotations.bus,          color: "var(--class-bus)",           shape: (c) => <><rect x="2" y="1" width="8" height="10" fill={c} /><rect x="3.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" /><rect x="6.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" /></> },
    { label: "Train",         count: segment.annotations.train,        color: "var(--class-train)",         shape: (c) => <><rect x="1" y="1" width="10" height="9" fill={c} /><line x1="1" y1="4.5" x2="11" y2="4.5" stroke="white" strokeWidth="0.8" opacity="0.6" /></> },
    { label: "Truck",         count: segment.annotations.truck,        color: "var(--class-truck)",         shape: (c) => <><rect x="0" y="4" width="9" height="5" fill={c} /><rect x="9" y="6" width="3" height="3" fill={c} /></> },
    { label: "Traffic Light", count: segment.annotations.trafficLight, color: "var(--class-traffic-light)", shape: (c) => <><rect x="3.5" y="1" width="5" height="10" rx="2.5" fill={c} /><circle cx="6" cy="3" r="1" fill="white" opacity="0.9" /><circle cx="6" cy="6" r="1" fill="white" opacity="0.9" /><circle cx="6" cy="9" r="1" fill="white" opacity="0.9" /></> },
    { label: "Stop Sign",     count: segment.annotations.stopSign,     color: "var(--class-road-sign)",     shape: (c) => <polygon points="8.6,2.5 10.5,5 10.5,7.5 8.6,10 5.9,10 4,7.5 4,5 5.9,2.5" fill={c} /> },
  ];

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>

      {/* ── Dark hero ────────────────────────────────────────────────────────── */}
      <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-5) var(--space-8)" }}>
        {/* Breadcrumb */}
        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", marginBottom: "var(--space-4)", fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          <button onClick={() => navigate("/routes")} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "rgba(255,255,255,0.3)" }} onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)")} onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.3)")}>Routes</button>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
          <button onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}`)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "rgba(255,255,255,0.3)" }} onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)")} onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.3)")}>
            {route.id}
          </button>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
          <span style={{ color: "rgba(255,255,255,0.6)" }}>Segment {String(segIdx).padStart(2, "0")}</span>
        </div>

        {/* Title row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "var(--space-3)", marginBottom: "var(--space-3)" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-3xl)", fontWeight: 700, color: "var(--text-on-inverse)", lineHeight: 1, letterSpacing: "-0.03em" }}>
              {String(segIdx).padStart(2, "0")}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "rgba(255,255,255,0.35)" }}>
              / {String(segments.length - 1).padStart(2, "0")}
            </span>
          </div>

          <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "3px var(--space-3)", border: `1px solid ${cfg.color}` }}>
            {segment.status === "uploaded" && <span style={{ color: cfg.color, fontSize: "9px", fontWeight: 800 }}>✓</span>}
            {segment.status === "failed"   && <span style={{ color: cfg.color, fontSize: "9px", fontWeight: 800 }}>✕</span>}
            <span style={{ fontSize: "9px", fontWeight: 700, color: cfg.color, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
              {cfg.label}
            </span>
          </div>
        </div>

        {/* Meta */}
        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", fontSize: "11px", fontFamily: "var(--font-mono)", color: "rgba(255,255,255,0.4)" }}>
          <span>{formatDate(route.createdAt)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>offset {formatOffset(segment.startSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDuration(segment.durationSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{segment.frameCount.toLocaleString()} frames</span>
        </div>
      </div>

      {/* ── Content ──────────────────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "var(--space-6)", marginTop: "var(--space-6)", alignItems: "start" }}>

        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>

          {/* Thumbnail */}
          <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", overflow: "hidden" }}>
            {imgErrored ? (
              <div style={{ height: "280px", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "var(--bg-elevated)" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  No preview available
                </span>
              </div>
            ) : (
              <img
                src={thumbnailSrc}
                alt={`Segment ${segIdx} thumbnail`}
                onError={() => setImgErrored(true)}
                style={{ width: "100%", display: "block", maxHeight: "400px", objectFit: "cover" }}
              />
            )}
          </div>

          {/* CVAT job runs */}
          <CvatJobRunsList routeId={route.id} segmentId={segIdx} />

          {/* Annotation breakdown — only shown when uploaded and annotations exist */}
          {isUploaded && totalAnnotations > 0 && (
            <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", padding: "var(--space-5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "var(--space-4)" }}>
                <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.09em", color: "var(--text-muted)", fontWeight: 600 }}>
                  Annotation Breakdown
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-xl)", fontWeight: 700, color: "var(--accent-go)", lineHeight: 1 }}>
                  {totalAnnotations}
                  <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 400, marginLeft: "4px" }}>total</span>
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                {annotationClasses.map(({ label, count, color, shape }) => {
                  const pct = totalAnnotations > 0 ? (count / totalAnnotations) * 100 : 0;
                  return (
                    <div key={label}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                          <svg width="14" height="14" viewBox="0 0 12 12" style={{ flexShrink: 0, overflow: "visible" }}>{shape(color)}</svg>
                          <span style={{ fontSize: "var(--text-xs)", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{label}</span>
                        </div>
                        <span style={{ fontSize: "var(--text-xs)", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" }}>{count}</span>
                      </div>
                      <div style={{ height: "3px", backgroundColor: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}>
                        <div style={{ height: "100%", width: `${pct}%`, backgroundColor: color }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>

          {/* Key stats */}
          <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)" }}>
            {[
              { label: "Segment",      value: `#${String(segIdx).padStart(2, "0")} of ${segments.length}` },
              { label: "Start offset", value: formatOffset(segment.startSeconds) },
              { label: "Duration",     value: formatDuration(segment.durationSeconds) },
              { label: "Frame count",  value: segment.frameCount.toLocaleString() },
              { label: "Created",      value: formatDate(route.createdAt) },
              { label: "Route",        value: route.id },
            ].map(({ label, value }, i, arr) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "var(--space-3)", padding: "var(--space-3) var(--space-4)", borderBottom: i < arr.length - 1 ? "1px solid var(--border-subtle)" : "none" }}>
                <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)", fontWeight: 600, flexShrink: 0 }}>{label}</span>
                <span style={{ fontSize: "var(--text-xs)", fontFamily: "var(--font-mono)", color: "var(--text-primary)", textAlign: "right", wordBreak: "break-all" }}>{value}</span>
              </div>
            ))}
          </div>

          {/* Prev / Next navigation */}
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <button
              onClick={() => prevSeg !== null && navigate(`/routes/${encodeURIComponent(route.id)}/segments/${prevSeg.index}`)}
              disabled={!prevSeg}
              style={{ flex: 1, padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: prevSeg ? "var(--bg-surface)" : "var(--bg-elevated)", color: prevSeg ? "var(--text-primary)" : "var(--text-muted)", cursor: prevSeg ? "pointer" : "not-allowed", fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", textAlign: "center" }}
            >
              ← {prevSeg ? `#${String(prevSeg.index).padStart(2, "0")}` : "—"}
            </button>
            <button
              onClick={() => nextSeg !== null && navigate(`/routes/${encodeURIComponent(route.id)}/segments/${nextSeg.index}`)}
              disabled={!nextSeg}
              style={{ flex: 1, padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: nextSeg ? "var(--bg-surface)" : "var(--bg-elevated)", color: nextSeg ? "var(--text-primary)" : "var(--text-muted)", cursor: nextSeg ? "pointer" : "not-allowed", fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", textAlign: "center" }}
            >
              {nextSeg ? `#${String(nextSeg.index).padStart(2, "0")}` : "—"} →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
