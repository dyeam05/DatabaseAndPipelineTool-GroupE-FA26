import type { JobDefinition } from "../../api/types";
import { TYPE_LABELS, TYPE_COLORS } from "./jobDefinitionConstants";

// ─── DefinitionDetail ─────────────────────────────────────────────────────────
// Expanded view shown below the selected card.

export function DefinitionDetail({ def }: { def: JobDefinition }) {
  const typeColor = TYPE_COLORS[def.type] ?? "var(--text-muted)";
  const configEntries = Object.entries(def.config);

  return (
    <div className="jd-detail">
      <div className="jd-detail__header">
        <div>
          <div className="jd-detail__name">{def.name}</div>
          <div className="jd-detail__meta">
            ID {def.id} · Created {new Date(def.createdAt).toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="jd-detail__grid">
        <div>
          <label className="jd-label">Type</label>
          <span className="jd-type-badge" style={{ backgroundColor: typeColor }}>
            {TYPE_LABELS[def.type] ?? def.type}
          </span>
        </div>
        <div>
          <label className="jd-label">Implementation Key</label>
          <div className="jd-detail__impl-key">{def.implementationKey}</div>
        </div>
      </div>

      <div className="jd-detail__section">
        <label className="jd-label">Description</label>
        <div className="jd-detail__description">
          {def.description || "No description provided."}
        </div>
      </div>

      {configEntries.length > 0 && (
        <div>
          <label className="jd-label">Config</label>
          <div className="jd-config-block">
            {configEntries.map(([k, v]) => (
              <div key={k}>
                <span className="jd-config-key">{k}:</span>{" "}
                <span className="jd-config-value">
                  {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
