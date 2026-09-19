# 代码规范与多 Agent 协作

本文件是日常编码、拆模块和 agent 交接规范。目录与依赖看 [overview.md](overview.md) 和 [modules.md](modules.md)，API 看 [../api/contract.md](../api/contract.md)，观感看 [../miniprogram/visual.md](../miniprogram/visual.md)，技术栈看 [stack.md](stack.md)。冲突时先遵守 `AGENTS.md` 和对应领域合同。

目标：改动半径可控、模块足够轻、下一位 agent 不用猜测。

## 命名

- 模块目录用 [handoff.md](../handoff.md) 已锁定或已预约的英文名。文件名、组件名用 `kebab-case`。
- TypeScript：变量 / 函数 / 属性 `camelCase`，类型 / 接口 / class `PascalCase`，常量 `UPPER_SNAKE_CASE`。
- 页面方法：`on` + 生命周期或 WXML 事件名（`onShow`、`onLike`）。页面专用 helper 可用动词。不要给 Page 方法规定 `handleSubmit` 这种前缀。
- Python：模块 / 函数 / 变量 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`。
- 传输层字段保持合同里的 `snake_case`；ID 是字符串。业务代码不用 `any`；`as` 只用于已由运行时条件证明的窄化。

## 调度层必须很薄

调度层只负责把请求、事件或生命周期交给谁，不负责业务规则。入口：`app.ts`、`core/request.ts`、`core/mock.ts`、`server/app/main.py`。新增模块只追加注册项，不改调度逻辑。入口里出现第二个产品名词分支，就立即下沉。

Mock 布局：

- `core/mock.ts`：注册各模块 routes + `matchPath`。禁止产品名词。
- 新 mock endpoint：写在 `modules/<feature>/services/mock.ts`，再在 `core/mock.ts` 追加一次 spread。
- 种子数据：`miniprogram/mocks/store.ts`（不是业务模块）。不要把 fixture 放进 `core/mock.ts`。
- 无产品名词的运行时 helper：`core/mock-runtime.ts`（`matchPath`、`paginate`、`copy`、`fail`、`newId`、`nowIso`、query helpers）。
- 跨模块写操作走对方公开函数（community：`mock-helpers.ts` 的 `publishPost` / `presentPost` / `syncAlbumToForum`；points：`mock-ledger.ts` 的 `addLedger` / `pointsSummary`），不要直接改另一模块的数组。

重量参考：`app.ts` 80 行，`core/request.ts` 180 行，`core/mock.ts` 220 行，`main.py` 120 行。超过先把注册表或 handler 拆到所属目录。

## 文件大小是拆分信号

超过后先拆再加行为。生成类型、资源清单、纯数据不计行数。

| 文件 | 参考线 | 优先拆法 |
|---|---:|---|
| 小程序页面 `.ts` | 300 行 | 抽页面专用组件、纯函数；页面只留编排 |
| 小程序组件 `.ts` / `.wxml` | 220 行 | 按可见职责拆兄弟组件 |
| 小程序 `services/*.ts` | 200 行 | 按资源或读写拆文件 |
| 小程序 `.scss` | 300 行 | 拆组件样式；token 放 `styles/` |
| FastAPI `router.py` | 150 行 | 业务判断进 `service.py` |
| FastAPI `service.py` / `repository.py` / `schemas.py` / `models.py` | 250 行 | 按用例或资源拆 |

`community/pages/detail/` 是已知例外（决策 2026-09-01）：必须保留 `detail.ts` 里的 `Page({...})`，额外流程放到同目录 sibling helper，**不要**抽 `detail-page.ts`。该屏行数按页面目录算。

两处真实重复且语义一致再抽 helper。模块生产源码约 2,000 行、单页三种以上独立流程、或一次需求改三个以上已有业务模块时，先判断模块边界。新模块走 [adding-a-module.md](adding-a-module.md)。

## 分层与契约

小程序：页面只编排；读写走本模块 `services/`，网络走 `core/request`。细则见 [miniprogram/README.md](../miniprogram/README.md)。

FastAPI：`router → service → repository`，见 [backend/README.md](../backend/README.md) 和 [modules.md](modules.md)。

API 兼容：已发布字段不改名、不改类型、不改成必填；变更先改 [../api/contract.md](../api/contract.md)。

## 并行与交接

两个 agent 不得写同一文件。`app.json`、`app.ts`、`core/`、`server/app/main.py`、API 合同、`docs/progress.md` 由主对话串行维护；子 agent 只回报应追加的注册项。

```text
范围：<模块 / 用例>
已改：<路径，逐项列出>
契约：<合同是否改变；改变列出路径>
验证：<命令 / 手工路径 / 结果>
风险：<已知缺口；没有则写「无」>
下一步：<下一位可直接执行的动作>
```

## 提交前

遵守 `AGENTS.md` 硬规则。再跑 `npm run typecheck`、`git diff --check`。涉及页面时请人用微信开发者工具打开仓库根目录点验。没跑过的检查不要写成已验证。
