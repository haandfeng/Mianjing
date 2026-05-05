---
title: Offer 看板
type: dashboard
updated: 2026-05-05
---

# Offer 看板

> 当前所有进行中的轮次 + 已挂 / 已通过状态。

## 当前 offer 状态

> 主表在 [[offer]]——这里是另一种视图。

## 各阶段轮次（来自复盘）

```dataview
TABLE WITHOUT ID
  company AS "公司",
  round AS "轮次",
  date AS "日期",
  verdict AS "结果"
FROM "wiki/复盘"
WHERE type = "review"
SORT date DESC
LIMIT 30
```

## 通过 / 挂 / 待定 数

```dataview
TABLE WITHOUT ID
  verdict AS "状态",
  length(rows) AS "次数"
FROM "wiki/复盘"
WHERE type = "review"
GROUP BY verdict
```

## 决策维度（从 [[offer]] 抽取）

> 维护这部分需要 [[offer]] 表持续更新。

参考决策标准：
1. **方向匹配** —— 该 offer 的工作内容跟简历强项对齐度
2. **薪资带** —— Total package
3. **地点** —— 城市 + 通勤 + 远程率
4. **团队** —— 招你的人 / 直属 leader 印象
5. **成长** —— 1 年后能学到啥

## 工作流

| 触发 | 你做 |
|---|---|
| 收到一面通知 | [[offer]] 加一行，状态 `一面待定` |
| 一面结束 | 跑 `/new-review` 建复盘，更新 [[offer]] 该行 |
| 收到 offer | [[offer]] 更新薪资 / 上班地 / 等待期 |
| 决策时 | 打开本 dashboard 全局对比 |
| 拒 / 接 | [[offer]] 更新最终结果 |

## 紧急情况

- 我面试一直没结果？→ 看本表里 `verdict: 待定` 的，挑出超过 7 天的去发邮件追
- 我有多个 offer 比不出来？→ 喊 Claude `帮我对比 X 公司 vs Y 公司 offer`
