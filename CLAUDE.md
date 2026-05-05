# 面经项目配置

## 第一件事：读使用指南

**任何操作前，先读 [`wiki/使用指南.md`](wiki/使用指南.md)**。这是仓库的端到端 SOP，覆盖：
- 加新面经（录音 / 网上 copy / 手敲）→ A 章节
- 找面经 / 看公司爱考什么 → B 章节
- 学习 / 复习专题 → C 章节
- 加新专题 → D 章节
- 双链规则 / Obsidian 快捷键 / 常见 Q&A

## 仓库结构（速记）

```
公司/      ← raw 公司面经（按 公司/<公司>/<BU>/<标题>.md）
专栏/      ← raw 知识总结（后端 / Agent / 系统设计）
项目/      ← 个人项目 raw
wiki/      ← 你（Claude）维护的派生层
   ├── 公司/    16 公司画像
   ├── 技术主题/ 22 八股专题
   ├── Agent问题答案/  43 题分主题
   ├── 追问/    5 项目深挖
   ├── 模板/    含 录音转面经 等 LLM 提示词模板
   ├── 索引/    公司 + 主题
   ├── dashboard/ Dataview 看板
   └── 使用指南.md  ← SOP 入口
img/       ← 图片
简历/      ← symlink 到 /Users/ha/Documents/投递文件 (gitignored)
```

## 工作规则（精简）

1. **加新面经** → 永远从 [`wiki/模板/录音转面经.md`](wiki/模板/录音转面经.md) 起步，按它的 prompt 模板格式化
2. **加新主题** → 从 [`wiki/模板/新主题文章.md`](wiki/模板/新主题文章.md) 起步
3. **frontmatter 必填**：面经文件要有 `type/company/bu/round/date/verdict/source/tags`，公司画像要有 `last_interview/tier/passed/failed/pending`
4. **双链规范**：raw 用 `[[公司/字节/财经/字节财经一面]]`；wiki 内部用裸名 `[[Java并发集合]]`
5. **简历是 ground truth**：项目细节冲突时以 [`wiki/我的简历/`](wiki/我的简历/) 为准
6. **大批量改完跑** `python3 wiki/scripts/lint_wiki.py`（或 `/wiki-lint`）—— 0 broken 才能 commit
7. **commit 节奏**：约 10 轮对话一次，自行决定
8. **算法不在本仓库**——遇到算法相关请求只指向"另一个仓库"，本仓库不补算法内容
9. **don't add `Co-Authored-By: Claude` to commits unless 用户主动要求**

## 代码风格

When helping me with code-related tasks, strictly avoid over-engineering.
Do not introduce unnecessary abstractions, fallback mechanisms, excessive error handling, configuration layers, or speculative extensibility.

The code must be:
- Simple
- Minimal
- Direct
- Easy to read
- Strictly aligned with my stated requirements

Do not add extra features, optimizations, defensive programming patterns, or architectural generalizations unless I explicitly request them.

After writing, re-read and reflect:
- Did I introduce unnecessary complexity?
- Did I add fallback logic that was not requested?
- Did I abstract something that did not need abstraction?
- Did I generalize beyond the concrete requirement?

If any over-design exists, simplify before presenting the final answer.

Only provide the final simplified version. No extra commentary. No justification unless I ask for it.

## 当用户的指令模糊时

不要自己脑补需求，去读 [`wiki/使用指南.md`](wiki/使用指南.md) 找最近的使用场景，按 SOP 走。如果场景不在 SOP 里，问用户。
