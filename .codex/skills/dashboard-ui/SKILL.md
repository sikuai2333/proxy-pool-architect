---
name: dashboard-ui
description: Use this skill when implementing the ProxyPool Architect web dashboard, UI components, frontend API client, charts, tables, and settings pages.
---

# Dashboard UI Skill

## Purpose

Build a safe, clear, and maintainable dashboard for authorized proxy quality management and network diagnostics.

## Rules

1. Use TypeScript for frontend code.
2. Prefer small components with clear props.
3. Keep API types in one place.
4. Every page must support loading, empty, and error states.
5. Every destructive action must use a confirmation dialog.
6. Mask proxy credentials by default.
7. Never log secrets, proxy passwords, tokens, cookies, or credentials.
8. Use mock data when backend endpoints are missing.
9. Keep charts operational and simple.
10. Update README or docs when adding pages or env variables.

## Safety Boundary

Allowed:

- Proxy quality monitoring
- Geo and ASN distribution
- Latency and score charts
- Provider health
- Validation job status
- Safe settings such as concurrency, timeout, and cooldown

Disallowed:

- CAPTCHA bypass
- WAF bypass
- Anti-bot evasion
- Account automation
- Credential stuffing
- Stealth fingerprinting
- Target-specific block circumvention
- Any UI that helps evade detection by third-party systems

## Recommended UI Components

- AppShell
- Sidebar
- Header
- MetricCard
- ProxyTable
- ProxyFilters
- ProxyDetailDrawer
- StatusBadge
- SchemeBadge
- AnonymityBadge
- ProviderTable
- CountryDistributionChart
- ValidationJobTable
- EventLogTable
- SettingsForm

## Definition of Done

Before finishing:

1. The page renders without runtime errors.
2. Loading state exists.
3. Empty state exists.
4. Error state exists.
5. Mock data works.
6. API integration is typed if implemented.
7. README or docs are updated.
8. No unsafe features are added.
