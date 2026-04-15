export function Pip({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <div style={{ width: "6px", height: "6px", backgroundColor: color, flexShrink: 0 }} />
      <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {label}
      </span>
    </div>
  );
}