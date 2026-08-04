---
title: Agent设计模式与MCP（概念骨架）
type: topic
updated: 2026-08-04
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

### 2. Skill (Agent Skills, Anthropic)

- 一个**目录** = `SKILL.md`（YAML frontmatter + Markdown 正文）+ 可选的附加 md / `scripts/` / 资料文件
- **frontmatter 只有两个必填字段**，但约束很具体：
  - `name`：≤ **64** 字符，只能小写字母 / 数字 / 连字符，**不能含 "anthropic" / "claude"**
  - `description`：非空，≤ **1024** 字符，**必须同时写「做什么」和「什么时候用」**——它是**唯一的触发依据**
- **核心机制：渐进披露（progressive disclosure）三级**

| 级 | 何时进上下文 | token 成本 | 内容 |
|---|---|---|---|
| **L1 元数据** | 启动就在系统提示里 | **约 100 token / skill** | `name` + `description` |
| **L2 正文** | 被触发时才读 | 官方建议 **< 5k token** | `SKILL.md` 正文 |
| **L3 资源与脚本** | 用到才读 | **没用到就是 0** | 附带文件；**脚本走 bash 执行，只有输出进上下文，代码本身不进** |

> 因为 L3 不用不花钱，**一个 skill 能捆的内容实际上没有上限**——这是官方明确讲的设计目的。

- **存放位置**：Claude Code `~/.claude/skills/`（个人）/ `.claude/skills/`（项目），文件系统直接发现；API 走 `/v1/skills` 上传（workspace 内共享）；claude.ai 传 zip（每人各自传）
- 🔴 **限制（说这些才显得真用过）**：
  - **不跨 surface 同步**——claude.ai / API / Claude Code 三边各管各的
  - **API 上跑在沙箱里：无网络、不能运行时装包**；Claude Code 里则有完整网络
  - `allowed-tools` 字段只在 Claude Code CLI 支持，且**有社区 issue 报告它被解析但没有真正强制**——**不能当安全边界用**
  - 安全模型等同于**安装软件**：只用自己写的或来自 Anthropic 的

