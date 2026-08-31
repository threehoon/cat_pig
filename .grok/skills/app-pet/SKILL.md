---
name: app-pet
description: Use when developing this WeChat miniprogram or FastAPI backend — adding pages, modules, mock, services, WXML/Sass/Skyline UI, API fields — or when the user says 按 skill 开发, 加页面, mock 接口, or /app-pet.
---

# app-pet

This repo is a WeChat **native** miniprogram (WXML + TypeScript + Sass, Skyline) plus a later FastAPI + PostgreSQL backend. Product: pet album / plaza / image-to-video / points.

Facts live in `docs/`. This skill is the **router**, not a second copy of the rules.

## Every turn

1. Read [AGENTS.md](../../../AGENTS.md) (hard rules + which doc to open).
2. Read [docs/progress.md](../../../docs/progress.md) for the current phase. Do that phase's work; do not skip ahead.
3. Open only the docs AGENTS.md names for this task.

Installed skill catalog: [docs/framework/skills.md](../../../docs/framework/skills.md).

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
- Mock lives in services or `core/request`'s mock branch.
- Module names: `auth` / `me` / `media` / `album` / `community` / `video` / `points`. New module: [docs/framework/adding-a-module.md](../../../docs/framework/adding-a-module.md).

## Phase gate

Phase F (current until `progress.md` says otherwise): pages and visual are in; **this turn's work is `services/` + mock**. Do not create a runnable FastAPI app. Do not restyle unless the user asks.

Phase 1+: `fastapi` skill + [docs/backend/README.md](../../../docs/backend/README.md). Same contract file. `router` → `service` → `repository`.

## Names that collide

- `/handoff` = conversation handoff skill. API/tabs/mock = `docs/handoff.md`.
- `/tdd` (mattpocock) and superpowers `test-driven-development` are both present; prefer `/tdd` when `implement` calls it.
