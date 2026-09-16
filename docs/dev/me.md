# 「我的」丰富（一次性开发文档）

**用完即删。** 按切片开发；全部切片点验通过后删除本文件。不要登记进 `AGENTS.md` / `docs/README.md`。不要当长期规范。改接口只改 `docs/api/contract.md`。

阶段：F（mock，不接 FastAPI）。模块：`me`（首页、设置）+ `community`（收藏 / 关注 / 粉丝列表）。页面只调**本模块** `services/`。「我的」首页只调 `modules/me/services/`，其它入口只跳路由。

当前切片：**切片 6 — 设置页（1–6 已实现，等人点验）**

新对话：读本文件 → 只做当前切片 → 停住等用户点验。用户回复「切片 N 过了」才改「当前切片」并动手。不要一次做完，不要先搭 FastAPI，不要重做视觉。

---

## 怎么开发

一次只做「当前切片」。做完停住。用户回复「切片 N 过了」才把「当前切片」改成下一片并动手。没过先修这一片。

1. 只改该片「改哪些文件」列出的路径。该片「不做」里的一律留下一片。
2. Agent 验：跑 `npm run typecheck`（切片 0 无代码，跳过）；看 `git diff`；字段与 `docs/api/contract.md` 逐字一致。没跑过的不写已验证。
3. **代码切片（2–6）在交点验清单之前，必须开一个独立子 agent 做 code review**（只看该片 diff，不要把实现过程讲给它）。安全问题和逻辑错误先修再交点验。风格建议不阻塞，除非违反 `AGENTS.md`。不要为 review 去 commit。切片 0 / 1 无代码，跳过 review。
4. 把该片「点验清单」原样交给用户。用户用微信开发者工具打开 **仓库根目录** 点。切片 0 / 1 / 2 无人脸点页面，把清单当确认项。
5. 交接写：范围 / 已改 / 契约 / 验证 / 风险 / 下一步。下一步只能是「等切片 N 点验通过」或「修点验问题」。

模拟器 `navigateTo` 空一拍不当失败。真机不卡即可。不为修模拟器改代码。业务代码禁止 `?.` / `??`。

不要改 `docs/progress.md` / `docs/handoff.md`，除非用户说整理 / 总结 / 更新对接文档。

---

## 已定

「我的」是当前用户入口，不是宠物列表。本包在现有资料卡和三行菜单上加计数、分组菜单、四个新页。

| 点 | 决定 |
|---|---|
| 资料卡 | 头像、昵称、积分（已有）+ 四个整数：动态 / 获赞 / 关注 / 粉丝 |
| 点头像或昵称 | 仍进 `modules/me/pages/profile/profile` |
| 点「动态」或「获赞」 | 进已有 `modules/community/pages/mine/mine`（不新开获赞列表） |
| 点「关注」 | 进关注页 |
| 点「粉丝」 | 进粉丝页 |
| 我的相册 | `wx.switchTab` 到相册 tab（`/modules/album/pages/list/list`） |
| 每日签到 | 已有积分页 `/modules/points/pages/list/list?checkin=1` |
| 作者页 | 本包不做。关注 / 粉丝行不 `navigateTo` 任何作者页 |
| 计数来源 | 只在 `GET /api/v1/me` 和 `PATCH /api/v1/me` 的 `Me` 上。不另开统计接口 |

### 资料卡四个计数

字段名锁死（切片 1 进合同）：

| 字段 | 界面 | 算法 |
|---|---|---|
| `post_count` | 动态 | 当前用户 `status === "published"` 的帖数。草稿 / 审核中 / 未通过不计 |
| `like_received_count` | 获赞 | 上述已发布帖的 `like_count` 之和 |
| `following_count` | 关注 | 当前用户主动关注的人数 |
| `follower_count` | 粉丝 | 关注当前用户的人数 |

四个都是非负整数。mock 在 `GET` / `PATCH /me` 时现算，不把这四个数存进 `store.me`。关注、取关、删帖、点赞之后，再进「我的」应看到新数字。

### 菜单分组（切片 3 画出全部行）

四张已有 `.card.menu`，行样式沿用 `.menu-row` / `.menu-row--last`。不新造视觉体系，不写死 hex。

