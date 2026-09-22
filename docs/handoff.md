# 对接文档

前后端、本地环境、**前端先行**时的 mock，以及页面 / 模块名的交界写在这里。

目录怎么拆见 [framework/overview.md](framework/overview.md)。产品做哪些功能见 [product/benchmark.md](product/benchmark.md)。阶段、下一步、已知风险只认 [progress.md](progress.md)。

## 新对话从这里开始

阶段 **F** 仍在进行，`useMock: true`。1a 后端按 [dev/backend-assistant-1a.md](dev/backend-assistant-1a.md) 串行；切片 A、B 已通过，切片 C（知识库，无 HTTP）2026-09-22 已通过。不要关 `useMock`。不要重做视觉（除非用户点名某一页）。

下一轮：只做切片 D（`/suggestion` + `/ask`）。不要接 LLM。不要关 `useMock`。不要建 `consult` / `experience`。小程序点验可并行。阶段、已知风险只认 [progress.md](progress.md)。

| 现在做 | 现在不做 |
|---|---|
| 按 1a 文档做当前切片；小程序保持 mock | 关 `useMock`、真 `wx.request` 打真实 API |
| 保持 `useMock: true` 与合同里的 path / 字段 | 真出片、真审核 |
| 保持五个 tab（首页 / 相册 / 小x / 广场 / 我的）和视觉 token | 把 mock 写进页面；未点名就重做视觉 |
| 页面只调本模块 `services/` | 每改一处就改文档 |

日常改代码不要改 `docs/`。用户说「整理」「总结」「更新对接文档」再改本文件和 progress。**改接口仍须先改** [api/contract.md](api/contract.md)。

### 当前基线

| 项 | 值 |
|---|---|
| 模块 | `auth` `me` `media` `album` `community` `video` `points` `assistant`（`auth` / `media` 无独立页） |
| 业务 service | 7 个（`me` `media` `album` `community` `video` `points` `assistant`）；登录在 `core/auth` |
| mock | 各模块 `services/mock.ts`；community 另有 `mock-helpers.ts`；points 另有 `mock-ledger.ts`；assistant 另有 `mock-knowledge.ts`；种子 `miniprogram/mocks/store.ts`；入口 `core/mock.ts`（只注册 / 匹配） |
| 页面 | `app.json` 23 项：21 个模块页 + `pages/index` + `pages/logs`（残留，不当入口） |
| 渲染 | `"renderer": "skyline"`；公共 `libVersion` `3.7.0` |
| 检查 | `npm run typecheck`（typescript 5.6） |
| 详情页 | `community/pages/detail/detail.ts` 保留 `Page({...})`，不要再抽 `detail-page.ts`；录音走 `recordSink` |

**预留接口是阶段 F 的完成条件，不是后补。** 路径和字段只认 [api/contract.md](api/contract.md)。前端 mock 按它返回 JSON；后端按它写 FastAPI。禁止另起字段名。后端开工后只改 `useMock` / `request` 实现。

前端先行允许先建小程序模块和页面，暂不建 `server/app/modules/<feature>/`。后端开工时必须用**同一套英文模块名**。

## 已锁定的模块名（前后端同名）

| 英文目录 / API feature | 能力 | 有没有页面 |
|---|---|---|
| `auth` | 微信登录、会话 | 无独立页；启动时走 `core/auth` |
| `me` | 当前用户资料、「我的」页 | 有 |
| `media` | 图片 / 语音文件上传与 URL | 无独立页；被相册、帖子、评论、视频引用 |
| `album` | 独立相册 | 有 |
| `community` | 首页门户、广场动态、帖子 | 有 |
| `video` | 图生视频任务 | 有（创作页不是 tab） |
| `points` | 积分流水、签到 | 有 |
| `assistant` | 站内助手「小x」；以后向量库 / RAG | 有（底栏中间 tab） |

