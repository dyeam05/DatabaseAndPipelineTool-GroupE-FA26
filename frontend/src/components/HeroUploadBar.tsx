import type { Segment } from "../api/types";

export function HeroUploadBar({ segments }: { segments: Segment[] }) {
  const total = segments.length;
  const uploaded = segments.filter((s) => s.status === "uploaded").length;
  const uploading = segments.filter((s) => s.status === "uploading" || s.status === "downloading").length;
  const failed = segments.filter((s) => s.status === "failed").length;
  const pct = total > 0 ? Math.round((uploaded / total) * 100) : 0;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "10px", color: "var(--text-on-inverse-secondary)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          {uploaded} / {total} segments uploaded
        </span>
        <span style={{ fontSize: "var(--text-sm)", fontWeight: 700, fontFamily: "var(--font-mono)", color: pct === 100 ? "var(--accent-go)" : pct === 0 ? "var(--text-on-inverse-dim)" : "var(--accent-caution)" }}>
          {total > 0 ? `${pct}%` : "—"}
        </span>
      </div>
      <div style={{ height: "4px", backgroundColor: "var(--bg-on-inverse-hover)", display: "flex", overflow: "hidden" }}>
        {uploaded > 0 && total > 0 && <div style={{ width: `${(uploaded / total) * 100}%`, backgroundColor: "var(--accent-go)", flexShrink: 0 }} />}
        {uploading > 0 && total > 0 && <div style={{ width: `${(uploading / total) * 100}%`, backgroundColor: "var(--accent-caution)", flexShrink: 0 }} />}
        {failed > 0 && total > 0 && <div style={{ width: `${(failed / total) * 100}%`, backgroundColor: "var(--accent-alert)", flexShrink: 0 }} />}
      </div>
    </div>
  );
}
