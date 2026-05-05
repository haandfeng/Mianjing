---
title: 模板索引
type: templates-root
updated: 2026-05-05
---

# 模板索引

> 加新内容时**永远从模板开始**——保证 frontmatter 一致、双链结构完整、Dataview 查得到。

| 何时用 | 模板 | 输出去哪 |
|---|---|---|
| 我面试录音 / 网上 copy 的面经 → 标准面经 | [[录音转面经]]（喂 LLM 的 prompt 模板）| `公司/<公司>/<BU>/<标题>.md` |
| 自己手敲新面经 | [[新面经原文]] | 同上 |
| 仓库出现新公司 | [[新公司画像]] | `wiki/公司/<公司>.md` |
| 出现新八股主题 | [[新主题文章]] | `wiki/技术主题/<主题>.md` |
| 项目被多家公司追问 | [[新追问QA]] | `wiki/追问/<项目>.md` |

## 怎么用

**方法 1: Claude（最常用）**

直接说：
- "帮我用[[模板/录音转面经]]整理这段面试录音内容..."
- "用[[模板/新主题文章]]建一个新主题：xxx"

Claude 会按模板生成。

**方法 2: Templater 插件**

装好 [[插件设置#2. Templater ★]] → 新建空文件 → `Cmd+Shift+T` → 选模板。

**方法 3: 复制**

打开模板 → 全选复制 → 新建文件粘贴 → 替换占位符。

## frontmatter 必填字段

```yaml
---
# 面经文件 (raw 公司/X.md)：
company: 字节
bu: 财经
date: 2024-08-15      # 不知道写约 YYYY-MM
round: 一面            # 一面 / 二面 / Leader / HR / 未知
verdict: 通过 / 挂 / 未知
source: 我面试 / 网上转载
tags: [java, mysql, redis, 并发, ...]   # 3-8 个

# 公司画像 (wiki/公司/X.md)：
company: 字节
tier: 大厂 / 中型 / 小公司
last_interview: 2026-05-05    # 该公司最近一次面经的日期
total_rounds: 6                # 该公司总轮次数
passed: 0
failed: 1
pending: 0

# 主题文章 (wiki/技术主题/X.md)：
domain: 数据库 / 缓存 / Java / 中间件 / 网络 / Agent
tags: [...]
---
```

> 填了这些字段，[[dashboard/README]] 才能自动渲染数据。
