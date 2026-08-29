# 小程序界面空壳设计

- 日期：2026-08-24
- 状态：已按讨论写入，代码已按本文落地（未在微信开发者工具模拟器里点过）
- 范围：微信原生小程序的可切换 tab 空壳、共用 page-shell、core 四个文件的签名。不是阶段 F 的完整界面。
- 产品功能与接口字段仍以 [product/](../../product/README.md)、[handoff.md](../../handoff.md)、[api/contract.md](../../api/contract.md) 为准。本文件只锁这一轮空壳怎么搭。

## 背景

`miniprogram/` 仍是微信官方模板：`pages/index`、`pages/logs`、自定义 `navigation-bar`。`core/` 与 `modules/` 只有 README。用户要求先搭**界面框架**，列表、表单、二级页、mock 数据后置。

已锁定选择：

- 能切 5 个 tab 的空壳，不做功能页
- 同时建 `core` 四个文件（页面这一轮不调用）
- 抽跨模块 `page-shell`
- 方案 2：壳 + 内核签名，不用自定义凸起 tabBar
- 官方模板页保留，不当入口；启动时不 mock 登录
- tab 顶栏用 tab 名；page-shell 留右侧插槽
- mock 未登记 path 返回统一错误信封，不返回空 `data`
- 暖米色底 + 橙色选中 + 原生 tabBar + 简单线框占位图标

## 目标

微信开发者工具打开本仓库根目录后：

1. 编译通过
2. 启动落在社区首页 tab
3. 底栏五个入口能切换：首页 / 相册 / 创作 / 论坛 / 我的
4. 每个 tab 是同一套壳：自定义顶栏 + 一句占位文案
5. `core` 可被以后的 `services/` import，本轮页面不引用

## 非目标（这一轮禁止做）

- 二级页：相册上传、发帖、帖子详情、我的发布、积分明细、视频任务列表 / 详情
- 列表、表单、入口九宫格、搜索、分栏
- 模块 `services/`、mock 业务数据、页面内假数组
- `points`、`media` 模块目录（没有本轮页面；不预建空业务目录）
- 自定义 tabBar、中间凸起加号
- 对标产品的品牌名、插画、文案原句
- FastAPI、数据库、真 `wx.login` 换 token
- 选图权限、隐私协议页
- 主按钮 / 卡片 / 空状态组件（那是 UI kit，不是壳）

## 架构

```text
miniprogram/
  app.ts / app.json / app.scss
  core/
    config.ts
    request.ts
    auth.ts
    storage.ts
  components/
    navigation-bar/          # 已有，page-shell 使用它
    page-shell/              # 新建
  assets/tab/                # 10 张占位图标（5 tab × 未选中/选中）
  modules/
    community/pages/home/
    community/pages/plaza/
    album/pages/list/
    video/pages/create/
    me/pages/index/
  pages/index、pages/logs    # 保留文件，仍登记在 pages 末尾，不进 tabBar
```

依赖方向：

```text
tab 页面 → page-shell → navigation-bar
以后：页面 → 本模块 services → core/request → core/auth（带 token）
本轮：页面不 import core，不 import 其它模块
```

`app.json` 的 `pages` 第一项必须是首页 tab。tabBar 五项路径与 [handoff.md](../../handoff.md) 逐字相同：

| Tab 文案 | 路径 |
|---|---|
| 首页 | `modules/community/pages/home/home` |
| 相册 | `modules/album/pages/list/list` |
| 创作 | `modules/video/pages/create/create` |
| 论坛 | `modules/community/pages/plaza/plaza` |
| 我的 | `modules/me/pages/index/index` |

然后才是 `pages/index/index`、`pages/logs/logs`。不要在模板页写产品 UI。不要新建 `miniprogram/pages/` 下的业务页。

`window.navigationStyle` 保持 `custom`。本轮可以改 `pages` 顺序和 `tabBar`（handoff 对 adding-a-module 的例外）。不改 Skyline / glass-easel 等渲染配置。

