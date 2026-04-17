import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listSegmentsForRoute } from "../api/segments";
import type { SegmentStatus } from "../api/types";
import { SEGMENT_TERMINAL_STATUSES } from "../api/types";
import { useRouteStatus } from "../hooks/useRouteStatus";
import { useJobRunsForRoute } from "../hooks/useJobRunsForRoute";
import { SEG_STATUS_CONFIG, DEFAULT_SEG_CFG } from "../utils/segmentStatusConfig";
import { RouteDetailHeader } from "../components/RouteDetailHeader";
import { SegmentCard } from "../components/route-detail/SegmentCard";

type SegFilterStatus = SegmentStatus | "all";
type SegSortKey = "index" | "status";

export default function RouteDetail() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const decodedRouteId = routeId ? decodeURIComponent(routeId) : "";

  const [statusFilter, setStatusFilter] = useState<SegFilterStatus>("all");
  const [sortBy, setSortBy] = useState<SegSortKey>("index");

  const { data: route, isLoading: routeLoading, error: routeError } = useRouteStatus(decodedRouteId || undefined);

  const { data: allSegments = [], isLoading: segsLoading, isFetching: segsFetching } = useQuery({
    queryKey: ["segments", decodedRouteId],
    queryFn: () => listSegmentsForRoute(decodedRouteId),
    enabled: !!decodedRouteId,
    refetchInterval: (query) => {
      const segs = query.state.data ?? [];
      return segs.some((s) => !SEGMENT_TERMINAL_STATUSES.includes(s.status)) ? 3000 : false;
    },
  });

  const { data: jobRuns = [], isFetching: jobsFetching } = useJobRunsForRoute(decodedRouteId || undefined);

  const loading = routeLoading || segsLoading;
  const error = routeError ? (routeError as Error).message ?? "Failed to load route" : null;
  const isPolling = (segsFetching || jobsFetching) && !loading;

  const segments = useMemo(() => {
    const filtered = allSegments.filter((s) => statusFilter === "all" || s.status === statusFilter);
    return [...filtered].sort((a, b) => {
      if (sortBy === "index") return a.index - b.index;
      if (sortBy === "status") return a.status.localeCompare(b.status);
      return 0;
    });
  }, [allSegments, statusFilter, sortBy]);

  if (loading) {
    return (
      <div style={{ paddingBottom: "var(--space-12)" }}>
        <div style={{ backgroundColor: "var(--bg-inverse)", margin: "var(--space-4) calc(-1 * var(--space-8)) 0", padding: "var(--space-6) var(--space-8) var(--space-5)", height: "220px", opacity: 0.4 }} />
        <div style={{ marginTop: "var(--space-5)", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "var(--space-3)" }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", height: "160px", opacity: 0.4 }} />
          ))}
        </div>
      </div>
    );
  }

  if (error || !route) {
    return (
      <div style={{ padding: "var(--space-12)", textAlign: "center" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          {error ?? `Route "${decodedRouteId}" not found.`}
        </div>
        <button
          onClick={() => navigate("/routes")}
          style={{ marginTop: "var(--space-4)", padding: "var(--space-2) var(--space-4)", backgroundColor: "var(--bg-inverse)", color: "var(--text-on-inverse)", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}
        >
          ← Back to Routes
        </button>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>
      <RouteDetailHeader
        route={route}
        segments={allSegments}
        jobRuns={jobRuns}
        isPolling={isPolling}
        onBack={() => navigate("/routes")}
        onDeleted={() => navigate("/routes")}
      />

      <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-5)", marginBottom: "var(--space-4)", flexWrap: "wrap" }}>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as SegFilterStatus)}
          style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}
        >
          <option value="all">All Statuses</option>
          <option value="download queue">Queued</option>
          <option value="downloading">Downloading</option>
          <option value="upload queue">Upload Queue</option>
          <option value="uploading">Uploading</option>
          <option value="uploaded">Uploaded</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SegSortKey)}
          style={{ padding: "var(--space-2) var(--space-3)", border: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-surface)", fontSize: "var(--text-sm)", color: "var(--text-primary)", outline: "none", cursor: "pointer" }}
        >
          <option value="index">Sort: Index</option>
          <option value="status">Sort: Status</option>
        </select>
      </div>

      <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.09em", fontWeight: 600, marginBottom: "var(--space-4)" }}>
        {segments.length} segment{segments.length !== 1 ? "s" : ""}
        {statusFilter !== "all" ? ` · ${(SEG_STATUS_CONFIG[statusFilter as SegmentStatus] ?? DEFAULT_SEG_CFG).label}` : ""}
      </div>

      {segments.length === 0 ? (
        <div style={{ padding: "var(--space-12)", textAlign: "center", color: "var(--text-muted)", border: "1px dashed var(--border-subtle)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>
          No segments match your filter.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "var(--space-3)" }}>
          {segments.map((seg) => (
            <SegmentCard
              key={seg.index}
              segment={seg}
              onClick={() => navigate(`/routes/${encodeURIComponent(route.id)}/segments/${seg.index}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
