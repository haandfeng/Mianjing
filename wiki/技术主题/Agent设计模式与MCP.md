---
title: Agent设计模式与MCP
type: topic
updated: 2026-05-04
---

# Agent设计模式与MCP

> Agent = 模型 + 工具循环 + 记忆 + 上下文管理；MCP 是 LLM ↔ 工具 / 数据源的标准协议；Skill 是给 Agent 装的能力包（SKILL.md + scripts + reference）。

## 高频问法
- "MCP 是什么；和 Function Calling / LangChain Tool 区别" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[小红书/小红书产品工程师一面面经]]、[[微软/Bing图像视频业务实习一面面经]]
- "MCP 通信方式（stdio / SSE）" — [[Agent相关问题]]、[[Agent技术专栏/MCP_SSE_文档]]
- "Tools 太多怎么办（token / 选择准确率）" — [[Agent技术专栏/MCP与Tool管理]]
- "Agent 设计模式 / 调用链怎么编排" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
- "LangChain vs LangGraph；什么场景选哪个" — [[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]、[[微软/Bing图像视频业务实习一面面经]]
- "Skill 是什么 / 和 MCP 区别" — [[Agent技术专栏/Skills]]、[[Agent相关问题]]
- "Agent 记忆系统设计（JSONL + .md）" — [[Agent技术专栏/OpenClaw 笔记]]
- "为什么固定调用 RAG，而不让模型选择性调用" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]
- "多轮对话怎么实现 / 长上下文压缩" — [[微软/Bing图像视频业务实习一面面经]]

## 答题骨架

### 1. MCP（Model Context Protocol）核心
- Anthropic 开源，LLM 应用 ↔ 外部工具 / 数据源 / Prompt 的标准接口
- **Host**（Claude Desktop、IDE 插件）内嵌 **MCP Client** 连多个 **MCP Server**
- Server 暴露三类能力：
  - **Tools**：可调用的函数
  - **Resources**：可读取的数据
  - **Prompts**：预定义的提示模板
- 类比 USB-C 统一了充电口；MCP 统一了 Agent 接工具的方式
- 与 LangChain Tool 区别：LangChain 是框架内抽象，MCP 是跨框架开放协议（LangChain 也已支持接 MCP）

### 2. MCP 通信方式
**stdio（本地）**：
- Agent spawn 子进程；通过子进程的 stdin / stdout 读写 JSON-RPC
- 适合本地工具（Claude Desktop 默认）

**SSE（远程）**：
- `GET /sse` 建立 SSE 长连接（接收响应）
- `POST /messages` 发送请求
- 两个端点合起来实现双向通信（SSE 是单向的 server→client）

所有消息都是 JSON-RPC 2.0 格式：
```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...} }
```

### 3. Tools 过多的两个核心问题
1. **Token 占用**：每个 tool schema 进 system prompt，几十个就几千 token
2. **选择准确率下降**：50 个 tool 比 5 个难选

**解法**（由轻到重）：
- **Tool 分组按需加载**：先判意图再载分组
- **Tool 描述优化**：写"什么时候用 / 什么时候不用"、避免"处理数据"模糊词
- **RAG 选 Tool**：把 tool 描述 embedding，按相似度 top-k
- **多级 Agent（Supervisor）**：路由到 sub-agent，每层只看到少量 tool
- **Fine-tune / Few-shot**：固定 tool 集合可微调

### 4. Agent 设计模式（OpenManus / OpenClaw 风格）
- **模板方法**：BaseAgent.run() 定义循环骨架，step() 由子类实现
- **策略模式**：不同 LLM provider / tool 调用策略可插拔
- **观察者模式**：tool 调用、状态变更通知
- **责任链 / Pipeline**：用户查询 → 实体解析 → 意图路由 → Tool 选择 → 执行 → 上下文更新

### 5. 调用链的两层路由（OpenClaw）
- **Skill Router**：硬规则关键词 + 轻量 LLM 兜底，把查询分类到任务模式（阅读 / 创作 / 检索 / 分析 / 创意）
- **Task Planner**：生成 Tool Call Plan（主工具 + 前置依赖 + 后置处理 + 回退策略）
- **Tool Selector**：相似工具间精确选择（用户偏好、内容类型、成本-质量）

