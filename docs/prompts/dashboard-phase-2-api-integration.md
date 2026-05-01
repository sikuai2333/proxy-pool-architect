# Codex Prompt: Dashboard Phase 2 - API Integration

Read:

- AGENTS.md
- DASHBOARD_PLAN.md
- .codex/skills/dashboard-ui/SKILL.md

Task:
Implement Dashboard Phase 2: API integration.

Scope:

1. Add typed API client under `dashboard/src/lib/api` or equivalent.
2. Add environment variable for backend URL:
   - NEXT_PUBLIC_API_BASE_URL or VITE_API_BASE_URL
3. Connect these endpoints if available:
   - GET /health
   - GET /stats
   - GET /proxy/list
   - GET /proxy/{proxy_id}
   - DELETE /proxy/{proxy_id}
4. If endpoints are missing, keep mock fallback and add TODOs.
5. Add request timeout and readable error handling.
6. Ensure no proxy credentials are logged.
7. Add loading, empty, and error states for all connected pages.
8. Update README with API base URL configuration.

Definition of done:

- Dashboard can run in mock mode.
- Dashboard can run against backend if endpoints exist.
- API errors are displayed clearly.
- No secrets are exposed.
