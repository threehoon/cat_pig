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

下一对话目标：用微信开发者工具打开仓库根目录，点验广场公开动态流（发动态不选板块；底栏/首页入口「广场」；推荐 / 关注是下划线；「大家都在看」横滑封面进详情，不是话题分类）。签到近 7 天进度条仍待点验，见 [dev/checkin-streak.md](dev/checkin-streak.md)。模拟器 `navigateTo` 空一拍、真机不卡，**不要回头改跳转**。不要先搭 FastAPI。不要重做视觉。不要把「已知风险」的延后项当成本轮必须做的事。

日常改代码**不要改** `docs/`。用户说「整理」「总结」「更新对接文档」再改本文件和 [handoff.md](handoff.md)。**改接口仍须先改** [api/contract.md](api/contract.md)。

必读（按顺序）：[AGENTS.md](../AGENTS.md) → 本文件 → [handoff.md](handoff.md) → [api/contract.md](api/contract.md) → [miniprogram/README.md](miniprogram/README.md)。点验签到进度条时再打开 [dev/checkin-streak.md](dev/checkin-streak.md)。写代码再读 [framework/code-standards.md](framework/code-standards.md)。改观感才读 [miniprogram/visual.md](miniprogram/visual.md)。产品范围：[product/benchmark.md](product/benchmark.md)。

开发走 `/app-pet`。打开仓库**根目录**。静态检查 `npm run typecheck`。

## 当前阶段

| 项 | 值 |
|---|---|
| 阶段 | F — 前端界面先行 |
| 状态 | 进行中（P0/P1 页面与 mock 已接；广场公开动态流、签到进度条等人点验） |
| 产品功能 | 对标「萌爪日记」同类：相册、图生视频、广场、积分；界面用 mock，不接真 API |
| 最后更新 | 2026-09-17 |

