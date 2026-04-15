import { useState } from "react";
import { createJobDefinition } from "../../api/job_definitions";
import type { JobType, JobDefinitionCreate } from "../../api/types";
import { JOB_TYPES, TYPE_LABELS } from "./jobDefinitionConstants";
import { ConfigEditor } from "./ConfigEditor";

// ─── CreateForm ───────────────────────────────────────────────────────────────

export function CreateForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [type, setType] = useState<JobType>("object_detection");
  const [implKey, setImplKey] = useState("");
  const [description, setDescription] = useState("");
  const [config, setConfig] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = Boolean(name.trim() && implKey.trim() && !submitting);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);

    // Attempt to JSON-parse each value; fall back to string
    const parsedConfig: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(config)) {
      if (!k.trim()) continue;
      try { parsedConfig[k] = JSON.parse(v); }
      catch { parsedConfig[k] = v; }
    }

    const payload: JobDefinitionCreate = {
      type,
      implementation_key: implKey,
      name: name.trim(),
      config: parsedConfig,
      description: description.trim(),
    };

    try {
      await createJobDefinition(payload);
      setName("");
      setImplKey("");
      setDescription("");
      setConfig({});
      setType("object_detection");
      onCreated();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create job definition");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="jd-create-card">
      <div className="jd-create-card__header">
        <div className="jd-create-card__title">New Job Definition</div>
        <div className="jd-create-card__subtitle">
          Define a new annotation job type for routes
        </div>
      </div>

      <div className="jd-create-card__body">
        {/* Name */}
        <div>
          <label className="jd-label">Name *</label>
          <input
            className="jd-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. YOLOv8 Object Detection"
          />
        </div>

        {/* Type + Implementation Key */}
        <div className="jd-type-impl-grid">
          <div>
            <label className="jd-label">Type *</label>
            <select
              className="jd-input jd-select"
              value={type}
              onChange={(e) => setType(e.target.value as JobType)}
            >
              {JOB_TYPES.map((t) => (
                <option key={t} value={t}>{TYPE_LABELS[t]}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="jd-label">Implementation Key *</label>
            <input
              className="jd-input"
              value={implKey}
              onChange={(e) => setImplKey(e.target.value)}
              placeholder="e.g. yolov8_detector"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="jd-label">Description</label>
          <textarea
            className="jd-input jd-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this job definition does..."
          />
        </div>

        {/* Config */}
        <ConfigEditor config={config} onChange={setConfig} />

        {/* Error */}
        {error && <div className="jd-error">{error}</div>}

        {/* Submit */}
        <button
          className="jd-btn jd-btn--submit"
          onClick={handleSubmit}
          disabled={!canSubmit}
          data-submitting={submitting}
        >
          {submitting ? "Creating…" : "Create Definition"}
        </button>
      </div>
    </div>
  );
}
