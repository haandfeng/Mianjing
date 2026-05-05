---
title: Agent问题答案 / Agent设计
type: answers
updated: 2026-05-04
---

# Agent 设计（项目背景 / 推理模式 / 调用流程 / 多 Agent / 范式）

> 涵盖：Q1、Q3、Q4、Q10、Q13、Q16、Q18、Q22、Q30、Q31。
> 主参考：[[Agent技术专栏/OpenClaw 笔记]]、[[Agent设计模式与MCP]]、[[西门子RAG]]、[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]。

---

## Q1 — 为什么做 Agent 项目

> 原题：为什么做 Agent 项目

**答题骨架**

- **业务驱动**：西门子 CT 机操作文档过厚（百页级英文 + 中文），现场工程师在线翻文档效率低。
- **技术契合**：医疗器械文档强结构、强领域术语，正好适合 RAG + 工具调用的 Agent 形态。
- **个人路径**：在用友做完后端 + 数据迁移后想往 LLM / Agent 方向延伸，已有的 RAG 框架（基于 LangChain Chat）正好是入口。
- **价值闭环**：上线到学城后月访问几千次，准确率从 76% 提到 92%，能形成一个 STAR 完整闭环的简历项目。

**拓展双链**：[[西门子RAG]]、[[wiki/我的简历/西门子实习]]

---

## Q3 — 讲下 Agent 项目

> 原题：讲下 Agent 项目

**答题骨架（STAR）**

- **S 场景**：组里已有基于 LangChain Chat 的基础 RAG（ES + 单链路），上游开源框架停止维护，无评测体系，效果不达上线标准。
- **T 目标**：搭评测流水线 → 重构 ETL / embedding → 提升回答准确率到可上线水平。
- **A 动作**：
  - LangSmith 测试流水线（200+ 中英文标准问答）跑出基线 76%。
  - 重写 ETL（XML→Markdown 嵌套表格、增量更新、多模型适配）。
  - 模型升级 BGE-M3 → 千问3，向量库 ES → Milvus（4096 维 + 稀疏向量）。
  - 多路混合检索（千问3 dense + BGE-M3 sparse + BM25）+ Reranker。
  - Query Refine 中英文同义词改写解决术语 gap。
- **R 结果**：准确率 76% → 92%，相关度 / 忠实度 99%+，已上线学城。

**拓展双链**：[[西门子RAG]]、[[wiki/我的简历/西门子实习]]、[[Agent问题答案/RAG]]

---

## Q4 — Agent 项目开发的框架

> 原题：Agent 项目开发的框架

**答题骨架**

- **编排**：LangGraph 做有状态图编排，节点 = Query Refine / 检索 / 重排 / 生成；边带条件，支持 checkpoint 与人工 review 中断。
- **组件**：LangChain 做胶水（Prompt 模板 / Chat Model / Output Parser），底层 LLM / Embedding / Milvus 经常自己直接调 SDK，框架封装够不够看场景。
- **可观测**：LangSmith trace + eval；正式产品考虑字节扣子（Coze）做内部部署。
- **MCP**：用 OpenManus 的 MCP Client / Server 实现，工具被重命名为 `mcp_<server_id>_<tool>` 加进 Agent 工具集。
- 经验：复杂生产系统通常自己控制底层实现，框架只用来快速搭原型 / 状态管理。

**拓展双链**：[[Agent设计模式与MCP]]（LangChain vs LangGraph 对比表）、[[西门子RAG]]（Q16）

---

## Q10 — Agent 项目背景

> 原题：Agent 项目背景

**答题骨架**

- **客户**：西门子医疗（Healthineers），目标产品是 CT 机现场操作助手。
- **痛点**：旧版本只是 RAG 单跳问答，效果差且没评测；机型多，文档多语言，工程师线下查找效率低。
- **数据**：文档来自测试中心，分中英文，按机型隔离权限。
- **上线场景**：内部学城（培训系统），日活 / 月活属于内部规模，月几千次。
- **合规约束**：医疗行业数据不能出公网，模型必须开源自部署（最终选 DeepSeek 671B）。

**拓展双链**：[[西门子RAG]]、[[公司/小红书]]（同领域参考）、[[wiki/我的简历/西门子实习]]

---

## Q13 — 推理模式的差异化设计

> 原题：推理模式的差异化设计

**答题骨架**

- **直答型**：单跳问答，prompt 内嵌检索结果直接生成；适合医疗 RAG 这种"答案需可追溯"的场景。
- **ReAct**：Reasoning + Acting 循环，模型每轮决定 think / act / observe；适合多工具串行的任务。
- **Plan-and-Execute**：先生成计划再执行，适合任务边界清楚但步骤多。
- **ToT / Self-Refine**：树搜索 / 反思迭代，适合需要尝试多个解的难题。
- **差异化原则**：用最简单能解决问题的模式；准确性敏感场景优先确定性流程（写死调用 RAG），灵活性场景才放权给模型。

