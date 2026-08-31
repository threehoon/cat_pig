# CLAUDE.md

Claude Code 在本仓库的会话入口。单仓项目：微信**原生**小程序（TypeScript + Sass + Skyline）+ **FastAPI** + PostgreSQL，做宠物内容小程序（相册 / 图生视频 / 广场 / 积分）。

本文件只做两件事：把你导向真正的规范，写清 Claude Code 专属的机制。**规范正文一律不写在这里**，否则同一条规则会在 `AGENTS.md`、`docs/`、本文件里各存一份并开始互相矛盾。

## 每次对话开始（不可跳过）

1. 读 [AGENTS.md](AGENTS.md)。它是所有 agent 的唯一入口，硬规则和「先读哪份」路由表都在那里。**Claude Code 不会自动加载它**，本文件是你唯一的提醒。
2. 读 [docs/progress.md](docs/progress.md)，确认当前阶段和下一步。做当前阶段的事，不要提前做后面阶段。
3. 只打开路由表为本任务点名的文档，不要把 `docs/` 整体读进上下文。

写或改代码时追加读 [docs/framework/code-standards.md](docs/framework/code-standards.md)（命名、模块重量、薄调度层、验证、交接）。

## 开发先起 skill

本仓库开发一律先走 **`/app-pet`**。它是路由，会点名该加载哪个同伴 skill；清单见 [docs/framework/skills.md](docs/framework/skills.md)。

skill 的唯一副本在 `.grok/skills/`（版本控制里就这一份，Grok 和 Codex 也读它）。Claude Code 读的 `.claude/skills/` 是**生成副本**，不进 git：

```bash
bash scripts/sync-claude-skills.sh
```

- `/app-pet` 不存在（新克隆、或列表里找不到）→ 先跑这条命令，再重启对话。skill 只在会话启动时加载。
- 跑过 `npx skills update`、或手改了 `.grok/skills/` → 重跑这条命令。
- 不要直接编辑 `.claude/skills/` 下的文件，下次同步会覆盖。改 `.grok/skills/`。
- 这里不用软链接：Claude Code 对软链接的 skill 目录会报 `Unknown skill`。

## Claude Code 专属约定

- **工具**：读写文件用 Read / Edit / Write，搜索用 Grep / Glob。不要用 `cat` / `sed` / `awk` / heredoc 改文件。
- **TodoWrite**：跨三个以上文件或跨模块的任务先列 todo 再动手；单文件小改不用。
- **先给方案**：动内核（`miniprogram/core/`、`app.ts`、`app.json`、`server/app/main.py`）、拆模块、或改 API 合同之前，先说清方案再落笔。
- **subagent**：只在需要并行搜索或独立评审时开，且必须按 code-standards 的文件所有权分工，两个 agent 不写同一个文件。共享高冲突文件（`app.json`、`app.ts`、`core/`、`main.py`、[docs/api/contract.md](docs/api/contract.md)、[docs/progress.md](docs/progress.md)）由主对话串行维护，子 agent 只回报「应追加的注册项」。
- **不自动提交**：用户没说提交就不要 `git commit` / `git push`，不要改 git 配置。
- **不主动改 `docs/`**：日常改代码不动它。用户说「整理 / 总结 / 更新对接文档」再改 [docs/progress.md](docs/progress.md) 和 [docs/handoff.md](docs/handoff.md)。**改接口仍必须先改** [docs/api/contract.md](docs/api/contract.md)。
- **说话算话**：没跑过的检查不写成「已验证」。

## 本仓库现在能跑什么检查

| 想验证的 | 现状 |
|---|---|
| TypeScript | **跑不了**。仓库没装 `typescript`，`npx --no-install tsc` 会命中 macOS 自带的 TeX `tsc`。要用先 `npm i -D typescript`，否则在交接里写「未运行」及原因 |
| 页面主路径 | 只有人能在微信开发者工具打开**仓库根目录**点验。你代跑不了；需要点验时明确请用户点 |
| 后端测试 | 阶段 1 之后才有（`server/tests/`） |

所以当前的验证手段是：读 `git diff`、逐字对照 [docs/api/contract.md](docs/api/contract.md) 的 path 与字段、走 code-standards 的「提交前门禁」自查。

## 交接

子任务结束按 code-standards 的最小格式写：范围 / 已改 / 契约 / 验证 / 风险 / 下一步。**验证一栏写实际结果**，跑不了的写原因，不要留给下一位 agent 重新考古。

## 最容易踩的坑

细则见 [AGENTS.md](AGENTS.md) 的硬规则，这里只列高频翻车点：

- 页面里写 `wx.request`、写死 API 主机名、写死品牌色 hex。
- 页面没有对应的 `services/` 就当做完了。
- 改字段不先改 [docs/api/contract.md](docs/api/contract.md)。
- 往 `core/mock.ts`、`core/request.ts`、`app.ts` 这些调度入口里加产品分支（积分 / 帖子 / 相册）。它们的行数参考线比业务文件更严。
- 新建已作废的模块名 `pet` / `journal` / `ledger` / `reminder`，或改已锁定的 tab 路径。
- 现在去搭可运行的 FastAPI —— 阶段 F 不做。
