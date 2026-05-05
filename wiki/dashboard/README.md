---
title: Dashboard 入口
type: dashboard-root
updated: 2026-05-05
note: 依赖 Dataview 插件 — 见 [[插件设置#1. Dataview ★]]
---

# Dashboard 入口

把 wiki 当数据库查。**装了 Dataview 才能看到表格**。

## 3 个核心 dashboard

| Dashboard | 干嘛 |
|---|---|
| [[面试历史]] | 所有面经按时间 / 公司 / 通过状态排表（主要看近一年）|
| [[公司爱考什么]] | 每家公司高频考点 tag 频次 |
| [[主题统计]] | 主题文章被引用次数 + raw 来源密度 |

## Dataview 极简语法

```
\`\`\`dataview
TABLE company, date, verdict
FROM "公司"
WHERE date >= date(today) - dur(365 days)
SORT date DESC
\`\`\`
```

- `TABLE` 选 frontmatter 字段做列
- `FROM "目录"` 限范围
- `WHERE` 过滤（含日期 / tag）
- `SORT` / `LIMIT`

## frontmatter 字段（要让 dashboard 能查）

| 字段 | 谁填 | 例 |
|---|---|---|
| `type` | 所有 | `面经` / `topic` / `company-profile` / `project` |
| `company` | 面经 / 公司画像 | `字节` |
| `bu` | 面经 | `财经` / `中国商业化` |
| `date` | 面经 | `2024-08-15` |
| `round` | 面经 | `一面` / `二面` / `Leader` / `HR` |
| `verdict` | 面经 | `通过` / `挂` / `未知` |
| `source` | 面经 | `我面试` / `网上转载` |
| `tags` | 面经 / 主题 | `[java, mysql, redis]` |
| `last_interview` | 公司画像 | `2026-05-05` |
| `tier` | 公司画像 | `大厂` / `中型` / `小公司` |
| `domain` | 主题 | `数据库` / `缓存` / `Java` / `Agent` |

> 用 [[模板/README]] 加新内容时模板已经把字段写好。已有文件慢慢补即可。
