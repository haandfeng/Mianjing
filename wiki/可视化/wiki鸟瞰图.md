---
title: wiki 自身鸟瞰图
type: visualization
updated: 2026-05-05
---

# wiki 自身鸟瞰图

> 一张图理解 wiki 内部分层。每层职责单一，跨层的依赖只有箭头方向。

## 五层架构

```mermaid
flowchart TD
    subgraph L0["📍 入口层"]
        ROOT[wiki/README.md]
        IDX[索引/<br/>公司·主题·追问·高频考点榜]
        WORKFLOW[工作流/<br/>考前1周/1天/1小时·周末复盘·添加新面经]
    end

    subgraph L1["📜 ground truth 层"]
        RESUME[我的简历/<br/>简历PDF结构化版 + 差异表]
    end

    subgraph L2["📚 知识库层"]
        COMPANY[公司/<br/>16 公司画像]
        TOPIC[技术主题/<br/>22 八股压缩文章]
        FOLLOW[追问/<br/>5 项目 Q&A 库]
        AGENT[Agent问题答案/<br/>43 题分主题答]
        ALGO[算法/<br/>6 模板 + 真题清单]
    end

    subgraph L3["🎯 反馈层"]
        REVIEW[复盘/<br/>每场面试 30 分钟内填]
        ASK[反问/<br/>通用·按公司·历史]
        OFFER[offer.md<br/>决策对比板]
    end

    subgraph L4["🔧 meta 层"]
        VIS[可视化/<br/>雷达·时间线·地图·依赖图·本图]
        HEALTH[health/<br/>raw 去重建议]
        SCRIPTS[scripts/<br/>lint_wiki.py]
        HOOKS[".claude/hooks<br/>raw 改动自动提醒"]
        SKILL[".claude/skills/<br/>wiki-lint · 复盘"]
    end

    subgraph RAW["💾 raw 层 (仓库根目录)"]
        FACE[公司/ — 13 公司面经]
        COL[专栏/ — 后端 + Agent + 系统设计]
        PROJ[项目/ — 个人项目]
        PDF[简历_谭演锋.pdf]
    end

    ROOT --> IDX
    ROOT --> WORKFLOW
    WORKFLOW --> COMPANY
    WORKFLOW --> TOPIC
    WORKFLOW --> ALGO
    WORKFLOW --> REVIEW

    IDX --> COMPANY
    IDX --> TOPIC
    IDX --> FOLLOW

    PDF -.编译.-> RESUME
    FACE -.聚合.-> COMPANY
    FACE -.聚合.-> TOPIC
    COL -.精简.-> TOPIC
    FACE -.聚合.-> AGENT
    FACE -.聚合.-> FOLLOW
    FACE -.聚合.-> ALGO

    RESUME -.权威源.-> FOLLOW

    COMPANY --> ASK
    REVIEW -.反馈.-> COMPANY
    REVIEW -.反馈.-> IDX
    REVIEW -.反馈.-> OFFER

    HOOKS -.触发.-> WORKFLOW
    SCRIPTS -.检查.-> ROOT
    SKILL -.操作.-> SCRIPTS
```

## 解读

- **L0 入口层**：所有人（你 / Claude / 未来的接手者）从这进。READ 顺序通常 `README → 工作流（按当下场景）→ 索引/主题（按知识域）`
- **L1 ground truth**：简历 PDF 是世界观。任何 wiki 内容跟简历冲突，简历赢
- **L2 知识库**：5 个并行子库——按"看问题的视角"分（按公司 / 按主题 / 按项目 / 按 Agent / 按算法）；同一信息会被多视角索引（一个考点既出现在公司画像，也在主题文章，也在算法清单）
- **L3 反馈层**：写入而非读取。复盘 → 自评 -1 → 高频榜重排，闭环
- **L4 meta 层**：自我维护。脚本检查、hook 提醒、skill 操作

## 数据流向（实箭头 = 直接引用，虚箭头 = 编译/派生关系）

- 所有 raw（公司面经 / 专栏 / PDF）→ 通过 LLM 编译 → 进入 L1 / L2
- L1 简历 → 提供项目权威定义给 L2 追问/
- L2 知识库 → 通过 索引/ 暴露给 L0 入口
- L3 复盘 → 反向更新 L0（高频榜）和 L2（公司画像）
- L4 工具 → 监控 / 维护整个 wiki

## 一句话总结

> raw 是事实，L1-L2 是结构化整理，L0 让人能找到，L3 让 wiki 自己进化，L4 防它腐烂。
