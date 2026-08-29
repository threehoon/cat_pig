# 对接文档

前后端、本地环境、**前端先行**时的 mock，以及页面 / 模块名的交界写在这里。

目录怎么拆见 [framework/overview.md](framework/overview.md)。产品做哪些功能见 [product/benchmark.md](product/benchmark.md)。当前进度见 [progress.md](progress.md)。

## 当前工作方式：前端界面先行

五个 tab、二级页、奶油水彩皮、`services/`、mock、帖子评论区（点赞 / 举报 / 配图 / 语音 / 艾特）已写入。`useMock: true`。不先做 FastAPI 和数据库。进度以 [progress.md](progress.md) 为准。

日常改代码不要改 `docs/`。用户说「整理」「总结」「更新对接文档」再改本文件和 progress。**改接口仍须先改** [api/contract.md](api/contract.md)。

| 现在做 | 现在不做 |
|---|---|
| 按用户点名继续小程序功能；开发者工具可点主路径 | `server/` 可运行工程 |
| 保持 `useMock: true` 与合同里的 path/字段 | 真 `wx.request` 打真实 API |
| 保持现有 tab 路径和视觉 token | 接微信登录换 JWT、真出片、真审核 |
| 页面只调本模块 `services/` | 把 mock 写进 page 的 wxml/ts 里；未点名就重做视觉；每改一处就改文档 |

**预留接口是阶段 F 的完成条件，不是后补。** 路径和字段的唯一依据是 [api/contract.md](api/contract.md)。前端 mock 按它返回 JSON；后端按它写 FastAPI。两端都禁止自己发明字段名。后端开工后只改 `useMock` / `request` 实现，不准改合同里的 path 和字段。

前端先行时允许 **先建小程序模块目录和页面，暂不建** `server/app/modules/<feature>/`。后端开工时必须用 **同一套英文模块名**。

## 已锁定的模块名（前后端同名）

| 英文目录 / API feature | 能力 | 有没有页面 |
|---|---|---|
| `auth` | 微信登录、会话 | 无独立页；启动时走 `core/auth` |
| `me` | 当前用户资料、「我的」页 | 有 |
| `media` | 图片 / 语音文件上传与 URL | 无独立页；被相册、帖子、评论、视频引用 |
| `album` | 独立相册 | 有 |
| `community` | 首页门户、广场 / 论坛、帖子 | 有 |
| `video` | 图生视频任务 | 有 |
| `points` | 积分流水、签到 | 有 |

禁止再用 `pet`、`journal`、`ledger`、`reminder`、`user`、`diary`、`forum`、`plaza`、`bill` 当模块目录名。广场和论坛是 `community` 的页面，不是两个模块。任务管理是 `video` 的列表页，不是独立模块。

## 界面先行：Tab 与页面

对标功能对等，**不抄参考产品的品牌名、插画和文案原句**。小程序最多 5 个 tab。本产品用满这 5 个：

| Tab | 文案 | 对应页面路径（登记进 `app.json`） |
|---|---|---|
| 1 | 首页 | `modules/community/pages/home/home`（首页） |
| 2 | 相册 | `modules/album/pages/list/list` |
| 3 | 创作 | `modules/video/pages/create/create`（中间加号） |
| 4 | 论坛 | `modules/community/pages/plaza/plaza` |
| 5 | 我的 | `modules/me/pages/index/index` |

非 tab、从上面推进去的页：

| 模块 | 路径 | 做什么 |
|---|---|---|
| album | `modules/album/pages/upload/upload` | 上传到相册 |
| community | `modules/community/pages/compose/compose` | 发布 / 编辑帖子、存草稿 |
| community | `modules/community/pages/detail/detail` | 帖子详情 |
| community | `modules/community/pages/mine/mine` | 我的发布 |
| points | `modules/points/pages/list/list` | 积分明细 |
| video | `modules/video/pages/tasks/tasks` | 任务管理（生成任务列表） |
| video | `modules/video/pages/detail/detail` | 一条生成任务详情 |

`pages/index`、`pages/logs`：界面接入后，把 `app.json` 的 `pages` 第一项改成社区首页，这两页不再当入口。不要在它们里面写产品 UI。

`window.navigationStyle` 已是 `custom`。新页面用现有 `components/navigation-bar`，或抽更通用的跨模块导航，放在 `miniprogram/components/`。

导航栏工作标题用 **「宠物记录」**（正式品名未定，不要擅自用对标品牌名）。

视觉：暖米色底、橙色主按钮；细则只认 [miniprogram/visual.md](miniprogram/visual.md)。气质可学 [product/reference/](product/reference/README.md) 截图，不贴对方素材。阶段 F 用**原生 tabBar**，第三项是加号；中间凸起不阻塞。

