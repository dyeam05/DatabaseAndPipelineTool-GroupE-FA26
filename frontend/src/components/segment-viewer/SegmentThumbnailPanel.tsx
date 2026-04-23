interface Props {
  src: string;
  segIdx: number;
  imgErrored: boolean;
  onError: () => void;
}

export function SegmentThumbnailPanel({ src, segIdx, imgErrored, onError }: Props) {
  return (
    <div style={{ border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", overflow: "hidden" }}>
      {imgErrored ? (
        <div style={{ height: "280px", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "var(--bg-elevated)" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            No preview available
          </span>
        </div>
      ) : (
        <img
          src={src}
          alt={`Segment ${segIdx} thumbnail`}
          onError={onError}
          style={{ width: "100%", display: "block", maxHeight: "400px", objectFit: "cover" }}
        />
      )}
    </div>
  );
}