| 组 | 入口 | 去哪 | 哪片接跳转 |
|---|---|---|---|
| 内容 | 我的发布 | 已有 `community/pages/mine` | 3 |
| 内容 | 我的收藏 | 新页 `community/pages/favorites` | 4（切片 3 只画行，不 bindtap） |
| 内容 | 我的相册 | `wx.switchTab` 相册 tab | 3 |
| 社交 | 我的关注 | 新页 `community/pages/follow` | 5（切片 3 只画行） |
| 社交 | 粉丝 | 新页 `community/pages/follower` | 5（切片 3 只画行） |
| 积分 | 积分明细 | 已有 `points/pages/list` | 3 |
| 积分 | 每日签到 | 已有积分页 `?checkin=1` | 3 |
| 积分 | 任务管理 | 已有 `video/pages/tasks` | 3 |
| 其它 | 设置 | 新页 `me/pages/settings` | 6（切片 3 只画行） |

整卡不要再套一层 `bindtap="onProfile"`。头像 + 昵称区域点进编辑；四个数字各自 `catchtap`，避免点数字误进编辑。

### 新页面归属

| 页 | 路径 | 调谁 |
|---|---|---|
| 我的收藏 | `miniprogram/modules/community/pages/favorites/` | `community` service |
| 我的关注 | `miniprogram/modules/community/pages/follow/` | `community` service |
| 粉丝 | `miniprogram/modules/community/pages/follower/` | `community` service |
| 设置 | `miniprogram/modules/me/pages/settings/` | 无网络；不新开接口 |

`app.json` 的 `pages` **只追加**，五个 tab 路径不动。追加发生在建该页的那一片，不要提前登记。

### 新接口（切片 1 进合同，切片 2 进 mock / service）

已有、不改：`POST /api/v1/community/post/{id}/favorite`、`POST /api/v1/community/follow`、`DELETE /api/v1/community/follow/{user_id}`。已关注再关注仍是 `CONFLICT`。关注自己仍是 `VALIDATION`（mock 已做，切片 1 写进合同）。

新增：

1. `GET /api/v1/community/post/favorite?page=1&page_size=20`  
   当前用户已收藏的帖。响应与帖子列表相同：`{ "data": { "items": [Post], "total", "page", "page_size" } }`。排序 `created_at` 新的在前。实现必须把本 path 注册在 `GET /post/{id}` **前面**，避免 `favorite` 被当成 id。
2. `GET /api/v1/community/follow?page=1&page_size=20`  
   我关注的人。`items` 的元素是现有 **Author**（`id` `nickname` `avatar_url`），不要加 `followed` 字段。
3. `GET /api/v1/community/follower?page=1&page_size=20`  
   关注我的人。`items` 同样是 Author。

粉丝页要区分「回关 / 取消关注」时：同一屏再调 `GET /follow`，用 id 集合在前端判断。不要为此改 Author。

### 种子（切片 2，为点验服务）

在 `miniprogram/mocks/store.ts`：

- 现有 `OTHER_USER_ID` / `邻家铲屎官` 保留。
- 新增 `THIRD_USER_ID = "30303030-3030-3030-3030-303030303030"`，昵称 `街角的猫`（自拟，不抄对标文案），头像用已有 `brandAssets.avatarDefault`。该用户可以没有帖。
- `store.follows = [OTHER_USER_ID]`（我关注邻家铲屎官）。
- `store.followers = [OTHER_USER_ID, THIRD_USER_ID]`（邻家铲屎官互关；街角的猫只粉我不回关）。
- 帖 `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbe`（今天的窗边光）设 `favorited: true`（`favorite_count` 至少 1，不要改成 0）。
- 解析 Author：用 `store.me` + 邻家 + 街角。不要为找人去扫全部帖。

由此 `GET /me` 应为：`post_count` 1（自己那条已发布；草稿不计）、`like_received_count` 2、`following_count` 1、`follower_count` 2。改种子导致对不上点验清单时，改种子算法说明，不要改字段名。

---

## 切片 0 — 本文档

**做完标准：** 用户确认切片清单，说「切片 0 过了」。

改哪些文件：`docs/dev/me.md`（本文件）。

做：锁规则、切片、点验、不做项。代码切片交点验前必须子 agent review（见「怎么开发」第 3 条）。

不做：合同、benchmark、代码、`AGENTS.md`、`docs/README.md`、`progress.md`、`handoff.md`。

点验清单：

1. 本文件在 `docs/dev/`，没有写进 `AGENTS.md` / `docs/README.md`。
2. 切片顺序是 0→6，当前切片是 0。
3. 四个计数的字段名是 `post_count` `like_received_count` `following_count` `follower_count`。
4. 本包不做消息中心、宠物档案、商城、作者页。
5. 代码切片（2–6）交点验前要开子 agent review。

