# 后端规范

路径：`server/`。技术选型见 [stack.md](../framework/stack.md)。模块契约见 [modules.md](../framework/modules.md)。HTTP 路径和字段只认 [api/contract.md](../api/contract.md)。环境、登录时序见 [handoff.md](../handoff.md)。

实现 router/schema 时对照合同逐条打勾。字段名、类型与合同不一致视为错误，不要「顺便」改成驼峰或数字 id。

阶段 1 才会创建可运行的 FastAPI 工程。本文件约束以后怎么写，避免先堆成单文件再拆。

## 包结构

```text
server/
  app/
    main.py                 # create_app()：挂中间件、发现 modules、健康检查
    core/
      settings.py           # 只从环境变量读配置
      db.py                 # 引擎、session factory
      security.py           # JWT 签发与校验
      exceptions.py         # 错误码与异常 → 统一 error body
      pagination.py
      wechat.py             # code2session，供认证类模块调用，不含用户表
    modules/
      <feature>/            # 见模块契约
  alembic/
  tests/
  pyproject.toml
```

`core/wechat.py` 只封装「用 code 换 openid」。用户表、JWT 与登录路由属于模块 `auth`，不要在 `core` 里写 `User` 模型。

## 启动与发现

- `main.py` 扫描 `app.modules` 下含有 `router` 的包，`include_router(router, prefix="/api/v1/<feature>")`。
- `<feature>` 等于目录名。禁止在 `main.py` 里为某个功能写 `if`。
- `GET /health` 挂在内核，不进业务模块。

## 分层

每个请求：`router` 解析与鉴权依赖 → `service` 业务 → `repository` 持久化。

- Session 只在 repository（或通过 deps 注入 repository）里出现。
- Schema 进、schema 出。ORM 模型不出现在 router 返回值。
- 跨模块：只调对方 service。

## 数据库

- 异步 SQLAlchemy 2 + Alembic。
- 每个模块自己的 `models.py` 必须能被 Alembic 的 `env.py`  import 到（阶段 1 做成自动 import 所有模块 models）。
- 迁移文件名带模块语义更好，但必须是新文件。

## 测试

`server/tests/modules/<feature>/`。测 service 与 router，不测其它模块的私有 repository。内核测试放 `server/tests/core/`。
