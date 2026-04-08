import { NavLink } from "react-router-dom";
import { Settings, Route } from "lucide-react";

const navItems = [
  { to: "/routes", label: "Routes", icon: Route },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function TopBar() {
  return (
    <header
      className="fixed left-0 right-0 flex items-center px-6 gap-8 z-50"
      style={{
        top: "3px", // sits just below the racing stripe
        height: "var(--topbar-height)",
        backgroundColor: "var(--bg-inverse)",
        borderBottom: "1px solid var(--border-black)",
      }}
    >
      {/* App name */}
      <span
        className="text-sm font-bold tracking-widest uppercase select-none"
        style={{ fontFamily: "var(--font-mono)", color: "var(--text-on-inverse)" }}
      >
        OpenPilot
      </span>

      {/* Nav links */}
      <nav className="flex items-center gap-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className="flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors no-underline"
            style={({ isActive }) => ({
              color: isActive ? "var(--bg-inverse)" : "var(--text-on-inverse)",
              backgroundColor: isActive ? "var(--text-on-inverse)" : "transparent",
              opacity: isActive ? 1 : 0.65,
            })}
          >
            <Icon size={14} />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
