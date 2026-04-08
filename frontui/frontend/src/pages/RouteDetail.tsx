import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";

// ─── Mock thumbnails ──────────────────────────────────────────────────────────

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

// ─── Mock data (mirrors RouteDashboard) ───────────────────────────────────────

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

const ROUTE_STATUS_CONFIG: Record<AnnotationStatus, { label: string; textColor: string }> = {
  recorded:   { label: "Recorded",   textColor: "var(--status-recorded-text)" },
  segmented:  { label: "Segmented",  textColor: "var(--text-secondary)"       },
  annotating: { label: "Annotating", textColor: "var(--accent-caution)"       },
  annotated:  { label: "Annotated",  textColor: "var(--accent-go)"            },
  reviewed:   { label: "Reviewed",   textColor: "var(--accent-go)"            },
  failed:     { label: "Failed",     textColor: "var(--accent-alert)"         },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

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

    // Deterministic shuffle based on route id
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
      thumbnailIndex: (route.thumbnailIndex + i) % MOCK_IMAGES.length,
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

function formatOffset(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

// ─── SegmentTimeline ──────────────────────────────────────────────────────────

function SegmentTimeline({ segments }: { segments: Segment[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: "2px",
          flexWrap: "wrap",
        }}
      >
        {segments.map((seg) => {
          const cfg = SEG_STATUS_CONFIG[seg.status];
          const isHovered = hoveredIdx === seg.index;
          return (
            <div
              key={seg.index}
              onMouseEnter={() => setHoveredIdx(seg.index)}
              onMouseLeave={() => setHoveredIdx(null)}
              title={`#${String(seg.index).padStart(2, "0")} · ${cfg.label} · ${formatOffset(seg.startSeconds)}`}
              style={{
                width: "16px",
                height: "8px",
                backgroundColor: isHovered ? "var(--text-on-inverse)" : cfg.timelineColor,
                flexShrink: 0,
                cursor: "default",
                transition: "background-color 80ms ease",
              }}
            />
          );
        })}
      </div>
      {hoveredIdx !== null && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "10px",
            fontFamily: "var(--font-mono)",
            color: "rgba(255,255,255,0.5)",
            letterSpacing: "0.04em",
          }}
        >
          seg{" "}
          <span style={{ color: "var(--text-on-inverse)", fontWeight: 700 }}>
            #{String(hoveredIdx).padStart(2, "0")}
          </span>
          {" · "}
          <span style={{ color: SEG_STATUS_CONFIG[segments[hoveredIdx].status].timelineColor }}>
            {SEG_STATUS_CONFIG[segments[hoveredIdx].status].label}
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
            fontSize: "10px",
            color: "rgba(255,255,255,0.45)",
            fontFamily: "var(--font-mono)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          {annotatedSegmentCount} / {segmentCount} segments annotated
        </span>
        <span
          style={{
            fontSize: "var(--text-sm)",
            fontWeight: 700,
            fontFamily: "var(--font-mono)",
            color: pct === 100 ? "var(--accent-go)" : pct === 0 ? "rgba(255,255,255,0.3)" : "var(--accent-caution)",
          }}
        >
          {pct}%
        </span>
      </div>
      <div
        style={{
          height: "4px",
          backgroundColor: "rgba(255,255,255,0.1)",
          display: "flex",
          overflow: "hidden",
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
    </div>
  );
}

// ─── SegStatusBadge ───────────────────────────────────────────────────────────

function SegStatusBadge({ status }: { status: SegmentStatus }) {
  const cfg = SEG_STATUS_CONFIG[status];
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "3px",
        paddingLeft: "var(--space-2)",
        paddingRight: "var(--space-2)",
        paddingTop: "2px",
        paddingBottom: "2px",
        borderLeft: `3px solid ${cfg.borderColor}`,
        backgroundColor: cfg.bg,
        backdropFilter: "blur(4px)",
      }}
    >
      {(status === "reviewed" || status === "annotated") && (
        <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✓</span>
      )}
      {status === "failed" && (
        <span style={{ color: cfg.textColor, fontSize: "8px", fontWeight: 800 }}>✕</span>
      )}
      <span
        style={{
          fontSize: "8px",
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

// ─── LabelShape ───────────────────────────────────────────────────────────────
// Each annotation class gets a semantically meaningful SVG shape.

type AnnotationKey = keyof Segment["annotations"];

const LABEL_META: Record<
  AnnotationKey,
  { color: string; title: string; shape: (color: string) => React.ReactNode }
> = {
  person: {
    color: "var(--class-pedestrian)",
    title: "Person",
    // circle — human silhouette
    shape: (c) => <circle cx="6" cy="6" r="5" fill={c} />,
  },
  bicycle: {
    color: "var(--class-cyclist)",
    title: "Bicycle",
    // two wheels
    shape: (c) => (
      <>
        <circle cx="3" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" />
        <circle cx="9" cy="8" r="2.5" stroke={c} strokeWidth="1.5" fill="none" />
        <polyline points="3,8 6,3 9,8" stroke={c} strokeWidth="1.2" fill="none" />
      </>
    ),
  },
  car: {
    color: "var(--class-vehicle)",
    title: "Car",
    // low wide rectangle with a cabin bump
    shape: (c) => (
      <>
        <rect x="1" y="6" width="10" height="4" fill={c} />
        <rect x="3" y="3" width="6" height="4" fill={c} />
      </>
    ),
  },
  motorbike: {
    color: "var(--class-motorbike)",
    title: "Motorbike",
    // single wheel with axle dot
    shape: (c) => (
      <>
        <circle cx="6" cy="6" r="4.5" stroke={c} strokeWidth="1.5" fill="none" />
        <circle cx="6" cy="6" r="1.2" fill={c} />
      </>
    ),
  },
  bus: {
    color: "var(--class-bus)",
    title: "Bus",
    // tall rectangle with windows
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
  train: {
    color: "var(--class-train)",
    title: "Train",
    // rectangle with horizontal rail lines
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
  truck: {
    color: "var(--class-truck)",
    title: "Truck",
    // cab + long flatbed
    shape: (c) => (
      <>
        <rect x="0" y="4" width="9" height="5" fill={c} />
        <rect x="9" y="6" width="3" height="3" fill={c} />
      </>
    ),
  },
  trafficLight: {
    color: "var(--class-traffic-light)",
    title: "Traffic Light",
    // vertical pill with 3 light circles
    shape: (c) => (
      <>
        <rect x="3.5" y="1" width="5" height="10" rx="2.5" fill={c} />
        <circle cx="6" cy="3" r="1" fill="white" opacity="0.9" />
        <circle cx="6" cy="6" r="1" fill="white" opacity="0.9" />
        <circle cx="6" cy="9" r="1" fill="white" opacity="0.9" />
      </>
    ),
  },
  stopSign: {
    color: "var(--class-road-sign)",
    title: "Stop Sign",
    // octagon
    shape: (c) => (
      <polygon
        points="8.6,2.5 10.5,5 10.5,7.5 8.6,10 5.9,10 4,7.5 4,5 5.9,2.5"
        fill={c}
      />
    ),
  },
};

function LabelShape({ type }: { type: AnnotationKey }) {
  const meta = LABEL_META[type];
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      style={{ flexShrink: 0, overflow: "visible" }}
      aria-label={meta.title}
    >
      {meta.shape(meta.color)}
    </svg>
  );
}

// ─── AnnotationDots ───────────────────────────────────────────────────────────

function AnnotationDots({ annotations }: { annotations: Segment["annotations"] }) {
  const items = (Object.keys(LABEL_META) as AnnotationKey[])
    .map((key) => ({ key, count: annotations[key], meta: LABEL_META[key] }))
    .filter((x) => x.count > 0);

  if (items.length === 0) return null;

  return (
    <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
      {items.map(({ key, count, meta }) => (
        <div
          key={key}
          title={meta.title}
          style={{ display: "flex", alignItems: "center", gap: "3px" }}
        >
          <LabelShape type={key} />
          <span
            style={{
              fontSize: "10px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
            }}
          >
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── SegmentCard ──────────────────────────────────────────────────────────────

function SegmentCard({
  segment,
  onClick,
}: {
  segment: Segment;
  onClick: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const thumbnail = MOCK_IMAGES[segment.thumbnailIndex % MOCK_IMAGES.length];
  const isAnnotated =
    segment.status === "annotated" || segment.status === "reviewed";
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
      <div style={{ position: "relative", height: "96px", overflow: "hidden", flexShrink: 0 }}>
        <img
          src={thumbnail}
          alt={`Segment ${segment.index}`}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center",
            display: "block",
            filter: hovered ? "brightness(1.05)" : "brightness(0.9)",
            transition: "filter var(--transition-fast)",
          }}
        />

        {/* Dark gradient overlay for readability */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(135deg, rgba(0,0,0,0.55) 0%, transparent 60%)",
            pointerEvents: "none",
          }}
        />

        {/* Segment index — top left */}
        <div
          style={{
            position: "absolute",
            top: "var(--space-2)",
            left: "var(--space-2)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "var(--text-lg)",
              fontWeight: 700,
              color: "var(--text-on-inverse)",
              lineHeight: 1,
              letterSpacing: "-0.02em",
              textShadow: "0 1px 4px rgba(0,0,0,0.6)",
            }}
          >
            {String(segment.index).padStart(2, "0")}
          </span>
        </div>

        {/* Status badge — bottom left */}
        <div
          style={{
            position: "absolute",
            bottom: "var(--space-2)",
            left: "var(--space-2)",
          }}
        >
          <SegStatusBadge status={segment.status} />
        </div>

        {/* Start time — bottom right */}
        <div
          style={{
            position: "absolute",
            bottom: "var(--space-2)",
            right: "var(--space-2)",
            backgroundColor: "rgba(17,17,17,0.7)",
            backdropFilter: "blur(4px)",
            padding: "2px 5px",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              fontWeight: 700,
              color: "var(--text-on-inverse)",
              letterSpacing: "0.04em",
            }}
          >
            {formatOffset(segment.startSeconds)}
          </span>
        </div>
      </div>

      {/* Card body */}
      <div
        style={{
          padding: "var(--space-2) var(--space-3)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-2)",
          flex: 1,
        }}
      >
        {/* Duration + frames */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--text-secondary)",
            }}
          >
            {formatDuration(segment.durationSeconds)}
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--text-muted)",
            }}
          >
            {segment.frameCount.toLocaleString()} fr
          </span>
        </div>

        {/* Annotation breakdown or placeholder */}
        {isAnnotated ? (
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                marginBottom: "4px",
              }}
            >
              <span
                style={{
                  fontSize: "9px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                }}
              >
                annotations
              </span>
              <span
                style={{
                  fontSize: "10px",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  color: "var(--accent-go)",
                }}
              >
                {totalAnnotations}
              </span>
            </div>
            <AnnotationDots annotations={segment.annotations} />
          </div>
        ) : (
          <div
            style={{
              fontSize: "9px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
            }}
          >
            {segment.status === "failed" ? "— processing failed" : "— pending annotation"}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── DarkStatCell ─────────────────────────────────────────────────────────────

function DarkStatCell({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: number | string;
  valueColor?: string;
}) {
  return (
    <div
      style={{
        padding: "var(--space-3) var(--space-4)",
        borderRight: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div
        style={{
          fontSize: "var(--text-xl)",
          fontWeight: 700,
          fontFamily: "var(--font-mono)",
          color: valueColor ?? "var(--text-on-inverse)",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: "9px",
          color: "rgba(255,255,255,0.35)",
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

// ─── RouteDetail ──────────────────────────────────────────────────────────────

type SegFilterStatus = SegmentStatus | "all";
type SegSortKey = "index" | "status" | "annotations";

export default function RouteDetail() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<SegFilterStatus>("all");
  const [sortBy, setSortBy] = useState<SegSortKey>("index");

  const route = useMemo(
    () => MOCK_ROUTES.find((r) => r.id === routeId) ?? null,
    [routeId]
  );

  const allSegments = useMemo(
    () => (route ? generateSegments(route) : []),
    [route]
  );

  const segments = useMemo(() => {
    let filtered = allSegments.filter((s) =>
      statusFilter === "all" ? true : s.status === statusFilter
    );
    filtered.sort((a, b) => {
      if (sortBy === "index") return a.index - b.index;
      if (sortBy === "status") return a.status.localeCompare(b.status);
      if (sortBy === "annotations") {
        const sum = (s: Segment) =>
          s.annotations.person + s.annotations.bicycle + s.annotations.car +
          s.annotations.motorbike + s.annotations.bus + s.annotations.train +
          s.annotations.truck + s.annotations.trafficLight + s.annotations.stopSign;
        const ta = sum(a);
        const tb = sum(b);
        return tb - ta;
      }
      return 0;
    });
    return filtered;
  }, [allSegments, statusFilter, sortBy]);

  // ── Not found ──────────────────────────────────────────────────────────────

  if (!route) {
    return (
      <div style={{ padding: "var(--space-12)", textAlign: "center" }}>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-sm)",
            color: "var(--text-muted)",
          }}
        >
          Route <code>{routeId}</code> not found.
        </div>
        <button
          onClick={() => navigate("/routes")}
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
          ← Back to Routes
        </button>
      </div>
    );
  }

  const routeCfg = ROUTE_STATUS_CONFIG[route.status];
  const completedSegs = allSegments.filter(
    (s) => s.status === "annotated" || s.status === "reviewed"
  ).length;
  const inProgressSegs = allSegments.filter((s) => s.status === "annotating").length;
  const failedSegs = allSegments.filter((s) => s.status === "failed").length;
  const pendingSegs = allSegments.filter((s) => s.status === "recorded").length;

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>

      {/* ── Dark hero header ──────────────────────────────────────────────── */}
      <div
        style={{
          backgroundColor: "var(--bg-inverse)",
          margin: "var(--space-4) calc(-1 * var(--space-8)) 0",
          padding: "var(--space-6) var(--space-8) var(--space-5)",
        }}
      >
        {/* Breadcrumb */}
        <button
          onClick={() => navigate("/routes")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 0,
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
            color: "rgba(255,255,255,0.4)",
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: "var(--space-4)",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.8)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.4)")
          }
        >
          ← Routes
        </button>

        {/* Route ID + status */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "var(--space-4)",
            flexWrap: "wrap",
            marginBottom: "var(--space-2)",
          }}
        >
          <h1
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "var(--text-lg)",
              fontWeight: 700,
              color: "var(--text-on-inverse)",
              letterSpacing: "-0.01em",
              margin: 0,
            }}
          >
            {route.id}
          </h1>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px var(--space-3)",
              border: `1px solid ${routeCfg.textColor}`,
            }}
          >
            {route.status === "reviewed" && (
              <span style={{ color: routeCfg.textColor, fontSize: "9px", fontWeight: 800 }}>
                ✓
              </span>
            )}
            <span
              style={{
                fontSize: "9px",
                fontWeight: 700,
                color: routeCfg.textColor,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                fontFamily: "var(--font-mono)",
              }}
            >
              {routeCfg.label}
            </span>
          </div>
        </div>

        {/* Meta row */}
        <div
          style={{
            display: "flex",
            gap: "var(--space-3)",
            alignItems: "center",
            flexWrap: "wrap",
            marginBottom: "var(--space-4)",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
            color: "rgba(255,255,255,0.45)",
          }}
        >
          <span>{route.vehicleId}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDate(route.recordedAt)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{formatDuration(route.durationSeconds)}</span>
          <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
          <span>{route.segmentCount} segments</span>
        </div>

        {/* Stat cells */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "var(--space-4)",
          }}
        >
          <DarkStatCell label="Segments" value={route.segmentCount} />
          <DarkStatCell
            label="Annotated"
            value={completedSegs}
            valueColor={completedSegs > 0 ? "var(--accent-go)" : undefined}
          />
          <DarkStatCell
            label="In Progress"
            value={inProgressSegs}
            valueColor={inProgressSegs > 0 ? "var(--accent-caution)" : undefined}
          />
          <DarkStatCell
            label="Failed"
            value={failedSegs}
            valueColor={failedSegs > 0 ? "var(--accent-alert)" : undefined}
          />
          <DarkStatCell label="Pending" value={pendingSegs} />
        </div>

        {/* Completion bar */}
        <div style={{ marginBottom: "var(--space-4)" }}>
          <HeroCompletionBar route={route} />
        </div>

        {/* Timeline strip */}
        <div>
          <div
            style={{
              fontSize: "9px",
              fontFamily: "var(--font-mono)",
              color: "rgba(255,255,255,0.25)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              marginBottom: "var(--space-2)",
            }}
          >
            Segment timeline
          </div>
          <SegmentTimeline segments={allSegments} />
        </div>
      </div>

      {/* ── Filter bar ───────────────────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          marginTop: "var(--space-5)",
          marginBottom: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as SegFilterStatus)}
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
          <option value="annotating">Annotating</option>
          <option value="annotated">Annotated</option>
          <option value="reviewed">Reviewed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SegSortKey)}
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
          <option value="index">Sort: Index</option>
          <option value="status">Sort: Status</option>
          <option value="annotations">Sort: Annotations</option>
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
        {segments.length} segment{segments.length !== 1 ? "s" : ""}
        {statusFilter !== "all" ? ` · ${SEG_STATUS_CONFIG[statusFilter].label}` : ""}
      </div>

      {/* ── Segment grid ─────────────────────────────────────────────────────── */}
      {segments.length === 0 ? (
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
          No segments match your filter.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))",
            gap: "var(--space-3)",
          }}
        >
          {segments.map((seg) => (
            <SegmentCard
              key={seg.index}
              segment={seg}
              onClick={() =>
                navigate(`/routes/${encodeURIComponent(route.id)}/segments/${seg.index}`)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
