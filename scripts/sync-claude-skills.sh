#!/usr/bin/env bash
#
# 把项目 skill 的唯一副本 .grok/skills/ 同步到 Claude Code 读取的 .claude/skills/。
#
# Grok 直接读 .grok/skills/。Codex 通过 .agents/skills 软链接读同一份。
# Claude Code 不能这么接：软链接的 skill 目录会导致 /app-pet 报 Unknown skill，
# 所以这里同步出一个真实目录。
# .claude/skills/ 是生成产物，已 gitignore，改动请改 .grok/skills/。
#
# 跑完要重启 Claude Code 对话，skill 只在会话启动时加载。

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$repo_root/.grok/skills"
dest="$repo_root/.claude/skills"

if [ ! -d "$src" ]; then
  echo "找不到 $src，无法同步。" >&2
  exit 1
fi

if command -v rsync >/dev/null 2>&1; then
  mkdir -p "$dest"
  rsync -a --delete --exclude '.DS_Store' "$src/" "$dest/"
else
  # 没有 rsync 时退回复制。只删生成目录本身，路径已由上面的 repo_root 固定。
  case "$dest" in
    */.claude/skills) rm -rf "$dest" ;;
    *) echo "目标路径异常，拒绝删除：$dest" >&2; exit 1 ;;
  esac
  mkdir -p "$dest"
  cp -R "$src/." "$dest/"
  find "$dest" -name '.DS_Store' -delete
fi

count="$(find "$dest" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"
echo "已同步 $count 个 skill 到 .claude/skills/（重启对话后生效）"
