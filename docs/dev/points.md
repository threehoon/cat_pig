# 积分任务 + 独立签到页（一次性开发文档）

**用完即删。** 按切片开发；全部切片点验通过后删除本文件。不要登记进 `AGENTS.md` / `docs/README.md`。不要当长期规范。改接口只改 `docs/api/contract.md`。

阶段：F（mock，不接 FastAPI）。模块：`points`（明细、任务、签到页）+ `community`（发帖 / 评论 / 点赞给分）+ `me`（只跳路由）。页面只调**本模块** `services/`。首页只跳签到页，**不 import** `points` service。

当前切片：**切片 1–5 连续执行**（用户已确认方案并说「开始执行」）。

新对话：若本文件仍在且切片未全部点验，先读本文件。不要先搭 FastAPI，不要重做全站视觉。

---

## 怎么开发

用户已说「开始执行」：切片 0 就是本文件；写完后连续做切片 1–5，**不要**在切片之间停下来等点验。全部做完后把下面各片点验清单一并交给用户。

1. 只改该片「改哪些文件」列出的路径。该片「不做」里的一律留下一片。
2. Agent 验：跑 `npm run typecheck`（切片 0 无代码，跳过）；看 `git diff`；字段与 `docs/api/contract.md` 逐字一致。没跑过的不写已验证。
3. **代码切片（2–5）在交点验清单之前，必须开一个独立子 agent 做 code review**（只看该片 diff）。安全问题和逻辑错误先修再交点验。风格建议不阻塞，除非违反 `AGENTS.md`。不要为 review 去 commit。切片 0 / 1 无代码，跳过 review。
4. 点验：用户用微信开发者工具打开 **仓库根目录** 点。模拟器 `navigateTo` 空一拍不当失败。
5. 交接写：范围 / 已改 / 契约 / 验证 / 风险 / 下一步。

业务代码禁止 `?.` / `??`。

不要改 `docs/progress.md` / `docs/handoff.md`，除非用户说整理 / 总结 / 更新对接文档。

---

## 已定

全产品 **一种整数积分**。签到从积分任务里拿掉，放到独立签到页。积分任务是带猫狗顶图的任务列表。

| 点 | 决定 |
|---|---|
| 货币 | 一种积分。不拆成长值 / 第二种币 |
| 签到入口 | 首页「签到」→ 独立页 `modules/points/pages/checkin/checkin`。首页不铺日历、不调积分接口 |
| 签到页 | 当月月历；可切到上个月；不能看下月、不能再往前翻。已签打点。近 7 天漏签可点补签。补签卡张数在日历上方。底部「今日签到」 |
| 积分任务 | 顶部猫狗大图；三条任务：发帖、评论、点赞。每条左边用现成入口/贴纸图标。**没有签到** |
| 领取 | 不做。做完自动入账。按钮是「去完成」/「已完成」 |
| 发帖 | +20，每天前 3 条；第 4 条起不加、不报错。去完成 → 发帖页 |
| 评论 | +5，每天 1 条；超出不加、不报错。去完成 → 论坛 tab |
| 点赞 | +2，每天 3 条；只算**帖子**点赞，不算评论点赞；取消不退分。去完成 → 论坛 tab |
| 上传相册 | 不给分、不当任务 |
| 连续签到 | 每天 +10；第 3 天、第 7 天再额外给一笔，并各送 1 张补签卡 |
| 补签 | 花 1 张补签卡补近 7 天里缺的一天（不含今天）。只 +10，不触发连续额外，不送卡 |
| 「我的」 | 积分明细、积分任务。不恢复「每日签到」菜单 |

### 积分规则（合同与页面同一张表）

获取：

| 事件 | 积分 | 限制 | 流水 title |
|---|---|---|---|
| 注册 | +100 | 账号一次 | `注册` |
| 每日签到 | +10 | 每个自然日一次 | `签到` |
| 连续第 3 天 | 额外 +20 | 当前连续天数恰好为 3 的那次签到 | `连续签到奖励` |
| 连续第 7 天 | 额外 +50 | 当前连续天数恰好为 7 的那次签到 | `连续签到奖励` |
| 帖子变为 published | +20 | 用户本地自然日最多 3 条；第 4 条起不加 | `发布帖子` |
| 发表评论 | +5 | 每个自然日 1 条；超出不加 | `评论` |
| 点赞帖子 | +2 | 每个自然日 3 条；取消不退；超出不加 | `点赞` |
| 补签 | +10 | 花 1 张卡；不触发连续额外 | `补签` |

