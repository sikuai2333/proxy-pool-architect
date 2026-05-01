import type { ReactNode } from "react";

import { navigationItems, routeTitles } from "../../navigation";
import type { DashboardRoute } from "../../types";

interface AppShellProps {
  activeRoute: DashboardRoute;
  modeLabel: string;
  themeLabel: string;
  onToggleTheme: () => void;
  children: ReactNode;
}

export function AppShell({
  activeRoute,
  modeLabel,
  themeLabel,
  onToggleTheme,
  children
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Dashboard navigation">
        <div className="brand">
          <span className="brand-mark">P</span>
          <span>ProxyPool Architect</span>
        </div>
        <nav className="nav-list">
          {navigationItems.map((item) => (
            <a
              key={item.route}
              className={item.route === activeRoute ? "nav-link nav-link-active" : "nav-link"}
              href={`#/${item.route}`}
              aria-current={item.route === activeRoute ? "page" : undefined}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <h1>{routeTitles[activeRoute]}</h1>
          <div className="topbar-actions">
            <button className="button button-secondary" type="button" onClick={onToggleTheme}>
              {themeLabel}
            </button>
            <span className="mode-badge">{modeLabel}</span>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
