import type { JobDefinition } from "../../api/types";
import { TYPE_LABELS, TYPE_COLORS } from "./jobDefinitionConstants";

// ─── DefinitionCard ───────────────────────────────────────────────────────────
// Compact list item shown in the left panel.

export function DefinitionCard({
  def,
  isSelected,
  onClick,
}: {
  def: JobDefinition;
  isSelected: boolean;
  onClick: () => void;
}) {
  const typeColor = TYPE_COLORS[def.type] ?? "var(--text-muted)";

  return (
    <div
      className={`jd-def-card${isSelected ? " jd-def-card--selected" : ""}`}
      onClick={onClick}
    >
      <div className="jd-def-card__badge-row">
        <span className="jd-type-badge" style={{ backgroundColor: typeColor }}>
          {TYPE_LABELS[def.type] ?? def.type}
        </span>
      </div>
      <div className="jd-def-card__name">{def.name}</div>
      <div className="jd-def-card__key">{def.implementationKey}</div>
    </div>
  );
}