## 阶段总览

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 锁定技术栈、仓库骨架、模块边界、文档体系 | 已完成 |
| 0b | 产品改向：内容小程序（相册 / 视频 / 广场 / 积分） | 已完成（文档） |
| F | 前端界面先行：core 空壳 + P0/P1 页面 + mock，微信开发者工具可点可跳 | 进行中（P0/P1 页面与 mock 已接；广场动态流、签到进度条等人点验） |
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
- 小程序内核与空壳：`core`（`useMock: true`，请求 / 登录 / 存储 / mock 运行时）、`components/page-shell`、五个 tab、原生 tabBar 图标。`app.json` 首页为 `modules/community/pages/home/home`。
- 五个 tab 画出可辨认界面（首页入口+动态、相册卡、创作表单、论坛分栏、我的入口）；二级页可跳：上传、发帖、详情、我的发布、积分明细、任务管理、任务详情。
- 项目 skill 已装到 `.grok/skills/`：`app-pet`（本仓库路由）+ `frontend-design` + 微信官方 Skyline 七件套 + FastAPI 官方 + 筛选后的 mattpocock 工程 skill。清单见 `docs/framework/skills.md`。
- 界面观感：奶油水彩 + 圆脸腮红。token 在 `miniprogram/styles/`，插画在 `assets/brand|icon|tab`，跨页组件 `empty-state` / `react-row`。规范 [miniprogram/visual.md](miniprogram/visual.md)。
- 阶段 F mock：各模块 `services/` + `types/` 已按 [api/contract.md](api/contract.md) 建好；`core/request` 在 `useMock: true` 时按 method+path 返回信封内 `data`；未命中仍 `MOCK_NOT_IMPLEMENTED`。页面改为只调本模块 service（相册/发帖/创作可调 `media`）。mock 种子：当前用户、两本相册、若干帖（含草稿）、一条视频任务、积分流水合计 180。发帖 `pending` 直接 `published` 并记 +20 积分。
- 模块轻量化重构：`core/mock.ts` 收敛为 36 行的 adapter 注册/匹配入口；业务 mock handlers 下沉到各模块 `services/mock.ts`，共享无业务运行时工具位于 `core/mock-runtime.ts`。`community` 详情页拆为 245 行编排页，并将评论视图、评论动作、输入编排、媒体上传、录音播放分别移至页面专用 helper；页面路径、事件名、service/API 行为保持不变。
- 详情页拆分收尾：安装 TypeScript 5.6 并加入 `npm run typecheck`，启用 `skipLibCheck`；页面对象已回到 `detail.ts` 的 `Page({ ... })`，删除 `detail-page.ts`；录音器回调改为单例注册并通过当前页回写；评论 composer、voice、actions helper 改为明确 state + patch/callback 接口；本次拆分文件已恢复单行 120 字符以内的可读格式。
- 详情页解耦收尾（第二轮）：`onLikeComment` / `onMoreComment` 改传 getter，`comments` / `post` 在异步响应回来时才读，消除「发请求前快照、响应回来时已过期」导致的覆盖；语音播完清 `playing` 的回写改为模块内 `playbackSink`，不再用 `getCurrentPages()` 猜栈顶页（原写法在详情页 `navigateTo` 进 compose 页后写不回详情页）；删掉 `comment-composer.ts` 里转发用的空壳 `uploadImages`，`onCommentInput` 复用 `setCommentBody`；`detail-voice.ts` / `comment-actions.ts` 的回调类型由 `Record<string, unknown>` 收紧为具体字段。`detail.ts` 367 行超参考线，属已知例外，见决策日志。
- 项目 skill 现在由 Grok 与 Codex 共用：实际内容位于 `.grok/skills/`，项目级 `.agents/skills/` 通过软链接指向同一目录；`.grok/skills/**` 已纳入版本控制。
- Claude Code 接入同一套 skill 与规范：新增根目录 `CLAUDE.md` 作为 Claude 会话入口（只写路由与 Claude 专属机制，规则仍在 `AGENTS.md`）；`scripts/sync-claude-skills.sh` 把 `.grok/skills/` 同步成 `.claude/skills/` 真实目录（生成产物，已 gitignore，改动只改 `.grok/skills/`），不用软链接是因为 Claude Code 会对软链接 skill 目录报 `Unknown skill`；`.claude/settings.json` 只放 git 只读命令与同步脚本的白名单。`AGENTS.md`、`docs/README.md`、`docs/framework/skills.md` 已登记，`app-pet` skill 补上 code-standards 入口与验证/交接要求。
- 代码规范已收口：`docs/framework/code-standards.md` 只保留命名、薄调度、行数信号、交接模板；`adding-a-module.md` 按阶段 F / 阶段 1+ 分开；字段来源只认合同。`CLAUDE.md` 与 `/app-pet` 的 TypeScript 检查改为 `npm run typecheck`。
- mock 产品规则迁出 `core/`：`core/mock.ts` 只注册路由；`core/mock-runtime.ts` 无产品名词；种子在 `miniprogram/mocks/store.ts`；发帖加积分走 `points/services/mock-ledger.ts`；相册同步广场走 `community/services/mock-helpers.ts` 的 `syncAlbumToForum`。已删除 `core/mock-store.ts`。
- Skyline：`app.json` 补 `"renderer": "skyline"`；公共 `project.config.json` 的 `libVersion` 为 `3.7.0`（本机私有配置已 gitignore，可能覆盖）。详情录音 `onStop` / `onError` 改为 `recordSink`，不再 `getCurrentPages()`。`.hint` 颜色进 `--color-hint-text`。`page-shell` 顶栏 inline 色与 token 相同 hex。media mock 按路径后缀区分图片 / 语音 mime。
- 微信开发者工具已打开仓库根目录：小程序可启动，界面与主路径正常。
- 帖子互动改为点赞 / 评论 / 收藏 / 转发。点赞和收藏互相独立；评论区可连续发、可评论别人。删评论：本人只能删自己的，贴主可删该帖任意一条，不连带删别人的；删帖才清掉该帖全部评论。转发走微信分享。
- 评论区补齐：点赞评论、三点菜单（复制 / 举报 / 有权限才删除）、配图（最多 9 张，列表最多露 3 张，超过叠放）、水彩贴纸资源可跟在正文后、语音评论、艾特。输入条：大圆角输入 + 相册 / @ / 表情 / 语音图标 + 发送。不做 AI 润色。艾特写入 `body` 的 `@昵称 `，评论列表里仅这段用主色；退格一次删掉整段。语音走 `audio_url` / `audio_duration`，按住说话松开发出。电脑端选图没有摄像头则退回相册；录音在电脑端可能失败。
- Skyline 列表骨架：业务页纵向 `scroll-view` 补 `type="list"`；广场横向滚动加 `enable-flex`；首页 / 广场 / 我的发布把 `post-card` 做成列表直接子节点；导航栏改为同步 `getSystemInfoSync` 并缓存。模拟器里 `navigateTo` 仍可能空一拍，**真机调试不卡**，见 [miniprogram/README.md](miniprogram/README.md)。
- 真机调试：`detail-voice.ts` 去掉 `recordSink?.`，改成显式判断。`es6` / `enhance` 仍关闭。
- 真机对照：点动态进详情不卡。模拟器 `navigateTo` 空一拍只当开发者工具现象。阶段 F 在此基础上继续，不再为跳转改详情。
- 「我的」编辑资料页已接：点资料卡进 `modules/me/pages/profile/profile`；头像走 `chooseAvatar`（含微信头像 / 相册 / 相机）；昵称普通输入 1–16 字，不用 `type="nickname"`；点保存才 `POST /api/v1/media`（若换头像）+ `PATCH /api/v1/me`。未保存返回有改动则确认。`catch-back` 仅本页开启。评论作者展示跟 `store.me`。
- 开发 CLI 口径收口为 Grok / Codex / Claude Code。已删除 `docs/framework/hermes.md` 及相关路由；skill 仍由 `.grok/skills/` 一份副本供三个 CLI 读取。
- Hermes 重新接入：仍读根目录 `AGENTS.md`（自动注入），项目 skill 走已有 `.agents/skills` 软链，本机 `hermes skills trust`。不恢复 `docs/framework/hermes.md`。
- 相册一次性开发文档已落盘：[dev/album.md](dev/album.md)。上传页、列表卡、详情、可见性三档已在 HEAD（`98621c9`）。不进 `AGENTS.md` / `docs/README.md`；点验通过后删除。
- 「我的」丰富已接 mock：资料卡四计数（动态 / 获赞 / 关注 / 粉丝）；菜单分组；收藏 / 关注 / 粉丝 / 设置页。合同增加 `Me` 四计数与 `GET /community/post/favorite`、`GET /community/follow`、`GET /community/follower`。一次性文档 [dev/me.md](dev/me.md)，不进 `AGENTS.md` / README；点验通过后删除。
- 积分任务与独立签到页已接 mock（`319b846`）：首页「签到」进 `modules/points/pages/checkin/checkin`（当月月历、可回上个月、近 7 天补签）；积分任务只留发帖 / 评论 / 点赞（每天 3 / 1 / 3，自动入账）；合同增加 `PointsSummary` 的 `checkin_dates`、三个今日计数，以及 `POST /api/v1/points/makeup`。一次性文档 [dev/points.md](dev/points.md)，点验通过后删除。
- 签到页近 7 天进度条已接（未点验）：第 1–7 天节点（第 3 天 +30 送卡、第 7 天 +60 送卡），只读 `streak` / `today_checked`，不加合同字段。种子改为昨天+前天、补签卡 0。一次性文档 [dev/checkin-streak.md](dev/checkin-streak.md)。
- 广场改为公开动态流已接（未点验）：发动态不选板块；底栏与首页入口文案「广场」；推荐 / 关注为下划线；「大家都在看」横滑封面进详情。合同：`board` 发帖可省略（默认 `daily`），列表可带 `topic`（界面不用芯片筛）。相册同步文案改为「广场」，字段仍是 `sync_to_forum`。

