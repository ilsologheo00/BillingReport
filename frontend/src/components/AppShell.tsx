import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../theme/ThemeContext";
import { CloudIcon, DashboardIcon, MapIcon, MoonIcon, SignOutIcon, SunIcon } from "./icons";

export function AppShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  const { theme, toggle } = useTheme();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-brand-mark">BR</span>
          <span className="sidebar-brand-name">BillingReport</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            <DashboardIcon />
            Dashboard
          </NavLink>
          <NavLink to="/ninjaone-mapping" className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            <MapIcon />
            NinjaOne mapping
          </NavLink>
          <NavLink to="/acronis-mapping" className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            <CloudIcon />
            Acronis mapping
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={toggle}>
            {theme === "light" ? <MoonIcon /> : <SunIcon />}
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>
          <button className="sidebar-link" onClick={logout}>
            <SignOutIcon />
            Sign out
          </button>
        </div>
      </aside>

      <main className="app-content">{children}</main>
    </div>
  );
}
