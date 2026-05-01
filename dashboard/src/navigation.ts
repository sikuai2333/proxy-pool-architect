import type { DashboardRoute, NavigationItem } from "./types";

export const navigationItems: NavigationItem[] = [
  { route: "overview", label: "Overview" },
  { route: "proxies", label: "Proxies" },
  { route: "providers", label: "Providers" },
  { route: "geo", label: "Geo" },
  { route: "validation", label: "Validation" },
  { route: "logs", label: "Logs" },
  { route: "settings", label: "Settings" }
];

export const routeTitles: Record<DashboardRoute, string> = {
  overview: "Overview",
  proxies: "Proxies",
  providers: "Providers",
  geo: "Geo",
  validation: "Validation",
  logs: "Logs",
  settings: "Settings"
};

export function toRoute(hash: string): DashboardRoute {
  const value = hash.replace(/^#\/?/, "") || "overview";
  const match = navigationItems.find((item) => item.route === value);
  return match?.route ?? "overview";
}
