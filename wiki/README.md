---
title: 面经 Wiki
type: wiki-root
updated: 2026-05-05
---

# 面经 Wiki

个人知识库。**4 件核心事**：

1. **面经合集** —— 我的 + 网上转载的，按公司 / BU / 时间分类，标记是否通过
2. **专题学习** —— 八股 / Agent / RAG / 项目深挖问答，方便复习和扩展
3. **模板** —— 让 LLM 从录音 / 网上 copy 生成新的面经文件
4. **面经 ↔ 专题双链** —— 互相索引

> 不在面试期。**算法在另一个仓库**，本仓库不管算法。

## 入口

| 你想干嘛 | 去哪儿 |
|---|---|
| 查公司爱考什么 | [[索引/公司]] → 对应 [[公司/字节]] 等 |
| 突击某个八股 | [[索引/主题]] |
| 全局视图（dashboard）| [[dashboard/README]] —— 装 Dataview 才有数据，见 [[插件设置]] |
| 加新面经（录音 / 网上 copy）| [[模板/录音转面经]] |
| 加新专题 | [[模板/新主题文章]] |
| 简历 ground truth | [[我的简历/README]]（PDF 在仓库根 `简历/` symlink → `/Users/ha/Documents/投递文件/`，gitignored）|

## 目录

```
wiki/
├── README.md              ← 你在这里
├── 使用指南.md            ← SOP
├── 插件设置.md            ← Dataview / Templater / Tasks
│
├── 公司/      (16)        公司画像（爱考什么 + 真题摘录）
├── 技术主题/   (22)        八股专题
├── Agent问题答案/ (6)      Agent / RAG / MCP 问答分册
├── 追问/      (5)         简历项目深挖问答
├── 我的简历/   (8)         项目权威源
│
├── 模板/      (5)         加新内容用的骨架（含录音转面经）
├── 索引/      (2)         公司 + 主题
├── dashboard/ (3)         面试历史 / 公司爱考什么 / 主题统计
└── scripts/lint_wiki.py
```

## 工作约定

- **加新面经**：从 [[模板/录音转面经]] 或 [[模板/新面经原文]] 起步 → 填好 frontmatter (date / company / bu / verdict / tags) → 放到 `公司/<公司>/` 目录
- **加新专题**：从 [[模板/新主题文章]] 起步 → raw 内容放 `专栏/后端/` 或 `专栏/Agent/`，wiki 里建对应主题文章
- **新公司画像**：[[模板/新公司画像]] → frontmatter 加 last_interview / total_rounds / passed
- **双链**：raw 用 `[[公司/字节/我的字节一面]]`；wiki 内部用裸名 `[[Java并发集合]]`

## 维护

- 大批量改完跑 `/wiki-lint`（或 `python3 wiki/scripts/lint_wiki.py`）
- 加新面经时 `.claude/hooks/wiki_refresh_hint.sh` 会提醒刷新公司画像
