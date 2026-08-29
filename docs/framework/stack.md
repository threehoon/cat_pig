# 技术栈

锁定如下。要换栈，先改本文件和 [设计记录](../superpowers/specs/2026-08-24-framework-and-stack-design.md)，再改代码。

## 选定

| 层 | 选择 | 说明 |
|---|---|---|
| 小程序 | 微信原生 | WXML + TypeScript + Sass；现有 `miniprogram/` |
| 渲染 | Skyline + glass-easel | 模板已开启，保持 |
| 后端语言 | Python 3.12 | |
| 后端框架 | FastAPI + Uvicorn | |
| 校验 / 文档 | Pydantic v2（FastAPI 自带 OpenAPI） | 小程序类型从 OpenAPI 生成 |
| ORM | SQLAlchemy 2.x（异步） | |
| 迁移 | Alembic | 只追加新迁移，不改已应用的历史文件 |
| 驱动 | asyncpg | |
| 数据库 | PostgreSQL 16 | 本地用 Docker Compose 跑，不要依赖机器上裸装的 Postgres |
| 包管理 | uv + `server/pyproject.toml` | |
| 鉴权 | JWT（后端签发） | 微信 `code` 只用于换 openid |
| 开发期文件 | 本地磁盘（或之后的 MinIO） | 表只存 URL |

## 明确不做（当前）

- Taro、uni-app、WePY、mpvue 等跨端框架
- NestJS / Node 作为主后端（已否决）
- 微信云开发当主后端
- Redis、消息队列、独立 H5、React Native / 独立 App（有真实需求再开文档）
- 把图生视频或模型推理塞进同步 API 进程（出片走异步 worker，不改模块契约）
- 预建具体业务模块目录

## 前端辅助

- 状态：先放在页面和模块 service，不上全局 Redux/MobX。出现跨页共享且属于内核的（登录态）才进 `core/auth`。
- 样式：Sass，与现有工程一致。
- npm：小程序侧不堆运行时框架依赖。
