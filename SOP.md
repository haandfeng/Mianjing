# SOP — 仓库使用 + 维护

> 这是入口提醒。**完整 SOP 在 [`wiki/使用指南.md`](wiki/使用指南.md)**。

## 30 秒上手

1. 装 Obsidian + 必装 3 个插件（Dataview / Templater / Tasks）—— [`wiki/插件设置.md`](wiki/插件设置.md)
2. 打开 [`wiki/README.md`](wiki/README.md) 找你需要的入口
3. 按场景走：
   - 距面 ≥ 7 天 → [`wiki/工作流/考前1周.md`](wiki/工作流/考前1周.md)
   - 距面 ≤ 1 小时 → [`wiki/工作流/考前1小时.md`](wiki/工作流/考前1小时.md)
   - 面后复盘 → `bash wiki/scripts/new_review.sh 字节 一面`（或 `/new-review` skill）
   - 加新面经 → [`wiki/工作流/添加新面经.md`](wiki/工作流/添加新面经.md)

## 三层入口

| 入口 | 干嘛 |
|---|---|
| [`README.md`](README.md) | 仓库整体说明 |
| 本文（`SOP.md`） | 30 秒上手 + 跳转到详细 SOP |
| [`wiki/使用指南.md`](wiki/使用指南.md) | 4 部分完整 SOP（Obsidian 操作 + 8 大场景 + 维护 + 紧急情况）|
| [`wiki/可视化/wiki鸟瞰图.md`](wiki/可视化/wiki鸟瞰图.md) | 一图理解整个仓库结构 |

## 一句话仓库结构

```
面经/
├── 公司/        ← 13 公司面经原文（raw）
├── 专栏/        ← 后端 / Agent / 系统设计（raw）
├── 项目/        ← 个人项目（raw）
├── wiki/        ← LLM 维护的派生层（索引/主题/追问/算法/反问/复盘/dashboard...）
├── img/         ← 图片资源
├── Excalidraw/  ← Diagram
├── README.md    ← 入口
├── SOP.md       ← 你在这里
├── CLAUDE.md    ← Claude 配置
└── 简历_谭演锋.pdf
```

详细见 [`wiki/可视化/wiki鸟瞰图.md`](wiki/可视化/wiki鸟瞰图.md)。
