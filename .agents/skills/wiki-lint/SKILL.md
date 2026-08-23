---
name: wiki-lint
description: 跑面经 wiki 的健康检查 —— 双链断链、TODO 标记、跨公司高频考点覆盖度、文件分布概览。当用户说"lint wiki / 检查 wiki / wiki 健康度 / 跑健康检查"时触发。
---

# wiki-lint

跑 `wiki/scripts/lint_wiki.py`，把结果直接报告给用户。

## 执行步骤

1. `python3 wiki/scripts/lint_wiki.py`（在仓库根目录）
2. 把脚本输出原样粘给用户
3. 如果有断链：
   - 列出最高频的 5 个断链目标
   - 主动提议自动修复方案（grep 出真实存在的相近文件名）
   - 等用户确认后再修
4. 如果有 TODO ≥10 个，提议清理 backlog 的优先级

## 何时主动跑

- 用户每次让你新加面经 / 修改主题文章后，跑一次确认 wiki 一致性
- 用户问"wiki 现在状态如何 / 还有什么 TODO 没做"时
- 用户问"哪些考点该建专题但还没建"时（覆盖度数据可回答）

## 不要做

- 不要在 lint 输出之外 paraphrase / 总结 —— 用户要看原始数据
- 不要自动 git commit —— lint 仅检查
- 不要修改 raw 层文件
