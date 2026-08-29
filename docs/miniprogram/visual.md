# 小程序视觉

改观感先读这份。配色、插画、组件放哪，只在这里定。信息架构、tab 路径看 [handoff.md](../handoff.md)。做 mock / 接口不要读这份，去 [api/contract.md](../api/contract.md)。

气质：**奶油水彩、圆脸腮红、留白**。插画只出现在顶图和空状态；列表用宠物照片。不抄对标品牌、插画和文案原句。

## 改一处、全站跟上

| 你要改 | 动哪里 | 不要动 |
|---|---|---|
| 颜色、圆角、阴影、字号 | `miniprogram/styles/tokens.scss` | 页面 scss 里写死 hex |
| 卡片、按钮、芯片、入口格、顶图框 | `miniprogram/styles/primitives.scss` | 每个页面复制一份 |
| 首页顶图、空状态、默认头像 | `miniprogram/assets/brand/` + `assets/paths.ts` | 页面写死另一套文件名 |
| 四个入口图、帖子动作、礼物 | `miniprogram/assets/icon/` + `assets/paths.ts` | 未选中 `react-*.png`，选中 `react-*-active.png`（like / reply / favorite / share） |
| 底栏图标 | `miniprogram/assets/tab/`（文件名锁死） | `app.json` 的 icon 路径 |
| 界面占位照片（接 mock 前） | `miniprogram/assets/mock/` | 当正式素材用 |
| 空列表 | `components/empty-state` | 页面内再画一套空状态 |
| 点赞 / 评论 / 收藏 / 转发 | `components/react-row` | 写成大色块按钮 |

`app.scss` 只 `@import` 上面两个 styles 文件。页面 scss 只写这一页的排版。

路径常量表：`miniprogram/assets/paths.ts`。换图只换文件，或只改这一份表。

## Token

写在 `page` 上，全页继承：

| 变量 | 用途 |
|---|---|
| `--color-bg` `#F7F0E6` | 纸底、顶栏 |
| `--color-card` `#FFFBF6` | 卡片、底栏 |
| `--color-primary` `#F0783C` | 主按钮、选中 |
| `--color-primary-soft` `#FDE4D4` | 浅底、提示 |
| `--color-blush` `#F5C6C8` | 少量点缀 |
| `--color-sage` `#D7E8D4` | 热聊卡 |
| `--color-text` `#3A2F26` | 正文 |
| `--color-text-muted` `#A3988E` | 辅助、未选中 tab |
| `--radius` `32rpx` | 卡片 |
| `--shadow` | 暖色浅阴影 |

原生 `switch` 的 `color` 只能写 hex，与 `--color-primary` 相同：`#F0783C`。

字：系统黑体。标题约 `36rpx / 600`，正文 `28rpx`。不装自定义字体。

Skyline：用 flex，不用 grid；滚动用 `scroll-view`；阴影用 `box-shadow`，不用 `filter: drop-shadow`。

## 素材

| 角色 | 路径 |
|---|---|
| 首页顶图（文案在 WXML，不烤进图） | `assets/brand/home-banner.jpg` |
| 角色原图（以后派生空状态） | `assets/brand/mascots.jpg` |
| 空相册 / 空广场 / 空任务 | `assets/brand/empty-*.jpg` |
| 默认头像 | `assets/brand/avatar-default.jpg` |
| 入口 | `assets/icon/entry-*.jpg` |
| 帖子动作、礼物 | `assets/icon/react-like|reply|favorite|share.png` 与 `-active`、`gift.png` |
| 底栏 5×2 | `assets/tab/<name>.png` 与 `<name>-active.png` |

底栏和表态图标用脚本画，保证 81px 清晰、两套颜色一致：

```bash
python3 -m venv .venv
.venv/bin/pip install Pillow
.venv/bin/python scripts/export-brand-icons.py
```

水彩插画（顶图、空状态、入口）是原画文件，不进脚本。换风格时先换 `mascots.jpg`，再派生空状态，并改 `paths.ts`。

## 组件边界

跨模块 UI 只放 `miniprogram/components/`：

- `page-shell` — 顶栏 + 内容槽
- `empty-state` — 插画 + 标题 + 行动
- `react-row` — 点赞 / 评论 / 收藏 / 转发

帖子卡片属于 `community`，放 `modules/community/components/post-card/`。其它模块不要 import 它。

## 明确不做

- 自定义凸起 tabBar（继续原生底栏，只换图标）
- 对标产品的插画和文案原句
- 把业务状态放进 `app.ts` / `globalData`
- 在页面里 `wx.request` 或再堆一套假数组（下一轮走 `services/`）
