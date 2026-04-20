export function StatCard({ label, value, accentColor }: { label: string; value: number | string; accentColor?: string }) {
  return (
    <div style={{ padding: "var(--space-3) var(--space-4)", backgroundColor: "var(--bg-surface)" }}>
      <div style={{ fontSize: "var(--text-xl)", fontWeight: 700, fontFamily: "var(--font-mono)", color: accentColor ?? "var(--text-primary)", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.09em", marginTop: "var(--space-1)", fontWeight: 600 }}>
        {label}
      </div>
    </div>
  );
}
