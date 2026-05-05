---
title: Agent问题答案 / RAG
type: answers
updated: 2026-05-04
---

# RAG（检索 / 评估 / 动态更新 / 多阶段召回 / 推理选择）

> 涵盖：Q6、Q11、Q14、Q17、Q20、Q26、Q36、Q38、Q39、Q42。
> 主参考：[[RAG优化全链路]]、[[西门子RAG]]、[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]。

---

## Q6 — RAG 系统流程

> 原题：RAG 系统流程

**答题骨架**

- 端到端链路：文档 ETL（XML→Markdown）→ Chunk 切分 → 多路嵌入（千问3 dense + BGE-M3 sparse + BM25）→ 向量库（Milvus）。
- 查询侧：Query Refine（多语言 / 同义词扩写）→ 多路召回 Top 20 → Reranker 精排 Top 10 → Reorder / 上下文压缩 → LLM 生成。
- 检索是写死调用（医疗场景宁愿延迟也要保证召回），生成阶段温度 0 防幻觉。
- 上线后用 LangSmith trace 每个节点的输入输出 + 耗时，定位失败 case。

**拓展双链**：[[RAG优化全链路]]、[[西门子RAG]]、[[专栏/Agent/MCP_SSE_文档]]、[[向量索引-HNSW和KNN-ANN区别]]

---

## Q11 — LLM 产生幻觉的原因及解决方案

> 原题：LLM 产生幻觉的原因及解决方案

**答题骨架**

- **原因**：训练数据噪声 / 时效性差 / 长尾知识稀疏；解码端温度高 → 概率分布扁平化随机出错；上下文不完整模型靠"先验"补。
- **数据侧**：高质量 SFT + 领域知识库 + 拒答样本（teach the model to say "I don't know"）。
- **检索侧**：固定调用 RAG，把"答案来源"作为强约束注入 prompt，要求模型只能基于 source 回答，否则回"无法回答"。
- **生成侧**：温度调低（医疗 0），开 structured output，做 self-consistency / verifier 二次校验。
- **评估侧**：LangSmith Groundedness 维度专门测幻觉，不及格的 case 反查链路。

**拓展双链**：[[RAG优化全链路]]、[[西门子RAG]]（温度 0 + 固定调用）

---

## Q14 — RAG 检索优化策略

> 原题：RAG 检索优化策略

**答题骨架**

- **Chunk 优化**：层次化 + 语义边界 + 滑动窗口（10-20% 重叠），技术文档约 500 token / chunk。
- **Embedding 升级**：BGE-M3 → 千问3（4096 维），稀疏仍走 BGE-M3，BM25 关键词补盲。
- **Query Refine**：多语言改写、同义词扩写、HyDE 生成假设答案再检索。
- **多路召回 + Reranker**：dense / sparse / BM25 三路 → BGE-M3 reranker 或 RRF（业务能等就 LLM rerank，延迟敏感用 RRF）。
- **过滤元数据**：按机型 / 部门 filter，避免跨域召回干扰。
- 西门子项目准确率 76% → 92%，主要靠 ETL 重构 + 嵌入模型替换 + 多路混合 + reranker。

**拓展双链**：[[RAG优化全链路]]、[[西门子RAG]]

---

## Q17 — 跨模块错误追踪的 Agent 知识库构建方案

> 原题：跨模块错误追踪的 Agent 知识库构建方案

**答题骨架**

- **数据源采集**：把日志、trace span（OpenTelemetry）、代码库、ticket / 工单、wiki 都接入。
- **结构化抽取**：错误码、调用栈、模块名、关联 PR、热修复链接做强结构字段；自由文本部分走 RAG。
- **检索分层**：先按错误码 / stack 哈希精确召回（关键词），再做语义补全（向量召回相似 case）。
- **GraphRAG 思路**：模块之间的依赖、错误传播链建图，多跳推理"上游谁先报错"。
- **Agent 行动**：失败时自动回查最近相似 case 的 root cause + 修复 PR；写回知识库形成闭环。
> 来源说明：本题无直接面试出处，答案基于通用知识 + 蔚来面经"DevOps + Agent 落地"方向背景。

**拓展双链**：[[RAG优化全链路]]、[[专栏/Agent/OpenClaw 笔记]]（Memory MD/JSONL 沉淀模式）

---

## Q20 — RAG 评估方案

> 原题：RAG 评估方案

**答题骨架**

- **三个维度**：Correctness（与标准答案一致）、Relevance（与问题相关）、Faithfulness / Groundedness（基于检索文档，无幻觉）。
- **数据集**：测试中心提供 200+ 中英文问答（西门子项目里的真实做法）。
- **判官**：LLM judge（DeepSeek V3 不带思考），人工抽样 double check；F1 ≈ 0.8 才采信 LLM judge。
- **trace 链路**：LangSmith 存测试问答 + 每节点入参 / 返回 / 耗时，失败 case 反查具体哪一段链路出错。
- **运维**：ETL 改动 / 模型升级前都跑评测集做 AB 对比，避免回归。

**拓展双链**：[[RAG优化全链路]]、[[西门子RAG]]（Q1 / Q2 提到 76% → 92%）、[[Agent问题答案/工程化]]（Q34 复杂任务评估）

---

## Q26 — 基于代码构建知识库的 Agent 设计

