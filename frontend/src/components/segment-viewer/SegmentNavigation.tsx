import { useNavigate } from "react-router-dom";
import type { Segment } from "../../api/types";

interface Props {
  routeId: string;
  prevSeg: Segment | null;
  nextSeg: Segment | null;
}

export function SegmentNavigation({ routeId, prevSeg, nextSeg }: Props) {
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", gap: "var(--space-2)" }}>
      <button
        onClick={() => prevSeg !== null && navigate(`/routes/${encodeURIComponent(routeId)}/segments/${prevSeg.index}`)}
        disabled={!prevSeg}
        style={{ flex: 1, padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: prevSeg ? "var(--bg-surface)" : "var(--bg-elevated)", color: prevSeg ? "var(--text-primary)" : "var(--text-muted)", cursor: prevSeg ? "pointer" : "not-allowed", fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", textAlign: "center" }}
      >
        ← {prevSeg ? `#${String(prevSeg.index).padStart(2, "0")}` : "—"}
      </button>
      <button
        onClick={() => nextSeg !== null && navigate(`/routes/${encodeURIComponent(routeId)}/segments/${nextSeg.index}`)}
        disabled={!nextSeg}
        style={{ flex: 1, padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: nextSeg ? "var(--bg-surface)" : "var(--bg-elevated)", color: nextSeg ? "var(--text-primary)" : "var(--text-muted)", cursor: nextSeg ? "pointer" : "not-allowed", fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", textAlign: "center" }}
      >
        {nextSeg ? `#${String(nextSeg.index).padStart(2, "0")}` : "—"} →
      </button>
    </div>
  );
}
