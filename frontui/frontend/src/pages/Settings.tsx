import { useState, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

type ConnectionState = "idle" | "checking" | "connected" | "failed";

interface CvatConfig {
  host: string;
  port: string;
  username: string;
  password: string;
  useHttps: boolean;
}

interface PostgresConfig {
  host: string;
  port: string;
  database: string;
  username: string;
  password: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function simulateCheck(
  onResult: (state: "connected" | "failed") => void
) {
  // Replace with real fetch/ping once backend is wired up
  const ok = Math.random() > 0.35;
  setTimeout(() => onResult(ok ? "connected" : "failed"), 1200 + Math.random() * 600);
}

// ─── StatusIndicator ──────────────────────────────────────────────────────────

function StatusIndicator({ state }: { state: ConnectionState }) {
  const map: Record<ConnectionState, { color: string; label: string; pulse: boolean }> = {
    idle:      { color: "var(--border-strong)",  label: "Not checked",  pulse: false },
    checking:  { color: "var(--accent-caution)", label: "Checking…",   pulse: true  },
    connected: { color: "var(--accent-go)",      label: "Connected",   pulse: false },
    failed:    { color: "var(--accent-alert)",   label: "Unreachable", pulse: false },
  };
  const { color, label, pulse } = map[state];

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
      <div style={{ position: "relative", width: "8px", height: "8px", flexShrink: 0 }}>
        {pulse && (
          <div
            style={{
              position: "absolute",
              inset: "-3px",
              borderRadius: "50%",
              backgroundColor: color,
              opacity: 0.3,
              animation: "ping 1s cubic-bezier(0,0,0.2,1) infinite",
            }}
          />
        )}
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            backgroundColor: color,
          }}
        />
      </div>
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: color,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
        }}
      >
        {label}
      </span>
    </div>
  );
}

// ─── SectionHeader ────────────────────────────────────────────────────────────

function SectionHeader({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div style={{ marginBottom: "var(--space-4)" }}>
      <h2
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: "var(--text-base)",
          fontWeight: 600,
          color: "var(--text-primary)",
          margin: 0,
        }}
      >
        {title}
      </h2>
      <p
        style={{
          fontSize: "var(--text-sm)",
          color: "var(--text-secondary)",
          marginTop: "2px",
          minHeight: "42px",
        }}
      >
        {description}
      </p>
    </div>
  );
}

// ─── Field ────────────────────────────────────────────────────────────────────