禁止再用 `pet`、`journal`、`ledger`、`reminder`、`user`、`diary`、`forum`、`plaza`、`bill`、`ai`、`rag`、`doctor` 当模块目录名。广场是 `community` 的页面，不是独立模块。任务管理是 `video` 的列表页，不是独立模块。

已预约、尚未建目录（产品边界见 [product/expansion.md](product/expansion.md)）。`consult` / `experience` 仍不建空目录、不写合同 path：

| 英文目录 / API feature | 能力 | 何时 |
|---|---|---|
| `consult` | 问诊 | 后期 |
| `experience` | 养宠经验分享 | 后期 |

## 界面先行：Tab 与页面

对标功能对等，**不抄参考产品的品牌名、插画和文案原句**。小程序最多 5 个 tab。本产品用满这 5 个：

| Tab | 文案 | 对应页面路径（登记进 `app.json`） |
|---|---|---|
| 1 | 首页 | `modules/community/pages/home/home`（首页） |
| 2 | 相册 | `modules/album/pages/list/list` |
| 3 | 小x | `modules/assistant/pages/chat/chat`（中间 C 位） |
| 4 | 广场 | `modules/community/pages/plaza/plaza` |
| 5 | 我的 | `modules/me/pages/index/index` |

非 tab、从上面推进去的页：

| 模块 | 路径 | 做什么 |
|---|---|---|
| album | `modules/album/pages/upload/upload` | 上传到相册 |
| community | `modules/community/pages/compose/compose` | 发布 / 编辑动态、存草稿 |
| community | `modules/community/pages/detail/detail` | 帖子详情 |
| community | `modules/community/pages/mine/mine` | 我的发布 |
| community | `modules/community/pages/favorites/favorites` | 我的收藏 |
| community | `modules/community/pages/follow/follow` | 我的关注 |
| community | `modules/community/pages/follower/follower` | 粉丝 |
| points | `modules/points/pages/list/list` | 积分明细 |
| points | `modules/points/pages/tasks/tasks` | 积分任务（发帖 / 评论 / 点赞） |
| points | `modules/points/pages/checkin/checkin` | 每日签到（月历、补签、近 7 天进度） |
| video | `modules/video/pages/create/create` | 图生视频表单（从首页入口进入，不是 tab） |
| video | `modules/video/pages/tasks/tasks` | 任务管理（生成任务列表） |
| video | `modules/video/pages/detail/detail` | 一条生成任务详情 |
| album | `modules/album/pages/detail/detail` | 相册详情 |
| me | `modules/me/pages/profile/profile` | 编辑资料（头像 / 昵称） |
| me | `modules/me/pages/settings/settings` | 设置（关于 + 注销占位） |

`pages/index`、`pages/logs`：界面接入后，把 `app.json` 的 `pages` 第一项改成社区首页，这两页不再当入口。不要在它们里面写产品 UI。

`window.navigationStyle` 已是 `custom`。新页面用现有 `components/navigation-bar`，或抽更通用的跨模块导航，放在 `miniprogram/components/`。

导航栏工作标题用 **「宠物记录」**（正式品名未定，不要擅自用对标品牌名）。

视觉：暖米色底、橙色主按钮；细则只认 [miniprogram/visual.md](miniprogram/visual.md)。气质可学 [product/reference/](product/reference/README.md) 截图，不贴对方素材。阶段 F 用**原生 tabBar**，第三项是小x。

相册编辑：同一 upload 页带 `?id=`。快捷提示词、分辨率选项是页面本地文案，写入 `prompt` / `resolution` 字段，不新开接口。「我的发布」顶部四个数字从 `GET /api/v1/community/post/mine` 聚合，不另开统计接口。资料卡「动态 / 获赞 / 关注 / 粉丝」走 `GET /api/v1/me` 的四个计数，不另开统计接口。收藏列表 `GET /api/v1/community/post/favorite`；关注 / 粉丝列表 `GET /api/v1/community/follow`、`GET /api/v1/community/follower`（item 为 Author）。

### 界面枚举（字段用英文，界面用这列中文）

