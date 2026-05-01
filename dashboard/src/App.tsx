import { useEffect, useState } from "react";

import { ErrorState } from "./components/common/ErrorState";
import { LoadingState } from "./components/common/LoadingState";
import { AppShell } from "./components/layout/AppShell";
import { useI18n } from "./i18n";
import { dashboardApi, dashboardDataMode } from "./lib/api-client";
import { routeTitleKeys, toRoute } from "./navigation";
import { GeoPage } from "./pages/GeoPage";
import { LoginPage } from "./pages/LoginPage";
import { LogsPage } from "./pages/LogsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProvidersPage } from "./pages/ProvidersPage";
import { ProxiesPage } from "./pages/ProxiesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ValidationPage } from "./pages/ValidationPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import type { AuthSessionStatus, DashboardRoute } from "./types";

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

function renderRoute(route: DashboardRoute, title: string) {
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

  return <PlaceholderPage title={title} />;
}

export function App() {
  const activeRoute = useHashRoute();
  const { t } = useI18n();
  const modeLabel = dashboardDataMode === "live" ? t("mode.live") : t("mode.mock");
  const { theme, toggleTheme } = useThemeMode();
  const activeTitle = t(routeTitleKeys[activeRoute]);
  const [authStatus, setAuthStatus] = useState<AuthSessionStatus | null>(
    dashboardDataMode === "live"
      ? null
      : { enabled: false, authenticated: false, auth_method: "disabled" }
  );
  const [authLoading, setAuthLoading] = useState(dashboardDataMode === "live");
  const [authError, setAuthError] = useState<string | null>(null);

  async function loadAuthStatus() {
    setAuthLoading(true);
    setAuthError(null);
    try {
      const next = await dashboardApi.getAuthSession();
      setAuthStatus(next);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : t("auth.sessionError"));
    } finally {
      setAuthLoading(false);
    }
  }

  useEffect(() => {
    if (dashboardDataMode !== "live") {
      return;
    }

    void loadAuthStatus();
  }, []);

  async function handleLogout() {
    try {
      const next = await dashboardApi.logout();
      setAuthStatus(next);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : t("auth.logoutError"));
    }
  }

  if (dashboardDataMode === "live" && authLoading) {
    return <LoadingState label={t("auth.loading")} />;
  }

  if (dashboardDataMode === "live" && authError) {
    return <ErrorState title={t("auth.sessionFailed")} message={authError} />;
  }

  if (dashboardDataMode === "live" && authStatus?.enabled && !authStatus.authenticated) {
    return <LoginPage onLoggedIn={loadAuthStatus} />;
  }

  return (
    <AppShell
      activeRoute={activeRoute}
      modeLabel={modeLabel}
      themeLabel={theme === "dark" ? t("theme.light") : t("theme.dark")}
      onToggleTheme={toggleTheme}
      userLabel={authStatus?.authenticated ? authStatus.username ?? t("auth.adminUser") : null}
      logoutLabel={authStatus?.enabled ? t("auth.logout") : null}
      onLogout={authStatus?.enabled ? () => void handleLogout() : undefined}
    >
      {renderRoute(activeRoute, activeTitle)}
    </AppShell>
  );
}
