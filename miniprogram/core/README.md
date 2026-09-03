# miniprogram/core

小程序内核。规范：[docs/miniprogram/README.md](../../docs/miniprogram/README.md)。合同：[docs/api/contract.md](../../docs/api/contract.md)。mock 约定：[docs/handoff.md](../../docs/handoff.md)。

| 文件 | 职责 |
|---|---|
| `config.ts` | `useMock`、`apiBaseUrl` |
| `request.ts` | `useMock` 时走 `handleMock`；否则封装 `wx.request` |
| `auth.ts` | 登录、读写 token。无独立登录页；调 `handleMock` / `request`，页面不写 `wx.request` |
| `session.ts` | 当前 token / 用户 id |
| `storage.ts` | `wx.setStorage` 薄封装 |
| `mock.ts` | 注册各模块 routes + 匹配；无产品名词 |
| `mock-runtime.ts` | 无产品名词的 helper |

handlers 在 `modules/<feature>/services/mock.ts`。种子在 `miniprogram/mocks/store.ts`。未命中仍 reject `{ code: 'MOCK_NOT_IMPLEMENTED' }`。该码只存在于小程序 mock，**不要写进 API 合同**。

页面和业务模块禁止直接 `wx.request`。静态检查：`npm run typecheck`。
