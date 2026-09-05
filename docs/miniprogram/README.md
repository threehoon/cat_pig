# 小程序规范

路径：`miniprogram/`。微信原生 + TypeScript + Sass。不要引入 Taro / uni-app。

模块契约见 [modules.md](../framework/modules.md)。页面路径、tab、mock、字段见 [handoff.md](../handoff.md)（**界面先行以 handoff 为准**）。

## 目录

```text
miniprogram/
  app.ts / app.json / app.scss
  styles/               # tokens + 跨页 primitives；页面不要复制
  assets/               # brand / icon / tab / mock；路径表 paths.ts
  core/                 # 内核：config、request、auth、session、storage、mock.ts、mock-runtime.ts
  mocks/store.ts        # mock 种子组合，不是业务模块
  modules/<feature>/    # 新功能只加这里
    pages/
    components/
    services/           # 含 mock.ts（handlers）
    types/              # 阶段 F 按合同手写
  components/           # 跨功能 UI（page-shell、empty-state、react-row）
  pages/                # 仅模板残留；禁止新增业务页
  utils/                # 纯函数 only（现有 `util.ts` 可以留着；新业务不要往这里加）
```

观感（配色、插画、通用组件）见 [visual.md](visual.md)。页面必须走 `services/`，不准再写页面内假数组。静态检查：`npm run typecheck`。

微信要求所有页面出现在 `app.json` 的 `pages` 里。页面文件在模块内，登记路径用 `modules/<feature>/pages/<page>/<page>`。

## 内核职责

| 文件 | 职责 |
|---|---|
| `core/config.ts` | `useMock`、`apiBaseUrl` |
| `core/request.ts` | `useMock` 时走 `handleMock`；否则封装 `wx.request`（基址、JWT、`error.code`） |
| `core/auth.ts` | 登录、读/写 token。无独立登录页。mock 下直接调 `handleMock`，真 API 走 `request`；页面不写 `wx.request` |
| `core/session.ts` | 当前 token / 用户 id |
| `core/storage.ts` | 对 `wx.setStorage` 的薄封装 |
| `core/mock.ts` | 注册各模块 routes + 匹配；无产品名词 |
| `core/mock-runtime.ts` | 无产品名词的 helper（`matchPath`、`paginate`、`copy`、`fail`、`newId`、`nowIso`、query） |
| `mocks/store.ts` | 种子数据（me / albums / posts / videos / ledger） |

handlers 在 `modules/<feature>/services/mock.ts`。未命中路由时 `handleMock` reject `{ code: 'MOCK_NOT_IMPLEMENTED' }`。该码只存在于小程序 mock，**不要写进 API 合同**。

业务 `services/` 只调用 `core/request`，不写 URL 主机名，不读 storage 里的 token 细节。每个会动数据的页面动作都必须有对应 service，path 和字段以 [api/contract.md](../api/contract.md) 为准；没有 service 的页面不算做完。

## 禁止

- 页面 `wx.request`、页面里写死 `http://127.0.0.1`
- 把相册、帖子、积分等业务状态放进 `App.globalData`
- 在 `pages/` 根下新建业务页面
- 为了跨端引入 Vue/React 运行时

## Skyline / 开发者工具

`app.json` 已 `"renderer": "skyline"`。公共 `project.config.json` 的 `libVersion` 是 `3.7.0`。`project.private.config.json` 已 gitignore，会覆盖公共基础库。

调试面板不是 Skyline 时：在开发者工具「详情」把基础库改成 3.7.0，或把本机私有配置里的 `libVersion` 改成与公共配置相同。打开仓库**根目录**，不是 `miniprogram/`。

真机调试：`project.config.json` 里 `es6` 和 `enhance` 都是 `false`，TS `target` 是 ES2020。写 `?.` / `??` 模拟器可能过，真机调试会 `SyntaxError: Unexpected token .`（已在 `detail-voice.ts` 的 `recordSink?.` 上发生过）。业务代码写成显式 `if`。不要为了这一个语法去开 `enhance`。

### 滚动

纵向 `scroll-view` 必须写 `type="list"`。横向再加 `enable-flex`。不设 `type` 会走退化路径，点击也不跟手。

`type="list"` 时，列表项必须是 `scroll-view` 的直接子节点。不要用一个 `page-pad` 把头图和卡片全包进去再标 `type="list"`——那样按需渲染退化。首页 / 论坛 / 我的发布：头用 `page-pad--head`，`post-card` 做直接子节点，底部用 `list-end`（论坛带 FAB 用 `list-end--fab`）。短页（我的、发帖、上传）可以保留单个 `page-pad`，但仍要有 `type`。

### 导航栏

`navigation-bar` 用同步 `wx.getSystemInfoSync()` 量高度并缓存（本仓库 typings 没有 `getWindowInfo`）。不要在 `attached` 里异步 `getSystemInfo` 再 `setData`，转场中途会跳顶栏。

### 跳转空一拍（真机不卡）

Tab 切换不卡。开发者工具模拟器里，页面点击后 `wx.navigateTo` 会抬手空一拍再转场。**真机调试没有这个问题。** 阶段 F 在当前骨架上继续做功能。不要把模拟器里的空一拍当成产品缺口去改详情第一帧。

公共骨架（`scroll-view type`、导航栏同步）仍按上面写。不要为「修模拟器卡顿」做这些（已试过或已排除）：

- 评论无限滚动。合同虽是 `page_size=20`，但评论是 `parent_id` 线程，按页切会把回复和楼主拆开。当前 mock 也只有几条评论。
- 给 Skyline 的 `image` 加 `lazy-load`。Skyline 默认已懒加载，那是 WebView 属性。
- 把详情 `reload` 整包挪到 `onLoad`。会更早堵住转场。
- 为修卡顿重写详情 WXML。已发生过少闭合标签、编译失败，整段撤回。改 WXML 后先核对开闭标签；编译不过先还原，不要再堆 `core/navigation.ts`、`detail-loading.ts` 这类新文件。

## 与模板页

`pages/index`、`pages/logs` 是官方 quickstart。阶段 F 把 `app.json` 首页改为 `modules/community/pages/home/home`。不要在模板页里堆产品 UI。
