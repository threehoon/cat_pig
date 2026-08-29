# API 合同（前后端唯一依据）

前端 mock、小程序 `services/`、以后 FastAPI 的 router/schema **只准实现这份文件里的路径和字段**。

对不上时改的是实现，不是各写一套。要加字段：先改本文件（只加可选字段或新路径），再改 mock，再改后端。禁止静默改名（`userId` / `user_id` 混用）。

页面怎么拆、tab、mock 开关见 [handoff.md](../handoff.md)。本文件不管 UI。

本文件对应产品：**宠物内容小程序**（相册 / 广场 / 图生视频 / 积分）。旧的 `pet` `journal` `ledger` `reminder` 路径作废，不要再实现。

## 总规则

| 项 | 规定 |
|---|---|
| 前缀 | `/api/v1/<module>`，module 只能是 `auth` `me` `media` `album` `community` `video` `points` |
| 字段 | 全部 `snake_case`。前端 types 也用下划线，不要在页面再转驼峰当传输层 |
| id | 字符串（uuid）。不要用数字 id |
| 日期 | `YYYY-MM-DD` |
| 时间 | ISO-8601 UTC，带 `Z`，例如 `2026-08-24T10:00:00Z` |
| 积分 | JSON integer，非负整数。不要用字符串、不要用「元」 |
| 空值 | 没有的可选字段用 `null`，不要省略导致前后端各猜一套 |
| 鉴权 | 除 `POST /api/v1/auth/login` 和 `GET /health` 外，Header：`Authorization: Bearer <token>` |
| 列表 | 一律 `{ "data": { "items": [], "total": 0, "page": 1, "page_size": 20 } }` |

成功：`{ "data": ... }`  
失败：`{ "error": { "code": "NOT_FOUND", "message": "..." } }`

稳定 `code`：`UNAUTHORIZED` `FORBIDDEN` `NOT_FOUND` `VALIDATION` `CONFLICT` `WECHAT_LOGIN_FAILED` `POINTS_NOT_ENOUGH` `INTERNAL`。

排序（列表未另指定时）：

- Album / Post / Video / Points ledger：`created_at` 新的在前

其它限制：

- 图片数组最多 **9** 张
- 相册 `image_urls` 至少 1 张
- 图生视频 `image_urls` **2–9** 张
- 帖子正文最多 500 字；标题可空字符串
- 签到：同一自然日（用户本地时区）只能成功一次，重复调用返回已签到，不重复加分
- 发帖默认 `status` 为 `pending`（待审核）；存草稿为 `draft`
- `DELETE` 只删当前用户自己的资源，否则 `FORBIDDEN`。例外：帖子作者可删该帖下任意一条评论（一次一条，不连带删别人的）。删帖时该帖全部评论一并删除。

`GET /health` → `{ "data": { "ok": true } }`。

---

## 资源形状（所有读写共用）

### Me

```json
{
  "id": "10101010-1010-1010-1010-101010101010",
  "nickname": "用户",
  "avatar_url": "https://example.com/a.jpg",
  "points_balance": 180
}
```

`nickname`、`avatar_url` 可 `null`（未设时）。`points_balance` 始终是整数。

### Media

```json
{
  "url": "https://example.com/up.jpg",
  "width": 800,
  "height": 600,
  "mime": "image/jpeg"
}
```

### Album

```json
{
  "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "title": "周末出门",
  "body": "去公园晒太阳",
  "image_urls": ["https://example.com/1.jpg"],
  "cover_url": "https://example.com/1.jpg",
  "tag_names": ["生活"],
  "sync_to_forum": false,
  "created_at": "2026-08-24T10:00:00Z"
}
```

`title`、`body` 必填非空。`cover_url` 默认等于 `image_urls[0]`。`tag_names` 始终是数组（可 `[]`）。预设标签：`写真` `美食` `生活` `温馨` `风景`，允许请求里带新字符串。`sync_to_forum` 为 true 时，后端在创建相册成功后 **另外** 调 community 发一条 `show` 帖（带同样的图和文）；失败不回滚相册，相册仍 `sync_to_forum: true`。

### Author（嵌在帖子里，不是独立资源）

```json
{
  "id": "10101010-1010-1010-1010-101010101010",
  "nickname": "用户",
  "avatar_url": "https://example.com/a.jpg"
}
```

### Post

```json
{
  "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  "author": {
    "id": "10101010-1010-1010-1010-101010101010",
    "nickname": "用户",
    "avatar_url": "https://example.com/a.jpg"
  },
  "board": "qa",
  "title": "给两只小狗起个标题",
  "body": "在草坪上跑。",
  "image_urls": ["https://example.com/1.jpg"],
  "topic_names": ["日常"],
  "status": "published",
  "followed": false,
  "like_count": 0,
  "comment_count": 0,
  "favorite_count": 0,
  "liked": false,
  "favorited": false,
  "created_at": "2026-08-24T10:00:00Z"
}
```

