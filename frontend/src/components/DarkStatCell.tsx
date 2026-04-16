export function DarkStatCell({ label, value, valueColor }: { label: string; value: number | string; valueColor?: string }) {
  return (
    <div style={{ padding: "var(--space-3) var(--space-4)", borderRight: "1px solid var(--border-on-inverse-faint)" }}>
      <div style={{ fontSize: "var(--text-xl)", fontWeight: 700, fontFamily: "var(--font-mono)", color: valueColor ?? "var(--text-on-inverse)", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: "9px", color: "var(--text-on-inverse-muted)", textTransform: "uppercase", letterSpacing: "0.09em", marginTop: "var(--space-1)", fontWeight: 600 }}>
        {label}
      </div>
    </div>
  );
}