## 进行中

- 阶段 F：P0/P1 页面、services、mock 已接。真机调试可用。广场公开动态流、签到进度条等人点验。

## 已知风险

不要把延后项当成阶段 F 缺口。

| 项 | 状态 | 何时处理 |
|---|---|---|
| `POST /api/v1/media` 真上传 | mock 按路径后缀区分图（`image/jpeg`）和语音（`audio/mpeg`），`url` 仍是微信临时路径。`core/request` 还没有 `wx.uploadFile` / multipart | **阶段 2** 关 `useMock` 之前 |
| mock 点赞/收藏 | 资源上的布尔，不是每用户一条；单用户先行够用 | 接真 API 后由后端处理 |
| mock 种子仍是一份 `mocks/store.ts` | 写路径已走 community `mock-helpers` / points `mock-ledger`；再按模块拆种子不阻塞阶段 F | 按需，不是现在 |
| 本机 `project.private.config.json` 覆盖基础库 | 已 gitignore。本机已点开正常。换机器或 DevTools 改回旧 `libVersion` 时，把私有配置改成与公共 `3.7.0` 一致 | 换环境若 Skyline 未亮 |
| 开发者工具 Skyline 模拟器 `navigateTo` 空一拍 | 模拟器里点动态 / 二级页抬手后转场会迟一拍；**真机调试不卡**。已补 `scroll-view type` 与导航栏同步 | 不当作产品缺口。不要为修模拟器去改详情第一帧或重做已撤回的详情 WXML |

## 下一步（给新对话，按此顺序）

