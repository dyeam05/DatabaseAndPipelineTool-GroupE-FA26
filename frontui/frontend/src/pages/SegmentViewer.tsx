import React from "react";
import { useParams, useNavigate } from "react-router-dom";

// ─── Types (mirrors RouteDetail) ─────────────────────────────────────────────

type AnnotationStatus =
  | "recorded"
  | "segmented"
  | "annotating"
  | "annotated"
  | "reviewed"
  | "failed";

type SegmentStatus = "recorded" | "annotating" | "annotated" | "reviewed" | "failed";

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

interface Segment {
  index: number;
  startSeconds: number;
  durationSeconds: number;
  frameCount: number;
  status: SegmentStatus;
  thumbnailIndex: number;
  annotations: {
    person: number;
    bicycle: number;
    car: number;
    motorbike: number;
    bus: number;
    train: number;
    truck: number;
    trafficLight: number;
    stopSign: number;
  };
}

// ─── Mock data ────────────────────────────────────────────────────────────────

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

// ─── Segment generation (same logic as RouteDetail) ───────────────────────────

function simpleHash(str: string, seed: number): number {
  let h = seed ^ 0xdeadbeef;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 0x9e3779b9);
    h ^= h >>> 16;
  }
  return Math.abs(h);
}

function generateSegments(route: Route): Segment[] {
  const segDuration = Math.floor(route.durationSeconds / route.segmentCount);

  const statuses: SegmentStatus[] = [];
  if (route.status === "reviewed") {
    for (let i = 0; i < route.segmentCount; i++) statuses.push("reviewed");
  } else {
    for (let i = 0; i < route.annotatedSegmentCount; i++) statuses.push("annotated");
    for (let i = 0; i < route.annotatingSegmentCount; i++) statuses.push("annotating");
    for (let i = 0; i < route.failedSegmentCount; i++) statuses.push("failed");
    while (statuses.length < route.segmentCount) statuses.push("recorded");

    const arr = [...statuses];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = simpleHash(route.id, i) % (i + 1);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    statuses.splice(0, statuses.length, ...arr);
  }

  return Array.from({ length: route.segmentCount }, (_, i) => {
    const isAnnotated = statuses[i] === "annotated" || statuses[i] === "reviewed";
    const h = (n: number) => simpleHash(route.id, i * 17 + n);
    return {
      index: i,
      startSeconds: i * segDuration,
      durationSeconds:
        i === route.segmentCount - 1
          ? route.durationSeconds - i * segDuration
          : segDuration,
      frameCount: Math.round(segDuration * 20),
      status: statuses[i],
      thumbnailIndex: (route.thumbnailIndex + i) % 12,
      annotations: isAnnotated
        ? {
            person:       h(0) % 5,
            bicycle:      h(1) % 4,
            car:          h(2) % 10,
            motorbike:    h(3) % 4,
            bus:          h(4) % 3,
            train:        h(5) % 2,
            truck:        h(6) % 5,
            trafficLight: h(7) % 4,
            stopSign:     h(8) % 3,
          }
        : { person: 0, bicycle: 0, car: 0, motorbike: 0, bus: 0, train: 0, truck: 0, trafficLight: 0, stopSign: 0 },
    };
  });
}

// ─── Status config ────────────────────────────────────────────────────────────

const SEG_STATUS_CONFIG: Record<
  SegmentStatus,
  { label: string; color: string; textColor: string; bg: string }
