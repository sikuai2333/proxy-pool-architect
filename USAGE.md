# 如何使用这些文件

## 1. 新建项目目录

```bash
mkdir proxy-pool-architect
cd proxy-pool-architect
git init
```

## 2. 把这些文件复制到项目根目录

复制后，你的目录应该像这样：

```text
proxy-pool-architect/
├─ PROJECT_PLAN.md
├─ AGENTS.md
├─ USAGE.md
├─ docs/
│  ├─ codex-kickoff-prompt.md
│  └─ prompts/
│     ├─ phase-1-storage.md
│     ├─ phase-2-providers.md
│     ├─ phase-3-validators.md
│     ├─ phase-4-api.md
│     ├─ phase-5-scheduler.md
│     └─ phase-6-dashboard.md
└─ .codex/
   ├─ config.toml
   └─ skills/
      ├─ safe-networking/SKILL.md
      ├─ async-validator/SKILL.md
      ├─ test-and-quality/SKILL.md
      ├─ fastapi-feature/SKILL.md
      └─ redis-storage/SKILL.md
```

## 3. 第一次启动 Codex

打开 Codex 后，在项目根目录输入：

```text
Read AGENTS.md, PROJECT_PLAN.md, and docs/codex-kickoff-prompt.md.
Implement Phase 0 only.
Keep the change small, tested, documented, and safe.
Do not implement future phases.
```

Phase 0 的目标只是初始化项目骨架，不要让 Codex 一次性写完整系统。

## 4. 每个阶段单独执行

Phase 0 完成并能跑通后，再执行 Phase 1：

```text
Read AGENTS.md, PROJECT_PLAN.md, and docs/prompts/phase-1-storage.md.
Implement Phase 1 only.
Do not implement provider fetching or validators yet.
Run tests and lint before finishing.
```

然后依次执行：

```text
docs/prompts/phase-2-providers.md
docs/prompts/phase-3-validators.md
docs/prompts/phase-4-api.md
docs/prompts/phase-5-scheduler.md
docs/prompts/phase-6-dashboard.md
```

## 5. 推荐 Codex 使用习惯

不要这样说：

```text
帮我把整个代理池项目全部写完。
```

要这样说：

```text
只实现当前 Phase。先读 AGENTS.md 和 PROJECT_PLAN.md，再读对应阶段 prompt。实现后运行 pytest、ruff 和 mypy，最后总结改动文件。
```

## 6. 每次报错时怎么给 Codex

把完整错误贴给 Codex：

```text
The command failed:

<粘贴完整错误日志>

Please diagnose the cause, propose the smallest fix, implement it, and run the relevant tests again.
```

不要一次贴多个无关错误。

## 7. 每次完成后要求 Codex 自查

可以输入：

```text
Before finishing, review your changes against AGENTS.md Definition of Done.
Check pytest, ruff, mypy, docs, safety rules, secrets, timeouts, and concurrency limits.
```

## 8. MCP 怎么用

`.codex/config.toml` 里已经放了示例 MCP 配置，但默认注释掉。你可以先不启用 MCP，等项目跑起来后再逐个启用。

建议优先级：

1. Context7 / docs MCP：查 FastAPI、Redis、httpx、aiohttp 文档。
2. Playwright MCP：后期做 Dashboard 时检查页面。
3. Filesystem MCP：让 Codex 更稳定地读取项目文件。
4. GitHub MCP：后期管理 issue、PR、CI。

## 9. Skills 怎么用

这些 skills 是给 Codex 的“固定工作习惯”。你不用手动执行它们，只要让 Codex 读取项目，Codex 会在需要时参考对应 skill。

建议你在提示词里明确要求：

```text
Use the relevant skills under .codex/skills, especially safe-networking, test-and-quality, redis-storage, and async-validator.
```

## 10. 第一条最推荐提示词

```text
Read AGENTS.md, PROJECT_PLAN.md, docs/codex-kickoff-prompt.md, and relevant skills under .codex/skills.
Implement Phase 0 only.
Do not implement future phases.
After coding, run pytest, ruff check ., and mypy app if applicable.
Summarize changed files and any commands that could not be run.
```
