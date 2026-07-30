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
- Server 暴露的原语：**Tools**（模型决定调）/ **Resources**（应用/用户决定的只读上下文）/ **Prompts**（用户显式触发的模板），另有 **Sampling / Elicitation**（server 反向发起）
- 通信方式（规范里只有两种）：**stdio**（本地子进程，一行一条消息，**server 往 stdout 打日志就把协议弄坏了**）/ **Streamable HTTP**（远程，**单端点** `/mcp` 同时支持 POST 和 GET，按需升级 SSE）
  - ⚠ 旧的 **HTTP+SSE 双端点**（`GET /sse` + `POST /messages`）已在 `2024-11-05` 后废弃 —— 它强制常驻长连接、socket fd 锁在单进程里，无法水平扩展也不兼容 serverless
- 消息格式：JSON-RPC 2.0（选它是因为**对称双向** —— server 也能反向发 request；且**传输无关**）
- 鉴权（HTTP）：OAuth 2.1，**MCP server 是 resource server 不是 authorization server**；401 + `WWW-Authenticate` → Protected Resource Metadata 发现授权服务器 → authorization code + 强制 PKCE + RFC 8707 `resource` 参数。两条铁律：**校验 token audience 是自己**、**绝不把 client 的 token 透传给上游**（confused deputy）
- 类比 USB-C 统一接口；本质是 **N 应用 × M 工具 → N+M**

→ 详细问答 [[Agent问题答案/MCP与协议]]（Q23 传输 / Q44 工具封装 / Q45 原理对比 / Q46 缺点 / Q47 流式）

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

### LCEL 链式 vs LangGraph 图编排

> ⚠ **别把它说成"LangChain vs LangGraph 二选一"** —— LangGraph 本身就是 LangChain 生态的一部分，`create_agent` 就构建在 LangGraph 上。真正的对比是 **LCEL（`prompt | model | parser` 链式写法）vs 图编排**。

| | LCEL 链式 | LangGraph 图 |
|---|---|---|
| 形状 | 有向无环管道，单向流 | 图（节点 + 条件边 + 环）|
| 每步能看到什么 | 只有上一步的输出 | 全图共享的 State |
| 循环 | ✗（DAG 表达不了 agent 的 while 循环）| ✅ 节点回环 + `recursion_limit` |
| 并行归并 | 固定字典合并 | ✅ 自定义 reducer |
| 动态并行 | ✗ | ✅ `Send`（运行时决定开几路）|
| 可恢复 | ✗ | ✅ Checkpointer 断点续跑 + time travel |
| Human-in-loop | ✗ | ✅ `interrupt()` 任意节点暂停 |
| 流式粒度 | token | ✅ 七种 `stream_mode`（节点/token/自定义/checkpoint/task）|

**判据**：需要环、需要跨步骤共享状态、需要中途暂停 → 图；单向数据变换管道 → LCEL 够了。
**金句**：**LCEL 管「一步怎么算」，LangGraph 管「步与步之间怎么走」** —— 节点内部照样写 `chain = prompt | model | parser`。

**v1 之后的选型阶梯**：单步变换 → LCEL；标准 ReAct agent → `create_agent()` + Middleware（内置摘要 / 人工确认 / 工具重试 / 模型 fallback / 限流 / PII 检测）；复杂多 agent 编排 → 手写 `StateGraph`。

→ 工程细节（State/BSP/Checkpoint/流式/重试降级）见 [[LangGraph工程实践]]

### MCP vs Function Calling vs Skill

| | MCP | Function Calling | Skill |
|---|---|---|---|
| 性质 | 跨厂协议 | 模型能力 | 能力包格式 |
| 谁拥有 | Anthropic 开源标准 | 各 LLM 厂商内置 | Anthropic 约定 |
| 关系 | FC 是底层；MCP 是更上层规范 | MCP 之下用 FC 实现 tool 调用 | 内可包含 MCP / FC 调用 |

不冲突；并行存在。

## 易错点（高频追问）

- **MCP 和 Function Calling 哪个好？** —— 不冲突，层级不同。**MCP 没有改变模型调工具的机制**，只改了"工具从哪来、在哪跑"
- **LangChain SequentialChain 能做循环吗？** —— 不能，必须 LangGraph
- **Tool 越多越好？** —— 错；Token 占用 + 选择准确率下降。详 [[Agent问题答案/MCP与协议]]
- **Multi-Agent 默认怎么做？** —— 默认串行，避免并行 race；显式声明并行。但注意在 LangGraph 里 **BSP 超步模型下并行节点本身没有内存竞态**，要防的是副作用不幂等（详 [[LangGraph工程实践]]）
- **Tool 选择不准怎么办？** —— 优先优化 description（不要"处理数据"模糊词，并且要写清**什么时候不用**），少改模型
- **MCP 现在还有 SSE 传输吗？** —— 规范里只有 stdio 和 Streamable HTTP，旧双端点 SSE 已废弃。答"三种传输"会显得停留在旧版本
- **MCP 返回结果支持流式吗？** —— 传输层支持，**但 `tools/call` 的返回值不支持增量返回**。陷阱题，详 [[Agent问题答案/MCP与协议#Q47]]
- **MCP 里 tool description 可信吗？** —— 不可信。它是一段 server 完全控制的 prompt 且**不签名**，可以在你信任之后被改掉（rug pull）

## 深入阅读

- 答题分册：[[Agent问题答案/README]]（43 题 + Q44-Q52 增补，分主题）
- 工程实践：[[LangGraph工程实践]] —— State/BSP/Checkpoint/流式/重试降级/选型
- raw 笔记本：
  - [[专栏/Agent/OpenClaw 笔记]] —— Agent 调用链 / Skill Router / Task Planner
  - [[专栏/Agent/MCP_SSE_文档]] —— MCP 协议详解
  - [[专栏/Agent/MCP与Tool管理]] —— Tool 太多怎么办
  - [[专栏/Agent/Skills]] —— Skill 包格式
  - [[专栏/Agent/Harness Engineering]] —— OpenAI / Anthropic 的 Harness 实战（上下文管理 / 验证器 / 生成-评估循环）
  - [[专栏/Agent/RAG到Agent进阶]] —— RAG → ReAct / Plan-Execute / LangGraph State 的演化路径
  - [[专栏/Agent/什么时候选择多智能体]] —— Anthropic 多 Agent 设计指南
- 原始 Q 清单：_Agent相关问题_（已移除）
- 真题来源：[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]] · [[小红书/小红书产品工程师一面面经]] · [[微软/Bing图像视频业务实习一面面经]] · [[字节/国际商业化/面经记录_国际商业化创业_3.9]] · [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]]（MCP 五连问 + LangGraph 四连问）
