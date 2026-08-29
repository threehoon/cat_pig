# AGENTS.md

本文件是 Agent 与开发者的**唯一入口**。先读这里，再按任务打开 `docs/` 里对应文档。

不要把长规范写进本文件。新约定写到 `docs/` 下独立文档，并同时在本文件的路由表和 `docs/README.md` 登记。没有登记的文档，视为不存在。

## 项目是什么

单仓项目：微信**原生**小程序（TypeScript + Sass）+ **FastAPI**（Python）+ **PostgreSQL**。

用来做宠物内容小程序。**产品对标「萌爪日记」同类能力**（相册、图生视频、广场 / 论坛、积分），功能对等、不抄品牌与插画。细则在 `docs/product/`。功能仍按模块增减，框架不预建业务目录。

## 先读哪份（路由）

| 当你要做的事 | 打开（按顺序） |
|---|---|
| 还不熟这个仓库 / 找所有文档 | [docs/README.md](docs/README.md) |
| 看现在做到哪、下一步是什么、更新进度 | [docs/progress.md](docs/progress.md) |
| 产品做什么、对标谁、学什么不学什么 | [docs/product/positioning.md](docs/product/positioning.md) |
| 和「萌爪日记」同类功能是否对等 | [docs/product/benchmark.md](docs/product/benchmark.md) |
| 能力优先级、P0/P1 实现顺序 | [docs/product/capabilities.md](docs/product/capabilities.md) |
| 产品文档目录 | [docs/product/README.md](docs/product/README.md) |
| 改目录、动内核、理解仓库骨架 | [docs/framework/overview.md](docs/framework/overview.md) |
| 加功能、拆模块、判断代码放哪 | [docs/framework/modules.md](docs/framework/modules.md) |
| **新建一个功能模块**（唯一合法流程） | [docs/framework/adding-a-module.md](docs/framework/adding-a-module.md) |
| 查技术栈（语言、库、明确不做的） | [docs/framework/stack.md](docs/framework/stack.md) |
| 写或改后端 | [docs/backend/README.md](docs/backend/README.md) |
| 写或改小程序 | [docs/miniprogram/README.md](docs/miniprogram/README.md) |
| **写/改任何接口、mock、FastAPI schema** | [docs/api/contract.md](docs/api/contract.md)（路径和字段的唯一依据） |
| **做小程序界面 / mock / 页面路径** | [docs/handoff.md](docs/handoff.md)、[docs/api/contract.md](docs/api/contract.md)、[docs/miniprogram/README.md](docs/miniprogram/README.md)、[docs/product/reference/](docs/product/reference/README.md) |
| **改小程序观感（配色、插画、通用组件）** | [docs/miniprogram/visual.md](docs/miniprogram/visual.md)、[docs/miniprogram/README.md](docs/miniprogram/README.md)、[docs/handoff.md](docs/handoff.md) |
| 前后端联调、环境变量、登录、模块英文名 | [docs/handoff.md](docs/handoff.md) |
| 查「为什么这么定」（技术栈） | [docs/superpowers/specs/2026-08-24-framework-and-stack-design.md](docs/superpowers/specs/2026-08-24-framework-and-stack-design.md) |
| 查「为什么改成广场/视频」 | [docs/superpowers/specs/2026-08-24-product-community-pivot.md](docs/superpowers/specs/2026-08-24-product-community-pivot.md) |
| 搭小程序空壳（tab / page-shell / core 签名） | [docs/superpowers/specs/2026-08-24-miniprogram-shell-design.md](docs/superpowers/specs/2026-08-24-miniprogram-shell-design.md)、[docs/handoff.md](docs/handoff.md)、[docs/miniprogram/README.md](docs/miniprogram/README.md) |
| **按项目 skill 开发** / 查已装哪些 skill | `/app-pet`，清单 [docs/framework/skills.md](docs/framework/skills.md) |

一次任务只加载上表里需要的文档，不要把 `docs/` 全部塞进上下文。

## 硬规则（摘要）

细则以卫星文档为准。这里只列违反了就必须停手改的：

1. 业务代码只进 `miniprogram/modules/<feature>/` 和 `server/app/modules/<feature>/`。不准堆进一个大 `api/`、`models/`、`utils/`。
2. 模块之间不准互相 import `models` / `repository` / `router`。跨模块只许走对方 `service` 的公开方法。
3. 小程序页面不准写 `wx.request`；只通过 `miniprogram/core` 的请求封装。
4. FastAPI 的 `router` 不准直接写 SQL / 碰 ORM session；只走本模块 `service` → `repository`。
5. 已发布的 API 字段不改名、不改类型、不改成必填。破坏性变更走新路径或 `/api/v2`。
6. 加功能时，`app.json` 只允许**追加** `pages`；不准把业务塞进 `app.ts` / `globalData`。
7. 完成一个阶段或合并一批改动后，必须更新 [docs/progress.md](docs/progress.md)。
8. 实现用户可见功能前必须读 [docs/product/positioning.md](docs/product/positioning.md)、[docs/product/benchmark.md](docs/product/benchmark.md)、[docs/product/capabilities.md](docs/product/capabilities.md)。benchmark 标明「无」的当作需求不存在。对标功能对等，禁止使用「萌爪日记」品牌名、插画与文案原句。
9. **接口只认 [docs/api/contract.md](docs/api/contract.md)。** 前端 mock、services 的 path/字段、后端 router/schema 必须与该文件逐字一致（含 `snake_case`、字符串 id、积分为整数）。禁止另起一套。改接口先改合同文件。页面只调 `services/` → `core/request`。没有对应 service 的页面不算做完。

## 如何新增或修改规范

1. 在 `docs/` 下合适目录新增或修改 Markdown（一个主题一份文件）。
2. 在 [docs/README.md](docs/README.md) 的目录表里登记。
3. 若 Agent 做某类任务时必须读它，在本文件「先读哪份」表加一行。
4. 不在本文件展开细则。不把同一条规则复制到三份文档；一份正文，其余只链过去。

## 当前阶段

以 [docs/progress.md](docs/progress.md) 为准。当前是 **阶段 F：前端界面先行**。页面和视觉已铺；新对话按进度里的「下一步」做各模块 `services/` + `core/request` mock，不要先搭 FastAPI。
