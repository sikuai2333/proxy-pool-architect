import type { DashboardRoute, NavigationItem } from "./types";

export const navigationItems: NavigationItem[] = [
  { route: "overview", labelKey: "nav.overview" },
  { route: "proxies", labelKey: "nav.proxies" },
  { route: "providers", labelKey: "nav.providers" },
  { route: "geo", labelKey: "nav.geo" },
  { route: "validation", labelKey: "nav.validation" },
  { route: "logs", labelKey: "nav.logs" },
  { route: "settings", labelKey: "nav.settings" },
  { route: "doc", labelKey: "nav.doc" }
];

export const routeTitleKeys: Record<DashboardRoute, NavigationItem["labelKey"]> = {
  overview: "nav.overview",
  proxies: "nav.proxies",
  providers: "nav.providers",
  geo: "nav.geo",
  validation: "nav.validation",
  logs: "nav.logs",
  settings: "nav.settings",
  doc: "nav.doc"
};

export function toRoute(hash: string): DashboardRoute {
  const value = hash.replace(/^#\/?/, "") || "overview";
  const match = navigationItems.find((item) => item.route === value);
  return match?.route ?? "overview";
}
