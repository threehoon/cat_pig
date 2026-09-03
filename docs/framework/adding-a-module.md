# 新增一个功能模块

新页面放 `modules/<feature>/pages/`，不要放进 `miniprogram/pages/`。

阶段 F 多数工作是**在已有模块上加页面**，不是新建模块。先判断是哪一种，再动手。一次改动不准搭车重构内核。

## 0. 新模块还是已有模块的新页面

- 已有模块加页面 / service / mock：走第 2 步（若有新字段）和第 3 步对应项，不要另起一套目录。
- 独立产品能力才新建模块。一个模块一件事。

## 1. 英文名

必须用 [handoff.md](../handoff.md) 已锁定的名字：`auth` / `me` / `media` / `album` / `community` / `video` / `points`。禁止中文目录和旧别名（`forum`、`plaza`、`journal`、`pet`）。后端开工时目录名必须与小程序一致。

## 2. 新 path / 字段

先改 [../api/contract.md](../api/contract.md)，再改 types / services / mock。

## 3. 阶段 F（前端先行）

按需创建 `miniprogram/modules/<feature>/{pages,components,services,types}`。

- `services/*.ts` + `services/mock.ts`（handlers）
- 在 `core/mock.ts` **追加**该模块 routes 的 spread；`mock.ts` 里不写业务
- `app.json` 只允许**追加** `pages`；已锁定的 tab 路径不改
- 默认不改 `window`；阶段 F 可以改 `window` / `tabBar` / `permission`，范围以 [handoff.md](../handoff.md) 为准
- 无独立 UI 的模块（`auth`、`media`）可以没有 `pages/`
- **不要**创建 `server/app/modules/`、Alembic 或可运行的 FastAPI

跨模块写 mock 数据：调用对方公开函数（community：`mock-helpers.ts` 的 `publishPost` / `presentPost` / `syncAlbumToForum`；points：`mock-ledger.ts` 的 `addLedger` / `pointsSummary`），不要直接改另一模块的数组。种子在 `miniprogram/mocks/store.ts`。

## 4. 阶段 1 及以后才做

- `server/app/modules/<feature>/` 六个文件：`router.py`、`schemas.py`、`models.py`、`repository.py`、`service.py`、`deps.py`，以及导出 router 的 `__init__.py`
- 表只写在该模块 `models.py`；新增**一条** Alembic 迁移，不改已应用的旧迁移
- 测试放 `server/tests/modules/<feature>/`
- `main.py` 无业务分支；其它模块不因本功能而改（除非走对方 service 的既有公开方法）

## 5. 提交前

- 页面没有 `wx.request`
- path / 字段与合同一致
- `npm run typecheck`
- 不要更新 [docs/progress.md](../progress.md)，除非用户要求整理 / 总结 / 更新对接文档，或阶段 / 合同本身变了

## 一次改动不准搭车

允许：本功能自己的小程序目录、`app.json` 追加的页面、该模块 mock 注册项。阶段 1+ 才带上后端六文件、迁移和测试。

不允许搭车重构其它模块、不允许顺便「整理」内核。
