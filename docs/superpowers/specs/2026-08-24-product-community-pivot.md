# 产品改向：内容小程序

- 日期：2026-08-24
- 状态：已写入 `docs/product/`、`handoff.md`、`api/contract.md`
- 范围：产品类型、模块名、页面、API 合同。不改技术栈。

## 背景

仓库先按「有猫的生活」锁了随手记、账单、提醒。用户随后提供「萌爪日记」截图，确认做成 **同一类产品**：首页门户、独立相册、图生视频、广场 / 论坛、积分。

## 决定

1. 对标对象改为截图中的「萌爪日记」同类能力。
2. 不再做随手记时间线、养宠账单、事项提醒、宠物档案模块。
3. 底栏改为：首页 / 相册 / 创作 / 论坛 / 我的。
4. 模块英文名改为：`auth` `me` `media` `album` `community` `video` `points`。
5. 不使用对方品牌名、插画、文案原句；工作标题仍为「宠物记录」。
6. 图生视频真出片放到 P2，走服务端异步 worker。

正文：[positioning.md](../../product/positioning.md)、[benchmark.md](../../product/benchmark.md)、[capabilities.md](../../product/capabilities.md)。