Agent 验：无代码，不跑 `typecheck`，不开 review。

---

## 切片 1 — 合同 + benchmark

**做完标准：** 合同已含四个计数和三条 GET；benchmark「我的」行已补；`capabilities.md` 的 P0「我的」那一行已按 benchmark 文内规则改完。用户说「切片 1 过了」。

先改合同，再改代码。本片还没有代码。禁止先改页面再补字段。

改哪些文件：`docs/api/contract.md`、`docs/product/benchmark.md`、`docs/product/capabilities.md`。

### 1a `docs/api/contract.md`

`Me` 示例 JSON 在 `points_balance` 后追加四个整数（示例值与种子一致）：

```json
{
  "id": "10101010-1010-1010-1010-101010101010",
  "nickname": "用户",
  "avatar_url": "https://example.com/a.jpg",
  "points_balance": 180,
  "post_count": 1,
  "like_received_count": 2,
  "following_count": 1,
  "follower_count": 2
}
```

`Me` 段落后追加（不要改 `PATCH` 请求仍只允许 `nickname` `avatar_url`）：

- 四个计数均为非负整数。`GET /api/v1/me` 与 `PATCH /api/v1/me` 的响应都带。不另开统计接口。
- `post_count`：当前用户 `status` 为 `published` 的帖数。
- `like_received_count`：这些已发布帖的 `like_count` 之和。
- `following_count` / `follower_count`：关注数 / 粉丝数。

`community` 接口清单：

- 在 `GET /api/v1/community/post/mine` 那段旁边（或 `GET /post/{id}` 之前）加 `GET /api/v1/community/post/favorite?page=1&page_size=20`，写明响应形状同帖子列表、只返回当前用户已收藏的帖、实现须把 `/post/favorite` 注册在 `/post/{id}` 前面。
- 在已有 `POST /follow`、`DELETE /follow/{user_id}` 旁加两条 GET；写明 `items` 为 Author。把「不能关注自己 → `VALIDATION`」写进 `POST /follow`（现在合同没写，mock 已经是这个行为）。

### 1b `docs/product/benchmark.md`

第 13 行「我的」的「我们」列改为包含：资料卡四计数（动态 / 获赞 / 关注 / 粉丝）、我的收藏、我的关注、粉丝、设置。不要写对标品牌名。

按该文件开头「改本表时同步 capabilities.md」：`docs/product/capabilities.md` P0 表「我的」那行「要做到」改为：入口：我的发布、收藏、相册、关注、粉丝、积分明细、签到、任务管理、设置；资料卡展示动态 / 获赞 / 关注 / 粉丝。P1「关注」行保持详情关注 + 广场关注流，不要删。

不做：`handoff.md`、`progress.md`、任何 `miniprogram/`、FastAPI、新模块名。

点验清单：

1. 打开合同，`Me` 能看到四个计数；`PATCH` 请求字段仍只有昵称和头像。
2. 能搜到 `GET /api/v1/community/post/favorite`、`GET /api/v1/community/follow`、`GET /api/v1/community/follower`。
3. benchmark 第 13 行提到收藏 / 关注 / 粉丝 / 设置。
4. 合同里没有 `GET /me/stats`，没有作者页 path，没有注销 API。

Agent 验：`rg` 四个字段名和三条 path；`PATCH /api/v1/me` 请求仍是 nickname / avatar_url。无代码，不开 review。

---

## 切片 2 — mock + types + service

**做完标准：** `npm run typecheck` 通过；种子能撑后面点验；子 agent review 的安全/逻辑问题已修。用户说「切片 2 过了」。本片不改页面。

改哪些文件：

- `miniprogram/modules/me/types/me.ts`（`Me` 加四个 number）
- `miniprogram/modules/me/services/mock.ts`（`presentMe`：copy `store.me` 再算四个计数）
- `miniprogram/modules/community/services/community.ts`（加 `listFavoritePosts` / `listFollows` / `listFollowers`，只包 `request`，path 与合同逐字相同）
- `miniprogram/modules/community/services/mock.ts`（三条 GET；`GET /post/favorite` 放在 `GET /post/{id}` 之前）
- `miniprogram/mocks/store.ts`（第三用户、`follows`、`followers`、一条 `favorited: true`）
- 若解析 Author 需要，可在 `community/services/mock-helpers.ts` 加小函数；不要改 `core/mock.ts` 逻辑（已 spread community routes，新 handler 进 community `mock.ts` 即可）

