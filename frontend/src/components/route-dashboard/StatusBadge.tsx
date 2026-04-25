import { getStatusCfg } from "../../utils/statusConfig";

export function StatusBadge({ status }: { status: string }) {
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
