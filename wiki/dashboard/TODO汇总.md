---
title: TODO 汇总
type: dashboard
updated: 2026-05-05
---

# TODO 汇总

> 真实未完成任务聚合视图。
> **已过滤掉模板 / 工作流清单 / 复盘示例**这种"模板形态" checkbox（不是真 to-do）。
> 装 [[插件设置#3. Tasks（可选但推荐）|Tasks 插件]] 后表格自动渲染。

## 真实未完成任务

排除：
- `wiki/工作流/` —— 流程模板，不是 to-do
- `wiki/模板/` —— 模板骨架
- `wiki/复盘/模板.md` 与 `wiki/复盘/示例-*.md` —— 模板和示例
- `wiki/dashboard/`、`wiki/scripts/`、`wiki/health/` —— meta 层不该有 to-do

```tasks
not done
path includes wiki/
path does not include wiki/工作流
path does not include wiki/模板
path does not include wiki/复盘/模板
path does not include wiki/复盘/示例
path does not include wiki/复盘/README
path does not include wiki/dashboard
path does not include wiki/scripts
path does not include wiki/health
sort by due, path
```

## 复盘里的"行动项"

> 每场面试后产生的真任务（来自填好的复盘文件，不是模板）。

```tasks
not done
path includes wiki/复盘
path does not include wiki/复盘/模板
path does not include wiki/复盘/示例
path does not include wiki/复盘/README
```

## wiki-gap 标记（待补的考点）

> 复盘文件里"完全没准备到的"题被打上 `#wiki-gap`。找出来一起补。

```dataview
LIST
FROM #wiki-gap
```

## 推测 / 待补全的 Agent 答案

> [[Agent问题答案/README]] 里 6 道用通用知识填的题。等真题或项目积累后补具体出处。

```dataview
LIST
FROM "wiki/Agent问题答案"
WHERE contains(file.content, "推测") OR contains(file.content, "// 待补全")
```

---

## 当前状态：学习期（不在面试）

> 你现在不在面试期，TODO 汇总以"学习产出"为主，不是"准备某场面试"。
> 复盘 / 反问 / Offer 这类清单暂时不用看。

**优先做的事**（按 ROI）：
1. 看 [[Agent问题答案/README]] 6 道推测题，挑感兴趣的根据自己最新理解填
2. 翻 [[索引/高频考点榜]]，自评列改成你最新真实掌握度
3. 整理新看到的 Agent / RAG 文章 → `专栏/Agent/` 目录下新增专栏

## 用法

- 周末扫一遍本页找还没做的
- Tasks 插件支持点方框直接打勾
- 不能打勾的回原文件改 `- [ ]` → `- [x]`
