# Codex Prompt: Dashboard Kickoff

Read these files first:

- AGENTS.md
- PROJECT_PLAN.md
- DASHBOARD_PLAN.md
- .codex/skills/dashboard-ui/SKILL.md

Task:
Implement Dashboard Phase 0 only.

Goal:
Create a modern web dashboard skeleton for ProxyPool Architect.

Requirements:

1. Create a dashboard frontend app under `dashboard/`.
2. Use TypeScript and React.
3. Prefer Next.js or Vite. If the repository already has a frontend standard, follow it.
4. Add a clean app shell with sidebar, header, and main content area.
5. Add routes/pages:
   - Overview
   - Proxies
   - Providers
   - Geo
   - Validation
   - Logs
   - Settings
6. Implement the Overview page with mock metrics:
   - Raw proxies
   - Checked proxies
   - Elite proxies
   - Dead proxies
   - Average latency
   - Success rate
   - Redis status
   - Scheduler status
7. Add mock data and a mock API client.
8. Add loading, empty, and error UI components.
9. Add README instructions for running the dashboard.
10. Do not implement backend changes unless absolutely required.
11. Do not implement future dashboard phases.

Safety boundary:
The dashboard is for authorized proxy quality management and network diagnostics. Do not add anti-bot bypass, CAPTCHA bypass, WAF bypass, credential abuse, fake account automation, stealth evasion, or target-specific circumvention features.

Definition of done:

- Dashboard starts locally.
- Overview page renders with mock data.
- Sidebar navigation works.
- README documents how to run it.
- No secrets or unsafe features are introduced.
- Summarize changed files and commands run.