`me/services/me.ts` 的 `getMe` / `patchMe` 不必改 path。`Me` 类型变了会自动带上字段。

做：

- `GET /me` 四个计数按「已定」现算。
- `GET .../post/favorite`：`store.posts` 里 `favorited === true`，`sortByCreated` + `paginate` + `presentPost`。
- `GET .../follow`：按 `store.follows` 倒序（后关注的在前）映射 Author；未知 id 跳过。
- `GET .../follower`：按 `store.followers` 倒序映射 Author。
- 关注 / 取关只改 `store.follows`，不要改 `store.followers`（单用户 mock：别人的粉丝列表不维护）。

不做：页面、`app.json`、合同（已在切片 1）、视觉。

点验清单（本片不进开发者工具点页面）：

1. Agent 说 `npm run typecheck` 通过。
2. 种子：关注 1、粉丝 2、收藏 1 条、自己已发布帖 1、获赞 2。
3. `GET /post/favorite` 的 mock 写在 `GET /post/{id}` 前面。

Agent 验：`npm run typecheck`；读 `git diff`：`Me` 类型四字段；三条 path 字符串与合同一致；没有页面文件。然后开子 agent review 该片 diff，修安全/逻辑问题。

---

## 切片 3 — 「我的」首页改版

**做完标准：** 点验清单 7 条用户都点过，且 `npm run typecheck` 通过；子 agent review 的安全/逻辑问题已修。用户说「切片 3 过了」。

改哪些文件：`miniprogram/modules/me/pages/index/`（`index.ts` / `index.wxml` / `index.scss` / `index.json` 按需）。只调 `getMe()`。

做：

- 资料卡：头像昵称积分 + `.stat-bar` 四个数字（token 已在 `styles/primitives.scss`，不要复制一套）。
- 点头像/昵称进编辑；点动态/获赞进我的发布；点关注/粉丝本片不跳（行还没接）。
- 四组菜单都画出来。已有跳转：发布、相册 `switchTab`、积分、签到 `?checkin=1`、任务。
- 收藏 / 关注 / 粉丝 / 设置：**有行、无 bindtap**。点了人还在「我的」。

不做：新页面、`app.json`、合同、改编辑资料页、改 tab 路径、重做视觉、import `community` / `points` / `album` service。

点验清单：

1. 「我的」资料卡能看到动态 1、获赞 2、关注 1、粉丝 2，以及积分。
2. 点头像或昵称进编辑资料；返回后数字还在。
3. 点「动态」或「获赞」进我的发布。
4. 点「我的相册」切到相册 tab（不是 navigateTo 上传页）。
5. 点「每日签到」进积分明细，能看到签到提示（已签或刚签）。
6. 我的发布 / 积分明细 / 任务管理仍能进。
7. 点「我的收藏」「我的关注」「粉丝」「设置」，人还在「我的」，没有新页。

Agent 验：`npm run typecheck`；`index.ts` 没有 `wx.request`，没有 import 其它模块 service。然后开子 agent review。

---

## 切片 4 — 我的收藏页

**做完标准：** 点验清单 5 条用户都点过，且 `npm run typecheck` 通过；子 agent review 的安全/逻辑问题已修。用户说「切片 4 过了」。

改哪些文件：新建 `miniprogram/modules/community/pages/favorites/`（`favorites.ts` / `favorites.wxml` / `favorites.scss` / `favorites.json`）。`app.json` 的 `pages` **只追加** `modules/community/pages/favorites/favorites`。「我的」首页给「我的收藏」加上 bindtap。

做：

- `listFavoritePosts()`。卡片复用 `post-card` + `toPostCard`，写法抄 `community/pages/mine`（点卡进详情，可取消收藏）。
- 空态用现有 `empty-state`：title「还没有收藏」，不要 action 按钮。
- 取消收藏后 `onShow` / 回调里该卡从本列表消失。
- `page-shell` 标题「我的收藏」，`back="{{true}}"`。纵向 `scroll-view type="list"`。

不做：作者页、合同、关注页、设置、改 `post-card` 组件本身。

点验清单：

1. 「我的」点「我的收藏」进新页，能看到「今天的窗边光」。
2. 点卡进详情；返回列表还在。
3. 在收藏页取消收藏，该卡消失，出现「还没有收藏」。
4. 去广场再收藏一条，回到收藏页能看到。
5. `app.json` 只追加了收藏页，五个 tab 路径没动。

Agent 验：`npm run typecheck`；页面只调 community service；path 是 `/api/v1/community/post/favorite`。然后开子 agent review。

---

