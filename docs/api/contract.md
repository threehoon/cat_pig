# API 合同（前后端唯一依据）

前端 mock、小程序 `services/`、以后 FastAPI 的 router/schema **只准实现这份文件里的路径和字段**。

对不上时改的是实现，不是各写一套。要加字段：先改本文件（只加可选字段或新路径），再改 mock，再改后端。禁止静默改名（`userId` / `user_id` 混用）。

页面怎么拆、tab、mock 开关见 [handoff.md](../handoff.md)。本文件不管 UI。

本文件对应产品：**宠物内容小程序**（相册 / 广场 / 图生视频 / 积分）。旧的 `pet` `journal` `ledger` `reminder` 路径作废，不要再实现。

## 总规则

| 项 | 规定 |
|---|---|
| 前缀 | `/api/v1/<module>`，module 只能是 `auth` `me` `media` `album` `community` `video` `points` `assistant` |
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
- 发帖变为 `published`：同一自然日最多给 **3** 条积分，超出不再加分、不报错
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
  "points_balance": 180,
  "post_count": 1,
  "like_received_count": 2,
  "following_count": 1,
  "follower_count": 2
}
```

`nickname`、`avatar_url` 可 `null`（未设时）。`points_balance` 始终是整数。用户保存时 `nickname` 去空白后须 1–16 字，空或超长返回 `VALIDATION`；未设仍允许 `null`。四个计数均为非负整数。`GET /api/v1/me` 与 `PATCH /api/v1/me` 的响应都带。不另开统计接口。`post_count`：当前用户 `status` 为 `published` 的帖数。`like_received_count`：这些已发布帖的 `like_count` 之和。`following_count` / `follower_count`：关注数 / 粉丝数。

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
  "visibility": "private",
  "sync_to_forum": false,
  "created_at": "2026-08-24T10:00:00Z"
}
```

`title`、`body` 必填非空。`cover_url` 默认等于 `image_urls[0]`。`tag_names` 始终是数组（可 `[]`）。预设标签：`写真` `美食` `生活` `温馨` `风景`，允许请求里带新字符串。`visibility` 为 `"public"` / `"private"` / `"friends"`；请求可省略，省略视为 `"private"`。仅 `visibility === "public"` 允许 `sync_to_forum: true`，其它值带 true 返回 `VALIDATION`。已是公开且 `sync_to_forum: true` 的相册，`PATCH` 把 `visibility` 改成非公开返回 `VALIDATION`。`sync_to_forum` 为 true 时，后端在创建相册成功后 **另外** 调 community 发一条 `show` 帖（带同样的图和文）；失败不回滚相册，相册仍 `sync_to_forum: true`。

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

`board`：`qa` \| `show` \| `share` \| `help` \| `daily` \| `experience`。响应里始终有。发帖请求可省略，省略视为 `daily`。相册同步论坛仍发 `show`。界面不用板块当房间。  
`status`：`draft` \| `pending` \| `published` \| `rejected`。  
`liked` / `favorited`：当前用户是否已点赞 / 已收藏，布尔。点赞和收藏互相独立。  
`like_count` / `comment_count` / `favorite_count`：非负整数。  
`title` 可空字符串。`body` 可空字符串，但与 `image_urls` 不能同时空。`topic_names` 始终是数组。预设话题：`可爱瞬间` `日常` `生日` `旅行` `活动`，允许新字符串。