相册编辑：同一 upload 页带 `?id=`。快捷提示词、分辨率选项是页面本地文案，写入 `prompt` / `resolution` 字段，不新开接口。「我的发布」顶部四个数字从 `GET /api/v1/community/post/mine` 聚合，不另开统计接口。

### 界面枚举（字段用英文，界面用这列中文）

| 字段 | 值 → 文案 |
|---|---|
| 广场 `tab` | `recommend` 推荐；`following` 关注；其余同 `board` |
| 帖子 `board` | `qa` 问答；`show` 晒宠；`share` 分享；`help` 求助；`daily` 日常；`experience` 经验 |
| 帖子 `status` | `draft` 草稿；`pending` 审核中；`published` 已发布；`rejected` 未通过 |
| 帖子动作 | 点赞 / 评论 / 收藏 / 转发（转发走微信分享，无单独接口） |
| 视频 `status` | `pending` 待执行；`running` 执行中；`success` 执行成功；`failed` 执行失败 |
| 视频 `resolution` | `540p` `720p` `1080p` `2k` `4k` 原样展示 |

### 入口约定（避免各写各的）

- 首页四个入口：图生视频 → 创作 tab；相册 → 相册 tab；论坛 → 论坛 tab；签到 → 积分明细页（可带 `checkin=1`，由 `points` 页调签到接口）。禁止首页 import `points` service。
- 首页下方动态：`GET /api/v1/community/post?tab=recommend`。点「更多」切到论坛 tab。
- 论坛 tab：搜索走 query `q`；顶部分栏对应 `tab`（推荐 / 关注 / 六个板块）。
- 创作 tab 打开即为图生视频表单，不是发帖。发帖从广场 / 我的发布进入。
- 相册 tab：只列当前用户相册；右下或空态「上传」进 upload 页。
- 「我的」：头像昵称走 `GET /api/v1/me`；三个入口分别进我的发布、积分明细、任务管理。

### 帖子互动（已接 mock）

卡片和详情底栏四个动作，文案固定：**点赞 / 评论 / 收藏 / 转发**。详情页下方标题是 **评论区**，不要写「回复」。

| 动作 | 行为 | 接口 |
|---|---|---|
| 点赞 | 独立开关 | `POST /api/v1/community/post/{id}/like` |
| 评论 | 详情底部输入条：相册 / @ / 表情 / 语音 / 发送；点某条可评论该人 | `GET/POST /api/v1/community/post/{id}/comment`，`DELETE .../comment/{comment_id}`，`POST .../comment/{comment_id}/like`，`POST .../comment/{comment_id}/report` |
| 收藏 | 独立开关，可与点赞同时亮 | `POST /api/v1/community/post/{id}/favorite` |
| 转发 | 微信分享，无后端接口 | 页面 `enableShareAppMessage` + `button open-type="share"` |

删评论：评论作者只能删自己的；贴主可删该帖下任意一条。只删点中的那一条，子评论改挂父级，不连带删别人的。删帖才清掉该帖全部评论。删除确认文案：标题「删除评论」，内容「删除后无法恢复」。

评论行右侧：点赞心形；三个点打开复制 / 举报（不能举报自己的）/ 有权限才有删除。举报原因：`spam` 垃圾广告、`abuse` 不友善、`porn` 色情低俗、`other` 其他。阶段 F mock 只提示已收到。

配图最多 9 张；列表同时最多露 3 张，超过则叠放一张并带剩余张数，点开 `previewImage`。贴纸 id 见合同，画在正文后；点开评论**不**自动弹出贴纸条。表情按钮打开系统 Emoji 面板。

语音：点麦克风切到「按住 说话」，松开即发一条语音评论（`audio_url` + `audio_duration` 秒）。电脑端录音可失败并提示。艾特：点 @ 选本帖出现过的其他人，写入 `body` 为 `@昵称 `（后面一个空格）；评论列表里仅这段用主色 `.mention-mark`，正文颜色不变；退格一次删掉整段。输入框本身不叠高亮层。不做 AI 润色。

`body`、贴纸、配图、语音不能同时空。选图：`wx.chooseMedia`，无摄像头时退回只用相册。

评论行 UI 在 `modules/community/components/comment-row/`。艾特切分在 `modules/community/mentions.ts`。贴纸目录在 `modules/community/stickers.ts`。

首页 / 论坛 / 我的发布 / 详情页已开分享。`react-row` 图标：`assets/icon/react-like|reply|favorite|share.png` 与 `-active`（评论按钮文件名仍是 `reply`，界面文案是「评论」）。

### tabBar 图标

五个 tab 必须都有未选中 / 选中两套图标（`miniprogram/assets/tab/`，文件名锁死：`home` / `album` / `create` / `plaza` / `me` 各一套普通 + `-active`）。现为圆润色块，重出用 `scripts/export-brand-icons.py`。颜色写入 `app.json` 的 `tabBar`（选中色橙色）。第三个 tab 用加号图，表示创作。

