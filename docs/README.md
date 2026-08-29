# 项目文档

这里是本仓库**所有项目文档的目录**。人类从这里找文件；Agent 从根目录 [AGENTS.md](../AGENTS.md) 按任务路由到这里的某一份。

文档分四类，不要混写：

| 类型 | 作用 | 目录 |
|---|---|---|
| 入口 / 路由 | 告诉 Agent 读哪份 | `/AGENTS.md` |
| 进度 | 现在做到哪、下一步、决策日志 | `progress.md` |
| 产品 | 对标、定位、能力优先级 | `product/` |
| 框架与规范 | 技术栈、目录、模块边界、增模块流程 | `framework/`、`backend/`、`miniprogram/` |
| 对接 | 环境、登录、API 形态、前后端各管什么 | `handoff.md` |
| 设计记录 | 选型过程与为什么，不指导日常改代码 | `superpowers/specs/` |

## 目录

| 文档 | 给谁用 | 内容 |
|---|---|---|
| [AGENTS.md](../AGENTS.md) | Agent 必读入口 | 路由表、硬规则摘要、如何登记新文档 |
| [progress.md](progress.md) | 人 + Agent | 项目进度、阶段、下一步、如何更新进度 |
| [product/README.md](product/README.md) | 人 + Agent | 产品文档目录 |
| [product/positioning.md](product/positioning.md) | 产品 | 定位、对标「萌爪日记」同类 |
| [product/benchmark.md](product/benchmark.md) | 产品 | 与对标产品的功能逐条对照 |
| [product/capabilities.md](product/capabilities.md) | 产品 | P0/P1/P2 实现顺序与模块边界 |
| [product/reference/](product/reference/README.md) | 产品 | 对标截图（只对照，不进小程序包） |
| [handoff.md](handoff.md) | 前后端联调 + 界面先行 | 模块名、tab/页面路径、必须预留的 service、mock、环境、登录 |
| [api/contract.md](api/contract.md) | 前端 mock + 后端 API | **路径和字段的唯一合同** |
| [framework/overview.md](framework/overview.md) | 结构 | 仓库骨架、内核 vs 模块、依赖方向 |
| [framework/stack.md](framework/stack.md) | 选型 | 锁定的技术栈与明确不做的 |
| [framework/modules.md](framework/modules.md) | 边界 | 变更半径、模块契约、禁止事项 |
| [framework/adding-a-module.md](framework/adding-a-module.md) | 开工清单 | 新增功能的唯一步骤 |
| [framework/skills.md](framework/skills.md) | Agent 开发 | 已安装的 skill、怎么调用、重名说明 |
| [backend/README.md](backend/README.md) | 后端 | FastAPI 分层、发现路由、迁移 |
| [miniprogram/README.md](miniprogram/README.md) | 小程序 | 页面、core、模块、微信约束 |
| [miniprogram/visual.md](miniprogram/visual.md) | 小程序观感 | 配色 token、插画目录、通用组件、禁止写死 hex |
| [superpowers/specs/2026-08-24-framework-and-stack-design.md](superpowers/specs/2026-08-24-framework-and-stack-design.md) | 追溯 | 技术栈与仓库骨架（产品方向以 product/ 为准） |
| [superpowers/specs/2026-08-24-product-community-pivot.md](superpowers/specs/2026-08-24-product-community-pivot.md) | 追溯 | 从日记账本改向内容小程序 |
| [superpowers/specs/2026-08-24-miniprogram-shell-design.md](superpowers/specs/2026-08-24-miniprogram-shell-design.md) | 追溯 | 小程序空壳：5 tab、page-shell、core 签名 |

## 写文档的规则

- 一份文档只回答一类问题。进度不写 API 字段，对接文档不写模块分层细节。
- 改规范时同步改链接，不要留死链。
- 产品功能清单只写在 `product/`，不写进框架文档。新功能落地时按模块加目录，并在 `progress.md` 记一笔。
- 代码目录里的 `README.md` 只指向本目录对应文档，不复制长文。
