# Codex Prompt: Dashboard Phase 1 - Proxy List

Read:

- AGENTS.md
- DASHBOARD_PLAN.md
- .codex/skills/dashboard-ui/SKILL.md

Task:
Implement Dashboard Phase 1: Proxy List.

Scope:

1. Build a Proxies page.
2. Add a proxy table with columns:
   - status / pool
   - scheme
   - host
   - port
   - source
   - country
   - ASN
   - anonymity
   - latency
   - score
   - success count
   - fail count
   - last checked
   - last error
   - actions
3. Add filters:
   - pool/status
   - scheme
   - anonymity
   - country
   - source
   - minimum score
   - search by host/IP
4. Add pagination.
5. Add ProxyDetailDrawer.
6. Add DeleteProxy confirmation dialog, but use mock behavior if backend endpoint is not ready.
7. Mask proxy credentials by default.
8. Add loading, empty, and error states.
9. Use mock data first if API is not ready.
10. Do not implement anti-bot, stealth, CAPTCHA, or WAF-related features.

Definition of done:

- Proxies page works with mock data.
- Filters and pagination work.
- Detail drawer works.
- Delete confirmation exists.
- README or dashboard docs are updated.
