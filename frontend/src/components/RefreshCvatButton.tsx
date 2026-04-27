import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { restartCvat } from "../api/cvat";

const COOLDOWN_SECONDS = 60;
const TOOLTIP =
  "Restart the CVAT server. Only use this if CVAT is frozen or unresponsive";

export default function RefreshCvatButton() {
  const [cooldownLeft, setCooldownLeft] = useState(0);

  const mutation = useMutation({
    mutationFn: restartCvat,
    onSuccess: () => setCooldownLeft(COOLDOWN_SECONDS),
  });

  useEffect(() => {
    if (cooldownLeft <= 0) return;
    const id = setInterval(() => setCooldownLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldownLeft]);

  const isCoolingDown = cooldownLeft > 0;
  const isPending = mutation.isPending;
  const disabled = isPending || isCoolingDown;

  const label = isPending
    ? "Restarting…"
    : isCoolingDown
    ? `Wait ${cooldownLeft}s`
    : "Refresh CVAT";

  const handleClick = () => {
    if (disabled) return;
    if (
      !confirm(
        "Restart the CVAT server?\n\n" +
          "This will end your active CVAT sessions\n" +
          "Only do this if CVAT is frozen.\n\n" +
          "After clicking OK, wait ~30 seconds, then refresh your CVAT browser tab to reconnect.",
      )
    )
      return;
    mutation.mutate();
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      title={
        mutation.isError
          ? `Restart failed: ${(mutation.error as Error).message}`
          : TOOLTIP
      }
      className="flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors border"
      style={{
        color: "var(--bg-inverse)",
        borderColor: "var(--text-on-inverse)",
        backgroundColor: "var(--text-on-inverse)",
        opacity: disabled ? 0.6 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
        fontFamily: "var(--font-mono)",
        letterSpacing: "0.05em",
      }}
    >
      <RotateCcw size={14} className={isPending ? "animate-spin" : undefined} />
      {label}
    </button>
  );
}
