# 产品文档

这里管 **做什么、对标谁、功能是否对等**。目录与接口见 [framework](../framework/overview.md)、[handoff.md](../handoff.md)。

不要把产品清单写进 `framework/`。

| 文档 | 内容 |
|---|---|
| [positioning.md](positioning.md) | 一句话、对标「萌爪日记」同类、学什么不学什么 |
| [benchmark.md](benchmark.md) | 与截图功能逐条对照（有的才做）；对标之外已批准的后期能力 |
| [capabilities.md](capabilities.md) | P0/P1/P2 实现顺序、模块边界；后期能力只排顺序 |
| [expansion.md](expansion.md) | 助手 / 问诊 / 养宠经验：模块名、边界、预留产品接口 |
| [reference/](reference/README.md) | 对标截图（只对照，不进小程序包） |

实现任何用户可见功能前，按顺序读 positioning → benchmark → capabilities。做助手、问诊、养宠经验、RAG 时再读 [expansion.md](expansion.md)。对标功能是否该做，以 benchmark 为准；这三块是否该做，以 expansion 为准。不以聊天记录为准。
