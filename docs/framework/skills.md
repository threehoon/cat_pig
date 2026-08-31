# 项目 Agent Skills

本仓库给 Grok 和 Codex 共用的 skill 装在 [`.grok/skills/`](../../.grok/skills/)。Codex 通过项目级 [`.agents/skills/`](../../.agents/skills/) 软链接读取同一份文件，清单变更只改这一份文件。

开发本产品时先走 **`/app-pet`**。其它 skill 是它点名才加载的同伴，不是第二套规范。规范正文仍在 `docs/`，skill 只负责触发和约束输出形态。

安装来源记在仓库根目录 `skills-lock.json`。更新第三方 skill：`npx skills update`。

## 怎么用

| 你想做的事 | 斜杠 |
|---|---|
| 按本仓库规矩写小程序 / mock / 模块 | `/app-pet` |
| 开做前把需求问清楚，并记术语 | `/grill-with-docs` |
| 把已经聊清的内容写成 spec | `/to-spec` |
| 把 spec 拆成可做的票 | `/to-tickets` |
| 按 spec / 票实现 | `/implement` |
| 先写失败测试再写实现 | `/tdd` |
| 页面观感 | `/frontend-design`（输出必须是 WXML + Sass，见 `/app-pet`） |
| Skyline 组件 / 样式 / 配置 | `/skyline-components` `/skyline-wxss` `/skyline-config` 等 |
| 阶段 1 以后写 FastAPI | `/fastapi` |
| 不知道该调哪个流程 | `/ask-matt` |

mattpocock 工程 skill 第一次在本仓库落地前，需要跑一次 **`/setup-matt-pocock-skills`**（选 issue 放哪、triage 标签、`CONTEXT.md` 布局）。没跑之前，`/to-spec` `/to-tickets` `/triage` 不知道票写到哪里。

## 已安装

### 本仓库

| Skill | 作用 |
|---|---|
| `app-pet` | 本产品开发路由：阶段、模块名、合同、WXML 约束 |

### 小程序 / 界面 / 后端

| Skill | 来源 |
|---|---|
| `frontend-design` | Anthropic |
| `skyline-overview` `skyline-config` `skyline-components` `skyline-wxss` `skyline-worklet` `skyline-route` `skyline-scroll-api` | 微信官方 `wechat-miniprogram/skyline-skills` |
| `fastapi` | FastAPI 官方 |

### 工程流程（mattpocock/skills，已筛选）

`setup-matt-pocock-skills` `ask-matt` `grill-me` `grilling` `grill-with-docs` `to-spec` `to-tickets` `implement` `tdd` `diagnosing-bugs` `codebase-design` `code-review` `domain-modeling` `prototype` `improve-codebase-architecture` `wayfinder` `research` `resolving-merge-conflicts` `writing-for-agents` `handoff` `wait-what` `triage` `wizard`

未装（和本仓库无关或会抢上下文）：`teach` `to-questionnaire`、写作三件套、`setup-ts-deep-modules`、`git-guardrails-claude-code`、`migrate-to-shoehorn`、`setup-pre-commit`、`scaffold-exercises`、`claude-handoff`、`implement-spec`、`loop-me`、`retro`。

## 重名

| 名字 | 是什么 |
|---|---|
| `/handoff` | 把当前对话交给下一个 Agent 的 skill |
| `docs/handoff.md` | 本仓库的对接文档（tab、模块名、mock） |
| `/tdd` | mattpocock 的红绿重构 |
| superpowers `test-driven-development` | 插件里另一份 TDD；`implement` 调的是 `/tdd` |

## 明确不装

- 腾讯云开发整包（本仓库不做微信云开发当主后端）
- `ui-ux-pro-max`（与 `frontend-design` 叠装；安全扫描有 Fail）
- React / Next / Prisma / Supabase 专用 skill
