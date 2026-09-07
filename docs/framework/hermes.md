# Hermes Agent 在本仓库

Hermes 在本仓库的专属机制。**规范正文仍在 [AGENTS.md](../../AGENTS.md) 和 `docs/`**，不要在这里另写一套。

Grok / Codex / Claude Code / Hermes 共用同一份规则和同一份 skill。skill 的唯一副本是 [`.grok/skills/`](../../.grok/skills/)，清单 [skills.md](skills.md)。

## 每次对话开始

1. 读 [AGENTS.md](../../AGENTS.md)（硬规则 +「先读哪份」）。Hermes **会自动加载它**。
2. 读 [docs/progress.md](../progress.md)，做当前阶段的事。
3. 开发走 **`/app-pet`**。项目 skill 只在**新开的会话**里出现；trust 或改 skill 之后不要指望当前对话立刻刷新。

## 为什么不建 `.hermes.md` / `HERMES.md`

Hermes 的项目上下文是 **first match wins**，只加载一份：

1. `.hermes.md` / `HERMES.md`（从 cwd 走到 git 根）
2. `AGENTS.md`（cwd）
3. `CLAUDE.md`
4. `.cursorrules`

根目录一旦有 `.hermes.md` 或 `HERMES.md`，`AGENTS.md` 就不会进系统提示。本仓库的唯一入口是 `AGENTS.md`，禁止另起一份把路由表再抄一遍。

## 项目 skill 怎么接

官方会扫两个目录（需本机 trust 之后才加载）：

| 目录 | 本仓库 |
|---|---|
| `.hermes/skills/` | **不要建**。和下面指向同一棵树会扫两遍 |
| `.agents/skills/` | 已有，软链接 → `../.grok/skills`（Codex 共用） |

本机第一次（或新克隆后）在仓库根目录跑：

```bash
hermes skills trust
```

它只改 `~/.hermes/config.yaml` 的 `skills.trusted_project_dirs`，不改仓库。不要手改 `config.yaml`。撤销：`hermes skills untrust`。

没 trust 时项目 skill 不会进会话；CLI 会提示有 skill 但未加载。trust 过的仓库里，项目 skill 优先于 `~/.hermes/skills/` 里的同名 skill。

改 skill 只改 `.grok/skills/`。不要在 `.agents/skills/`、`.claude/skills/` 或 `~/.hermes/skills/` 另放一份 `app-pet`。

## Hermes 专属约定

- **工具**：读写用 `read_file` / `patch` / `write_file`，搜索用 `search_files`。不要用 `cat` / `sed` / `awk` / heredoc 改文件。
- **先给方案**：动内核（`miniprogram/core/`、`app.ts`、`app.json`、`server/app/main.py`）、拆模块、或改 API 合同之前，先说清方案再落笔。
- **并行**：两个 agent 不写同一个文件。共享高冲突文件由主对话串行维护，见 [code-standards.md](code-standards.md)。
- **不自动提交**：用户没说提交就不要 `git commit` / `git push`。
- **不主动改 `docs/`**：日常改代码不动它。用户说「整理 / 总结 / 更新对接文档」再改进度和对接。**改接口仍必须先改** [api/contract.md](../api/contract.md)。Agent 入口变化时才改 [progress.md](../progress.md)。
- **说话算话**：没跑过的检查不写成「已验证」。

## 本仓库现在能跑什么检查

| 想验证的 | 现状 |
|---|---|
| TypeScript | **可跑** `npm run typecheck` |
| 页面主路径 | 只有人能在微信开发者工具打开**仓库根目录**点验 |
| 后端测试 | 阶段 1 之后才有（`server/tests/`） |

验证：`npm run typecheck`、读 `git diff`、逐字对照 [api/contract.md](../api/contract.md)、走 code-standards 的提交前自查。

## 最容易踩的坑

- 在仓库根建 `.hermes.md` / `HERMES.md`，把 `AGENTS.md` 盖掉。
- 再建 `.hermes/skills` 软链接，和 `.agents/skills` 重复扫描。
- 没跑 `hermes skills trust`，会话里没有 `/app-pet`。
- 把项目 skill 复制进 `~/.hermes/skills/`，和仓库副本分叉。
