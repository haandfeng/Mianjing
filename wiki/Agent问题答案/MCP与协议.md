---
title: Agent问题答案 / MCP与协议
type: answers
updated: 2026-05-04
---

# MCP 与协议（FC / SSE / A2A / Skill 区分 / 推理模型支持）

> 涵盖：Q7、Q12、Q15、Q21、Q23、Q27、Q37、Q41。
> 主参考：[[Agent技术专栏/MCP_SSE_文档]]、[[Agent技术专栏/MCP与Tool管理]]、[[Agent技术专栏/Skills]]、[[Agent设计模式与MCP]]、[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]。

---

## Q7 — MCP 和 Function Calling

> 原题：MCP 和 Function Calling

**答题骨架**

- **Function Calling** 是模型层能力：模型按预定义 schema 输出工具调用 JSON，框架解析后执行。
- **MCP（Model Context Protocol）** 是 Anthropic 开源的协议层规范：定义 Host ↔ Client ↔ Server 之间用 JSON-RPC 2.0 怎么发现 tools / resources / prompts、怎么调用、怎么返回结果。
- 关系：FC 解决"模型怎么决定调"，MCP 解决"工具怎么暴露 / 跨进程跨网络通信"，可以叠加用。
- 类比：FC 是函数指针，MCP 是 USB-C 接口标准；之前每接入一个工具就要写一遍适配，MCP 让工具方实现一次 Server，所有 Host 都能用。
- 与 LangChain Tool：LangChain 是框架内抽象，MCP 是跨框架协议；LangChain 也已经支持接 MCP Server。

**拓展双链**：[[Agent设计模式与MCP]]、[[Agent技术专栏/MCP与Tool管理]]、[[Agent技术专栏/MCP_SSE_文档]]

---

## Q12 — MCP 协议的核心内容

> 原题：MCP 协议的核心内容

**答题骨架**

- **架构**：Host（Claude Desktop / IDE 插件）内嵌 **MCP Client**，连接多个 **MCP Server**。
- **Server 三类能力**：Tools（可调函数）、Resources（可读数据）、Prompts（预定义模板）。
- **消息格式**：JSON-RPC 2.0；典型 method 有 `initialize`、`tools/list`、`tools/call`、`resources/read`、`prompts/get`。
- **交互流**：握手协商版本与能力 → list 工具 → call 工具 → 持续会话 / 断开。
- **传输层**：stdio（本地子进程）/ SSE（HTTP 长连接）/ Streamable HTTP（新增），后两者支持远程。
- 实战：OpenManus 实现了完整 Client + Server，工具会被重命名为 `mcp_<server_id>_<tool>` 加进 Agent 工具集。

**拓展双链**：[[Agent技术专栏/MCP_SSE_文档]]（图示完整流程）、[[Agent设计模式与MCP]]

---

## Q15 — 特定推理模型不支持 MCP 的技术原因

> 原题：特定推理模型不支持 MCP 的技术原因

**答题骨架**

- **MCP 不是模型能力，而是 Host 端工程能力**：模型只要能输出 tool_use 格式（structured output / function calling）就可以接 MCP。
- 所谓"不支持"通常是这几种情况：
  - 模型没训练过 tool use（输出格式不稳定），需要 Host 端做 JSON 修复 / 重试，准确率差。
  - 推理模型（如某些 reasoning-only 模型）默认走纯文本 CoT，没有专门的工具调用 token 头，schema 控制差。
  - 上下文窗口太小，几十个工具的 schema 装不下 → 退化成"假装支持"。
  - 模型 provider 的 SDK 还没接 MCP（这是工程问题，非协议问题）。
- 解决：要么换支持 FC 的模型；要么用轻量包装层把 MCP 工具描述塞进 system prompt 让模型 zero-shot；要么 fine-tune 一个 tool-use head。
- // 待补全：暂无 raw 来源（推测）。可在专门面经里补"R1 / o1 系列对 tool use 支持差"等具体例子。

**拓展双链**：[[Agent技术专栏/MCP与Tool管理]]、[[Agent设计模式与MCP]]

---

## Q21 — SSE 的局限性

> 原题：SSE 的局限性

**答题骨架**

- **单向**：只能 server → client，client 想发要另开 `POST /messages`，所以 MCP 远程模式得搭两个 endpoint。
- **协议受限**：基于 HTTP/1.1 长连接，不能像 WebSocket 一样发二进制；浏览器原生 EventSource 只支持 GET，没法带 body。
- **代理 / CDN**：很多反向代理默认会缓冲 / 关闭长连接，需要专门配 `proxy_buffering off`、`X-Accel-Buffering: no`。
- **断线重连**：要客户端实现 `Last-Event-ID` 续传，否则丢消息。
- **并发上限**：浏览器对同一 origin 的 SSE 连接有上限（HTTP/1.1 ~6 个），HTTP/2 才能突破。
- 替代：长任务 / 双向高频用 WebSocket；只读流用 SSE 仍然最简单。

