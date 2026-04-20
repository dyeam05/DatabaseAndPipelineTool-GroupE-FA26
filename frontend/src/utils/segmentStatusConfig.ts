import type { SegmentStatus } from "../api/types";

export const SEG_STATUS_CONFIG: Record<
  SegmentStatus,
  { label: string; timelineColor: string; textColor: string; bg: string; borderColor: string }
> = {
  "download queue": { label: "Queued",       timelineColor: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)", borderColor: "var(--border-strong)"  },
  downloading:      { label: "Downloading",  timelineColor: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)",  borderColor: "var(--accent-caution)" },
  "upload queue":   { label: "Upload Queue", timelineColor: "var(--border-strong)",  textColor: "var(--status-recorded-text)", bg: "var(--status-recorded-bg)", borderColor: "var(--border-strong)"  },
  uploading:        { label: "Uploading",    timelineColor: "var(--accent-caution)", textColor: "var(--status-caution-text)",  bg: "var(--status-caution-bg)",  borderColor: "var(--accent-caution)" },
  uploaded:         { label: "Uploaded",     timelineColor: "var(--accent-go)",      textColor: "var(--status-go-text)",       bg: "var(--status-go-bg)",       borderColor: "var(--accent-go)"      },
  failed:           { label: "Failed",       timelineColor: "var(--accent-alert)",   textColor: "var(--status-alert-text)",    bg: "var(--status-alert-bg)",    borderColor: "var(--accent-alert)"   },
};

export const DEFAULT_SEG_CFG = SEG_STATUS_CONFIG["download queue"];
