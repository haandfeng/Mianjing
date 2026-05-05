# MianJing

不知道2几fall菜鸟的面经。我的所有面试经验。

> **2025-11 哥们复活了。回来找工了。** 仓库重新整理 + 加 wiki 派生层。
> **推荐用 Obsidian 打开**。

---

## 仓库结构

```
面经/
├── 公司/         ← 13 公司面经原文（raw）
│   ├── 字节/     │   ├── 国际广告/
│   ├── 快手/     ├── 腾讯/    ├── 阿里云/
│   ├── 蚂蚁/     ├── 京东/    ├── 小红书/
│   ├── 微软/     ├── 蔚来/    ├── 虾皮/
│   ├── TT/       ├── 小鹅通/  └── 其他/   ← Cider/PingCAP/昆仑/心潮无限/...
├── 专栏/         ← 后端 / Agent / 系统设计（raw）
├── 项目/         ← 个人项目（raw，含卡码信息课程笔记）
├── wiki/         ← LLM 维护的派生层：索引/主题/公司画像/追问/算法/反问/复盘/dashboard...
├── img/          ← 图片资源
├── Excalidraw/   ← 手绘 Diagram
│
├── README.md     ← 入口
├── SOP.md        ← 30 秒上手
├── CLAUDE.md     ← Claude 配置
├── Agent相关问题.md  ← 43 题原始清单（已被 wiki/Agent问题答案/ 吸收）
└── 简历_谭演锋.pdf
```

→ 一图看懂层级关系：[`wiki/可视化/wiki鸟瞰图.md`](wiki/可视化/wiki鸟瞰图.md)

## 第一次来

1. **装 Obsidian**：[obsidian.md](https://obsidian.md/)
2. **装插件**（必装）：Dataview / Templater / Tasks —— 详见 [`wiki/插件设置.md`](wiki/插件设置.md)
3. **看说明书**：[`wiki/使用指南.md`](wiki/使用指南.md) —— 5 分钟从零上手
4. **看全貌**：[`wiki/可视化/wiki鸟瞰图.md`](wiki/可视化/wiki鸟瞰图.md) —— 一图理解结构

## 怎么贡献新面经

按 [`wiki/工作流/添加新面经.md`](wiki/工作流/添加新面经.md) 6 步走。简版：raw 文件放对目录 → 用模板写 → 同步刷新 wiki → 跑 lint → commit。

## 怎么用作面试复习

| 场景 | 文档 |
|---|---|
| 收到通知，距面 ≥ 7 天 | [`wiki/工作流/考前1周.md`](wiki/工作流/考前1周.md) |
| 距面 ≤ 24 小时 | [`wiki/工作流/考前1天.md`](wiki/工作流/考前1天.md) |
| 距面 ≤ 1 小时 | [`wiki/工作流/考前1小时.md`](wiki/工作流/考前1小时.md) |
| 面后复盘 | [`wiki/复盘/模板.md`](wiki/复盘/模板.md) 或脚本 `bash wiki/scripts/new_review.sh 字节 一面` |
| 临时查考点 | `Cmd + O` 输关键词，进 [`wiki/索引/主题.md`](wiki/索引/主题.md) |
| 算法 | [`wiki/算法/README.md`](wiki/算法/README.md) |

详细的所有场景见 [`wiki/使用指南.md`](wiki/使用指南.md)。

---

![Profile Views](https://komarev.com/ghpvc/?username=mianjing&color=58A6FF&style=for-the-badge&label=PROFILE+VIEWS)
