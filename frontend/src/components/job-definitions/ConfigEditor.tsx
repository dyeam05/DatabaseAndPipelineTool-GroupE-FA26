// ─── ConfigEditor ─────────────────────────────────────────────────────────────
// Dynamic key/value pair editor used inside the create form.

export function ConfigEditor({
  config,
  onChange,
}: {
  config: Record<string, string>;
  onChange: (c: Record<string, string>) => void;
}) {
  const entries = Object.entries(config);

  const addEntry = () => onChange({ ...config, "": "" });

  const updateKey = (_oldKey: string, newKey: string, idx: number) => {
    const next: Record<string, string> = {};
    Object.entries(config).forEach(([k, v], i) => {
      next[i === idx ? newKey : k] = v;
    });
    onChange(next);
  };

  const updateValue = (key: string, value: string) =>
    onChange({ ...config, [key]: value });

  const removeEntry = (key: string) => {
    const next = { ...config };
    delete next[key];
    onChange(next);
  };

  return (
    <div>
      <label className="jd-label">Config (key / value pairs)</label>
      <div className="jd-config-list">
        {entries.map(([key, value], idx) => (
          <div key={idx} className="jd-config-row">
            <input
              className="jd-input"
              placeholder="key"
              value={key}
              onChange={(e) => updateKey(key, e.target.value, idx)}
            />
            <input
              className="jd-input"
              placeholder="value"
              value={value}
              onChange={(e) => updateValue(key, e.target.value)}
            />
            <button
              className="jd-btn jd-btn--remove"
              onClick={() => removeEntry(key)}
              title="Remove entry"
            >
              ×
            </button>
          </div>
        ))}
        <button className="jd-btn jd-btn--add" onClick={addEntry}>
          + Add field
        </button>
      </div>
    </div>
  );
}