1. 用微信开发者工具打开仓库根目录，点验广场：发动态不选板块、推荐里能看到刚发的、大家都在看点进详情、底栏是「广场」。不要先搭 FastAPI。不要回头修 `navigateTo`。不要改已锁定的 tab 路径。
2. 仍待点验：签到进度条，按 [dev/checkin-streak.md](dev/checkin-streak.md)。点验通过后删除该文件。相册 [dev/album.md](dev/album.md)、「我的」[dev/me.md](dev/me.md)、积分 [dev/points.md](dev/points.md) 点验通过后同样删除。
3. 不要每改一处就更新文档。用户说整理 / 总结 / 更新对接文档再改本文件和 handoff。**改接口仍须先改** [api/contract.md](api/contract.md)。
4. 阶段 2 接真 API 前，先在 `miniprogram/core/request.ts` 补 media 的 multipart（`wx.uploadFile`，字段名 `file`）。这不是下一对话的默认任务。

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
| 2026-08-29 | 帖子互动改为点赞 / 回复 / 收藏 / 转发 | 用户不要心/骨头/星；点赞和收藏可同时点。回复有 mock 评论；转发用微信分享 |
| 2026-08-29 | 回复可连续、可回别人、可删；删帖/删回复级联 | 按常见社交软件：输入条常在；`parent_id` 线程；删一条带上子回复 |
| 2026-08-29 | 删回复权限：本人或贴主；不连带删别人的 | 普通人只能删自己的评论；贴主可删帖下任意一条；子回复改挂父级 |
| 2026-08-29 | 互动文案统一为评论 / 评论区 | 不用「回复」；删除确认为普通「删除后无法恢复」 |
| 2026-08-29 | 日常改代码不写 docs，点名整理再更新 | 每改一次都写文档太慢；改接口仍先改 contract.md |
| 2026-08-29 | 评论输入条：相册 / @ / 表情 / 语音，不做 AI 润色 | 对标常见内容 App 底栏；表情面板是系统 Emoji，水彩贴纸可出现在已发评论里，点开评论不再自动弹出贴纸条 |
| 2026-08-29 | 评论可配图、可语音、可艾特；评论可点赞 / 举报 | 配图最多 9、展示最多 3 张其余叠放；语音 `audio_url`+秒数；艾特只写进 `body`，列表主色标记，退格整段删除 |
| 2026-08-29 | 实现先保证手机，电脑能点能发即可 | 不为电脑另做布局；选图无摄像头退回相册；录音在电脑端可不支持 |
| 2026-08-31 | 增加代码规范与多 Agent 交接规范 | 让并行开发遵守同一套模块边界、文件重量和验证标准，降低维护与迭代成本 |
| 2026-08-31 | Claude Code 与 Grok / Codex 共用同一份 skill 和规范 | 三个 CLI 一份规范，避免各写一套；Claude 侧用同步脚本而不是软链接，软链接会让 `/app-pet` 报 `Unknown skill` |
| 2026-09-01 | 详情页 helper 只接收 state 与回调，页面对象回到 `Page({ ... })` | 恢复微信 `this` 类型上下文，避免页面实例跨 helper 传播；录音器保留全局单例注册，避免重复回调 |
| 2026-09-01 | `detail.ts` 367 行列为已知例外，不再拆；参考线该按页面目录算 | 页面对象必须留在 `Page({ ... })` 里才有 `this` 类型，拆成 `xxx-page.ts` 只是绕行数参考线并丢掉类型安全。detail 目录合计 1029 行，要改的是「按单个文件名算」这条规则本身 |
| 2026-09-01 | helper 需要页面 state 时传 getter，不传快照 | 快照在异步响应回来时可能已过期，会把 reload 之前的旧列表整个写回去；getter 只暴露一个字段、调用时求值，不等于把 page 实例传回 helper |
| 2026-09-03 | mock 种子与产品 helper 离开 `core/` | 拆文件后业务仍堆在 `mock-store` / `mock-runtime`。改为 `mocks/store.ts` + community `mock-helpers` / points `mock-ledger`；`core/mock.ts` 只注册路由 |
| 2026-09-03 | `app.json` 声明 `"renderer": "skyline"`，基础库 3.7.0 | 原先只有 `rendererOptions`，`project.private.config.json` 仍钉在 2.32.3，Skyline 不会启用 |
| 2026-09-03 | 录音 `onStop` / `onError` 走 `recordSink` | 与播放的 `playbackSink` 对齐，不再 `getCurrentPages()` 猜栈顶 |
| 2026-09-03 | 已知风险只登记在 progress.md | 人点验、私有基础库覆盖、media multipart、单用户 mock 点赞、种子仍一份 store，分清「现在」和「阶段 2」 |
| 2026-09-03 | 跳转卡顿先改公共骨架，不先动详情评论 | 当时只在模拟器里看到 `navigateTo` 空一拍；评论分页 / `lazy-load` 对当前几条评论无收益且会拆线程 |
| 2026-09-06 | 模拟器 `navigateTo` 空一拍不当作产品缺口 | 真机调试点动态进详情不卡；空一拍只出现在开发者工具验证 |
| 2026-09-07 | 「我的」用独立编辑资料页改头像昵称；头像只走 `chooseAvatar`；昵称普通输入，不用微信昵称快捷填入；点保存才 PATCH | 微信已收回 getUserProfile 真头像；官方头像选择已含相册/相机；草稿预览避免误触写库；昵称不绑微信名 |
| 2026-09-07 | Hermes 与 Grok / Codex / Claude Code 共用同一份 skill 和规范 | **已被 2026-09-08 覆盖**：当时接过 Hermes；现已停用 |
| 2026-09-08 | 不再用 Hermes 开发 | 用户确认只保留 Grok / Codex / Claude Code；删除 `docs/framework/hermes.md`、相关路由和本机 Hermes 配置。**已被 2026-09-16 覆盖** |
| 2026-09-16 | 再用 Hermes 开发，与其它 CLI 共用 `AGENTS.md` 和 `.grok/skills/` | 用户要求 Hermes 自动读 skill 与 Agent 文档，且不影响 Grok / Codex / Claude。不恢复独立 `hermes.md`；本机 `hermes skills trust`，不要加 `.hermes.md`（会盖掉 `AGENTS.md`） |
| 2026-09-07 | 相册 tab 是自己的管理页；可见性公开 / 私密 / 好友可见；好友 = 互相关注；别人的相册后期从内容进入；看别人只见公开 + 好友可见，私密当不存在 | 用户确认。黑名单后期插入同一套 `can_view`。本阶段仅公开可同步论坛 |
| 2026-09-07 | 相册排版：列表 L3（分档 + 双列卡）、详情 D1（封面英雄图）、上传 V1（三芯片）；新建默认私密 | 用户确认。切片 2 先出卡、切片 4 再出分档和角标 |
| 2026-09-07 | 相册按 [dev/album.md](dev/album.md) 分切片开发，每片点验过关再做下一片 | 用户要求先文档后代码；一次性文档，不进 `AGENTS.md` / README |
| 2026-09-16 | 「我的」资料卡四计数；菜单分组；新页收藏 / 关注 / 粉丝 / 设置 | 用户确认。计数只在 `GET/PATCH /me`；收藏/关注/粉丝列表归 community；不进作者页、消息中心、商城 |
| 2026-09-16 | 签到从积分任务拆到独立页；任务只留发帖 / 评论 / 点赞 | 首页「签到」进月历页，不铺日历、不调积分接口。发帖每天前 3 条 +20，评论每天 1 条 +5，点赞帖子每天 3 条 +2（取消不退）。连续第 3 / 7 天额外积分并各送 1 张补签卡；补签只 +10 |
| 2026-09-16 | 签到页上方面「第 1–7 天」进度条，不是周一到周日 | 月历管哪天签过、点哪天补签；进度条只展示连续加码。合同不加字段，页面用已有 `streak` / `today_checked` |
| 2026-09-17 | 广场是公开动态流，不是论坛板块房间 | 发帖必选板块像进房间。推荐 / 关注留下；话题可写在帖上，不当广场分类条。「大家都在看」横滑图进详情。底栏文案「广场」。`board` 响应仍有，发帖可省略默认 `daily` |
| 2026-09-03 | 改 WXML 必须保持标签配对 | 为修卡顿重写详情时少闭合导致编译失败，已撤回；编译不过先还原，不要继续堆新文件 |
| 2026-09-05 | 业务代码不写 `?.` / `??` | `es6`/`enhance` 为 false，真机调试把 `recordSink?.` 编进 js 后 SyntaxError，已改成显式判断 |

## 未决（不阻塞阶段 F）

- 产品正式名称（界面暂用「宠物记录」）。
- 生产对象存储用哪家云（开发期本地磁盘或 MinIO）。
- 图生视频出片提供商与密钥：P2 再锁，不进小程序。
- 微信隐私协议页：上线前再补，阶段 F 开发者工具可关校验。
