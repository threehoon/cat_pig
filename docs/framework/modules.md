# 模块边界与变更半径

目标：**改一个功能，只动这个功能自己的目录；其它模块保持能编译、能跑。**

模块叫什么由产品决定。本文件不列举业务名称。

## 变更半径

| 你改的是 | 允许动 | 禁止 |
|---|---|---|
| 某个业务功能 | `miniprogram/modules/<feature>/`、`server/app/modules/<feature>/`、该功能自己的 Alembic 迁移 | 改其它 `modules/*`；改 `core`「顺便兼容」这个功能 |
| 登录 / 请求 / 配置 | `miniprogram/core/`、`server/app/core/` | 业务模块里再写一套 token 或 base URL |
| 某张表 | 该模块 `models.py` + **新的一条**迁移 | 改已经应用的历史迁移；改别人的表 |
| API 字段 | 该模块 `schemas.py`；只加可选字段或新路径 | 改已有字段名 / 类型 / 改为必填 |
| 新页面 | 该模块 `pages/` + `app.json` 的 `pages` **追加一行** | 业务写进 `app.ts`、`globalData` |
| 换存储 / 换 JWT 实现 | 只动内核 | `service.py` 里出现 OSS、路径拼接、密钥 |

`app.json` 是全局文件里**唯一**允许随新功能改动的地方（登记页面）。`main.py` 只做模块发现，不为某个功能加分支。

## 后端模块契约

每个 `server/app/modules/<feature>/` 必须具备：

| 文件 | 职责 | 不准做 |
|---|---|---|
| `router.py` | HTTP 路由 | SQL、直接 Session、调其它模块 models |
| `schemas.py` | 入参出参（对外契约） | 暴露 ORM 对象 |
| `models.py` | 本模块的表 | 定义别的模块该有的表 |
| `repository.py` | 唯一碰数据库的地方 | HTTP、微信 API |
| `service.py` | 本模块对外的唯一入口 | 依赖其它模块的 repository |
| `deps.py` | 本模块的 FastAPI Depends | 全局单例业务状态 |

内部依赖单向：`router → service → repository → models`。

## 小程序模块契约

每个 `miniprogram/modules/<feature>/`：

| 目录 | 职责 |
|---|---|
| `pages/` | 该功能页面（须在 `app.json` 登记完整路径） |
| `components/` | 仅该功能使用的组件 |
| `services/` | 只调用该功能的 `/api/v1/<feature>` |
| `types/` | 该功能的 TS 类型（由 OpenAPI 生成） |

跨功能 UI 才放 `miniprogram/components/`。

## 模块之间

- 禁止 `from app.modules.other.models import ...`（以及 repository、router）。
- 必须复用时：只调用对方 `service` 的公开函数，返回 DTO/schema，不返回 ORM 实例。
- 一张表只属于一个模块。其它模块可存对方资源的 id，不改对方表结构。
- 小程序页面禁止 import 另一模块的 `services` 去拼业务。跳转用路由；数据走自己的 API 或 `core/auth`。

## 契约稳定

- URL：`/api/v1/<feature>/...`。破坏性变更用新路径或 `/api/v2`。
- OpenAPI 是字段唯一来源。
- 错误码在 `server/app/core`，模块只使用。小程序按 `error.code` 分支。

## 代码不准进仓的信号

出现任一条就停下来拆模块，不要继续堆：

- 模块 A import 模块 B 的 `models` / `repository`
- 页面或业务组件里出现 `wx.request`
- `globalData` 开始堆业务字段
- `core` 出现某个功能的表名、文案、页面路径
- 为了一个新功能改了三个以上已有模块
- `utils/` 里出现请求、鉴权、某张表的拼接 SQL
