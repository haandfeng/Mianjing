---
title: 模板索引
type: templates-root
updated: 2026-05-05
---

# 模板索引

> 加新内容时**永远从模板开始**——保证 frontmatter 一致、双链结构完整、未来 Dataview 查得到。

| 何时用 | 模板 | 输出文件去哪 |
|---|---|---|
| 面试结束 30 分钟内 | [[复盘/模板]] | `wiki/复盘/<日期>-<公司>-<轮次>.md` |
| 加一份新面经原文 | [[新面经原文]] | `<公司>/<方向>/<标题>.md` 或 `其他/<标题>.md` |
| 仓库出现新公司 | [[新公司画像]] | `wiki/公司/<公司>.md` |
| 出现新八股主题 | [[新主题文章]] | `wiki/技术主题/<主题>.md` |
| 项目被多家公司追问 | [[新追问QA]] | `wiki/追问/<项目>.md` |

## 怎么用模板

### 方法 1：Templater（最快）

装好 [[插件设置#2. Templater ★]] 后：
1. 新建空文件，命名好（如 `wiki/复盘/2026-05-05-字节-一面.md`）
2. 按 `Cmd + Shift + T` → 选对应模板
3. 模板内容填进来，YAML 已自动补好日期 / 标题

### 方法 2：复制（不装插件也行）

1. 打开模板文件（如 [[新面经原文]]）
2. 全选 → 复制
3. 新建目标文件 → 粘贴
4. 把 `{{...}}` 占位符替换成实际内容

### 方法 3：脚本（仅复盘）

```bash
bash wiki/scripts/new_review.sh 字节 一面
```

或在 Claude Code 里：`/new-review 字节 一面` —— 自动搞定。

## 命名约定汇总

| 类型 | 命名 | 例 |
|---|---|---|
| 复盘 | `<YYYY-MM-DD>-<公司>-<轮次>.md` | `2026-05-05-字节-一面.md` |
| 面经原文 | `{我的}<公司><方向>{一面/二面}面经.md` | `我的快手支付一面.md` |
| 公司画像 | `<公司>.md` | `字节.md` / `小红书.md` |
| 主题文章 | `<主题名>.md` | `MySQL索引与执行计划.md` |
| 追问 Q&A | `<项目名>.md` | `西门子RAG.md` / `Java-RPC框架.md` |

## frontmatter 约定

让 [[dashboard/README]] 能查到的 5 个核心字段：

```yaml
---
title: 标题（必填）
type: review | company-profile | topic | project | template | ask | sop | ...
updated: 2026-05-05
# 视类型加：
company: 字节   # type=review/company-profile 时填
round: 一面     # type=review 时填
date: 2026-05-05  # type=review 时填
verdict: 通过 / 挂 / 未知 / 待定  # type=review 时填
---
```

> 不强制——但填了之后 Dataview dashboard 就能自动渲染。