**拓展双链**：[[Agent技术专栏/MCP_SSE_文档]]（fetch + ReadableStream 突破 GET-only 限制）

---

## Q23 — MCP 通信方式

> 原题：MCP 通信方式

**答题骨架**

- **stdio（本地）**：Agent 作为父进程 spawn 子进程；通过子进程的 stdin / stdout 读写 JSON-RPC，零网络、低延迟、自动启动。
- **SSE（远程）**：`GET /sse` 长连接接收 server push；`POST /messages` 发请求；两端拼起来实现双向。
- **Streamable HTTP**（较新）：单 endpoint 支持双向，更接近 WebSocket 体验。
- **选型**：本地工具 / Claude Desktop 默认 stdio；跨机器 / 多客户端共享走 SSE 或 Streamable HTTP。
- 配置示例（OpenManus `config/mcp.json`）：`type: "stdio"` 配 command + args；`type: "sse"` 配 url。

**拓展双链**：[[Agent技术专栏/MCP_SSE_文档]]、[[Agent设计模式与MCP]]

---

## Q27 — A2A 协议

> 原题：A2A 协议

**答题骨架**

- **A2A（Agent2Agent）** 是 Google 2025 年开源的多 Agent 协作协议，目标是解决"Agent 之间如何发现 / 通信 / 协作"。
- **核心抽象**：Agent Card（自描述：能力、技能、endpoint）；Tasks（带状态机的工作单元）；Messages / Artifacts（消息和产物）。
- **传输**：HTTP + JSON-RPC + SSE，复用 MCP 已熟悉的链路。
- **典型流程**：A 通过 well-known URL 拉 B 的 AgentCard → 创建 Task → 发 message → 订阅 Task 状态流 → 拿 Artifact。
- **和 MCP 的分工**：MCP 是 Agent ↔ Tool；A2A 是 Agent ↔ Agent；可叠加，外层 A2A 调度，内层 MCP 取数据。
- // 待补全：暂无 raw 来源（推测）。本节内容基于 Google 公开 spec，等真题积累再补面试细节。

**拓展双链**：[[Agent问题答案/MCP与协议#Q41]]、[[Agent设计模式与MCP]]

---

## Q37 — MCP 和 skill 区别

> 原题：MCP 和 skill 区别

**答题骨架**

- **MCP** 是协议：规定 Agent 如何**远程**发现和调用 tools / resources / prompts；强调"接入外部能力"。
- **Skill** 是 Anthropic 的能力包打包格式：本地目录 `skills/<name>/` 含 `SKILL.md`（带 YAML frontmatter）+ `scripts/` + `reference/` + `assets/`。
- **触发机制**：MCP 工具一直在 prompt 里描述；Skill 用 description 让模型按需触发，不触发就不占 token。
- **执行环境**：MCP 工具跑在 Server 端进程；Skill 由 Agent 在本地按 SKILL.md 步骤执行（可以调脚本、读模板）。
- **类比**：MCP = "外部 API 服务"；Skill = "内置技能包 / 插件"。两者可以并存：Skill 调脚本 → 脚本里再走 MCP 拿外部数据。

**拓展双链**：[[Agent技术专栏/Skills]]、[[Agent技术专栏/MCP与Tool管理]]、[[Agent设计模式与MCP]]

---

## Q41 — A2A 与 MCP 区别

> 原题：A2A 与 MCP 区别

**答题骨架**

- **定位不同**：MCP 是 Agent ↔ Tool / Data，A2A 是 Agent ↔ Agent。
- **抽象单位**：MCP 有 Tools / Resources / Prompts；A2A 有 AgentCard / Task / Message / Artifact。
- **状态模型**：MCP 单次调用为主（tools/call），无状态；A2A 任务有完整生命周期（submitted → working → completed / failed），支持长任务和流式 Artifact。
- **能力发现**：MCP 通过 `tools/list` 拉清单；A2A 通过 well-known URL 发布 AgentCard 自描述。
- **协同**：A2A 在外层做多 Agent 编排，每个 Agent 内部仍可走 MCP 调工具，两层协议各司其职。
- // 待补全：暂无 raw 来源（推测）。

**拓展双链**：[[Agent问题答案/MCP与协议#Q27]]、[[Agent设计模式与MCP]]

---

## 双链回到主索引

- [[Agent问题答案/README]]
- [[Agent相关问题]]
