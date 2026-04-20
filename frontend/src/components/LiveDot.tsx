export function LiveDot() {
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