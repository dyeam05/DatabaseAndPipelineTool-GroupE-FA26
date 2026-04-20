import { useState } from "react";
import type { Segment } from "../../api/types";
import { getThumbnailUrl } from "../../api/routes";

export function SegmentThumbnail({ segment, hovered }: { segment: Segment; hovered: boolean }) {
  const [errored, setErrored] = useState(false);
  const src = getThumbnailUrl(segment.routeId, segment.index);

  if (errored) {
    return (
      <div style={{ width: "100%", height: "100%", backgroundColor: "var(--bg-elevated)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          No preview
        </span>
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={`Segment ${segment.index}`}
      onError={() => setErrored(true)}
      style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", display: "block", filter: hovered ? "brightness(1.05)" : "brightness(0.9)", transition: "filter var(--transition-fast)" }}
    />
  );
}
