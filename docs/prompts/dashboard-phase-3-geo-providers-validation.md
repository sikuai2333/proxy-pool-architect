# Codex Prompt: Dashboard Phase 3 - Geo, Providers, Validation

Read:

- AGENTS.md
- DASHBOARD_PLAN.md
- .codex/skills/dashboard-ui/SKILL.md

Task:
Implement Dashboard Phase 3: Geo, Providers, and Validation pages.

Scope:

1. Geo page:
   - Country distribution chart
   - ASN distribution table
   - Average latency by country
   - Elite proxy count by country

2. Providers page:
   - Provider list table
   - Enabled/disabled status
   - Last fetch time
   - Fetched count
   - Valid count
   - Error summary

3. Validation page:
   - Recent validation jobs
   - Success/failure trend
   - Common error types
   - Timeout rate
   - Dead proxy count

4. Use mock data if backend endpoints are missing.
5. Keep all API calls typed.
6. Add loading, empty, and error states.
7. Update docs.

Safety:
These pages must show operational status only. Do not add features for bypassing detection, CAPTCHA, WAF, rate limits, or target-specific restrictions.
