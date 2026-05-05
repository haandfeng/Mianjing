---
title: Dashboard 入口
type: dashboard-root
updated: 2026-05-05
note: 全部 dashboard 依赖 Dataview 插件 — 见 [[插件设置#1. Dataview ★]]
---

# Dashboard 入口

> 这一栏是把整个 wiki 当数据库查的视图。**装了 [[插件设置#1. Dataview ★]] 才能看到表格内容**——没装的话只能看到查询代码块。

## Dashboard 列表

| Dashboard | 干嘛 |
|---|---|
| [[面试历史]] | 所有复盘按日期 / 公司 / 结果排表 |
| [[公司面试矩阵]] | 公司 × 已收集面经数 |
| [[主题文章统计]] | 22 个主题文章 + 它们的 raw 出处密度 |
| [[追问统计]] | 5 个项目 Q&A 库 + 题数 + 涉及公司 |
| [[Offer看板]] | 当前 offer 状态（也可直接看 [[offer]]）|
| [[TODO汇总]] | 全 wiki 未完成任务聚合 |
| [[最近更新]] | 这周 / 这月改了哪些 |

## Dataview 极简语法（5 分钟看懂）

```
\`\`\`dataview
TABLE field1, field2, field3
FROM "wiki/复盘"
WHERE type = "review"
SORT date DESC
LIMIT 20
\`\`\`
```

- `TABLE` 选要显示的列（来自 frontmatter）
- `FROM "目录"` 限制扫描范围
- `WHERE` 过滤条件
- `SORT ... DESC/ASC` 排序
- `LIMIT N` 限行

不会写就抄 dashboard 文件里的现成例子，改字段名就行。

## frontmatter 字段约定（让查询能查到）

| 字段 | 哪些文件填 | 例 |
|---|---|---|
| `type` | 所有 wiki 文件 | `review` / `topic` / `company-profile` / `project` / `template` |
| `company` | 复盘 / 公司画像 | `字节` / `快手` |
| `round` | 复盘 | `一面` / `二面` / `Leader` / `HR` |
| `date` | 复盘 | `2026-05-05` |
| `verdict` | 复盘 | `通过` / `挂` / `未知` |
| `tier` | 公司画像 | `大厂` / `中型` / `小公司` |
| `domain` | 主题文章 | `数据库` / `缓存` / `Java` / `Agent` |

> 加新内容时按 [[模板/README]] 走就自动有这些字段。已有文件可能缺字段——dashboard 会显示空值，**你可以慢慢补**，不影响其他列。