## 切片 5 — 我的关注 + 粉丝页

**做完标准：** 点验清单 6 条用户都点过，且 `npm run typecheck` 通过；子 agent review 的安全/逻辑问题已修。用户说「切片 5 过了」。

改哪些文件：新建 `miniprogram/modules/community/pages/follow/`、`.../follower/`（各 ts/wxml/scss/json）。`app.json` **只追加**这两页。「我的」首页给「我的关注」「粉丝」加上 bindtap。资料卡「关注」「粉丝」数字也跳到对应页。

做：

- 关注页：`listFollows()`。行：头像、昵称、按钮「取消关注」。点按钮 `unfollowUser`。空态 title「还没有关注」，无 action。点行（非按钮）不跳转。
- 粉丝页：`listFollowers()` + `listFollows()` 做 id 集合。未关注显示「回关」（`followUser`）；已关注显示「取消关注」。空态 title「还没有粉丝」，无 action。点行不跳转。
- `page-shell` 标题「我的关注」/「粉丝」，`back="{{true}}"`。`scroll-view type="list"`。头像用已有 `.avatar`。
- 取关后回到「我的」，`onShow` 拉 `getMe()`，关注数减 1。回关后关注数加 1。

不做：作者页、消息、黑名单、合同、设置页。

点验清单：

1. 「我的」点「关注」数字或菜单「我的关注」：列表有「邻家铲屎官」，能取消关注；取消后空态「还没有关注」；返回「我的」关注数为 0。
2. 「我的」点「粉丝」：两行，「邻家铲屎官」和「街角的猫」。
3. 「街角的猫」按钮是「回关」；点了变成「取消关注」，返回「我的」关注数为 1。
4. 「邻家铲屎官」在粉丝页是「取消关注」（互关）。
5. 点头像或昵称不进任何新页。
6. `app.json` 只追加了这两页，tab 路径没动。

Agent 验：`npm run typecheck`；无作者页 path；列表 item 类型是 `Author`。然后开子 agent review。

---

## 切片 6 — 设置页

**做完标准：** 点验清单 4 条用户都点过，且 `npm run typecheck` 通过；子 agent review 的安全/逻辑问题已修。用户说「切片 6 过了」。

改哪些文件：新建 `miniprogram/modules/me/pages/settings/`。`app.json` **只追加** `modules/me/pages/settings/settings`。「我的」首页给「设置」加上 bindtap。

做：

- `page-shell` 标题「设置」，`back="{{true}}"`。
- 关于：工作标题「宠物记录」；版本文案写「开发版」（不要编 `1.0.0`，不要调不存在的接口）。
- 注销账号：`wx.showModal` 确认后 `wx.showToast`「开发期不能注销」。不调任何 API，不清 token，不回登录页。

不做：改密码、绑定手机、消息中心、真删号、隐私协议页、合同、FastAPI、handoff/progress（等用户说整理）。

点验清单：

1. 「我的」点「设置」进新页，看得到「宠物记录」和「开发版」。
2. 点注销 → 取消，人还在设置页。
3. 点注销 → 确认，提示「开发期不能注销」，人还在设置页，再回「我的」资料还在。
4. `app.json` 只追加了设置页，tab 路径没动。

Agent 验：`npm run typecheck`；settings 页没有 `wx.request`、没有新 path。然后开子 agent review。

---

## 本文件不做

- FastAPI、关 `useMock`、真上传 multipart
- 改五个 tab 路径、重做全站视觉、页面写死 hex
- 消息中心、宠物档案、商城、会员、客服 IM、积分兑换
- 作者主页、「他的相册」、黑名单 UI
- 注销真接口、改密码、绑定手机
- `GET /me/stats`、给 Author 加字段、新模块目录名
- 把业务写进 `pages/index`、`pages/logs`、`app.ts` / `globalData`
- 登记本文件到 `AGENTS.md` / `docs/README.md`

作者页、互关过滤别人的相册、黑名单：另开文档。

---

## 代码边界

- 计数和设置在 `miniprogram/modules/me/`。收藏 / 关注 / 粉丝页和对应 GET 在 `miniprogram/modules/community/`。
- 「我的」首页禁止 import `community` / `points` / `album` / `video` 的 service。
- `app.json`、合同由做那一片的主对话改。两个 agent 不写同一文件。
- 切片 0 只写本文件。切片 1 先改合同再改 types/mock。切片 2 起才动 `miniprogram/`。
- 切片 2–6 交点验前必须子 agent review；不要为 review 去 commit。
