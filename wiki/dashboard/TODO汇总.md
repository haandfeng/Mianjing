---
title: TODO 汇总
type: dashboard
updated: 2026-05-05
---

# TODO 汇总

> 全 wiki 未完成 checkbox 聚合视图。装 [[插件设置#3. Tasks（可选但推荐）|Tasks 插件]] 后表格自动渲染。

## 全部未完成任务（Tasks 插件）

```tasks
not done
path includes wiki/
sort by due, path
```

## 按文件分组（Dataview 备用版）

```dataview
TASK
FROM "wiki"
WHERE !completed
GROUP BY file.link
```

## 仅工作流的待办

```tasks
not done
path includes wiki/工作流
```

## 仅复盘里的"行动项"

```tasks
not done
path includes wiki/复盘
```

## wiki-gap 标记（待补的考点）

```dataview
LIST
FROM "wiki" AND #wiki-gap
```

> 复盘文件里"完全没准备到的"题被打上 `#wiki-gap`，找出来一起补。

---

## 用法

- 周末复盘第 1 步先看本页——所有未完成任务一目了然
- Tasks 插件支持点击任务前的方框直接打勾，会同步原文件
- Tasks 不能打勾的，请在原文件里手动改 `- [x]`

## 维护

任务完成后：
1. 直接点本页方框（如果有 Tasks 插件）
2. 或回到原文件 `- [ ]` → `- [x]`