`app.ts`：删掉模板自带的 `logs` 写入和 `wx.login`。保留空的 `App({ globalData: {} })`。不在 `onLaunch` 里登录，不把业务状态放进 `globalData`。

## 组件：page-shell

路径：`miniprogram/components/page-shell/`。跨模块通用 UI，不属于任何一个 feature 模块。

职责：顶栏 + 内容区。不管 tabBar（原生底栏自己占位），不管业务内容。

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| `title` | string | `''` | 顶栏标题 |
| `back` | boolean | `false` | 是否显示返回。tab 页为 false |

插槽：

- 默认插槽：标题下方内容
- `right`：顶栏右侧，转给 `navigation-bar` 的 right 插槽。本轮五个 tab 都不传

内部使用现有 `components/navigation-bar`（`page-shell.json` 里 `usingComponents` 指 `../navigation-bar/navigation-bar`）。`styleIsolation` 用 `apply-shared`，以便吃到 `app.scss` 的 CSS 变量。顶栏文字色用 `--color-text`，背景用 `--color-bg`。必须把 `back` 显式传给 `navigation-bar`（该组件默认 `back` 为 true，tab 页不能当返回按钮）。内容区铺满顶栏以下剩余高度，背景同样是 `--color-bg`。不内置 scroll-view：以后内容变长由各页自己加。

五个 tab 页结构相同：

```xml
<page-shell title="首页">
  <view class="placeholder">这里以后放首页</view>
</page-shell>
```

占位文案（不要写成对标产品的句子）：

| 页面 | `title` | 占位 |
|---|---|---|
| home | 首页 | 这里以后放首页 |
| list | 相册 | 这里以后放相册 |
| create | 创作 | 这里以后放图生视频 |
| plaza | 论坛 | 这里以后放论坛 |
| index（我的） | 我的 | 这里以后放我的 |

工作名「宠物记录」本轮不写进顶栏。正式品名仍未定。

每个 tab 页的 json 只声明 `page-shell`。页面 ts 不请求、不读 storage、不写 `globalData`。

## 内核：core

四个文件都要有可 import 的实现，不是只写 README。本轮没有任何页面调用它们。

### `config.ts`

```ts
export const config = {
  useMock: true,
  apiBaseUrl: 'http://127.0.0.1:8000',
}
```

禁止页面写死主机名。以后接真 API 只改这里的 `useMock`。

### `storage.ts`

对 `wx.setStorageSync` / `getStorageSync` / `removeStorageSync` 的薄封装：`get` / `set` / `remove`。不定义业务 key。

### `auth.ts`

只管会话 token，key 固定为 `auth_token`，读写走 `storage`。

公开方法：`getToken()`、`setToken(token)`、`clearToken()`。没有 token 时 `getToken()` 返回 `null`。本轮不调用 `wx.login`，不请求 `/api/v1/auth/login`。

### `request.ts`

唯一允许发 HTTP 的地方。签名：

```ts
request<T>(options: {
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  path: string
  data?: Record<string, unknown>
  query?: Record<string, string | number | boolean | undefined>
}): Promise<T>
```

`path` 从 `/api/v1/...` 写起，与 [api/contract.md](../../api/contract.md) 一致。禁止在这里拼业务 path 常量以外的别名。

行为：

1. 成功：HTTP 信封 `{ data }` → **resolve 为 `data` 本身**（拆开信封）。
2. 失败：信封 `{ error: { code, message } }` → **reject `{ code, message }`**。调用方按 `code` 分支，禁止按中文 `message` 分支。
3. `useMock === true`：本轮没有业务 mock 表。任何 path 都 reject `{ code: 'MOCK_NOT_IMPLEMENTED', message: '<method> <path>' }`。`MOCK_NOT_IMPLEMENTED` 只存在于小程序 mock 分发，**不要写进 API 合同**。下一轮按 path 登记 mock 时，未命中仍走这个错误。
4. `useMock === false`：`wx.request` 打 `apiBaseUrl + path`；若 `getToken()` 非空，带 `Authorization: Bearer <token>`。不用页面去写 `wx.request`。

本轮不实现按 path 返回相册/帖子的 mock 分发器。

