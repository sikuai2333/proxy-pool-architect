# How to Use These Dashboard Files with Codex

## 1. Copy files into your project

Copy these files into the root of your existing ProxyPool Architect project:

```text
DASHBOARD_PLAN.md
USAGE_DASHBOARD.md
docs/prompts/dashboard-kickoff.md
docs/prompts/dashboard-phase-1-proxy-list.md
docs/prompts/dashboard-phase-2-api-integration.md
docs/prompts/dashboard-phase-3-geo-providers-validation.md
docs/prompts/dashboard-phase-4-settings-polish.md
docs/ui/api-contract.md
docs/ui/mock-data-spec.md
.codex/skills/dashboard-ui/SKILL.md
```

If you already have `.codex/skills`, merge the `dashboard-ui` skill into it.

## 2. First Codex command

Use this prompt first:

```text
Read AGENTS.md, PROJECT_PLAN.md, DASHBOARD_PLAN.md, docs/ui/api-contract.md, docs/ui/mock-data-spec.md, and .codex/skills/dashboard-ui/SKILL.md.

Then read docs/prompts/dashboard-kickoff.md and implement Dashboard Phase 0 only.

Do not implement future phases.
Do not modify backend code unless absolutely required.
Use mock data first if backend APIs are incomplete.
After coding, run the relevant frontend build/lint/test commands if available.
Summarize changed files and commands run.
```

## 3. Development order

Use these prompts in order:

```text
docs/prompts/dashboard-kickoff.md
docs/prompts/dashboard-phase-1-proxy-list.md
docs/prompts/dashboard-phase-2-api-integration.md
docs/prompts/dashboard-phase-3-geo-providers-validation.md
docs/prompts/dashboard-phase-4-settings-polish.md
```

## 4. Important instruction for Codex

Do not ask Codex to build the entire dashboard at once. Ask it to implement one phase at a time.

## 5. Recommended frontend commands

Depending on the stack Codex chooses:

### Vite

```bash
cd dashboard
npm install
npm run dev
npm run build
```

### Next.js

```bash
cd dashboard
npm install
npm run dev
npm run build
```

## 6. Backend API

If backend endpoints are missing, Codex should keep the dashboard in mock mode and add TODOs instead of blocking development.

## 7. Safety wording

Keep the project framed as:

```text
authorized proxy quality management and network diagnostics
```

Avoid wording such as:

```text
bypass detection
anti-bot evasion
high-risk automation
WAF bypass
CAPTCHA bypass
```
