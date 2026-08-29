# 项目进度

这是进度的**唯一登记处**。Agent 在完成一个可交付阶段后必须改这份文件，不要只在对话里说「做完了」。

## 如何更新

改代码或规范之后，按下面做：

1. 更新「当前阶段」的状态（未开始 / 进行中 / 已完成）。
2. 在「已完成」里用一行写清事实，不要写过程感想。
3. 把下一步写成具体动作（文件路径或模块名），不要写「继续优化」。
4. 有新的技术或产品决定，追加到「决策日志」。
5. 改 `最后更新` 日期。

未合并、未验证的工作不要标成已完成。

## 新对话请从这里开始

下一对话目标：**用微信开发者工具点通主路径**（登录占位 → 首页入口 → 上传相册 → 发帖出现在广场 → 创作提交后任务列表多一条）。不要先搭 FastAPI。不要重做视觉（除非用户点名改某一页）。

各模块已有 `services/`；`core/request` 在 `useMock: true` 时按 method+path 返回合同形状的假数据。页面不再内置假数组。尚未在微信开发者工具里点验。

必读（按顺序）：[AGENTS.md](../AGENTS.md) → 本文件 → [handoff.md](handoff.md)（tab/页面/mock 约定）→ [api/contract.md](api/contract.md)（path 和 JSON 唯一依据）→ [miniprogram/README.md](miniprogram/README.md)。改观感才读 [miniprogram/visual.md](miniprogram/visual.md)。产品范围：[product/benchmark.md](product/benchmark.md)。对照截图在 [product/reference/](product/reference/README.md)。

开发走 `/app-pet`。人用微信开发者工具打开**仓库根目录**点验。做完一批页面后更新本文件。

## 当前阶段

| 项 | 值 |
|---|---|
| 阶段 | F — 前端界面先行 |
| 状态 | 进行中（页面、services、mock 已接；尚未在微信开发者工具点验） |
| 产品功能 | 对标「萌爪日记」同类：相册、图生视频、广场、积分；界面用 mock，不接真 API |
| 最后更新 | 2026-08-29 |

## 阶段总览

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 锁定技术栈、仓库骨架、模块边界、文档体系 | 已完成 |
| 0b | 产品改向：内容小程序（相册 / 视频 / 广场 / 积分） | 已完成（文档） |
| F | 前端界面先行：core 空壳 + P0/P1 页面 + mock，微信开发者工具可点可跳 | 进行中（页面 / services / mock 已接；开发者工具未点验） |
| 1 | 后端内核：FastAPI 启动、配置、DB 会话、健康检查 + Docker Postgres | 未开始（界面之后） |
| 2 | 小程序 `core/request` 切到真 API，关掉 `useMock` | 未开始 |
| 3 | P0 接真数据：登录 → 相册 → 广场发帖 | 未开始 |
| 3b | P1 接真数据：积分、签到、关注、表态 | 未开始 |
| 3c | P2 真出片：视频 worker | 未开始 |
| 4 及以后 | 每加一个产品能力 = 一个新模块，不改内核 | 未开始 |

阶段 F 的页面路径、模块英文名、mock 信封见 [handoff.md](handoff.md)。功能是否该做见 [product/benchmark.md](product/benchmark.md)。

## 已完成

- 前端锁定：微信原生小程序 + TypeScript + Sass（沿用现有 `miniprogram/`，不用 Taro / uni-app）。
- 后端锁定：Python 3.12 + FastAPI；数据库 PostgreSQL 16（延后到阶段 1）。
- 仓库形态锁定：单仓；后端放 `server/`，小程序保持 `miniprogram/`。
- 结构锁定：稳定内核 + 可增删的 `modules/<feature>`；不预建空业务模块（界面开工时才建小程序模块目录）。
- 文档体系落地：根目录 `AGENTS.md` 做路由，细则在 `docs/`。
- 产品改向：对标「萌爪日记」同类（相册、图生视频、广场、积分）；「有猫的生活」方案作废。见 `docs/product/`。
- 模块英文名锁定：`auth` / `me` / `media` / `album` / `community` / `video` / `points`。
- 对接文档、API 合同已按新产品重写。
- 对标截图放入 `docs/product/reference/`（只对照，不进小程序包）。handoff 已锁定枚举中文、media 调用例外、mock 发帖直接 published。
- 小程序空壳：`core` 四文件（`useMock: true`，无业务 mock）、`components/page-shell`、五个 tab、原生 tabBar 线框图标。`app.json` 首页为 `modules/community/pages/home/home`。
- 五个 tab 画出可辨认界面（首页入口+动态、相册卡、创作表单、论坛分栏、我的入口）；二级页可跳：上传、发帖、详情、我的发布、积分明细、任务管理、任务详情。
- 项目 skill 已装到 `.grok/skills/`：`app-pet`（本仓库路由）+ `frontend-design` + 微信官方 Skyline 七件套 + FastAPI 官方 + 筛选后的 mattpocock 工程 skill。清单见 `docs/framework/skills.md`。
- 界面观感：奶油水彩 + 圆脸腮红。token 在 `miniprogram/styles/`，插画在 `assets/brand|icon|tab`，跨页组件 `empty-state` / `react-row`。规范 [miniprogram/visual.md](miniprogram/visual.md)。未在微信开发者工具里点过。
- 阶段 F mock：各模块 `services/` + `types/` 已按 [api/contract.md](api/contract.md) 建好；`core/request` 在 `useMock: true` 时按 method+path 返回信封内 `data`；未命中仍 `MOCK_NOT_IMPLEMENTED`。页面改为只调本模块 service（相册/发帖/创作可调 `media`）。mock 种子：当前用户、两本相册、若干帖（含草稿）、一条视频任务、积分流水合计 180。发帖 `pending` 直接 `published` 并记 +20 积分。
- 表态改为可同时点亮：合同字段 `my_react` 换成 `my_reacts` 数组；心 / 骨头 / 星互相独立。`react-row` 图标加大，选中换彩色图并有弹跳。

