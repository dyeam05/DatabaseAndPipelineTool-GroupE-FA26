import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listJobDefinitions } from "../api/job_definitions";
import { DefinitionCard } from "../components/job-definitions/DefinitionCard";
import { DefinitionDetail } from "../components/job-definitions/DefinitionDetail";
import { CreateForm } from "../components/job-definitions/CreateForm";

export default function JobDefinitions() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: definitions = [], isLoading, error } = useQuery({
    queryKey: ["job-definitions"],
    queryFn: listJobDefinitions,
    refetchInterval: 30_000,
  });

  const selectedDef = definitions.find((d) => d.id === selectedId) ?? null;

  const handleCreated = () =>
    queryClient.invalidateQueries({ queryKey: ["job-definitions"] });

  return (
    <div className="jd-page">
      <div className="jd-page__header">
        <h1 className="jd-page__title">Job Definitions</h1>
        <p className="jd-page__subtitle">
          Manage annotation job types and their configurations
        </p>
      </div>

      <div className="jd-layout">
        {/* Left — definition list */}
        <div>
          <span className="jd-section-label">
            Existing definitions ({definitions.length})
          </span>

          {isLoading && <div className="jd-loading">Loading…</div>}

          {error && (
            <div className="jd-list-error">Failed to load definitions</div>
          )}

          {!isLoading && definitions.length === 0 && !error && (
            <div className="jd-empty">No job definitions yet</div>
          )}

          <div className="jd-card-list">
            {definitions.map((def) => (
              <DefinitionCard
                key={def.id}
                def={def}
                isSelected={selectedId === def.id}
                onClick={() =>
                  setSelectedId(selectedId === def.id ? null : def.id)
                }
              />
            ))}
          </div>

          {selectedDef && (
            <div style={{ marginTop: "var(--space-4)" }}>
              <DefinitionDetail def={selectedDef} />
            </div>
          )}
        </div>

        {/* Right — create form */}
        <CreateForm onCreated={handleCreated} />
      </div>
    </div>
  );
}
