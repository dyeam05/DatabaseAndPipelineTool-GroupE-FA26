import { useQuery } from "@tanstack/react-query";
import { getRoute } from "../api/routes";
import { ROUTE_TERMINAL_STATUSES } from "../api/types";

export function useRouteStatus(routeId?: string) {
  return useQuery({
    queryKey: ["route", routeId],
    queryFn: () => {
      if (!routeId) throw new Error("Missing routeId");
      return getRoute(routeId);
    },
    enabled: !!routeId,
    // In TanStack Query v5, refetchInterval receives the Query object — use query.state.data
    refetchInterval: (query) => {
      const route = query.state.data;
      if (!route) return 5000;
      return ROUTE_TERMINAL_STATUSES.includes(route.status) ? false : 5000;
    },
  });
}
