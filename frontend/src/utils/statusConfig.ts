export const STATUS_CONFIG: Record<
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

export const DEFAULT_STATUS_CFG = {
  label: "Unknown",
  barColor: "var(--border-strong)",
  textColor: "var(--text-secondary)",
  bg: "var(--status-recorded-bg)",
};

export function getStatusCfg(status: string) {
  return STATUS_CONFIG[status] ?? DEFAULT_STATUS_CFG;
}