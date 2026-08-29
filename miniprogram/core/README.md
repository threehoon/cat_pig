# miniprogram/core

小程序内核（config / request / auth / storage）。**阶段 F 就要有实现**（`useMock: true`）。阶段 2 只是把 mock 关掉打真 API。

当前：`useMock: true` 时 `mock.ts` 按 method+path 返回合同形状的本地数据；未命中仍 reject `{ code: 'MOCK_NOT_IMPLEMENTED' }`。该码只存在于小程序 mock，**不要写进 API 合同**。

页面和业务模块禁止直接 `wx.request`。规范：[docs/miniprogram/README.md](../../docs/miniprogram/README.md)。mock 约定：[docs/handoff.md](../../docs/handoff.md)。合同：[docs/api/contract.md](../../docs/api/contract.md)。
