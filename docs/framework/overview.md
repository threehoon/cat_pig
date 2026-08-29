# 仓库骨架

本仓库是**单仓**。微信开发者工具打开仓库根目录（已有 `project.config.json`，`miniprogramRoot` 为 `miniprogram/`）。后端是旁边的 `server/`，不是另一个 git 仓库。

功能增加时只增加 `modules/<feature>`，不把骨架改成「按技术层分的大文件夹」。

## 目标目录

```text
app_pet/
  AGENTS.md                     # Agent 入口（路由，不是细则）
  docs/                         # 项目文档（本目录）
  miniprogram/                  # 微信原生小程序
    app.ts / app.json / app.scss
    styles/                     # 视觉 token + 跨页 primitives（见 miniprogram/visual.md）
    assets/                     # brand / icon / tab / mock；路径表 paths.ts
    core/                       # 小程序内核（请求、登录、配置、存储）
    modules/                    # 业务模块（按功能增删）
    components/                 # 跨模块通用 UI
    pages/                      # 仅保留微信模板残留页，新页面不放这里
    utils/                      # 只放纯函数；不准放请求和业务
  server/
    app/
      main.py                   # 组装应用、发现模块；无业务 if
      core/                     # 后端内核（配置、DB、JWT、异常、分页）
      modules/                  # 业务模块（按功能增删）
    alembic/                    # 迁移
    tests/
    pyproject.toml
  docker-compose.yml            # 本地 Postgres（阶段 1 添加）
```

`server/` 的 Python 包与 Compose 在阶段 1 创建。现在 `server/app/core` 与 `server/app/modules` 只有说明文件，防止业务被写到错误位置。

## 内核 vs 模块

| | 内核 `core/` | 模块 `modules/<feature>/` |
|---|---|---|
| 何时改 | 登录协议、请求封装、数据库连接、错误码这类跨功能基础设施 | 某个产品能力 |
| 频率 | 很少 | 每个新功能一次 |
| 例子 | JWT 校验、分页参数、请求封装 | 已锁定：`auth` `me` `media` `album` `community` `video` `points` |
| 禁止 | 写具体业务表名、页面文案、功能路径 | 复制一套 request / 再造一套 JWT |

判断：已经被**两个**模块用到的，才允许抽到内核。禁止预抽「以后可能通用」。

## 依赖方向

```text
小程序 pages/组件  →  本模块 services  →  miniprogram/core/request
                                              ↓
                                      FastAPI /api/v1/<feature>
                                              ↓
                         该模块 router → service → repository → 本模块表

core  ←  任何模块可用
模块 A  ↛  模块 B 的 models / repository / 私有组件
```

## 和现有模板的关系

官方模板自带 `pages/index`、`pages/logs`、`components/navigation-bar`。在第一个业务模块落地前可以保留，便于开发者工具能打开。新页面必须建在 `miniprogram/modules/<feature>/pages/`，并在 `app.json` 的 `pages` 数组里指向该路径。不要继续往 `miniprogram/pages/` 加业务页。