消耗：

| 事件 | 积分 | 限制 | 流水 title |
|---|---|---|---|
| 创建视频任务 | −50 | 余额不够 → `POINTS_NOT_ENOUGH` | `图生视频` |

第 8 天及以后：只要不断，每天仍 +10，不再给第 3 / 7 天那种额外积分和补签卡。断一天（且未补签）连续天数归零，下一次签到算第 1 天。

关注、上传相册、评论点赞：v1 不给分。不做「平台添加」发放入口。

### 连续天数

按用户本地自然日。有签到记录（含补签）的相邻日历日往回数。

- 今天已签：连续天数 = 今天往回连着有记录的天数。
- 今天未签、昨天有记录：连续天数仍算到昨天，页面提示「今日未签」。
- 今天未签、昨天也没有（又没补）：连续天数为 0。

### 补签卡

补签卡 **不是积分**，不进积分流水。只在签到页展示张数。

| 点 | 决定 |
|---|---|
| 怎么得 | 连续第 3 天 +1 张；连续第 7 天 +1 张。v1 没有别的来源 |
| 怎么花 | 点月历上可补的日子，确认后 `POST` 补签，1 张补 1 个缺的自然日 |
| 能补哪天 | 今天之前、含今天在内共 7 个自然日里，还没有签到记录的日子。不能补今天、不能补未来、不能补 7 天以外 |
| 补签给什么 | 只给那天的 +10（流水 title `补签`）。不触发第 3 / 7 天额外积分，不送补签卡 |
| 补完连续 | 按「连续天数」规则重算。补上缺口后，连续可以接上 |
| 没卡 / 日期不合法 / 那天已经签过 | `VALIDATION`，不扣卡 |

新用户没有补签卡，连到第 3 天才有第一张。这是故意的。种子张数仍为 **0**。

### 两个入口

| 入口 | 去哪 | 干什么 |
|---|---|---|
| 首页「签到」 | 新页 `modules/points/pages/checkin/checkin` | 月历、今日签到、补签 |
| 「我的」积分明细 | 已有 `modules/points/pages/list/list` | 汇总 + 规则说明 + 流水 |
| 「我的」积分任务 | 已有 `modules/points/pages/tasks/tasks` | 发帖 / 评论 / 点赞，没有签到 |

### 签到页

```
连续签到 N 天          补签卡 x 张

‹  YYYY年M月  ›     （只能回到上个月）

日 一 二 三 四 五 六
[ 当月格子；上月空白占位；已签打点；
  今天未签描边；近 7 天漏签可点 ]

[今日签到] 或 「今天已经签过了」
```

- 点「今日签到」→ `POST /api/v1/points/checkin`。不要点日历格子来签今天。
- 点近 7 天漏签格子 → 弹出「是否补签这一天？」；确认后有卡则 `POST /api/v1/points/makeup`，没卡提示「无法补签」。已签 / 未来 / 空白格子无反馈。漏签格子不高亮。
- 超过 7 天的漏签、未来、空白格：不可补。
- 不要在签到页再画流水。

### 积分任务页

```
[ 猫狗大图 mascots.jpg ]

(图标) 发布动态    +20 · 0/3    [去完成]
(图标) 发表评论    +5 · 0/1     [去完成]
(图标) 点赞帖子    +2 · 0/3     [去完成]
```

图标用现成资源，不新画：发帖 `entry-plaza`，评论 `compose-emoji`，点赞 `react-like`。

已完成按钮灰掉，不可点。去完成：发帖 `navigateTo` 发帖页；评论 / 点赞 `switchTab` 论坛。

进度来自 summary 的今日计数（已给分的次数），不是前端自己数。

### 积分明细页

已有汇总和流水筛选保留。规则说明补上评论 +5、点赞 +2。本页不签到、不补签。

### 日期

签到、补签、发帖 / 评论 / 点赞每日上限、流水 `range=month`，都用 **用户本地自然日**，与现有 `todayDate()` 一致。不要混 UTC 日。