广场 tab 查询值 `tab`：主路径 `recommend` \| `following`。仍接受与 `board` 相同的六个值（兼容）。`topic` 可省略；有则只返回 `topic_names` 含该字符串的帖。

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
  "balance": 180,
  "streak": 2,
  "makeup_card_count": 0,
  "today_checked": false,
  "makeup_dates": ["2026-08-23"],
  "checkin_dates": ["2026-08-23"],
  "today_post_count": 0,
  "today_comment_count": 0,
  "today_like_count": 0
}
```

`earned` `spent` `balance` 仍是非负整数。追加字段：`streak`（当前连续签到天数，非负整数）、`makeup_card_count`（补签卡张数，非负整数）、`today_checked`（今天是否已签，boolean）、`makeup_dates`（可补签的本地自然日 `YYYY-MM-DD` 数组，新的日期在前；没有可补时为 `[]`）、`checkin_dates`（当前本地月 + 上一本地月里已签到或补签的 `YYYY-MM-DD` 数组）、`today_post_count` `today_comment_count` `today_like_count`（今天已给分次数，非负整数，不超过各自每日上限）。补签卡不是积分，不进流水、不进 `Me`。

连续天数按用户本地自然日：有签到记录（含补签）的相邻日历日往回数。今天已签则算到今天；今天未签、昨天有记录则算到昨天；昨天也没有则为 0。第 8 天及以后只要不断，每天仍只发签到 +10，不再给第 3 / 7 天那种额外积分和补签卡。断一天且未补，连续归零。

可补签的日子：今天之前、含今天在内共 7 个自然日里还没有签到记录的日子。不能补今天、不能补未来、不能补 7 天以外。

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

积分发放（接真 API 后由对应模块调 `points` service，合同里不另开发放接口）。补签卡不是积分，不进流水。

| 事件 | kind | amount | title | 限制 |
|---|---|---|---|---|
| 注册 | earn | 100 | 注册 | 账号一次 |
| 每日签到 | earn | 10 | 签到 | 每个自然日一次 |
| 连续第 3 天 | earn | 20 | 连续签到奖励 | 当前连续恰好为 3 的那次签到；另送 1 张补签卡 |
| 连续第 7 天 | earn | 50 | 连续签到奖励 | 当前连续恰好为 7 的那次签到；另送 1 张补签卡 |
| 帖子变为 published | earn | 20 | 发布帖子 | 用户本地自然日最多 3 条；第 4 条起不加、不报错 |
| 发表评论 | earn | 5 | 评论 | 用户本地自然日最多 1 条；超出不加、不报错 |
| 点赞帖子 | earn | 2 | 点赞 | 用户本地自然日最多 3 条；只算帖子点赞，不算评论点赞；取消不退分；超出不加、不报错 |
| 补签 | earn | 10 | 补签 | 花 1 张补签卡；不触发连续额外积分，不送补签卡 |
| 创建视频任务 | spend | 50 | 图生视频 | 余额不够 → `POINTS_NOT_ENOUGH` |

第 3 / 7 天签到写 **两行** 流水：`签到` +10，再 `连续签到奖励` +20 或 +50。

### AssistantSuggestion

```json
{
  "id": "e1111111-1111-1111-1111-111111111111",
  "question": "夏天怎么给狗降温"
}
```

空态可点的推荐问题。`question` 非空。

### AssistantAsk

```json
{
  "conversation_id": "f1111111-1111-1111-1111-111111111111",
  "answer": "避开正午出门，给足阴凉饮水。",
  "source": "knowledge",
  "citations": [
    {
      "id": "k1111111-1111-1111-1111-111111111111",
      "title": "夏天给狗降温",
      "snippet": "避开正午出门，室内通风，提供阴凉饮水。"
    }
  ],
  "related_posts": [
    {
      "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "title": "给两只小狗起个标题",
      "body": "想把两只小狗放到草地上跑一跑，有人试过图生视频吗？",
      "cover_url": "https://example.com/1.jpg"
    }
  ]
}
```

`source`：`knowledge` | `search` | `generated`。  
`citations`、`related_posts` 始终是数组，可 `[]`。  
`related_posts` 是已发布帖摘要，不当回答证据；`cover_url` 无图时为 `null`；`title` 可空字符串。  
响应里的 `conversation_id` 始终是字符串。请求里可 `null`（新开对话）；之后把上次响应的 id 原样传回。

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
请求：`{ "title", "body", "image_urls", "cover_url", "tag_names", "visibility", "sync_to_forum" }`
`cover_url` 可省略（用首图）。`visibility` 可省略（视为 `private`）。响应：`{ "data": Album }`

`GET /api/v1/album/{id}` → `{ "data": Album }`  
`PATCH /api/v1/album/{id}` 子集 → `{ "data": Album }`  
`DELETE /api/v1/album/{id}` → `{ "data": { "ok": true } }`

### community

`GET /api/v1/community/post?tab=recommend&q=&topic=&page=1&page_size=20`  
`tab` 默认 `recommend`。`q` 可省略（搜标题、正文、话题名）。`topic` 可省略。  
`tab=following` 为已关注作者的已发布帖。  
响应：`{ "data": { "items": [Post], "total", "page", "page_size" } }`  
列表不包含 `draft` / `pending` / `rejected`（除非走 `/post/mine`）。

`GET /api/v1/community/post/mine?status=&page=1&page_size=20`  
`status` 可省略（全部）或为 `draft` \| `pending` \| `published` \| `rejected`。  
实现时必须把 `/post/mine` 注册在 `/post/{id}` **前面**，避免 `mine` 被当成 id。

`GET /api/v1/community/post/favorite?page=1&page_size=20`  
只返回当前用户已收藏的帖。响应：`{ "data": { "items": [Post], "total", "page", "page_size" } }`。排序 `created_at` 新的在前。  
实现时必须把 `/post/favorite` 注册在 `/post/{id}` **前面**，避免 `favorite` 被当成 id。

`POST /api/v1/community/post`  
请求：`{ "board", "title", "body", "image_urls", "topic_names", "status" }`  
`board` 可省略（视为 `daily`）。`status` 只允许 `draft` 或 `pending`。响应：`{ "data": Post }`

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
已关注再调：`CONFLICT`。不能关注自己：`VALIDATION`。

`GET /api/v1/community/follow?page=1&page_size=20`  
我关注的人。响应：`{ "data": { "items": [Author], "total", "page", "page_size" } }`。

`GET /api/v1/community/follower?page=1&page_size=20`  
关注我的人。响应：`{ "data": { "items": [Author], "total", "page", "page_size" } }`。

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
响应：`{ "data": { "awarded": 10, "balance": 190, "already_done": false, "date": "2026-08-24", "streak": 1, "extra": 0, "makeup_cards_awarded": 0, "makeup_card_count": 0 } }`  
`awarded` 为本次写入流水的积分合计（普通签到 10；第 3 天 30；第 7 天 60；已签则为 0）。`extra` 为本次额外积分，没有则为 0。`makeup_cards_awarded` 为本次送的卡，没有则为 0。`makeup_card_count` 为送完后的张数。当日已签：`awarded` 为 0，`already_done` 为 true，`extra` 与 `makeup_cards_awarded` 为 0，不报错。

`POST /api/v1/points/makeup`  
请求：`{ "date": "2026-09-14" }`（用户本地自然日 `YYYY-MM-DD`）。  
响应：`{ "data": { "awarded": 10, "balance": 190, "date": "2026-09-14", "streak": 4, "makeup_card_count": 0 } }`  
非法日期 / 无卡 / 那天已有签到或补签记录 / `date` 是今天：`VALIDATION`。成功则扣 1 张补签卡，写流水 `补签` +10，并按连续天数规则重算 `streak`。

### assistant

`GET /api/v1/assistant/suggestion?page=1&page_size=20`  
响应：`{ "data": { "items": [AssistantSuggestion], "total", "page", "page_size" } }`

`POST /api/v1/assistant/ask`  
请求：`{ "question", "conversation_id" }`  
`conversation_id` 可 `null`。`question` 去空白后为空 → `VALIDATION`。  
响应：`{ "data": AssistantAsk }`

---

## 谁必须遵守

| 角色 | 必须 |
|---|---|
| 前端 mock | `core/request` 按 method+path 返回上面的 JSON |
| 小程序 services | path 字符串与本文件逐字相同 |
| FastAPI | 同 path、同字段、同类型；Pydantic 模型与本文件一致 |
| 改接口 | 先改本文件，再改两端；已有字段不改名、不改类型、不改成必填 |

后端实现完成后，以本文件为准对照 OpenAPI；若生成结果与本文件冲突，改代码，不要另起前端字段。
