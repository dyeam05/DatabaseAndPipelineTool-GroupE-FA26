import type { CvatAction, CvatActionState } from "../../utils/jobSegmentRunConfig";

const VARIANT_CLASSES: Record<CvatActionState, string> = {
  unavailable: "bg-[var(--bg-elevated)] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-not-allowed opacity-50",
  load:        "bg-[var(--bg-inverse)] text-[var(--text-on-inverse)] border border-[var(--border-strong)] cursor-pointer",
  in_progress: "bg-[var(--bg-elevated)] text-[var(--accent-caution)] border border-[var(--accent-caution)] cursor-not-allowed opacity-70",
  open:        "bg-[var(--bg-inverse)] text-[var(--accent-cvat)]! border border-[var(--accent-cvat)] cursor-pointer",
};

const BTN = "shrink-0 flex items-center gap-[6px] py-[var(--space-2)] px-[var(--space-3)] [font-family:var(--font-mono)] text-[9px] font-bold uppercase tracking-[0.07em] whitespace-nowrap no-underline!";

interface Props {
  action: CvatAction;
  taskUrl: string | null;
  onLoad: () => void;
}

export function CvatActionButton({ action, taskUrl, onLoad }: Props) {
  const cls = `${BTN} ${VARIANT_CLASSES[action.state]}`;

  const icon = action.state === "in_progress"
    ? <span className="w-[5px] h-[5px] rounded-full bg-[var(--accent-caution)] shrink-0 inline-block" />
    : <div className="w-3 h-3 bg-[var(--accent-cvat)] flex items-center justify-center shrink-0">
        <span className="[font-family:var(--font-mono)] font-bold text-[var(--text-on-inverse)] tracking-[0.03em] leading-none text-[7px]">CV</span>
      </div>;

  if (action.state === "open" && taskUrl) {
    return <a href={taskUrl} target="_blank" rel="noopener noreferrer" className={cls}>{icon}{action.label}</a>;
  }
  const canClick = action.state === "load";
  return <button type="button" disabled={!canClick} onClick={canClick ? onLoad : undefined} className={cls}>{icon}{action.label}</button>;
}
