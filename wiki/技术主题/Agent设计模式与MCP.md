---
title: Agent设计模式与MCP（概念骨架）
type: topic
updated: 2026-05-05
note: 本文是概念骨架。具体问答见 [[Agent问题答案/README]] 5 个分册。
---

# Agent 设计模式与 MCP（概念骨架）

> Agent = 模型 + 工具循环 + 记忆 + 上下文管理。MCP 是 LLM ↔ 工具/数据源的标准协议。Skill 是给 Agent 装的能力包。

> ⚠ **本文只放概念骨架 + 对比表 + 易错点**。具体问答（怎么答某个面试题）请去 [[Agent问题答案/README]] 找。

## 概念地图

```
Agent
├── 模型层      : LLM (Claude / GPT / DeepSeek / 千问)
├── 工具层      : Tools (Function Calling / MCP)
├── 记忆层      : Memory (短期 conversation / 长期 vector / 文件 .md)
├── 上下文管理  : Context (window / summarization / 压缩)
└── 编排层      : 设计模式 (ReAct / Plan-Execute / Multi-Agent)
```

## 三个核心概念

### 1. MCP (Model Context Protocol)
- Anthropic 开源标准，统一 LLM 接外部工具的方式
- **Host** ↔ **MCP Client** ↔ 多个 **MCP Server**
- Server 暴露 3 类能力：**Tools / Resources / Prompts**
- 通信方式：**stdio**（本地子进程）/ **SSE**（远程长连接，`GET /sse` + `POST /messages`）
- 消息格式：JSON-RPC 2.0
- 类比 USB-C 统一接口

→ 详细问答 [[Agent问题答案/MCP与协议]]

### 2. Skill (Anthropic)
- 给 AI 装的"能力包" = `SKILL.md`（YAML 头）+ `scripts/` + `reference/` + `assets/`
- LLM 根据 description 决定是否触发
- vs MCP：MCP 是协议（拉外部能力）；Skill 是本地能力包（带 prompt + 代码）

→ 详细问答 [[Agent问题答案/MCP与协议]]（Q37 MCP vs Skill）

### 3. Agent 设计模式
- **ReAct**：Reasoning → Action → Observation 循环
- **Plan-Execute**：先 plan（拆任务），再 execute（执行）
- **Multi-Agent**：Supervisor 路由 + Worker 并行（默认串行，显式并行）
- **Reflection**：执行完反思，错了重试

→ 详细问答 [[Agent问题答案/Agent设计]]

## 关键对比表

### LangChain vs LangGraph

| | LangChain | LangGraph |
|---|---|---|
| 定位 | 通用组件库 | 有状态流程 / Agent 编排 |
| 控制流 | 链式调用 | 图（节点 + 条件边 + 循环）|
| 状态 | 自补 | 内置 + checkpoint |
| 可恢复 | ✗ | ✅ 中断后从断点恢复 |
| Human-in-loop | ✗ | ✅ interrupt 等审核 |
| 适用 | 简单 chain | 复杂多步、生产 |

实战组合：LangGraph 编排 + LangChain 组件。

### MCP vs Function Calling vs Skill

| | MCP | Function Calling | Skill |
|---|---|---|---|
| 性质 | 跨厂协议 | 模型能力 | 能力包格式 |
| 谁拥有 | Anthropic 开源标准 | 各 LLM 厂商内置 | Anthropic 约定 |
| 关系 | FC 是底层；MCP 是更上层规范 | MCP 之下用 FC 实现 tool 调用 | 内可包含 MCP / FC 调用 |

不冲突；并行存在。

## 易错点（高频追问）

- **MCP 和 Function Calling 哪个好？** —— 不冲突，层级不同
- **LangChain SequentialChain 能做循环吗？** —— 不能，必须 LangGraph
- **Tool 越多越好？** —— 错；Token 占用 + 选择准确率下降。详 [[Agent问题答案/MCP与协议]]
- **Multi-Agent 默认怎么做？** —— 默认串行，避免并行 race；显式声明并行
- **Tool 选择不准怎么办？** —— 优先优化 description（不要"处理数据"模糊词），少改模型

## 深入阅读

- 答题分册：[[Agent问题答案/README]]（43 题分主题）
- raw 笔记本：[[Agent技术专栏/OpenClaw 笔记]] · [[Agent技术专栏/MCP_SSE_文档]] · [[Agent技术专栏/MCP与Tool管理]] · [[Agent技术专栏/Skills]]
- 原始 Q 清单：[[Agent相关问题]]
- 真题来源：[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]] · [[小红书/小红书产品工程师一面面经]] · [[微软/Bing图像视频业务实习一面面经]] · [[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
