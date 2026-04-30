# Codex Kickoff Prompt

Copy this prompt into Codex when starting the project.

```text
You are working on a new project from scratch: ProxyPool Architect.

Goal:
Build a modern Python 3.11+ proxy pool system with FastAPI, Redis, async validation, scoring, three-layer pools, and Docker Compose.

Important safety boundary:
This project is for lawful, authorized network testing and proxy quality management. Do not implement anti-bot bypass, CAPTCHA bypass, credential abuse, account automation, stealth evasion, or attack features.

Please implement Phase 0 only.

Phase 0 requirements:
1. Create a Python project using pyproject.toml.
2. Add FastAPI app entrypoint at app/main.py.
3. Add config module using pydantic-settings.
4. Add loguru logging setup.
5. Add Redis service in docker-compose.yml.
6. Add Dockerfile.
7. Add /health endpoint.
8. Add pytest setup.
9. Add ruff and mypy configuration.
10. Add README with setup and run instructions.
11. Add AGENTS.md if missing.
12. Make sure the project runs with:
   - docker compose up -d
   - uv run uvicorn app.main:app --reload
   - uv run pytest
   - uv run ruff check .

Deliverables:
- Working code
- Tests
- README update
- Clear summary of changed files

Do not implement Phase 1 yet.
```