function Field({
  label,
  children,
  mono,
}: {
  label: string;
  children: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <label
        style={{
          display: "block",
          fontSize: "10px",
          fontFamily: "var(--font-mono)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "var(--text-muted)",
          fontWeight: 600,
          marginBottom: "var(--space-1)",
        }}
      >
        {label}
      </label>
      <div style={{ fontFamily: mono ? "var(--font-mono)" : undefined }}>
        {children}
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "var(--space-2) var(--space-3)",
  border: "1px solid var(--border-subtle)",
  backgroundColor: "var(--bg-primary)",
  fontFamily: "var(--font-mono)",
  fontSize: "var(--text-sm)",
  color: "var(--text-primary)",
  outline: "none",
  boxSizing: "border-box",
};

// ─── CvatSettings ─────────────────────────────────────────────────────────────

function CvatSettings() {
  const [cfg, setCfg] = useState<CvatConfig>({
    host: "localhost",
    port: "8080",
    username: "admin",
    password: "",
    useHttps: false,
  });
  const [connState, setConnState] = useState<ConnectionState>("idle");
  const [showPassword, setShowPassword] = useState(false);
  const [saved, setSaved] = useState(false);

  const derivedUrl = `${cfg.useHttps ? "https" : "http"}://${cfg.host}:${cfg.port}`;

  const handleCheck = useCallback(() => {
    setConnState("checking");
    simulateCheck((result) => setConnState(result));
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div
      style={{
        border: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-surface)",
      }}
    >
      {/* Card header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "var(--space-4) var(--space-5)",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              backgroundColor: "var(--accent-cvat)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                fontSize: "8px",
                color: "var(--text-on-inverse)",
                letterSpacing: "0.04em",
              }}
            >
              CV
            </span>
          </div>
          <div>
            <div
              style={{
                fontSize: "var(--text-sm)",
                fontWeight: 600,
                color: "var(--text-primary)",
              }}
            >
              CVAT
            </div>
            <div
              style={{
                fontSize: "10px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)",
              }}
            >
              {derivedUrl}
            </div>
          </div>
        </div>
        <StatusIndicator state={connState} />
      </div>

      {/* Fields */}
      <div
        style={{
          padding: "var(--space-5)",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-4)",
        }}
      >
        <Field label="Host" mono>
          <input
            style={inputStyle}
            value={cfg.host}
            onChange={(e) => setCfg({ ...cfg, host: e.target.value })}
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Port" mono>
          <input
            style={inputStyle}
            value={cfg.port}
            onChange={(e) => setCfg({ ...cfg, port: e.target.value })}
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Superuser Username" mono>
          <input
            style={inputStyle}
            value={cfg.username}
            onChange={(e) => setCfg({ ...cfg, username: e.target.value })}
            autoComplete="username"
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Password" mono>
          <div style={{ position: "relative" }}>
            <input
              style={{ ...inputStyle, paddingRight: "36px" }}
              type={showPassword ? "text" : "password"}
              value={cfg.password}
              placeholder="••••••••"
              onChange={(e) => setCfg({ ...cfg, password: e.target.value })}
              autoComplete="current-password"
              onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((p) => !p)}
              style={{
                position: "absolute",
                right: "var(--space-2)",
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                padding: "2px 4px",
              }}
            >
              {showPassword ? "hide" : "show"}
            </button>
          </div>
        </Field>

        <Field label="Protocol">
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            {(["http", "https"] as const).map((proto) => {
              const active = cfg.useHttps === (proto === "https");
              return (
                <button
                  key={proto}
                  type="button"
                  onClick={() => setCfg({ ...cfg, useHttps: proto === "https" })}
                  style={{
                    padding: "var(--space-2) var(--space-3)",
                    border: `1px solid ${active ? "var(--border-black)" : "var(--border-subtle)"}`,
                    backgroundColor: active ? "var(--bg-inverse)" : "var(--bg-primary)",
                    color: active ? "var(--text-on-inverse)" : "var(--text-secondary)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "var(--text-xs)",
                    cursor: "pointer",
                    fontWeight: active ? 700 : 400,
                  }}
                >
                  {proto}
                </button>
              );
            })}
          </div>
        </Field>
      </div>

      {/* Actions */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          padding: "var(--space-3) var(--space-5)",
          borderTop: "1px solid var(--border-subtle)",
          justifyContent: "flex-end",
        }}
      >
        <button
          type="button"
          onClick={handleCheck}
          disabled={connState === "checking"}
          style={{
            padding: "var(--space-2) var(--space-4)",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-primary)",
            color: connState === "checking" ? "var(--text-muted)" : "var(--text-primary)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            cursor: connState === "checking" ? "not-allowed" : "pointer",
          }}
        >
          {connState === "checking" ? "Checking…" : "Test Connection"}
        </button>
        <button
          type="button"
          onClick={handleSave}
          style={{
            padding: "var(--space-2) var(--space-4)",
            border: "none",
            backgroundColor: saved ? "var(--accent-go)" : "var(--bg-inverse)",
            color: "var(--text-on-inverse)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            cursor: "pointer",
            fontWeight: 700,
            transition: "background-color var(--transition-base)",
          }}
        >
          {saved ? "✓ Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

// ─── PostgresSettings ─────────────────────────────────────────────────────────

function PostgresSettings() {
  const [cfg, setCfg] = useState<PostgresConfig>({
    host: "localhost",
    port: "5432",
    database: "openpilot",
    username: "postgres",
    password: "",
  });
  const [connState, setConnState] = useState<ConnectionState>("idle");
  const [showPassword, setShowPassword] = useState(false);
  const [saved, setSaved] = useState(false);

  const derivedDsn = `postgresql://${cfg.username}@${cfg.host}:${cfg.port}/${cfg.database}`;

  const handleCheck = useCallback(() => {
    setConnState("checking");
    simulateCheck((result) => setConnState(result));
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div
      style={{
        border: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-surface)",
      }}
    >
      {/* Card header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "var(--space-4) var(--space-5)",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              backgroundColor: "var(--accent-postgres)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                fontSize: "8px",
                color: "var(--text-on-inverse)",
                letterSpacing: "0.02em",
              }}
            >
              PG
            </span>
          </div>
          <div>
            <div
              style={{
                fontSize: "var(--text-sm)",
                fontWeight: 600,
                color: "var(--text-primary)",
              }}
            >
              PostgreSQL
            </div>
            <div
              style={{
                fontSize: "10px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                maxWidth: "260px",
              }}
            >
              {derivedDsn}
            </div>
          </div>
        </div>
        <StatusIndicator state={connState} />
      </div>

      {/* Fields */}
      <div
        style={{
          padding: "var(--space-5)",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-4)",
        }}
      >
        <Field label="Host" mono>
          <input
            style={inputStyle}
            value={cfg.host}
            onChange={(e) => setCfg({ ...cfg, host: e.target.value })}
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Port" mono>
          <input
            style={inputStyle}
            value={cfg.port}
            onChange={(e) => setCfg({ ...cfg, port: e.target.value })}
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Database" mono>
          <input
            style={inputStyle}
            value={cfg.database}
            onChange={(e) => setCfg({ ...cfg, database: e.target.value })}
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Username" mono>
          <input
            style={inputStyle}
            value={cfg.username}
            onChange={(e) => setCfg({ ...cfg, username: e.target.value })}
            autoComplete="username"
            onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
          />
        </Field>

        <Field label="Password" mono>
          <div style={{ position: "relative" }}>
            <input
              style={{ ...inputStyle, paddingRight: "36px" }}
              type={showPassword ? "text" : "password"}
              value={cfg.password}
              placeholder="••••••••"
              onChange={(e) => setCfg({ ...cfg, password: e.target.value })}
              autoComplete="current-password"
              onFocus={(e) => (e.target.style.borderColor = "var(--border-black)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((p) => !p)}
              style={{
                position: "absolute",
                right: "var(--space-2)",
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                padding: "2px 4px",
              }}
            >
              {showPassword ? "hide" : "show"}
            </button>
          </div>
        </Field>

        {/* Read-only DSN preview */}
        <Field label="Connection String" mono>
          <div
            style={{
              padding: "var(--space-2) var(--space-3)",
              border: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-elevated)",
              fontFamily: "var(--font-mono)",
              fontSize: "var(--text-xs)",
              color: "var(--text-secondary)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            title={derivedDsn}
          >
            {derivedDsn}
          </div>
        </Field>
      </div>

      {/* Actions */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          padding: "var(--space-3) var(--space-5)",
          borderTop: "1px solid var(--border-subtle)",
          justifyContent: "flex-end",
        }}
      >
        <button
          type="button"
          onClick={handleCheck}
          disabled={connState === "checking"}
          style={{
            padding: "var(--space-2) var(--space-4)",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-primary)",
            color: connState === "checking" ? "var(--text-muted)" : "var(--text-primary)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            cursor: connState === "checking" ? "not-allowed" : "pointer",
          }}
        >
          {connState === "checking" ? "Checking…" : "Test Connection"}
        </button>
        <button
          type="button"
          onClick={handleSave}
          style={{
            padding: "var(--space-2) var(--space-4)",
            border: "none",
            backgroundColor: saved ? "var(--accent-go)" : "var(--bg-inverse)",
            color: "var(--text-on-inverse)",
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            cursor: "pointer",
            fontWeight: 700,
            transition: "background-color var(--transition-base)",
          }}
        >
          {saved ? "✓ Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export default function Settings() {
  return (
    <div style={{ paddingBottom: "var(--space-12)" }}>

      {/* Page header */}
      <div style={{ marginBottom: "var(--space-8)" }}>
        <h1
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "var(--text-2xl)",
            fontWeight: 600,
            color: "var(--text-primary)",
            margin: 0,
          }}
        >
          Settings
        </h1>
        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "var(--text-sm)",
            marginTop: "2px",
          }}
        >
          Pipeline configuration and service connections
        </p>
      </div>

      {/* Side-by-side cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "var(--space-6)",
          alignItems: "start",
        }}
      >
        <div style={{ minWidth: 0 }}>
          <SectionHeader
            title="CVAT"
            description="Annotation tool connection. Credentials are used to create tasks and manage annotation jobs as a superuser."
          />
          <CvatSettings />
        </div>

        <div style={{ minWidth: 0 }}>
          <SectionHeader
            title="PostgreSQL"
            description="Annotation metadata store. Used to read route and segment records and write annotation results."
          />
          <PostgresSettings />
        </div>
      </div>

      {/* Ping animation keyframe injected inline */}
      <style>{`
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