`board`：`qa` \| `show` \| `share` \| `help` \| `daily` \| `experience`。  
`status`：`draft` \| `pending` \| `published` \| `rejected`。  
`liked` / `favorited`：当前用户是否已点赞 / 已收藏，布尔。点赞和收藏互相独立。  
`like_count` / `comment_count` / `favorite_count`：非负整数。  
`title` 可空字符串。`body` 可空字符串，但与 `image_urls` 不能同时空。`topic_names` 始终是数组。预设话题：`可爱瞬间` `日常` `生日` `旅行` `活动`，允许新字符串。

广场 tab 查询值 `tab`：`recommend` \| `following` \| 与 `board` 相同的六个值。

### Comment（嵌在帖子下，不是独立模块）

```json
{
  "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  "author": {
    "id": "10101010-1010-1010-1010-101010101010",
    "nickname": "用户",
    "avatar_url": "https://example.com/a.jpg"
  },
  "body": "也想试试。",
  "parent_id": null,
  "reply_to": null,
  "sticker_ids": ["blush"],
  "image_urls": [],
  "audio_url": null,
  "audio_duration": 0,
  "like_count": 0,
  "liked": false,
  "created_at": "2026-08-24T11:00:00Z"
}
```

`body` 可空字符串，最多 200 字。`sticker_ids` 始终是数组，最多 8 个；取值只能是 `blush` `happy` `cry` `paw` `heart` `sleep` `wow` `kiss`。`image_urls` 始终是数组，最多 9 张。`audio_url` 无语音时为 `null`。`audio_duration` 为整数秒，无语音时为 `0`，有语音时 1–60。`body`、`sticker_ids`、`image_urls`、`audio_url` 不能同时空。`liked` / `like_count`：当前用户是否已点赞及点赞数，再点取消，规则同帖子点赞。艾特写进 `body` 文本（`@昵称 `）。  

`parent_id` 为所评论的**顶层**评论 id，直接评帖为 `null`。`reply_to` 为被评论的人（Author），直接评帖为 `null`。列表按 `created_at` **旧的在前**（对话顺序），含子评论，扁平返回。  

谁可删评论：评论作者只能删自己的；帖子作者（贴主）可删该帖下任意一条。删一条只删这一条，子评论改挂到被删条的 `parent_id`。删帖时该帖全部评论一并删除，并回写 `comment_count`。不能举报自己的评论。

### Video

```json
{
  "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
  "title": "周末成长视频",
  "image_urls": ["https://example.com/1.jpg", "https://example.com/2.jpg"],
  "prompt": "草地上跑",
  "resolution": "720p",
  "status": "pending",
  "result_url": null,
  "points_cost": 50,
  "error_message": null,
  "created_at": "2026-08-24T10:00:00Z"
}
```

`resolution`：`540p` \| `720p` \| `1080p` \| `2k` \| `4k`。  
`status`：`pending` \| `running` \| `success` \| `failed`。  
`prompt` 最多 100 字，可空字符串。`title` 可空，服务端可用日期占位。`points_cost` 创建时固定 **50**。余额不足：`POINTS_NOT_ENOUGH`。`result_url` 仅 `success` 时非 null。

### PointsSummary

```json
{
  "earned": 180,
  "spent": 0,
  "balance": 180
}
```

### PointsEntry

```json
{
  "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
  "kind": "earn",
  "amount": 20,
  "title": "发布帖子",
  "balance_after": 180,
  "created_at": "2026-08-24T10:00:00Z"
}
```

`kind`：`earn` \| `spend`。`amount` 正整数。

积分发放（接真 API 后由对应模块调 `points` service，合同里不另开发放接口）：

| 事件 | kind | amount | title |
|---|---|---|---|
| 注册 | earn | 100 | 注册 |
| 每日签到 | earn | 10 | 签到 |
| 帖子变为 published | earn | 20 | 发布帖子 |
| 创建视频任务 | spend | 50 | 图生视频 |

---

## 接口清单

未列的 path 前后端都不要实现。`{id}` 为资源 id 字符串。

### auth

`POST /api/v1/auth/login`  
请求：`{ "code": "wx_login_code" }`  
响应：`{ "data": { "token": "jwt-or-mock", "expires_in": 604800 } }`  
不带 Authorization。首次登录由后端写入「注册」积分。

### me

`GET /api/v1/me` → `{ "data": Me }`

`PATCH /api/v1/me`  
请求：`{ "nickname", "avatar_url" }`（均可 null）  
响应：`{ "data": Me }`

### media

`POST /api/v1/media` multipart 文件字段名：`file`  
响应：`{ "data": Media }`  
mock：可直接返回占位 `url`（微信临时路径也可当字符串）。

### album

`GET /api/v1/album?page=1&page_size=20`  
响应：`{ "data": { "items": [Album], "total", "page", "page_size" } }`  
只返回当前用户自己的相册。

`POST /api/v1/album`  
请求：`{ "title", "body", "image_urls", "cover_url", "tag_names", "sync_to_forum" }`  
`cover_url` 可省略（用首图）。响应：`{ "data": Album }`