### 6. LangChain vs LangGraph
| | LangChain | LangGraph |
|---|---|---|
| 定位 | 通用 LLM 应用组件库 | 有状态流程 / Agent 编排 |
| 控制流 | 链式调用 | 图（节点 + 条件边 + 循环） |
| 状态 | 自己补 | 内置 + checkpoint |
| 可恢复 | ✗ | ✅ 中断后从断点恢复 |
| 可回溯 | ✗ | ✅ 完整执行历史 |
| Human-in-loop | ✗ | ✅ interrupt 等待审核 |
| 适用 | 简单 chain | 复杂多步、长流程、生产 |

实战组合：LangGraph 编排 + LangChain 组件

### 7. Skill（Anthropic）
- 给 AI 装的能力包结构：
```
skills/pptx/
├── SKILL.md       # 入口说明书 + 触发条件 + 步骤
├── scripts/       # 可复用脚本
├── reference/     # 示例 / 模板 / 规范
└── assets/        # 字体 / 图片 / Logo
```
- SKILL.md 头部 YAML：name / description / license
- LLM 根据 description 判断是否触发该 skill
- vs MCP：MCP 是协议（拉外部能力）；Skill 是本地能力包（带 prompt + 代码 + 资源）

### 8. Agent 记忆系统（OpenClaw 模式）
- **JSONL 转录**：每行一条 JSON，原始对话日志（user message、tool call、result、response），偏审计
- **MEMORY.md / memory/*.md**：人工整理的长期事实 + 偏好，偏经验
- **统一索引**：MD 分块 + JSONL 文本块 都进 SQLite，一次 `memory_search` 同时查两类（带 source 标记）
- **沉淀机制**：`/new` 或 `/reset` 时 hook 把最近 N 条对话总结成 `memory/YYYY-MM-DD-slug.md`
- 朴素简单但可解释；缺点：旧记忆不自然遗忘，需显式版本化和有效期

### 9. RAG 在 Agent 中：固定调用 vs 选择性调用
- **固定调用**：每次都先 RAG，避免模型跳过必要检索；适合医疗 / 金融等准确性高的场景
- **选择性调用**：模型决定要不要调；灵活但有"应该调没调"风险
- 实战：医疗场景温度 = 0 + 固定调用，宁可"我无法回答"也不能编造

### 10. 长上下文 / 多轮对话
- 简单方案：达到 N 轮触发 summary，把前面对话压缩到一条 summary message
- 进阶：window memory（保留最近 K 轮）+ summary memory（前面长期记忆）
- Context Window Guard：上下文快满时压缩 / 降级 / 优雅停

### 11. 工具调用 SSE 流式事件结构（Anthropic）
- `content_block_start`：tool_use 开始
- `content_block_delta`：参数 JSON 流式片段
- `content_block_stop`：本块结束
- `message_delta`：`stop_reason: tool_use` → 模型等结果继续

## 易错点 & 追问
- "MCP 和 Function Calling 哪个更好" → 不冲突；FC 是模型能力，MCP 是协议规范工具如何被发现和调用
- LangChain SequentialChain 实现不了"分数 < 9 重新改"的循环，必须 LangGraph
- Skill 不是 MCP，Skill 是 Anthropic 的"能力包打包格式"，可包含 prompt + 脚本
- Agent 不是越多越好，Cognition "Don't Build Multi-Agents" 提醒：默认串行，显式并行
- Tool 选择准确率不够时优先优化描述（少改模型）

## 深入阅读
- Agent 专栏 [[Agent技术专栏/OpenClaw 笔记]]
- Agent 专栏 [[Agent技术专栏/MCP与Tool管理]]
- Agent 专栏 [[Agent技术专栏/MCP_SSE_文档]]
- Agent 专栏 [[Agent技术专栏/Skills]]
- 入门题集 [[Agent相关问题]]
- 真题来源 [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[小红书/小红书产品工程师一面面经]]、[[微软/Bing图像视频业务实习一面面经]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