| 字段 | 值 → 文案 |
|---|---|
| 广场 `tab` | `recommend` 推荐；`following` 关注。六个 `board` 值仍接受，不作主路径 |
| 帖子 `board` | 响应仍有；发帖可省略，默认 `daily`。界面不展示板块房间 |
| 广场 `topic` | 列表 query 仍可带；广场界面不用话题芯片筛 |
| 帖子 `status` | `draft` 草稿；`pending` 审核中；`published` 已发布；`rejected` 未通过 |
| 帖子动作 | 点赞 / 评论 / 收藏 / 转发（转发走微信分享，无单独接口） |
| 视频 `status` | `pending` 待执行；`running` 执行中；`success` 执行成功；`failed` 执行失败 |
| 视频 `resolution` | `540p` `720p` `1080p` `2k` `4k` 原样展示 |

### 入口约定（避免各写各的）

- 首页四个入口：图生视频 → `navigateTo` `modules/video/pages/create/create`；相册 → 相册 tab；广场 → 广场 tab；签到 → `modules/points/pages/checkin/checkin`。禁止首页 import `points` service。带着 `?checkin=1` 进积分明细不会自动签到。
- 首页下方动态：`GET /api/v1/community/post?tab=recommend`。点「更多」切到广场 tab。
- 广场 tab：搜索走 query `q`；顶部分栏 `tab`（推荐 / 关注，下划线不是芯片）。「大家都在看」横滑封面进详情，数据来自 `tab=recommend` 且带图的帖。不在广场用话题芯片筛选。发动态不传 `board`。
- 小x tab：底栏中间进 `modules/assistant/pages/chat/chat`。广场不加助手入口。相近帖点进已有详情，不 import community service。
- 创作页打开即为图生视频表单，不是发动态，也不是 tab。发动态从广场 / 我的发布进入。
- 相册 tab：只列当前用户相册；右下或空态「上传」进 upload 页。
- 「我的」：头像昵称和四计数走 `GET /api/v1/me`。点头像/昵称进编辑资料页；点「动态 / 获赞」进我的发布；点「关注 / 粉丝」进对应列表。菜单分组：我的发布 / 我的收藏 / 我的相册（`switchTab` 相册 tab）/ 生成记录；我的关注 / 粉丝；积分明细 / 积分任务；设置。没有「每日签到」菜单（签到只从首页进）。编辑资料：头像只走 `chooseAvatar`（含微信头像 / 相册 / 相机）；昵称普通输入，1–16 字，不用 `type="nickname"`；点保存才 `POST /api/v1/media`（若换了头像）+ `PATCH /api/v1/me`。未保存返回有改动则确认。`page-shell` / `navigation-bar` 的 `catch-back` 默认关，仅本页开启。设置页无接口：关于写「宠物记录 / 开发版」；注销只提示「开发期不能注销」。关注 / 粉丝行不进作者页。

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

首页 / 广场 / 我的发布 / 我的收藏 / 详情页已开分享。`react-row` 图标：`assets/icon/react-like|reply|favorite|share.png` 与 `-active`（评论按钮文件名仍是 `reply`，界面文案是「评论」）。

### tabBar 图标

五个 tab 必须都有未选中 / 选中两套图标（`miniprogram/assets/tab/`，文件名锁死：`home` / `album` / `assistant` / `plaza` / `me` 各一套普通 + `-active`）。现为圆润色块，重出用 `scripts/export-brand-icons.py`。颜色写入 `app.json` 的 `tabBar`（选中色橙色）。第三个 tab 文案「小x」。

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
| mock 数据 | 不存在 | handlers 在各模块 `services/mock.ts`；种子在 `miniprogram/mocks/store.ts`；`core/mock.ts` 只注册。跨模块写走 community `mock-helpers` / points `mock-ledger` |

## 必须预留的 service（与接口一一对应）

每个模块建 `services/`，方法名可按习惯，但 **path、method、body/query 字段必须如下**。没有列出的接口不要先造。