---

## 新接口与字段（切片 1 进合同，切片 2 进 mock）

已有、要扩展、不改名：

- `GET /api/v1/points/summary` 仍返回 `earned` `spent` `balance` `streak` `makeup_card_count` `today_checked` `makeup_dates`。**再追加**：`checkin_dates`（当前本地月 + 上一本地月里已签/补签的 `YYYY-MM-DD` 数组）、`today_post_count` `today_comment_count` `today_like_count`（非负整数，今天已给分次数，不超过各自上限）。
- `POST /api/v1/points/checkin` 字段不改。
- `POST /api/v1/points/makeup` 字段不改。
- `GET /api/v1/points/ledger` 不改。

不加 `GET /points/tasks`、不加规则配置接口、不把补签卡写进 `Me`。评论 / 点赞给分仍由 community 调 points 公开函数，合同不另开发放接口。

---

## 种子（切片 2）

- 现有余额、流水、`checkin_dates: ['2026-08-23', '2026-08-21']` 可留。
- `makeup_card_count` 仍为 **0**。
- 不要把「今天」写成已签。
- 发帖 / 评论 / 点赞每日上限：给分前数今天、对应 title 的流水条数。

---

## 排版

气质：`docs/miniprogram/visual.md` 的 token。页面 scss 只写这一页。Skyline：flex，不用 grid；纵向 `scroll-view type="list"`。不写死 hex。不抄对标文案原句。

签到页日历用 flex 七列换行。已签用主色浅底圆点，不要系统打勾 emoji。任务页按钮已完成态用浅底，不要另做一套视觉体系。插画例外：积分任务顶图允许用 `mascots.jpg`（本页指定，不是全站列表插画）。

---

## 切片 0 — 本文档

**做完标准：** 本文件已按锁定方案写完。

改哪些文件：`docs/dev/points.md`（本文件）。

不做：合同、代码、`AGENTS.md`、`docs/README.md`、`progress.md`、`handoff.md`。

---

## 切片 1 — 合同 + benchmark

**做完标准：** 合同含 `checkin_dates`、三个今日计数、发放表含评论 / 点赞；benchmark / capabilities 已改签到入口和任务口径。

改哪些文件：`docs/api/contract.md`、`docs/product/benchmark.md`、`docs/product/capabilities.md`。

### 1a `docs/api/contract.md`

`PointsSummary` 示例追加 `checkin_dates` `today_post_count` `today_comment_count` `today_like_count`。写明 `checkin_dates` 只含当前月 + 上一月。

发放表增加评论 +5 / 天 1 条、点赞 +2 / 天 3 条（只算帖子点赞，取消不退）。

### 1b benchmark / capabilities

- 第 11 行积分：明细含规则；发帖每天前 3 条；评论每天 1 条 +5；点赞每天 3 条各 +2。
- 第 12 行每日签到：首页入口进独立签到页（月历、补签卡、补签）。
- 验收第 5 条改为在签到页签到一次。
- `capabilities.md` P1 积分流水补评论 / 点赞给分；每日签到补独立签到页 / 月历。发帖 / 评论 / 点赞给分仍由 community 调 points。

不做：`handoff.md`、`progress.md`、任何 `miniprogram/`、FastAPI。

点验清单：

1. 合同能搜到 `checkin_dates`、`today_comment_count`、流水 title `评论` / `点赞`。
2. `GET /api/v1/points/summary` 旧字段都在，只是多了字段。
3. 没有 `GET /points/tasks`，没有补签卡商城，没有第二种积分。
4. benchmark 签到是独立页 + 月历，不是积分任务里签到。

Agent 验：`rg` 新字段；无代码，不开 review。

---

## 切片 2 — mock + types + service

**做完标准：** `npm run typecheck` 通过。今日计数和给分上限按合同。

改哪些文件：`miniprogram/modules/points/types/points.ts`、`services/points.ts`、`services/mock.ts`、`services/mock-ledger.ts`、`miniprogram/modules/community/services/mock.ts`（点赞转亮、发评论时调公开给分函数）。不要改页面。

做：