阶段 F 允许改 `app.json` 的 `pages` 顺序、`tabBar`、以及选图 / 录音所需的 `permission` / `requiredPrivateInfos`（这是对 [adding-a-module.md](framework/adding-a-module.md)「不改 window」的明确例外）。选图：`scope.camera` 文案「用于上传宠物照片到相册、帖子、评论和视频」。录音：`scope.record` 文案「用于录制评论语音」。不需要定位权限。微信隐私协议页上线前再补。

首页顶部运营位阶段 F 用本地占位，不新开 banner 接口。

## 职责切分

| 事项 | 后端 (`server/`) | 小程序 (`miniprogram/`) |
|---|---|---|
| 微信 `code` 换 `openid` | 负责，openid 只存库 | 只调 `wx.login` 拿 `code` |
| 会话 | 签发与校验 JWT | `core/auth` 存 token |
| 校验、写库、审核状态 | 负责（接真 API 之后） | UI 可做空态/格式提示，不做最终判定 |
| 图生视频出片 | worker 异步；密钥只在服务端 | 只提交任务、查状态、播 `result_url` |
| 字段名、错误码 | 始终以 [api/contract.md](api/contract.md) 为准；OpenAPI 必须对上合同 | 先行按合同写 `types/`；接真 API 后可用生成文件覆盖，但仍须等于合同 |
| 页面、交互、选图 | 不出现页面文案 | 负责 |
| 图片二进制 | 收文件、存对象存储、返回 URL | 先行阶段可用本地临时路径占位；接 API 后走 `media` |
| mock 数据 | 不存在 | 只允许出现在 services 或 `core/request` 的 mock 分支 |

## 必须预留的 service（与接口一一对应）

每个模块建 `services/`，方法名可按习惯，但 **path、method、body/query 字段必须如下**。没有列出的接口不要先造。

| 模块文件 | 用户动作 | method + path |
|---|---|---|
| `auth`（可放 `core/auth` 内） | 启动登录 | `POST /api/v1/auth/login` |
| `modules/me/services/` | 当前用户 | `GET/PATCH /api/v1/me` |
| `modules/media/services/` | 上传图或评论语音 | `POST /api/v1/media` |
| `modules/album/services/` | 相册列表 / 详情 / 上传 / 改 / 删 | `GET/POST /api/v1/album`，`GET/PATCH/DELETE /api/v1/album/{id}` |
| `modules/community/services/` | 广场、发帖、详情、我的发布、点赞、收藏、评论、关注 | `GET/POST /api/v1/community/post`，`GET /api/v1/community/post/mine`，`GET/PATCH/DELETE /api/v1/community/post/{id}`，`POST .../like`，`POST .../favorite`，`GET/POST .../comment`，`DELETE .../comment/{comment_id}`，`POST .../comment/{comment_id}/like`，`POST .../comment/{comment_id}/report`，`POST/DELETE /api/v1/community/follow` |
| `modules/video/services/` | 创建任务、列表、详情、删 | `GET/POST /api/v1/video`，`GET/DELETE /api/v1/video/{id}` |
| `modules/points/services/` | 汇总、流水、签到 | `GET /api/v1/points/summary`，`GET /api/v1/points/ledger`，`POST /api/v1/points/checkin` |

页面事件处理里只出现 `xxxService.list()` 这类调用。字段名用下划线：`image_urls`、`sync_to_forum`、`points_balance`，不要在页面层再映射一套驼峰再丢掉。

**例外：** `media` 没有自己的页面。相册 / 发帖 / 创作在选图后可以调用 `modules/media/services` 拿 `url`，再交给本模块 service。其它跨模块仍然只许跳路由，不许互相 import service。

首页、我的若只展示其它模块的数据：首页帖预览走 **本模块** `community` service；积分入口只跳路由，不在 `me` 页面 import `points` 的 service。`GET /api/v1/me` 已带 `points_balance`，我的页展示余额用这个字段。

### 页面做完的自检

- [ ] 该页所有读写都经过本模块 `services/`
- [ ] service 的 path 与 [api/contract.md](api/contract.md) 逐字相同
- [ ] 请求/响应字段与合同里的资源 JSON 相同（`snake_case`、字符串 id）
- [ ] `useMock: true` 时能走通；切换 `false` 不需要改页面
- [ ] 没有 `wx.request`、没有页面内假数组、没有 `TODO 接接口`

## Mock 约定（界面先行必守）