| 模块文件 | 用户动作 | method + path |
|---|---|---|
| `auth`（可放 `core/auth` 内） | 启动登录 | `POST /api/v1/auth/login` |
| `modules/me/services/` | 当前用户 | `GET/PATCH /api/v1/me` |
| `modules/media/services/` | 上传图或评论语音 | `POST /api/v1/media` |
| `modules/album/services/` | 相册列表 / 详情 / 上传 / 改 / 删 | `GET/POST /api/v1/album`，`GET/PATCH/DELETE /api/v1/album/{id}` |
| `modules/community/services/` | 广场、发帖、详情、我的发布、收藏列表、点赞、收藏、评论、关注、粉丝 | `GET/POST /api/v1/community/post`，`GET /api/v1/community/post/mine`，`GET /api/v1/community/post/favorite`，`GET/PATCH/DELETE /api/v1/community/post/{id}`，`POST .../like`，`POST .../favorite`，`GET/POST .../comment`，`DELETE .../comment/{comment_id}`，`POST .../comment/{comment_id}/like`，`POST .../comment/{comment_id}/report`，`GET/POST/DELETE /api/v1/community/follow`，`GET /api/v1/community/follower` |
| `modules/video/services/` | 创建任务、列表、详情、删 | `GET/POST /api/v1/video`，`GET/DELETE /api/v1/video/{id}` |
| `modules/points/services/` | 汇总、流水、签到、补签 | `GET /api/v1/points/summary`，`GET /api/v1/points/ledger`，`POST /api/v1/points/checkin`，`POST /api/v1/points/makeup` |
| `modules/assistant/services/` | 推荐问题、提问 | `GET /api/v1/assistant/suggestion`，`POST /api/v1/assistant/ask` |

页面事件处理里只出现 `xxxService.list()` 这类调用。字段名用下划线：`image_urls`、`sync_to_forum`、`points_balance`，不要在页面层再映射一套驼峰再丢掉。

**例外：** `media` 没有自己的页面。相册 / 发帖 / 创作 / 编辑资料在选图后可以调用 `modules/media/services` 拿 `url`，再交给本模块 service。阶段 F 的 mock 可以直接把微信临时路径当作 `url`；当前 `uploadMedia` 仍通过 `core/request` 传递路径，切真 API 前必须在内核补 `multipart` 上传适配。其它跨模块仍然只许跳路由，不许互相 import service。

首页、我的若只展示其它模块的数据：首页帖预览走 **本模块** `community` service；积分 / 相册 / 收藏 / 关注入口只跳路由，不在 `me` 页面 import 其它模块 service。`GET /api/v1/me` 已带 `points_balance` 和四个计数，我的页展示用这些字段。

### 页面做完的自检

- [ ] 该页所有读写都经过本模块 `services/`
- [ ] service 的 path 与 [api/contract.md](api/contract.md) 逐字相同
- [ ] 请求/响应字段与合同里的资源 JSON 相同（`snake_case`、字符串 id）
- [ ] `useMock: true` 时能走通；切换 `false` 不需要改页面
- [ ] 没有 `wx.request`、没有页面内假数组、没有 `TODO 接接口`

## Mock 约定（界面先行必守）

1. `miniprogram/core/config.ts` 提供 `useMock: true`（先行默认）和 `apiBaseUrl`。
2. 页面 **不准** `wx.request`，不准写死主机名，不准直接 import 一份「页面专用假数据」。
3. 模块 `services/` 只调 `core/request`。`useMock === true` 时，`request` 把 method+path 交给 `core/mock.ts`（只注册 / 匹配）。handlers 在各模块 `services/mock.ts`，种子在 `miniprogram/mocks/store.ts`。跨模块写操作走对方公开函数（community `mock-helpers.ts`、points `mock-ledger.ts`），不要直接改另一模块的数组。返回值符合 [api/contract.md](api/contract.md)。
4. 成功 / 失败信封与真 API 相同，JSON 形状见 [api/contract.md](api/contract.md)。
5. 假数据足够点通主路径即可：当前用户、若干相册、若干已发布帖（含别人的帖和一条带评论的帖）、一条视频任务、几条积分流水。不要做后台。
6. 没有审核员：mock 里 `POST` 帖子若 `status` 为 `pending`，直接存成 `published`，否则广场列表看不到刚发的帖。接真 API 后再走审核。
7. mock 登录在 `core/auth` 启动时同步完成（`jwt-or-mock` + 写入当前用户 id），页面 `onShow` 时已有会话。