> = {
  recorded:   { label: "Recorded",   color: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)" },
  annotating: { label: "Annotating", color: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)"  },
  annotated:  { label: "Annotated",  color: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  reviewed:   { label: "Reviewed",   color: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)"       },
  failed:     { label: "Failed",     color: "var(--accent-alert)",   textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)"    },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDuration(s: number): string {
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

// ─── SegmentViewer ────────────────────────────────────────────────────────────

// Placeholder — replace with real CVAT base URL when ready
const CVAT_BASE_URL = "https://cvat.example.com";

export default function SegmentViewer() {
  const { routeId, segmentId } = useParams<{ routeId: string; segmentId: string }>();
  const navigate = useNavigate();

  const route = MOCK_ROUTES.find((r) => r.id === routeId) ?? null;
  const segIdx = segmentId !== undefined ? parseInt(segmentId, 10) : NaN;
  const segments = route ? generateSegments(route) : [];
  const segment: Segment | null =
    !isNaN(segIdx) && segIdx >= 0 && segIdx < segments.length
      ? segments[segIdx]
      : null;

  const prevSeg = segment && segIdx > 0 ? segments[segIdx - 1] : null;
  const nextSeg = segment && segIdx < segments.length - 1 ? segments[segIdx + 1] : null;

  // ── Not found ────────────────────────────────────────────────────────────

  if (!route || !segment) {
    return (
      <div style={{ padding: "var(--space-12)", textAlign: "center" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          Segment not found.
        </div>
        <button
          onClick={() => navigate(`/routes/${encodeURIComponent(routeId ?? "")}`)}
          style={{
            marginTop: "var(--space-4)",
            padding: "var(--space-2) var(--space-4)",
            backgroundColor: "var(--bg-inverse)",
            color: "var(--text-on-inverse)",
            border: "none",
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-sm)",
          }}
        >
          ← Back
        </button>
      </div>
    );
  }

  const cfg = SEG_STATUS_CONFIG[segment.status];
  const isAnnotated = segment.status === "annotated" || segment.status === "reviewed";
  const totalAnnotations =
    segment.annotations.person +
    segment.annotations.bicycle +
    segment.annotations.car +
    segment.annotations.motorbike +
    segment.annotations.bus +
    segment.annotations.train +
    segment.annotations.truck +
    segment.annotations.trafficLight +
    segment.annotations.stopSign;

  const cvatUrl = `${CVAT_BASE_URL}/tasks?search=${encodeURIComponent(route.id)}&segment=${segIdx}`;

  const annotationClasses: {
    label: string;
    count: number;
    color: string;
    shape: (c: string) => React.ReactNode;
  }[] = [
    {
      label: "Person", count: segment.annotations.person, color: "var(--class-pedestrian)",
      shape: (c) => <circle cx="6" cy="6" r="5" fill={c} />,
    },
    {
      label: "Bicycle", count: segment.annotations.bicycle, color: "var(--class-cyclist)",
      shape: (c) => (
        <>
          <circle cx="3" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" />
          <circle cx="9" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" />
          <polyline points="3,8 6,3 9,8" stroke={c} strokeWidth="1.2" fill="none" />
        </>
      ),
    },
    {
      label: "Car", count: segment.annotations.car, color: "var(--class-vehicle)",
      shape: (c) => (
        <>
          <rect x="1" y="6" width="10" height="4" fill={c} />
          <rect x="3" y="3" width="6" height="4" fill={c} />
        </>
      ),
    },
    {
      label: "Motorbike", count: segment.annotations.motorbike, color: "var(--class-motorbike)",
      shape: (c) => (
        <>
          <circle cx="6" cy="6" r="4.5" stroke={c} strokeWidth="1.5" fill="none" />
          <circle cx="6" cy="6" r="1.2" fill={c} />
        </>
      ),
    },
    {
      label: "Bus", count: segment.annotations.bus, color: "var(--class-bus)",
      shape: (c) => (
        <>
          <rect x="2" y="1" width="8" height="10" fill={c} />
          <rect x="3.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" />
          <rect x="6.5" y="2.5" width="2" height="2" fill="white" opacity="0.6" />
          <rect x="3.5" y="5.5" width="2" height="2" fill="white" opacity="0.6" />
          <rect x="6.5" y="5.5" width="2" height="2" fill="white" opacity="0.6" />
        </>
      ),
    },
    {
      label: "Train", count: segment.annotations.train, color: "var(--class-train)",
      shape: (c) => (
        <>
          <rect x="1" y="1" width="10" height="9" fill={c} />
          <line x1="1" y1="4.5" x2="11" y2="4.5" stroke="white" strokeWidth="0.8" opacity="0.6" />
          <line x1="1" y1="7.5" x2="11" y2="7.5" stroke="white" strokeWidth="0.8" opacity="0.6" />
          <rect x="3" y="9.5" width="2" height="1.5" fill={c} />
          <rect x="7" y="9.5" width="2" height="1.5" fill={c} />
        </>
      ),
    },
    {
      label: "Truck", count: segment.annotations.truck, color: "var(--class-truck)",
      shape: (c) => (
        <>
          <rect x="0" y="4" width="9" height="5" fill={c} />
          <rect x="9" y="6" width="3" height="3" fill={c} />
        </>
      ),
    },
    {
      label: "Traffic Light", count: segment.annotations.trafficLight, color: "var(--class-traffic-light)",
      shape: (c) => (
        <>
          <rect x="3.5" y="1" width="5" height="10" rx="2.5" fill={c} />
          <circle cx="6" cy="3" r="1" fill="white" opacity="0.9" />
          <circle cx="6" cy="6" r="1" fill="white" opacity="0.9" />
          <circle cx="6" cy="9" r="1" fill="white" opacity="0.9" />
        </>
      ),
    },
    {
      label: "Stop Sign", count: segment.annotations.stopSign, color: "var(--class-road-sign)",
      shape: (c) => (
        <polygon points="8.6,2.5 10.5,5 10.5,7.5 8.6,10 5.9,10 4,7.5 4,5 5.9,2.5" fill={c} />
      ),
    },
  ];

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>

      {/* ── Dark hero ───────────────────────────────────────────────────────── */}
      <div
        style={{
          backgroundColor: "var(--bg-inverse)",
          margin: "var(--space-4) calc(-1 * var(--space-8)) 0",
          padding: "var(--space-5) var(--space-8)",
        }}
      >
        {/* Breadcrumb */}
        <div
          style={{
            display: "flex",
            gap: "var(--space-2)",
            alignItems: "center",
            marginBottom: "var(--space-4)",
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          <button
            onClick={() => navigate("/routes")}
            style={{
              background: "none", border: "none", cursor: "pointer", padding: 0,
              color: "rgba(255,255,255,0.3)",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.3)")}
          >
            Routes
          </button>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
          <button
            onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}`)}
            style={{
              background: "none", border: "none", cursor: "pointer", padding: 0,
              color: "rgba(255,255,255,0.3)",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.3)")}
          >
            {route.id}
          </button>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
          <span style={{ color: "rgba(255,255,255,0.6)" }}>
            Segment {String(segIdx).padStart(2, "0")}
          </span>
        </div>

        {/* Title row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "var(--space-3)",
            marginBottom: "var(--space-3)",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-3xl)",
                fontWeight: 700,
                color: "var(--text-on-inverse)",
                lineHeight: 1,
                letterSpacing: "-0.03em",
              }}
            >
              {String(segIdx).padStart(2, "0")}
            </span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-sm)",
                color: "rgba(255,255,255,0.35)",
              }}
            >
              / {String(segments.length - 1).padStart(2, "0")}
            </span>
          </div>

          {/* Status badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px var(--space-3)",
              border: `1px solid ${cfg.color}`,
            }}
          >
            {(segment.status === "reviewed" || segment.status === "annotated") && (
              <span style={{ color: cfg.color, fontSize: "9px", fontWeight: 800 }}>✓</span>
            )}
            {segment.status === "failed" && (
              <span style={{ color: cfg.color, fontSize: "9px", fontWeight: 800 }}>✕</span>
            )}
            <span
              style={{
                fontSize: "9px",
                fontWeight: 700,
                color: cfg.color,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                fontFamily: "var(--font-mono)",
              }}
            >
              {cfg.label}
            </span>
          </div>
        </div>

        {/* Meta */}
        <div
          style={{
            display: "flex",
            gap: "var(--space-3)",
            flexWrap: "wrap",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
            color: "rgba(255,255,255,0.4)",
          }}
        >
          <span>{route.vehicleId}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>offset {formatOffset(segment.startSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDuration(segment.durationSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{segment.frameCount.toLocaleString()} frames</span>
        </div>
      </div>

      {/* ── Content ─────────────────────────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 280px",
          gap: "var(--space-6)",
          marginTop: "var(--space-6)",
          alignItems: "start",
        }}
      >
        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>

          {/* CVAT link — primary action */}
          <div
            style={{
              border: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-surface)",
              padding: "var(--space-5)",
            }}
          >
            <div
              style={{
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
                letterSpacing: "0.09em",
                color: "var(--text-muted)",
                fontWeight: 600,
                marginBottom: "var(--space-4)",
              }}
            >
              Annotation Tool
            </div>

            <a
              href={cvatUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: "none" }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "var(--space-4) var(--space-5)",
                  backgroundColor: "var(--bg-inverse)",
                  border: "2px solid var(--bg-inverse)",
                  cursor: "pointer",
                  transition: "background-color var(--transition-fast), border-color var(--transition-fast)",
                }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.backgroundColor = "var(--bg-inverse-hover)";
                  el.style.borderColor = "var(--accent-cvat)";
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.backgroundColor = "var(--bg-inverse)";
                  el.style.borderColor = "var(--bg-inverse)";
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
                  {/* CVAT icon block */}
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      backgroundColor: "var(--accent-cvat)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "9px",
                        color: "var(--text-on-inverse)",
                        letterSpacing: "0.04em",
                      }}
                    >
                      CV
                    </span>
                  </div>
                  <div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "var(--text-sm)",
                        color: "var(--text-on-inverse)",
                      }}
                    >
                      Open in CVAT
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "10px",
                        color: "rgba(255,255,255,0.35)",
                        marginTop: "2px",
                      }}
                    >
                      {route.id} · seg {String(segIdx).padStart(2, "0")}
                    </div>
                  </div>
                </div>
                <span style={{ color: "rgba(255,255,255,0.4)", fontSize: "var(--text-sm)" }}>↗</span>
              </div>
            </a>

            <p
              style={{
                marginTop: "var(--space-3)",
                fontSize: "11px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)",
              }}
            >
              CVAT base URL is configurable — update <code>CVAT_BASE_URL</code> in{" "}
              <code>SegmentViewer.tsx</code>.
            </p>
          </div>

          {/* Annotation breakdown — only if annotated */}
          {isAnnotated && (
            <div
              style={{
                border: "1px solid var(--border-subtle)",
                backgroundColor: "var(--bg-surface)",
                padding: "var(--space-5)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  marginBottom: "var(--space-4)",
                }}
              >
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase",
                    letterSpacing: "0.09em",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                  }}
                >
                  Annotation Breakdown
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "var(--text-xl)",
                    fontWeight: 700,
                    color: "var(--accent-go)",
                    lineHeight: 1,
                  }}
                >
                  {totalAnnotations}
                  <span
                    style={{
                      fontSize: "10px",
                      color: "var(--text-muted)",
                      fontWeight: 400,
                      marginLeft: "4px",
                    }}
                  >
                    total
                  </span>
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                {annotationClasses.map(({ label, count, color, shape }) => {
                  const pct = totalAnnotations > 0 ? (count / totalAnnotations) * 100 : 0;
                  return (
                    <div key={label}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "4px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                          <svg width="14" height="14" viewBox="0 0 12 12" style={{ flexShrink: 0, overflow: "visible" }}>
                            {shape(color)}
                          </svg>
                          <span
                            style={{
                              fontSize: "var(--text-xs)",
                              fontFamily: "var(--font-mono)",
                              color: "var(--text-secondary)",
                            }}
                          >
                            {label}
                          </span>
                        </div>
                        <span
                          style={{
                            fontSize: "var(--text-xs)",
                            fontFamily: "var(--font-mono)",
                            fontWeight: 700,
                            color: "var(--text-primary)",
                          }}
                        >
                          {count}
                        </span>
                      </div>
                      <div
                        style={{
                          height: "3px",
                          backgroundColor: "var(--bg-elevated)",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            width: `${pct}%`,
                            backgroundColor: color,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right column — segment info */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>

          {/* Key stats */}
          <div
            style={{
              border: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-surface)",
            }}
          >
            {[
              { label: "Segment",      value: `#${String(segIdx).padStart(2, "0")} of ${segments.length}` },
              { label: "Start offset", value: formatOffset(segment.startSeconds) },
              { label: "Duration",     value: formatDuration(segment.durationSeconds) },
              { label: "Frame count",  value: segment.frameCount.toLocaleString() },
              { label: "Vehicle",      value: route.vehicleId },
              { label: "Route",        value: route.id },
            ].map(({ label, value }, i, arr) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  gap: "var(--space-3)",
                  padding: "var(--space-3) var(--space-4)",
                  borderBottom: i < arr.length - 1 ? "1px solid var(--border-subtle)" : "none",
                }}
              >
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase",
                    letterSpacing: "0.07em",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                    flexShrink: 0,
                  }}
                >
                  {label}
                </span>
                <span
                  style={{
                    fontSize: "var(--text-xs)",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-primary)",
                    textAlign: "right",
                    wordBreak: "break-all",
                  }}
                >
                  {value}
                </span>
              </div>
            ))}
          </div>

          {/* Prev / Next navigation */}
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <button
              onClick={() =>
                prevSeg !== null &&
                navigate(
                  `/routes/${encodeURIComponent(route.id)}/segments/${prevSeg.index}`
                )
              }
              disabled={!prevSeg}
              style={{
                flex: 1,
                padding: "var(--space-2) var(--space-3)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: prevSeg ? "var(--bg-surface)" : "var(--bg-elevated)",
                color: prevSeg ? "var(--text-primary)" : "var(--text-muted)",
                cursor: prevSeg ? "pointer" : "not-allowed",
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-xs)",
                textAlign: "center",
              }}
            >
              ← {prevSeg ? `#${String(prevSeg.index).padStart(2, "0")}` : "—"}
            </button>
            <button
              onClick={() =>
                nextSeg !== null &&
                navigate(
                  `/routes/${encodeURIComponent(route.id)}/segments/${nextSeg.index}`
                )
              }
              disabled={!nextSeg}
              style={{
                flex: 1,
                padding: "var(--space-2) var(--space-3)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: nextSeg ? "var(--bg-surface)" : "var(--bg-elevated)",
                color: nextSeg ? "var(--text-primary)" : "var(--text-muted)",
                cursor: nextSeg ? "pointer" : "not-allowed",
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-xs)",
                textAlign: "center",
              }}
            >
              {nextSeg ? `#${String(nextSeg.index).padStart(2, "0")}` : "—"} →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
