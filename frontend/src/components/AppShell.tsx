import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../theme/ThemeContext";
import { useLanguage } from "../i18n/LanguageContext";
import { SyncSidebarSection } from "./SyncSidebarSection";
import { CloudIcon, DashboardIcon, GlobeIcon, MapIcon, MoonIcon, SignOutIcon, SunIcon } from "./icons";

export function AppShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  const { theme, toggle } = useTheme();
  const { t, toggle: toggleLang } = useLanguage();

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
            {t("nav.dashboard")}
          </NavLink>
          <NavLink to="/ninjaone-mapping" className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            <MapIcon />
            {t("nav.ninjaMapping")}
          </NavLink>
          <NavLink to="/acronis-mapping" className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            <CloudIcon />
            {t("nav.acronisMapping")}
          </NavLink>
        </nav>

        <SyncSidebarSection />

        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={toggleLang}>
            <GlobeIcon />
            {t("nav.language")}
          </button>
          <button className="sidebar-link" onClick={toggle}>
            {theme === "light" ? <MoonIcon /> : <SunIcon />}
            {theme === "light" ? t("nav.darkMode") : t("nav.lightMode")}
          </button>
          <button className="sidebar-link" onClick={logout}>
            <SignOutIcon />
            {t("nav.signOut")}
          </button>
        </div>
      </aside>

      <main className="app-content">{children}</main>
    </div>
  );
}