> 📌 字段限制 / 三级 token 成本 / 沙箱限制来自 [Anthropic 官方文档](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) + [官方工程博客](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)；`allowed-tools` 不强制来自 [claude-code issue #37683](https://github.com/anthropics/claude-code/issues/37683)（社区 issue，未见官方确认）・ 查证于 2026-08-04

→ 详细问答 [[Agent问题答案/MCP与协议]]（Q37 MCP vs Skill）；真题见 [[公司/米哈游/米哈游一面（我面试）_约2026-08]] Q7/Q8

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

### 旧范式（workflow 编排）vs 新范式（agent loop）—— 比 LCEL/LangGraph 更高一层的选型

> ⚠️ 这是**范式层面**的对比，跟上面"LCEL vs LangGraph"不是一回事——上面讨论的是**同一代框架内部**的编排方式选择；这里讨论的是**要不要让人类把流程写死**。LangGraph 属于旧范式的工程实现之一；Claude Code / Codex 这类 harness 属于新范式。
> 📌 本节是一场面试现场双方讨论归纳出的分析框架，不是查证过源码的官方定义——具体机制断言仍以 [[LangGraph工程实践]] 已核实的内容为准。出处：[[公司/上海AI Lab/后训练数据/上海AI Lab后训练数据一面_2026-07-31]]

| | 旧范式（LangChain/LangGraph 式 workflow） | 新范式（Claude Code/Codex 式 agent loop） |
|---|---|---|
| 流程由谁定 | 人类先画好图/写好 if-else，模型只在节点里做局部推理 | 只给模型目标和工具，流程本身由模型自己探索 |
| 前提 | 流程可穷举 | 模型要足够聪明才能可靠 follow 复杂指令（skill 本质是一段 prompt） |
| 结果确定性 | 高，路径和产出结构可预测 | 低，两次探索路径可能不同，产出结构可能跑偏 |
| 维护成本 | 分支持续膨胀时，维护 if-else 图的成本会超线性增长 | 分支膨胀不需要改流程，但要靠校验门禁收敛不确定性 |
| 推理成本 | 通常可以用较便宜的模型 | 通常需要更聪明（更贵）的模型才能撑住自由探索 |

**选型判据（三个维度）**：
1. **流程可枚举性**——分支能穷举且数量可控 → 旧范式；分支持续膨胀或你自己说不清完整流程 → 新范式
2. **对结果确定性的要求**——需要严格 schema 保证 → 旧范式，或在新范式外面加决策树/校验门禁把不确定性收敛住
3. **模型能力与成本的匹配**——旧范式配便宜模型 vs 新范式配贵模型，算综合成本（开发+维护+推理）

**一句话**：**分支可枚举 + 要强确定性 + 成本敏感 → 旧范式；分支会持续膨胀 + 能接受用校验代替写死流程 + 模型能力和预算都够 → 新范式。**

**为什么 23/24 年只有 LangChain/LangGraph，26 年才出现新一代？** 遵不遵从指令的问题——早期模型不够聪明，没法可靠 follow 复杂 prompt/指令，只能靠人类把流程写死；模型能力提升到能可靠执行一段自然语言 skill 之后，新范式才有意义。

### MCP vs Function Calling vs Skill

| | MCP | Function Calling | Skill |
|---|---|---|---|
| 性质 | 跨厂协议 | 模型能力 | 能力包格式 |
| 谁拥有 | Anthropic 开源标准 | 各 LLM 厂商内置 | Anthropic 约定 |
| 关系 | FC 是底层；MCP 是更上层规范 | MCP 之下用 FC 实现 tool 调用 | 内可包含 MCP / FC 调用 |

不冲突；并行存在。

### MCP vs Skill（面试高频，五维展开）

**一句话对立：MCP 解决「够不够得到」，Skill 解决「会不会做」。**

| | **MCP** | **Skill** |
|---|---|---|
| 性质 | **协议**（JSON-RPC 2.0，跑在 stdio 或 Streamable HTTP 上） | **目录约定**（`SKILL.md` + frontmatter + 可选脚本/资料） |
| 要不要跑进程 | **要**，server 是独立进程或远程服务 | **不要**，就是文件，跟着 agent 一起跑 |
| 上下文成本 | **工具定义常驻**——装得多，会话还没开始就先吃掉一大块窗口 | **渐进披露**，没触发时只占约 100 token |
| 带来什么 | 新的**能力**（连数据库、发消息、读私有系统） | 新的**流程与判断**（步骤、模板、检查清单） |
| 谁决定用它 | 模型从工具列表里挑一个调 | 模型拿 `description` 匹配用户请求，决定要不要加载 |
| 安全坑 | tool description 是 server 完全控制的 prompt 且**不签名**，可被 rug pull | 带可执行代码，**只用可信来源**，恶意 skill 可致数据外泄 |

**统一起来的一句话**（自己的归纳，非官方口径）：
> **两者治的是同一个病——上下文窗口有限。MCP 把能力放到进程外，Skill 把知识放到窗口外。**

**选型**：要连活数据 / 有状态服务 / 跨应用复用 → MCP；要固化一套做事方法、模板、检查清单 → Skill；**生产系统通常两个都要**（官方口径也是互补不是替代）。

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
- 真题来源：[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]] · [[小红书/小红书产品工程师一面面经]] · [[微软/Bing图像视频业务实习一面面经]] · [[字节/国际商业化/面经记录_国际商业化创业_3.9]] · [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]]（MCP 五连问 + LangGraph 四连问）· [[公司/上海AI Lab/后训练数据/上海AI Lab后训练数据一面_2026-07-31]]（旧范式 vs 新范式选型）· [[公司/米哈游/米哈游一面（我面试）_约2026-08]]（**Skill vs MCP + Skill 特性**两连问）
