import { useState } from "react";
import type { Route } from "../../api/types";
import { getThumbnailUrl } from "../../api/routes";

export function RouteThumbnail({ route, hovered }: { route: Route; hovered: boolean }) {
  const [errored, setErrored] = useState(false);
  const src = getThumbnailUrl(route.id, 0);

  return errored ? (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "var(--bg-elevated)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        No preview
      </span>
    </div>
  ) : (
    <img
      src={src}
      alt="Route thumbnail"
      onError={() => setErrored(true)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: "center",
        display: "block",
        filter: hovered ? "brightness(1.05)" : "brightness(0.95)",
      }}
    />
  );
}