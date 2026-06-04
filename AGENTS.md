# Agent Rules

## Python (UV)

- Deps: `uv sync`, `uv add/rm <pkg>`
- Run: `uv run python <script>`

## Shell

- Use **PowerShell**

## Commits

- Format: `<type>(<scope>): <subject>`
- Types: feat, fix, docs, style, refactor, perf, test, chore, ci, revert
- Example: `feat(auth): add login endpoint`

## Intent Money OS - 技术栈快照

### 当前配置（2026-05-20 更新）

- **数据库**: SQLite（aiosqlite 异步驱动，替代 PostgreSQL）
  - 文件: `intent_money.db`（位于 backend 目录下）
  - Alembic 迁移已启用 `render_as_batch=True` 兼容 SQLite
- **AI 模型**: DeepSeek V4 Flash（via OpenRouter API）
  - SDK: `openai`（AsyncOpenAI），替代 `anthropic`
  - 配置项: `AI_API_KEY`, `AI_BASE_URL`（默认 `https://openrouter.ai/api/v1`）, `AI_MODEL`
  - 默认模型: `deepseek/deepseek-chat-v3-0324:free`
- **部署**: Docker Compose 已移除 PostgreSQL 容器，仅保留 FastAPI + Frontend + Nginx

## Journey memory

Use `journey/` as the shared project memory across agent sessions.

- Read `journey/design.md` first at the start of each session. It is the canonical snapshot of the project: current strategy, key design decisions, trade-offs, constraints, and scope.
- Use `journey/logs/` for chronological process notes, progress, experiments, and failed paths.
- Use `journey/research/` for research notes and background findings.
- Update `journey/design.md` whenever the effective understanding of the project changes. Do not leave important decisions or trade-offs only in logs.

For any new project, planning-focused request, or sufficiently complex task, start with a fresh plan and write it to `journey/plans/YYYY-MM-DD-{title}.md` before implementing. Treat files in `journey/plans/` as the canonical plans. As work progresses, record concise updates in `journey/logs/YYYY-MM-DD-{title}.md` using the same date and title convention. In chat, provide only a brief summary and the relevant file path(s).