接真 API：`useMock` 改为 `false`，确认 `apiBaseUrl`。页面和 service **方法名**不用改；`core/request` 必须能走 `POST /api/v1/media` 的 multipart（`wx.uploadFile`，字段名 `file`），见 [progress.md](progress.md) 已知风险。

## 开发者工具（阶段 F）

打开仓库**根目录**（不是 `miniprogram/`）。`app.json` 已 `"renderer": "skyline"`，公共 `libVersion` 是 `3.7.0`。本机已点开，界面正常。

`project.private.config.json` 已 gitignore，会盖掉公共基础库。换机器或面板不是 Skyline 时：开发者工具「详情」改成 3.7.0，或改私有配置里的 `libVersion`。细则 [miniprogram/README.md](miniprogram/README.md)。

## 本地怎么对上（后端落地之后）

切片 A 已能在本机跑 Postgres 和 `GET /health`。小程序仍走 mock，不连这台 API。

1. Docker Compose 只跑 PostgreSQL（`pgvector/pgvector:pg16`，库 `app_pet` 与 `app_pet_test`）。
2. FastAPI：`http://127.0.0.1:8000`，`GET /health`。
3. 微信开发者工具打开本仓库根目录；开发期关闭「校验合法域名」。
4. 关 `useMock` 之后，`apiBaseUrl` 才指向 `http://127.0.0.1:8000`（真机预览改为电脑局域网 IP）。

`wx.request` 不是浏览器，没有 CORS。正式版要配微信公众平台 request / uploadFile 合法域名。

## 环境变量（后端）

样例在 `server/.env.example`。本地复制为 `server/.env`（gitignore，不提交）。

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
| `API_PREFIX` | 固定。Settings 声明，路由前缀在 `main.py` 写死 | `/api/v1` |
| `EMBEDDING_BASE_URL` | 嵌入服务根地址 | 空。C 起读取；三个嵌入项都空则走假向量 |
| `EMBEDDING_API_KEY` | 嵌入密钥 | 空，不进 git |
| `EMBEDDING_MODEL` | 嵌入模型名 | 空 |
| `EMBEDDING_DIM` | 向量维度 | `1024` |
| `EMBEDDING_MIN_COSINE` | 余弦下限 | `0.25` |
| 视频出片密钥 | 只放服务端 `.env` | 接 P2 真出片时再登记，不进小程序 |

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
2. [progress.md](progress.md)（阶段、下一步、已知风险）
3. [product/expansion.md](product/expansion.md)（助手 / 问诊 / 经验边界）
4. 本文件（模块名、tab / 页面路径、帖子互动、service、mock 布局）
5. [api/contract.md](api/contract.md)（path 和 JSON）
6. [miniprogram/README.md](miniprogram/README.md)
7. 写代码时再读 [framework/code-standards.md](framework/code-standards.md)
8. [product/benchmark.md](product/benchmark.md)（只做表里标「有」的）

改观感才打开 [miniprogram/visual.md](miniprogram/visual.md)。后端只做 [dev/backend-assistant-1a.md](dev/backend-assistant-1a.md) 的当前切片。改接口先改合同。不要每改一处就改文档。新模块 / 新页走 [framework/adding-a-module.md](framework/adding-a-module.md)。阶段 F 的小程序改动不要顺手建后端业务目录。

开发走 `/app-pet`。静态检查：`npm run typecheck`。页面改动请人在开发者工具点一下。已知延后项（media multipart、mock 单用户点赞、种子仍一份 store）见 [progress.md](progress.md)，不要当阶段 F 缺口去「顺便做掉」。
