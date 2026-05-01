import { useEffect, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { dashboardDataMode } from "./lib/api-client";
import { routeTitles, toRoute } from "./navigation";
import { GeoPage } from "./pages/GeoPage";
import { LogsPage } from "./pages/LogsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProvidersPage } from "./pages/ProvidersPage";
import { ProxiesPage } from "./pages/ProxiesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ValidationPage } from "./pages/ValidationPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import type { DashboardRoute } from "./types";

type ThemeMode = "dark" | "light";

function useHashRoute() {
  const [route, setRoute] = useState<DashboardRoute>(() => toRoute(window.location.hash));

  useEffect(() => {
    function handleHashChange() {
      setRoute(toRoute(window.location.hash));
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return route;
}

function useThemeMode() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const persisted = window.localStorage.getItem("dashboard-theme");
    return persisted === "light" ? "light" : "dark";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("dashboard-theme", theme);
  }, [theme]);

  return {
    theme,
    toggleTheme() {
      setTheme((current) => (current === "dark" ? "light" : "dark"));
    }
  };
}

function renderRoute(route: DashboardRoute) {
  if (route === "overview") {
    return <OverviewPage />;
  }

  if (route === "proxies") {
    return <ProxiesPage />;
  }

  if (route === "geo") {
    return <GeoPage />;
  }

  if (route === "providers") {
    return <ProvidersPage />;
  }

  if (route === "validation") {
    return <ValidationPage />;
  }

  if (route === "logs") {
    return <LogsPage />;
  }

  if (route === "settings") {
    return <SettingsPage />;
  }

  return <PlaceholderPage title={routeTitles[route]} />;
}

export function App() {
  const activeRoute = useHashRoute();
  const modeLabel = dashboardDataMode === "live" ? "Live API" : "Mock data";
  const { theme, toggleTheme } = useThemeMode();

  return (
    <AppShell
      activeRoute={activeRoute}
      modeLabel={modeLabel}
      themeLabel={theme === "dark" ? "Light theme" : "Dark theme"}
      onToggleTheme={toggleTheme}
    >
      {renderRoute(activeRoute)}
    </AppShell>
  );
}