**拓展双链**：[[Agent问题答案/Agent设计#Q16]]、[[Agent技术专栏/OpenClaw 笔记]]（Skill Router 决策框架）

---

## Q16 — Agent 推理模式

> 原题：Agent 推理模式

**答题骨架**

- **ReAct = Reasoning + Acting**：Think → Act → Observe → Think... 直到完成或达上限。
- **实现要点**（蔚来面经 OpenManus 代码）：
  - 模板方法：BaseAgent 定义 `run()` 循环骨架，子类实现 `step()`。
  - ReActAgent.step() 内部调 `think()` 决策 + `act()` 执行。
  - ToolCallAgent.think() 调 LLM ask_tool，传 messages + tools schema，返回 tool_calls。
  - act() 遍历 tool_calls 执行 → 工具结果作为 tool message 写回 memory → 下一轮 think 看到。
- **终止条件**：达 max_steps（默认 20）、模型输出 final answer、显式调 terminate 工具。
- **防卡死**：检测连续多轮无新增信息（is_stuck）就强制结束并兜底。
- **观察存储**：所有 tool_call 与 result 都进 Memory.messages，下一轮 think 拿到完整对话历史。

**拓展双链**：[[Agent技术专栏/OpenClaw 笔记]]（Agentic Loop 节）、[[Agent设计模式与MCP]]、[[Agent问题答案/Agent设计#Q13]]

---

## Q18 — 多 Agent 执行策略的智能选择和切换机制设计

> 原题：多 Agent 执行策略的智能选择和切换机制设计

**答题骨架**

- **Supervisor 模式**：一个调度 Agent 拿到 query 后路由到专门的 sub-agent；每个 sub-agent 只持有自己领域的工具，减小 prompt 体积、提升选择准确率。
- **路由决策**：先硬规则关键词匹配（成本最低），再轻量 LLM 兜底分类，最后才让大模型决策。
- **切换机制**：sub-agent 输出 final_answer 或 handoff 时把控制权交回 Supervisor；状态由 LangGraph 持久化，支持中断后从 checkpoint 恢复。
- **默认串行**：参考 Cognition "Don't Build Multi-Agents"，并行只在显式低风险任务（定时任务、独立子查询）开启。
- **失败兜底**：sub-agent 失败 N 次自动降级到 fallback 简单链路，避免无限循环。
- // 部分推测：Supervisor 模式来自 LangGraph 文档与 [[Agent技术专栏/MCP与Tool管理]]，"切换机制"对蔚来项目的具体落地是推测。

**拓展双链**：[[Agent设计模式与MCP]]（5. 多级 Agent 架构）、[[Agent技术专栏/OpenClaw 笔记]]（lane / 串行默认）

---

## Q22 — 举例复杂任务下执行流程

> 原题：举例复杂任务下执行流程

**答题骨架**（用西门子 RAG 的复杂查询为例）

- **示例 query**：「这个 CT 机型 X 在剂量调整时，遇到 error 0xA13 怎么处理？同时把英文操作步骤也给我。」
- **步骤 1 实体解析**：抽出机型 X、错误码 0xA13；用机型做 metadata filter。
- **步骤 2 Query Refine**：生成 5 个中英文改写版本（"剂量调整 dose adjustment"、"error 0xA13"、错误码语义化等）。
- **步骤 3 多路召回**：千问3 dense + BGE-M3 sparse + BM25 三路各取 Top 20，按机型 filter。
- **步骤 4 BGE-M3 reranker** 精排到 Top 10，LongContextReorder 把最相关的放头尾。
- **步骤 5 LLM 生成**：温度 0，prompt 强制要求引用 source；如果没找到 → 回"无法回答"。
- **步骤 6 trace**：LangSmith 记录每节点输入输出 + 耗时，失败 case 反查。

**拓展双链**：[[西门子RAG]]、[[Agent问题答案/RAG#Q14]]

---

## Q30 — 演示 Agent 项目实现细节

> 原题：演示 Agent 项目实现细节

**答题骨架**

- **代码结构**（参考 OpenManus）：
  - `agent/base.py`：BaseAgent 定义 run / step / state / memory。
  - `agent/react.py`：ReActAgent 抽象 think / act。
  - `agent/toolcall.py`：ToolCallAgent 实现工具调用版 think / act。
  - `agent/manus.py`：组合工具集 + MCP Clients + Browser Helper。
  - `tool/`：每个 BaseTool 子类是一个工具，带 name / description / parameters / execute。
  - `mcp/server.py`：FastMCP 把本地工具暴露为 MCP 服务。
- **配置**：`config/mcp.json` 列 stdio / sse 的 server，启动时自动加载并把工具加进 Agent。
- **运行**：`agent = await Manus.create()` → `agent.run(prompt)` → 内部循环 think / act 直到完成或 max_steps。
- **观察**：trace / log 写到本地 jsonl + LangSmith。

**拓展双链**：[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]（OpenManus 代码示例最详）、[[Agent技术专栏/OpenClaw 笔记]]

---

## Q31 — 了解其他的 Agent 范式吗

> 原题：了解其他的 Agent 范式吗

**答题骨架**

- **AutoGPT / BabyAGI**：早期任务循环范式，自我生成 todo list；问题是经常陷入循环，工程上很少直接用。
- **AutoGen**（Microsoft）：多 Agent 对话框架，按角色（User / Assistant / Critic）协作。
- **CrewAI**：把 Agent 抽象为"角色 + 任务"，做结构化的多 Agent 工作流。
- **LangGraph**：状态机 / 图编排，强调 checkpoint、可恢复、人工审核中断（[[Agent设计模式与MCP]] 有详细对比）。
- **OpenManus / OpenClaw**：偏工程化的开源 ReAct + MCP 实现，源码可读性好。
- **Anthropic Skill**：能力包打包格式，按 description 触发。
- **Cognition Devin**：长期任务 + 沙箱执行，强调"默认串行"和可回放转录。

**拓展双链**：[[Agent设计模式与MCP]]、[[Agent技术专栏/OpenClaw 笔记]]、[[Agent技术专栏/Skills]]

---

## 双链回到主索引

- [[Agent问题答案/README]]
- [[Agent相关问题]]
