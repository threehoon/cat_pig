# miniprogram/modules

每个子目录是一个业务模块。新页面放在 `modules/<feature>/pages/`，不要放回 `miniprogram/pages/`。

mock handlers 放该模块 `services/mock.ts`。种子不在这里，在 `miniprogram/mocks/store.ts`。跨模块写操作走对方公开函数（如 community `mock-helpers.ts`、points `mock-ledger.ts`），不要直接改另一模块的数组。

新增流程：[docs/framework/adding-a-module.md](../../docs/framework/adding-a-module.md)。
