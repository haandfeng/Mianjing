---
title: Agent问题答案 索引
type: index
updated: 2026-05-04
---

# Agent 问题答案

> 入口文档。把 [[Agent相关问题]] 里的 43 道开放题按 5 个主题归类，每题给出**答题骨架**（3-5 bullets，1-2 sentence each — 面试节奏，不写长篇）。
>
> 来源：
> - 真题：[[Agent相关问题]]
> - 参考：[[Agent技术专栏/OpenClaw 笔记]]、[[Agent技术专栏/MCP_SSE_文档]]、[[Agent技术专栏/MCP与Tool管理]]、[[Agent技术专栏/Skills]]、[[wiki/技术主题/Agent设计模式与MCP]]、[[wiki/技术主题/RAG优化全链路]]、[[追问/西门子RAG]]、[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]

## 5 个主题

| 主题 | 题号 | 文件 |
|---|---|---|
| RAG（检索 / 评估 / 动态更新 / 多阶段召回 / 推理选择） | 6, 11, 14, 17, 20, 26, 36, 38, 39, 42 | [[Agent问题答案/RAG]] |
| MCP 与协议（FC / SSE / A2A / Skill 区分 / 推理模型支持） | 7, 12, 15, 21, 23, 27, 37, 41 | [[Agent问题答案/MCP与协议]] |
| Agent 设计（项目背景 / 推理模式 / 调用流程 / 多 Agent / 范式） | 1, 3, 4, 10, 13, 16, 18, 22, 30, 31 | [[Agent问题答案/Agent设计]] |
| Prompt 工程（写法 / 多轮对话 / 关键词提取 / 实践 / 示例） | 8, 9, 19, 25, 40 | [[Agent问题答案/Prompt工程]] |
| 工程化（市面 Agent / 大模型 / 代码占比 / 长文本 / 模型预热 / NL2SQL / 评估 / IDE / AI 辅助） | 2, 5, 24, 28, 29, 32, 33, 34, 35, 43 | [[Agent问题答案/工程化]] |

## 题号 → 文件 速查

| 题号 | 题目 | 文件 |
|---|---|---|
| 1 | 为什么做 Agent 项目 | [[Agent问题答案/Agent设计]] |
| 2 | 了解过市面上有哪些 Agent | [[Agent问题答案/工程化]] |
| 3 | 讲下 Agent 项目 | [[Agent问题答案/Agent设计]] |
| 4 | Agent 项目开发的框架 | [[Agent问题答案/Agent设计]] |
| 5 | 介绍一些 AI 大模型 | [[Agent问题答案/工程化]] |
| 6 | RAG 系统流程 | [[Agent问题答案/RAG]] |
| 7 | MCP 和 Function Calling | [[Agent问题答案/MCP与协议]] |
| 8 | 如何写好的 prompt | [[Agent问题答案/Prompt工程]] |
| 9 | 多轮对话的实现方案 | [[Agent问题答案/Prompt工程]] |
| 10 | Agent 项目背景 | [[Agent问题答案/Agent设计]] |
| 11 | LLM 产生幻觉的原因及解决方案 | [[Agent问题答案/RAG]] |
| 12 | MCP 协议的核心内容 | [[Agent问题答案/MCP与协议]] |
| 13 | 推理模式的差异化设计 | [[Agent问题答案/Agent设计]] |
| 14 | RAG 检索优化策略 | [[Agent问题答案/RAG]] |
| 15 | 特定推理模型不支持 MCP 的技术原因 | [[Agent问题答案/MCP与协议]] |
| 16 | Agent 推理模式 | [[Agent问题答案/Agent设计]] |
| 17 | 跨模块错误追踪的 Agent 知识库构建方案 | [[Agent问题答案/RAG]] |
| 18 | 多 Agent 执行策略的智能选择和切换机制设计 | [[Agent问题答案/Agent设计]] |
| 19 | 简历关键词提取的技术实现 | [[Agent问题答案/Prompt工程]] |
| 20 | RAG 评估方案 | [[Agent问题答案/RAG]] |
| 21 | SSE 的局限性 | [[Agent问题答案/MCP与协议]] |
| 22 | 举例复杂任务下执行流程 | [[Agent问题答案/Agent设计]] |
| 23 | MCP 通信方式 | [[Agent问题答案/MCP与协议]] |
| 24 | 项目中 AI 贡献的代码占比 | [[Agent问题答案/工程化]] |
| 25 | Prompt 工程的实践经验 | [[Agent问题答案/Prompt工程]] |
| 26 | 基于代码构建知识库的 Agent 设计 | [[Agent问题答案/RAG]] |
| 27 | A2A 协议 | [[Agent问题答案/MCP与协议]] |
| 28 | 长文本生成的技术方案 | [[Agent问题答案/工程化]] |
| 29 | Agent skills | [[Agent问题答案/工程化]] |
| 30 | 演示 Agent 项目实现细节 | [[Agent问题答案/Agent设计]] |
| 31 | 了解其他的 Agent 范式吗 | [[Agent问题答案/Agent设计]] |
| 32 | 模型预热机制 | [[Agent问题答案/工程化]] |
| 33 | NL2SQL 场景下的 SQL 安全防护 | [[Agent问题答案/工程化]] |
| 34 | 复杂任务执行准确率提升的评估方法 | [[Agent问题答案/工程化]] |
| 35 | AI 辅助 IDE 开发工具 | [[Agent问题答案/工程化]] |
| 36 | RAG 动态知识更新 | [[Agent问题答案/RAG]] |
| 37 | MCP 和 skill 区别 | [[Agent问题答案/MCP与协议]] |
| 38 | 推理模式的选择机制 | [[Agent问题答案/RAG]] |
| 39 | 企业内部知识库 RAG 的动态持续更新方案 | [[Agent问题答案/RAG]] |
| 40 | Prompt 设计示例 | [[Agent问题答案/Prompt工程]] |
| 41 | A2A 与 MCP 区别 | [[Agent问题答案/MCP与协议]] |
| 42 | 多阶段召回策略优化 | [[Agent问题答案/RAG]] |
| 43 | AI 辅助开发的实践经验 | [[Agent问题答案/工程化]] |

## 标记说明

- 部分问题 raw 来源覆盖不充分（如 Q15 推理模型不支持 MCP 的"技术原因"、Q27 A2A 协议、Q33 NL2SQL 安全），文中以 `// 待补全：暂无 raw 来源` + **推测** 标记给出最佳近似回答，等真题 / 项目积累后补全。
- 双链命名约定：项目内 wiki = 裸名；raw 专栏 = 全路径（如 `[[Agent技术专栏/OpenClaw 笔记]]`）。