> 原题：基于代码构建知识库的 Agent 设计

**答题骨架**

- **预处理**：按函数 / 类 / 文件三级切分（用 AST / Tree-sitter），每片段带 path、symbol、签名等元数据。
- **嵌入**：代码用 code-aware embedding（CodeBERT / Qwen-Code）；docstring 单独走通用 embedding。
- **多路检索**：函数名精确（BM25）、签名 / 注释语义（dense）、调用关系（图）。
- **Agent 工作流**：先理解 query → 检索相关函数 → 取上下文（调用方 + 被调方）→ 生成补丁 / 解释。
- **持续更新**：按 commit hash 做增量索引，删除被改 / 删函数的旧向量；CI 钩子触发重建。
- **代表系统**：Cursor、Sourcegraph Cody、GitHub Copilot Workspace 都是这个架构。
> 来源说明：无直接面试出处，答案基于通用知识 + 行业代表系统（Cursor / Cody / Copilot Workspace）。

**拓展双链**：[[RAG优化全链路]]、[[专栏/Agent/OpenClaw 笔记]]（Computer Use + 文件工具）

---

## Q36 — RAG 动态知识更新

> 原题：RAG 动态知识更新

**答题骨架**

- **增量嵌入**：每篇文档唯一 ID，更新时按 ID 覆盖 / 删除单条向量；避免全量重建。
- **触发模式**：手动触发（新机型上架）、定时（按权限开放时间表）、事件驱动（webhook / 消息队列）。
- **冷热分离**：高频更新走流式管道（小批量 + 异步），低频文档走批处理夜间任务。
- **失败兜底**：和正常 ETL 流水线一样要做不丢不重 + 死信队列，doc_id + chunk_index 幂等。
- 西门子项目里离线为主，配合 Ollama 异步 API + batch，吞吐提升 ×2。

**拓展双链**：[[西门子RAG]]（Q7 / Q8）、[[Agent问题答案/RAG#Q39]]（Q39 企业内部知识库持续更新）

---

## Q38 — 推理模式的选择机制

> 原题：推理模式的选择机制

**答题骨架**

- **场景驱动**：直接问答 → 单步 prompt；多步任务 → ReAct（Reasoning + Acting）；并行子任务 → Plan-and-Execute；探索性 → ToT / 自反思（Self-Refine）。
- **成本驱动**：简单查询走小模型 / 单跳；复杂查询才升级到 ReAct + 多工具循环。
- **判定信号**：query 复杂度（长度、子句数）、是否需要外部数据、是否多回合澄清。
- **Skill Router 思路**（[[专栏/Agent/OpenClaw 笔记]]）：硬规则关键词匹配 + 轻量 LLM 兜底，先走确定性路径，边缘 case 才用大模型分类。
- 不要一上来就堆多 Agent，Cognition "Don't Build Multi-Agents" 提醒：默认串行，显式并行。

**拓展双链**：[[Agent设计模式与MCP]]、[[专栏/Agent/OpenClaw 笔记]]（Skill Router）、[[Agent问题答案/Agent设计#Q13]]（推理模式差异化）

---

## Q39 — 企业内部知识库 RAG 的动态持续更新方案

> 原题：企业内部知识库 RAG 的动态持续更新方案

**答题骨架**

- **数据通道**：用 RabbitMQ / Kafka 解耦 ETL 各阶段：Q1 待解析 → 解析 worker → Q2 待嵌入 → embedding worker → Q3 待落库 → Milvus；只在队列里放 doc_id + action + ts。
- **批量推理**：Q2 用 prefetch_count = 32 + 超时 200ms 攒批，提升 GPU / NPU 利用率。
- **不丢不重**：生产者 confirm + queue / message durable + 消费者手动 ACK + 死信队列；doc_id + chunk_index 做幂等。
- **近实时观测**：监控每个队列积压量，端到端目标秒级。
- **权限隔离**：嵌入时把 ACL（部门 / 项目）作为 metadata，检索时按用户身份 filter。
- **回滚方案**：保留旧向量分区，新版本上线异常可秒级切回。

**拓展双链**：[[西门子RAG]]（Q8 钉钉知识库场景）、[[消息队列不丢不重]]、[[Agent问题答案/RAG#Q36]]

---

## Q42 — 多阶段召回策略优化

> 原题：多阶段召回策略优化

**答题骨架**

- **阶段一 粗排**：BM25 + dense 各取 Top 50，覆盖关键词 + 语义；目标召回率 95%+。
- **阶段二 融合**：RRF（每路排名取倒数相加）做初步合并，毫秒级，兼顾各路特长。
- **阶段三 精排**：Reranker（BGE-M3 / Cohere reranker）在融合 Top 30 上重排到 Top 10。
- **可选阶段 多样性**：MMR 在精排基础上去重，避免相邻 chunk 内容雷同。
- **动态终止**：相关度阈值低于阈值就停（节省 LLM token）；阈值高就直接答。
- **延迟与召回率平衡**：业务能等用 LLM reranker（10 文档 + 2s）；延迟敏感用 RRF（毫秒级）。

**拓展双链**：[[RAG优化全链路]]、[[西门子RAG]]（Q5 / Q6 多路召回 + Reranker）

---

## 双链回到主索引

- [[Agent问题答案/README]]
- _Agent相关问题_（已移除）