- types / service 与合同逐字一致。
- `awardPublishedPost` 保持；新增 `awardComment` / `awardLike`（超限直接 return）。
- summary 带 `checkin_dates`（当前月 + 上一月）和三个今日计数。
- 帖子 `liked` 从 false→true 才给分；取消不退。评论点赞不给分。

不做：页面、菜单、合同（已在切片 1）。

点验清单（读代码 / mock）：

1. `PointsSummary` 有 `checkin_dates` 和三个 `today_*_count`。
2. 今天第 2 条评论不再加分。
3. 今天第 4 次帖子点赞不再加分；取消点赞余额不变。
4. 评论的点赞不写 `点赞` 流水。

Agent 验：`npm run typecheck`；对照合同；开子 agent review。

---

## 切片 3 — 签到页 + 首页跳转

**做完标准：** 点验清单用户能点；`npm run typecheck` 通过。

改哪些文件：新建 `miniprogram/modules/points/pages/checkin/`（ts / wxml / scss / json，日历纯函数可放同目录 `checkin-calendar.ts`）。`app.json` 的 `pages` **只追加** `modules/points/pages/checkin/checkin`。`miniprogram/modules/community/pages/home/home.ts` 签到跳转。

做：

- 月历、连续天数、补签卡、今日签到、点漏签补签。
- 首页「签到」→ `/modules/points/pages/checkin/checkin`。
- 首页仍然不 import `points`。

不做：积分任务改版（切片 4）、明细文案（切片 5）。

点验清单：

1. 首页「签到」进的是签到页，不是积分任务、不是明细。
2. 能看到当月月历、连续天数、补签卡张数（种子 0 张）。
3. 点今日签到成功，积分 +10，按钮变成已签；再点不加分。
4. 能切到上个月，不能切到下月，不能再往前。
5. 点近 7 天漏签弹出「是否补签」；没卡确认后提示无法补签，不出现「没有补签卡」。其它日期点了没提示。
6. `app.json` 只追加了签到页，五个 tab 路径没动。

---

## 切片 4 — 积分任务页

**做完标准：** 点验清单用户能点；`npm run typecheck` 通过。

改哪些文件：`miniprogram/modules/points/pages/tasks/`。

做：顶图猫狗、三条任务、去完成 / 已完成。去掉签到按钮、连续天数、补签列表。

不做：改签到页、改明细、新画角色。

点验清单：

1. 「我的」积分任务进的仍是任务页。
2. 顶部能看到猫狗图。
3. 三条：发布动态、发表评论、点赞帖子；没有今日签到。
4. 未完成点「去完成」：发帖进发帖页，评论 / 点赞切到论坛 tab。
5. 进度是 0/3、0/1、0/3（种子今天还没做）。

---

## 切片 5 — 积分明细规则

**做完标准：** 规则说明含评论 / 点赞；`npm run typecheck` 通过。

改哪些文件：`miniprogram/modules/points/pages/list/`。

做：规则说明补「评论 +5（每天 1 条）」「点赞 +2（每天 3 条）」。

不做：新筛选、自动签到、补签按钮。

点验清单：

1. 积分明细规则里能看到评论 +5、点赞 +2。
2. 带着 `?checkin=1` 进明细，不会自动签到。

---

## 本文件不做

- FastAPI、关 `useMock`、真上传
- 改五个 tab 路径、重做全站视觉
- 第二种积分、积分商城、平台发放后台、领取按钮
- 用积分买补签卡、补签卡商城
- 上传相册给分、关注给分、评论点赞给分
- 图生视频给分（继续只扣 50）
- 连续第 14 / 21 天再加码
- `GET /points/tasks`、规则配置接口
- 把补签卡显示在「我的」资料卡上
- 首页铺日历或半层弹窗
- 首页 import `points` service

---

## 代码边界

- 积分余额、流水、连续天数、补签卡、今日任务计数只进 `miniprogram/modules/points/`。
- community 发帖 / 评论 / 点赞给分，只调 points 已有公开函数，不准自己改 `store.ledger`。
- 发帖每日 3 条：流水 title `发布帖子`。评论 title `评论`。点赞 title `点赞`。
- 签到页、任务页都在 `points`。`app.json`、合同由主对话改。
- 切片 0 不改合同。切片 1 先改合同再改 types / mock / 页面。