1. `miniprogram/core/config.ts` 提供 `useMock: true`（先行默认）和 `apiBaseUrl`。
2. 页面 **不准** `wx.request`，不准写死主机名，不准直接 import 一份「页面专用假数据」。
3. 模块 `services/` 只调 `core/request`。`useMock === true` 时，`request` 返回符合 [api/contract.md](api/contract.md) 的本地数据（按 method+path 分发）。
4. 成功 / 失败信封与真 API 相同，JSON 形状见 [api/contract.md](api/contract.md)。
5. 假数据足够点通主路径即可：当前用户、若干相册、若干已发布帖（含别人的帖和一条带评论的帖）、一条视频任务、几条积分流水。不要做后台。
6. 没有审核员：mock 里 `POST` 帖子若 `status` 为 `pending`，直接存成 `published`，否则广场列表看不到刚发的帖。接真 API 后再走审核。
7. mock 登录在 `core/auth` 启动时同步完成（`jwt-or-mock` + 写入当前用户 id），页面 `onShow` 时已有会话。

接真 API：`useMock` 改为 `false`，确认 `apiBaseUrl`，services 不用改方法名。

## 本地怎么对上（后端落地之后）

现在还没有这些进程。目标：

1. Docker Compose 只跑 PostgreSQL（以及可选的 MinIO）。
2. FastAPI：`http://127.0.0.1:8000`。
3. 微信开发者工具打开本仓库根目录；开发期关闭「校验合法域名」。
4. `apiBaseUrl` 指向 `http://127.0.0.1:8000`（真机预览改为电脑局域网 IP）。

`wx.request` 不是浏览器，没有 CORS。正式版要配微信公众平台 request / uploadFile 合法域名。

## 环境变量（后端，界面先行可暂不建）

| 变量 | 含义 | 本地 |
|---|---|---|
| `APP_ENV` | `local` / `staging` / `prod` | `local` |
| `DATABASE_URL` | SQLAlchemy 异步连接串 | Compose 里的 Postgres |
| `JWT_SECRET` | 签名密钥 | 仅本地默认值，禁止用于生产 |
| `JWT_ALGORITHM` | 固定 `HS256` | 不要在业务模块里改算法 |
| `JWT_EXPIRE_SECONDS` | 会话时长 | 开发可用 7 天 |
| `WECHAT_APPID` | 小程序 AppId | 与 `project.config.json` 一致：`wxe7c6ce42979250cd` |
| `WECHAT_SECRET` | 小程序 AppSecret | 只放环境变量或未提交文件，不进 git |
| `MEDIA_ROOT` | 开发期本地上传目录 | 例如 `server/var/media` |
| `API_PREFIX` | 固定 | `/api/v1` |
| 视频出片密钥 | 只放服务端 `.env` | 接 P2 真出片时再登记，不进小程序 |

本地用 `server/.env`（忽略提交）。

## HTTP 契约

路径、字段、类型、示例 JSON **只认** [api/contract.md](api/contract.md)。本文件不再重复字段表，避免两份合同打架。

补充（环境级，合同里不写的）：

- FastAPI 另提供 `GET /openapi.json`、`GET /docs`，生成结果必须能对上合同。
- 小程序按 `error.code` 分支，禁止按中文 `message` 分支。

## 登录时序（接真 API 后）

1. 小程序 `wx.login` → `code`。
2. `POST /api/v1/auth/login`，`{ "code": "..." }`。
3. 后端用 AppId + Secret 向微信换 `openid`。`session_key` 不准下发。
4. upsert 用户，签发 JWT；首次登录写入注册积分。
5. `core/auth` 存 token；之后 `core/request` 自动带上。

界面先行：启动可跳过真登录，mock 成已登录，直接进首页 tab。

## 媒体

- 二进制不进 PostgreSQL。库中只存 URL、宽高、mime、所属模块与资源 id。
- 开发期：`MEDIA_ROOT`；以后换 OSS 只改内核。
- 界面先行：选图后用 `wx` 临时路径展示即可，services 仍当作 `image_urls: string[]`。

## 类型同步

接真 API 后：用 OpenAPI 覆盖 `modules/<feature>/types/`。禁止长期手改生成结果。生成脚本在后端内核落地时写进 [progress.md](progress.md)。

## 发布时对接

- 正式版：request / uploadFile 合法域名指向生产 API。
- 生产密钥不得进仓库。
- 上传包只含 `miniprogram/`；`.md` 已在 `packOptions` 忽略。

## 下一对话建议读取顺序

1. [AGENTS.md](../AGENTS.md)
2. [progress.md](progress.md)（确认阶段 F、下一步、文档节奏）
3. 本文件（模块名、页面路径、帖子互动、必须预留的 service、mock 约定）
4. [api/contract.md](api/contract.md)（每个 service 的 path 和 JSON）
5. [miniprogram/README.md](miniprogram/README.md)
6. [product/benchmark.md](product/benchmark.md)（只做表里标「有」的）

改观感才打开 [miniprogram/visual.md](miniprogram/visual.md)。不要先做 FastAPI。改接口先改合同。不要每改一处就改文档。