## 进行中

- 阶段 F：services / mock 已接。未在微信开发者工具里点验。

## 下一步（给新对话，按此顺序）

1. 用微信开发者工具打开仓库根目录，点通主路径：首页四个入口 → 上传相册能出现在列表 → 发帖后广场看得到 → 创作页选 2 张图提交后任务列表多一条；签到写入积分流水。
2. 点验时修交互或空态问题；不要改合同字段，不要重做视觉。
3. 不要创建可运行的 FastAPI。不要把业务写进 `pages/index`、`pages/logs`。不要再建 `pet` / `journal` / `ledger` / `reminder`。不要改已锁定的 tab 路径和 API 字段。改皮走 [miniprogram/visual.md](miniprogram/visual.md)，不要在页面写死 hex。

写后端（阶段 1 之后）时：router/schema 必须对同一份 [api/contract.md](api/contract.md)，禁止另起字段名。

## 决策日志

| 日期 | 决定 | 原因 |
|---|---|---|
| 2026-08-24 | 不做微信云开发，自建后端 | 长期产品，要自己管数据和模块边界 |
| 2026-08-24 | 后端用 FastAPI，不用 NestJS | 选定 Python 作为后端语言 |
| 2026-08-24 | 前端保持微信原生，不上 Taro / uni-app | 当前只做微信；跨端框架的价值在「跨」 |
| 2026-08-24 | 单仓 + 领域模块，不按技术层堆目录 | 避免改一处牵动全仓；功能可扩展但不写死 |
| 2026-08-24 | 不预建空业务目录 | 框架管契约，目录在真正开工时才建 |
| 2026-08-24 | 主 `AGENTS.md` 只做路由，规范拆到 `docs/` | 便于单独更新、按任务按需加载 |
| 2026-08-24 | 产品对标微信小程序「萌爪日记」 | 当时按案例文案锁定能力路径 |
| 2026-08-24 | 更正：萌爪日记在微信搜不到 | 当时不能当界面或功能对照 |
| 2026-08-24 | 产品对标「有猫的生活」现有功能 | 随手记、相册、账单、提醒；**已被同日改向覆盖** |
| 2026-08-24 | 开发顺序改为前端界面先行 | 下一对话先出可点击的小程序界面，后端内核后置 |
| 2026-08-24 | 前端必须预留接口再画页面 | 避免后端数据对不上 |
| 2026-08-24 | 以 docs/api/contract.md 为前后端唯一 API 合同 | 路径/字段/类型只此一份 |
| 2026-08-24 | **产品改向：萌爪日记同类内容小程序** | 用户提供截图并确认走社区 + 相册 + 图生视频 + 积分，不再做账单/提醒/随手记 |
| 2026-08-24 | 模块名改为 auth/me/media/album/community/video/points | 旧名 pet/journal/ledger/reminder 作废 |
| 2026-08-24 | 不使用对标品牌名与插画 | 学类型和信息架构，不套壳 |
| 2026-08-24 | 阶段 F 先做可切 tab 的空壳 | 用户确认：page-shell + core 签名；二级页、列表、mock 数据后置。设计见 `docs/superpowers/specs/2026-08-24-miniprogram-shell-design.md` |
| 2026-08-29 | 开发走项目 skill：`/app-pet` 为入口 | 装 Anthropic `frontend-design`、微信官方 Skyline、FastAPI 官方、mattpocock 工程子集。不装云开发 / React / `ui-ux-pro-max`。清单 `docs/framework/skills.md` |
| 2026-08-29 | 界面气质：奶油水彩、稍可爱、留白；插画自绘 | 用户选 A 再选「刚好」这一档。token/组件/素材目录化，禁止页面写死 hex。底栏仍原生，只换图标 |
| 2026-08-29 | 帖子表态可同时多项；`my_react` 改为 `my_reacts` 数组 | 阶段 F 未接真 API；点赞后再点星不应取消心。再点同一项才取消 |

## 未决（不阻塞阶段 F）

- 产品正式名称（界面暂用「宠物记录」）。
- 生产对象存储用哪家云（开发期本地磁盘或 MinIO）。
- 图生视频出片提供商与密钥：P2 再锁，不进小程序。
- 微信隐私协议页：上线前再补，阶段 F 开发者工具可关校验。
