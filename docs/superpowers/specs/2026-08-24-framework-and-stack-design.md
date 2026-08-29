# 框架与技术栈设计

- 日期：2026-08-24
- 状态：已按讨论写入仓库，待你审阅本文件与 `docs/` 卫星文档
- 产品：已改向，见 `docs/product/` 与 [2026-08-24-product-community-pivot.md](2026-08-24-product-community-pivot.md)。本文件只管技术栈与仓库骨架。
- 范围：技术栈、仓库骨架、模块边界、文档体系。产品能力见 `docs/product/`，不在本文件展开页面与表结构。

## 背景

仓库已是微信官方 TypeScript + Sass 模板（Skyline / glass-easel，AppId 已配）。需求是长期可迭代的产品，不是 demo。后端要自建，本地先跑通数据库。功能集合会变，不能把框架写成「用户 / 宠物 / 日记 / 媒体」四件套。

## 目标

1. 前后端技术栈明确，本地能跑 PostgreSQL，小程序打自建 API。
2. 结构化管理：一功能一模块，禁止把代码堆进单一分层大目录。
3. 变更隔离：改功能 A 的默认半径是 A 自己的目录。
4. 文档可被 Agent 按任务调用：主 `AGENTS.md` 只路由，细则在 `docs/`。
5. 进度与前后端对接有固定文件，不靠聊天记录。

## 非目标

- 确定具体产品功能与信息架构
- 跨端（H5、App、其它小程序平台）
- 本阶段实现 FastAPI 可运行代码与业务模块
- Redis、队列、AI worker

## 技术栈

见 [stack.md](../../framework/stack.md)。摘要：

- 小程序：微信原生 + TypeScript + Sass
- 后端：Python 3.12 + FastAPI
- 数据库：PostgreSQL 16（Docker Compose）
- ORM：SQLAlchemy 2 + Alembic
- 鉴权：wx.login code → 后端换 openid → JWT
- 契约：OpenAPI → 小程序 TS 类型

曾考虑 NestJS（与小程序同为 TS、模块是框架原语）。因后端语言选定 Python，主 API 用 FastAPI；模块化改为目录契约 + `AGENTS.md` 强制执行。Python 推理若以后需要，另开 worker，不作为现在的 API 层。

曾考虑 Taro / uni-app。当前只做微信，跨端框架的收益不抵运行时与微信新能力滞后。H5 与 RN 不在本阶段。

## 架构

单仓：根目录保持微信工程；`server/` 放 FastAPI。

稳定内核（`core/`）+ 可插拔模块（`modules/<feature>/`）。`main.py` 发现模块路由，不为功能写分支。小程序新页面落在模块内，仅 `app.json` 追加登记。

依赖单向：页面 → 模块 service → core/request → FastAPI 模块 router → service → repository → 本模块表。模块之间默认不互引 models。

详情：[overview.md](../../framework/overview.md)、[modules.md](../../framework/modules.md)。

## 文档体系

| 文件 | 职责 |
|---|---|
| `/AGENTS.md` | Agent 入口、任务 → 文档路由、硬规则摘要 |
| `docs/README.md` | 人类用文档目录 |
| `docs/progress.md` | 进度与决策日志 |
| `docs/handoff.md` | 环境、登录、HTTP、职责切分 |
| `docs/framework/*` | 骨架、栈、模块、增模块流程 |
| `docs/backend/README.md` | 后端写法 |
| `docs/miniprogram/README.md` | 小程序写法 |
| 本文件 | 选型记录，不替代日常规范 |

新增规范必须同时改 `AGENTS.md` 路由表和 `docs/README.md`。禁止把长文堆回 `AGENTS.md`。

## 错误处理

后端统一 `{ "error": { "code", "message" } }`。`code` 稳定，定义在 core。小程序按 code 处理。见 [handoff.md](../../handoff.md)。

## 测试

内核测 `server/tests/core/`；模块测 `server/tests/modules/<feature>/`。不测其它模块私有层。小程序侧测试策略在有可运行内核后再补文档，不在本文件发明第二套框架。

## Key Decisions

1. **自建 FastAPI + PostgreSQL，不用云开发 / 不用 Nest。** 长期控数据与模块；后端语言选 Python。
2. **微信原生，不跨端框架。** 单端微信，性能与 API 完整度优先。
3. **单仓。** 早期联调与 OpenAPI 生成同仓完成；有独立发布团队再拆仓。
4. **按功能模块而不是按技术层分目录。** 避免 models/api 成为所有功能的堆放处。
5. **框架不预写业务模块名。** 契约写死，产品清单不写死。
6. **主 Agent 文档只路由。** 进度、对接、规范可独立改、按需加载。
7. **产品方向以 `docs/product/` 为准。** 本条原写「有猫的生活」随手记方案，已被 [产品改向记录](2026-08-24-product-community-pivot.md) 覆盖。

## 实施顺序（确认文档后）

实施顺序以 [progress.md](../../progress.md) 为准（现为阶段 F 前端先行，小程序 `core` 在阶段 F 就要有）。本文件里旧的「1 后端 → 2 小程序 core → 3 业务」已被覆盖。
