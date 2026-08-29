# 小程序规范

路径：`miniprogram/`。微信原生 + TypeScript + Sass。不要引入 Taro / uni-app。

模块契约见 [modules.md](../framework/modules.md)。页面路径、tab、mock、字段见 [handoff.md](../handoff.md)（**界面先行以 handoff 为准**）。

## 目录

```text
miniprogram/
  app.ts / app.json / app.scss
  styles/               # tokens + 跨页 primitives；页面不要复制
  assets/               # brand / icon / tab / mock；路径表 paths.ts
  core/                 # 内核：config、request、auth、storage
  modules/<feature>/    # 新功能只加这里
    pages/
    components/
    services/
    types/
  components/           # 跨功能 UI（page-shell、empty-state、react-row）
  pages/                # 仅模板残留；禁止新增业务页
  utils/                # 纯函数 only（现有 `util.ts` 可以留着；新业务不要往这里加）
```

观感（配色、插画、通用组件）见 [visual.md](visual.md)。各模块 `services/` 与 `core/request` mock 已按 [api/contract.md](../api/contract.md) 接入，见 [progress.md](../progress.md)、[handoff.md](../handoff.md)。页面必须走 `services/`，不准再写页面内假数组。

微信要求所有页面出现在 `app.json` 的 `pages` 里。页面文件在模块内，登记路径用 `modules/<feature>/pages/<page>/<page>`。

## 内核职责

| 文件（阶段 F 就要有） | 职责 |
|---|---|
| `core/config.ts` | `useMock`、`apiBaseUrl` |
| `core/request.ts` | `useMock` 时返回本地信封；否则封装 `wx.request`（基址、JWT、`error.code`） |
| `core/auth.ts` | 登录、读/写 token；mock 时可当成已登录 |
| `core/storage.ts` | 对 `wx.setStorage` 的薄封装 |

业务 `services/` 只调用 `core/request`，不写 URL 主机名，不读 storage 里的 token 细节。每个会动数据的页面动作都必须有对应 service，path 和字段以 [api/contract.md](../api/contract.md) 为准；没有 service 的页面不算做完。

## 禁止

- 页面 `wx.request`、页面里写死 `http://127.0.0.1`
- 把相册、帖子、积分等业务状态放进 `App.globalData`
- 在 `pages/` 根下新建业务页面
- 为了跨端引入 Vue/React 运行时

## 与模板页

`pages/index`、`pages/logs` 是官方 quickstart。阶段 F 把 `app.json` 首页改为 `modules/community/pages/home/home`。不要在模板页里堆产品 UI。
