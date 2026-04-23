export function SegmentViewerSkeleton() {
  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>
      <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-5) var(--space-8)", height: "140px", opacity: 0.4 }} />
      <div style={{ marginTop: "var(--space-6)", height: "300px", backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", opacity: 0.4 }} />
    </div>
  );
}
