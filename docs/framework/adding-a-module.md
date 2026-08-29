# 新增一个功能模块

这是加产品能力的**唯一合法流程**。不要先写页面再补目录，不要把代码丢进 `pages/` 或 `utils/`。

`<feature>`：必须使用已锁定的英文名（`auth` / `me` / `media` / `album` / `community` / `video` / `points`）。见 [handoff.md](../handoff.md)。禁止中文目录、禁止别名（如 `forum`、`plaza`、`journal`、`pet`）。

阶段 F（前端先行）：可以只建 `miniprogram/modules/<feature>/`，暂不建后端模块。后端开工时目录名必须与小程序一致。

## 步骤

1. **命名**  
   确认这是一个独立能力，不是某个已有模块的小改动。一个模块一件事。

2. **后端目录**  
   创建 `server/app/modules/<feature>/`，放入契约文件：`router.py`、`schemas.py`、`models.py`、`repository.py`、`service.py`、`deps.py`，以及导出 router 的 `__init__.py`。  
   空实现也要能被 `main.py` 发现并挂到 `/api/v1/<feature>`。

3. **表与迁移**  
   表只写在该模块 `models.py`。新增 **一条** Alembic 迁移。禁止修改已应用的旧迁移文件。

4. **小程序目录**  
   创建 `miniprogram/modules/<feature>/pages|components|services|types`。  
   页面路径形如 `modules/<feature>/pages/<page>/<page>`。

5. **登记页面**  
   在 `miniprogram/app.json` 的 `pages` 数组**追加**（或阶段 F 把首页改到社区首页）。不要为单个功能去改其它业务页。阶段 F 可以改 `tabBar` 和选图权限，见 [handoff.md](../handoff.md)。

6. **不要改的**  
   `main.py` 无业务分支；其它模块不因本功能而改（除非走对方 service 的既有公开方法，且该方法语义仍然成立）。

7. **测试**  
   后端测试放 `server/tests/modules/<feature>/`。不测其它模块内部。

8. **进度**  
   在 [docs/progress.md](../progress.md) 记：模块名、这一步打通了什么（例如「创建 + 列表」）。

## 一次改动允许包含

- 该功能的后端模块
- 该功能的小程序模块
- 该功能的迁移
- `app.json` 追加的页面路径
- `progress.md` 一行记录

不允许搭车重构其它模块、不允许顺便「整理」内核。

## 清单（提交前）

- [ ] 没有从其它模块 import `models` / `repository`
- [ ] 页面没有 `wx.request`
- [ ] `router` 没有直接 Session
- [ ] 新字段若已有客户端：是可选的，或走新路径
- [ ] 已更新 `docs/progress.md`
