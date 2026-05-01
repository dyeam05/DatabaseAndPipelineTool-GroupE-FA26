// Insert a zero-width space before "|" and "--" so the browser breaks long
// route IDs at natural separators instead of mid-token.
export function routeIdWithBreakHints(routeId: string): string {
  return routeId.replace(/(\||--)/g, "\u200B$1");
}
