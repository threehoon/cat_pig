---
name: app-pet
description: Use when developing this WeChat miniprogram or FastAPI backend — adding pages, modules, mock, services, WXML/Sass/Skyline UI, API fields — or when the user says 按 skill 开发, 加页面, mock 接口, or /app-pet.
---

# app-pet

This repo is a WeChat **native** miniprogram (WXML + TypeScript + Sass, Skyline) plus a later FastAPI + PostgreSQL backend. Product: pet album / plaza / image-to-video / points.

Facts live in `docs/`. This skill is the **router**, not a second copy of the rules.

## Every turn

1. Read [AGENTS.md](../../../AGENTS.md) (hard rules + which doc to open).
2. Read [docs/progress.md](../../../docs/progress.md) for the current phase. Confirm against `git log -5 --oneline` and `git status -sb` before coding — HEAD can already contain work the progress file still lists as next. If they disagree, report and ask; do not start from the stale slice. Do that phase's work; do not skip ahead.
3. Open only the docs AGENTS.md names for this task.
4. Writing, moving or splitting code? Also read [docs/framework/code-standards.md](../../../docs/framework/code-standards.md) — naming, module weight, thin dispatch layers, file ownership when several agents work in parallel, verification, handoff.

Installed skill catalog: [docs/framework/skills.md](../../../docs/framework/skills.md).

This skill is shared by Grok, Codex, Claude Code and Hermes. The one real copy is `.grok/skills/`; Codex and Hermes read it through `.agents/skills` (Hermes: after local `hermes skills trust`). Claude Code reads a synced copy in `.claude/skills/`. Edit `.grok/skills/` only. Do not add `.hermes.md` — Hermes would load it instead of AGENTS.md.

## Companion skills

| Task | Invoke |
|---|---|
| New feature / unclear UX | `grill-with-docs` then `to-spec` |
| Page or visual UI | `frontend-design` + matching `skyline-*` |
| List / scroll / form / swiper | `skyline-components`, `skyline-scroll-api` |
| WXSS / layout bugs | `skyline-wxss` |
| `app.json` / page json / Skyline flags | `skyline-config` |
| Mock / services / FastAPI schema | none of the UI skills; follow the contract |
| FastAPI (phase 1+) | `fastapi` |
| Tests | `tdd` |
| Hard bug | `diagnosing-bugs` |
| Module seam | `codebase-design` |

## UI (miniprogram)

`frontend-design` sets taste. **Deliverable is WXML + Sass + TypeScript**, Skyline-safe.

- Units: `rpx`. Custom nav already on. Palette and illustration rules: [docs/miniprogram/visual.md](../../../docs/miniprogram/visual.md)（暖米色 + 橙色；不要在页面写死 hex）。
- Copy: original; never the benchmark brand name or its illustration/copy.
- Pages live in `miniprogram/modules/<feature>/pages/`. Register by **appending** `app.json` `pages`.
- Throwaway HTML from `prototype` stays outside `miniprogram/`.

## Data

Path and JSON fields: [docs/api/contract.md](../../../docs/api/contract.md) only (`snake_case`, string ids, integer points).

- Pages call `modules/<feature>/services/` → `core/request`. A page without its service is not done.
- Mock handlers: `modules/<feature>/services/mock.ts`. Seed: `miniprogram/mocks/store.ts`. Entry: `core/mock.ts` (register + match only, no product nouns). Runtime: `core/mock-runtime.ts` (no product nouns).
- Module names: `auth` / `me` / `media` / `album` / `community` / `video` / `points` / `assistant`. New module: [docs/framework/adding-a-module.md](../../../docs/framework/adding-a-module.md).

## Phase gate

Phase and next step = [docs/progress.md](../../../docs/progress.md). Do that phase's work; do not skip ahead. Phase F: do not create a runnable FastAPI. Do not restyle unless the user asks.

Phase 1+: `fastapi` skill + [docs/backend/README.md](../../../docs/backend/README.md). Same contract file. `router` → `service` → `repository`.

## With this user

Do not write `docs/dev/` unless they asked for a document. After clarifying questions, implement; they verify by tapping WeChat DevTools (repo root).

## Verify and hand off

TypeScript check: `npm run typecheck`. Pages can only be clicked through by a human in WeChat DevTools, opened on the **repo root**.

So verification means: `npm run typecheck`, read `git diff`, check every path and field word-for-word against [docs/api/contract.md](../../../docs/api/contract.md), and walk the pre-commit checklist in [code-standards.md](../../../docs/framework/code-standards.md). Never write 已验证 for a check you did not run — write what you skipped and why. Hand off in the code-standards format: 范围 / 已改 / 契约 / 验证 / 风险 / 下一步.

## Names that collide

- `/handoff` = conversation handoff skill. API/tabs/mock = `docs/handoff.md`.
- `/tdd` (mattpocock) and superpowers `test-driven-development` are both present; prefer `/tdd` when `implement` calls it.
