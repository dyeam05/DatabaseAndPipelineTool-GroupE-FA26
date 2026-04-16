import { useState } from "react";
import type { JobDefinition } from "../../api/types";
import { TYPE_LABELS, TYPE_COLORS } from "./jobDefinitionConstants";
import { DefinitionDetail } from "./DefinitionDetail";

// ─── DefinitionCard ───────────────────────────────────────────────────────────
// Accordion card — click header to expand/collapse the detail inline.

export function DefinitionCard({
  def,
  isExpanded,
  onToggle,
  onDelete,
}: {
  def: JobDefinition;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => Promise<void>;
}) {
  const typeColor = TYPE_COLORS[def.type] ?? "var(--text-muted)";
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Would you like to delete ${def.name}? \nAll associated jobs runs will also be deleted.`)) return;
    setDeleting(true);
    try {
      await onDelete();
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className={`jd-def-card${isExpanded ? " jd-def-card--selected" : ""}`}>
      <div className="jd-def-card__trigger" onClick={onToggle}>
        <div className="jd-def-card__badge-row">
          <span className="jd-type-badge" style={{ backgroundColor: typeColor }}>
            {TYPE_LABELS[def.type] ?? def.type}
          </span>
        </div>
        <div className="jd-def-card__name">{def.name}</div>
        <div className="jd-def-card__key">{def.implementationKey}</div>
        <span className={`jd-def-card__chevron${isExpanded ? " jd-def-card__chevron--open" : ""}`}>
          ▸
        </span>
        <button
          className="jd-def-card__delete"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete definition"
          type="button"
        >
          {deleting ? "…" : "✕"}
        </button>
      </div>

      {isExpanded && (
        <div className="jd-def-card__detail">
          <DefinitionDetail def={def} />
        </div>
      )}
    </div>
  );
}