`GET /api/v1/album/{id}` → `{ "data": Album }`  
`PATCH /api/v1/album/{id}` 子集 → `{ "data": Album }`  
`DELETE /api/v1/album/{id}` → `{ "data": { "ok": true } }`

### community

`GET /api/v1/community/post?tab=recommend&q=&page=1&page_size=20`  
`tab` 默认 `recommend`。`q` 可省略（搜标题和正文）。  
`tab=following` 为已关注作者的已发布帖。  
响应：`{ "data": { "items": [Post], "total", "page", "page_size" } }`  
列表不包含 `draft` / `pending` / `rejected`（除非走 `/post/mine`）。

`GET /api/v1/community/post/mine?status=&page=1&page_size=20`  
`status` 可省略（全部）或为 `draft` \| `pending` \| `published` \| `rejected`。  
实现时必须把 `/post/mine` 注册在 `/post/{id}` **前面**，避免 `mine` 被当成 id。

`POST /api/v1/community/post`  
请求：`{ "board", "title", "body", "image_urls", "topic_names", "status" }`  
`status` 只允许 `draft` 或 `pending`。响应：`{ "data": Post }`

`GET /api/v1/community/post/{id}` → `{ "data": Post }`  
`PATCH /api/v1/community/post/{id}` 子集（含把 `draft` 改为 `pending`）→ `{ "data": Post }`  
`DELETE /api/v1/community/post/{id}` → `{ "data": { "ok": true } }`

`POST /api/v1/community/post/{id}/like`  
请求体空对象 `{}`。再点取消。响应：`{ "data": Post }`

`POST /api/v1/community/post/{id}/favorite`  
请求体空对象 `{}`。再点取消。响应：`{ "data": Post }`

`GET /api/v1/community/post/{id}/comment?page=1&page_size=20`  
响应：`{ "data": { "items": [Comment], "total", "page", "page_size" } }`

`POST /api/v1/community/post/{id}/comment`  
请求：`{ "body", "parent_id", "sticker_ids", "image_urls", "audio_url", "audio_duration" }`。`parent_id` 可 `null` 或省略（直接评帖）。`sticker_ids` / `image_urls` 可省略（当作 `[]`）。`audio_url` 可 `null` 或省略；有语音时 `audio_duration` 为 1–60。若指向一条子评论，服务端记到该线程的顶层 `parent_id`，`reply_to` 为被点的那条作者。响应：`{ "data": Comment }`

`DELETE /api/v1/community/post/{id}/comment/{comment_id}`  
评论作者只能删自己的；贴主可删该帖下任意一条。不连带删除别人的评论。响应：`{ "data": { "ok": true, "comment_count": 0 } }`  
非作者且非贴主：`FORBIDDEN`。

`POST /api/v1/community/post/{id}/comment/{comment_id}/like`  
请求体空对象 `{}`。再点取消。响应：`{ "data": Comment }`

`POST /api/v1/community/post/{id}/comment/{comment_id}/report`  
请求：`{ "reason": "spam" | "abuse" | "porn" | "other" }`。不能举报自己的评论：`FORBIDDEN`。响应：`{ "data": { "ok": true } }`

`POST /api/v1/community/follow`  
请求：`{ "user_id": "..." }` → `{ "data": { "ok": true } }`  
已关注再调：`CONFLICT`

`DELETE /api/v1/community/follow/{user_id}` → `{ "data": { "ok": true } }`

### video

`GET /api/v1/video?status=&page=1&page_size=20`  
`status` 可省略。只返回当前用户的任务。  
响应：`{ "data": { "items": [Video], "total", "page", "page_size" } }`

`POST /api/v1/video`  
请求：`{ "title", "image_urls", "prompt", "resolution" }`  
响应：`{ "data": Video }`（`status` 为 `pending`，已扣 50 分）

`GET /api/v1/video/{id}` → `{ "data": Video }`  
`DELETE /api/v1/video/{id}` → `{ "data": { "ok": true } }`  
已在 `running` 时删除：`CONFLICT`

### points

`GET /api/v1/points/summary` → `{ "data": PointsSummary }`

`GET /api/v1/points/ledger?kind=&range=all&page=1&page_size=20`  
`kind` 可省略或 `earn` \| `spend`。  
`range`：`all` \| `month` \| `quarter`（当前自然月 / 近三个自然月，用户本地时区）。

`POST /api/v1/points/checkin`  
请求体空对象 `{}`。  
响应：`{ "data": { "awarded": 10, "balance": 190, "already_done": false, "date": "2026-08-24" } }`  
当日已签：`awarded` 为 0，`already_done` 为 true，不报错。

---

## 谁必须遵守

| 角色 | 必须 |
|---|---|
| 前端 mock | `core/request` 按 method+path 返回上面的 JSON |
| 小程序 services | path 字符串与本文件逐字相同 |
| FastAPI | 同 path、同字段、同类型；Pydantic 模型与本文件一致 |
| 改接口 | 先改本文件，再改两端；已有字段不改名、不改类型、不改成必填 |

后端实现完成后，以本文件为准对照 OpenAPI；若生成结果与本文件冲突，改代码，不要另起前端字段。