## 视觉

在 `app.scss` 的 `page` 上定义 CSS 变量，全页继承：

| 变量 | 值 | 用途 |
|---|---|---|
| `--color-bg` | `#F6EFE4` | 页面与顶栏底 |
| `--color-primary` | `#F0783C` | 主色、tab 选中 |
| `--color-text` | `#2C241C` | 标题与正文 |
| `--color-text-muted` | `#9A9188` | 占位文案、tab 未选中 |
| `--page-padding` | `48rpx` | 占位区边距 |

`page { background: var(--color-bg); color: var(--color-text); }`

tabBar（原生，写入 `app.json`）：

- `color`：`#9A9188`
- `selectedColor`：`#F0783C`
- `backgroundColor`：`#FFF9F2`
- `borderStyle`：`white`
- 第三项「创作」图标为加号；其余为简单线框（首页房子、相册图片框、论坛气泡、我的人形）
- 图标放 `miniprogram/assets/tab/`，每项 `iconPath` + `selectedIconPath` 都必须有文件，避免编译失败。文件名锁死：

| tab | 未选中 | 选中 |
|---|---|---|
| 首页 | `home.png` | `home-active.png` |
| 相册 | `album.png` | `album-active.png` |
| 创作 | `create.png` | `create-active.png` |
| 论坛 | `plaza.png` | `plaza-active.png` |
| 我的 | `me.png` | `me-active.png` |

- 81×81 PNG，选中态用主色，未选中用灰色。不贴对标截图素材，不做彩色圆底、不做中间凸起

占位文案居中、使用 `--color-text-muted`。不要插画、不要假列表。

## 数据流

本轮无数据流。页面只渲染壳。

下一轮（不在本次实现）约定：页面事件 → 本模块 `services/` → `core/request`。跨模块只跳路由。`media` 是唯一允许被相册/发帖/创作 import service 的例外，见 handoff；本轮不建 `media`。

## 错误处理

- 内核：`request` 用信封，失败带稳定 `code`
- 本轮页面不调用 `request`，因此没有页面级错误 UI、没有 toast 封装
- 不要在 page-shell 里 catch 请求

## 测试与验收

没有小程序单测框架，本轮不写测试文件。验收：

1. TypeScript 编译无新增错误（微信开发者工具 / 现有 tsconfig）
2. `app.json` 的 tabBar 五项都能解析到页面和 png 图标
3. 人工：开发者工具打开仓库根目录，启动见「首页」占位，能切到另外四个 tab，顶栏标题与底栏文案一致

本环境没有微信开发者工具 GUI。实现后在进度里写明：人要用开发者工具打开根目录验证切换。Agent 用读 `app.json`、确认页面文件与图标存在、跑 `tsc`（若项目脚本支持）作为代替检查，并写明未在模拟器里点过。

## 实现后必须改的文档

- [progress.md](../../progress.md)：阶段 F 标为进行中；已完成写「空壳：5 tab + page-shell + core 签名」；下一步改为铺页面内容与 mock（仍不要先做 FastAPI）
- 决策日志追加本文件的选择（空壳先行、page-shell、core 签名、原生 tabBar）

不把本文件的细则复制进 `miniprogram/README.md`。日常改代码仍读 miniprogram README + handoff；本文件只回答「为什么空壳做成这样」。

## 关键决定

1. **先壳后功能。** 阶段 F 的完整页面和 mock 拆成后续任务，避免空壳被列表和接口拖住。
2. **page-shell 是唯一新建的通用 UI。** 按钮/卡片/空状态等有第二处页面再用时再抽。
3. **core 先有签名、没有业务 mock。** 防止页面直接 `wx.request`；又避免本轮发明一套假数据。
4. **只建有 tab 的模块目录。** `community` `album` `video` `me`。`auth` 会话放 `core/auth`。`points` `media` 等有页面或有调用时再建模块。
5. **原生 tabBar。** 中间凸起不阻塞空壳。
6. **模板页保留在 pages 末尾。** 删入口但不删文件，降低开发者工具对残留路径的惊吓。
