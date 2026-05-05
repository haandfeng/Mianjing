---
title: Agent问题答案 / Prompt工程
type: answers
updated: 2026-05-04
---

# Prompt 工程（写法 / 多轮对话 / 关键词提取 / 实践 / 示例）

> 涵盖：Q8、Q9、Q19、Q25、Q40。
> 主参考：[[专栏/Agent/OpenClaw 笔记]]、[[西门子RAG]]、[[微软/Bing图像视频业务实习一面面经]]、[[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]。

---

## Q8 — 如何写好的 prompt

> 原题：如何写好的 prompt

**答题骨架**

- **结构化分区**：Role / Task / Context / Constraints / Output Format / Examples 六段；用 XML 标签或 Markdown 标题让模型清楚边界。
- **强约束输出**：要 JSON 就给 schema 或 example，配 structured output / json mode；要拒答就明确写"找不到 source 必须回答 'I don't know'"。
- **少示例（Few-shot）**：给 2-3 个高质量示例胜过冗长解释，特别是格式敏感任务。
- **正向 + 反向例子**：写"应该这样"和"不应该这样"，帮助模型 disambiguate。
- **动态拼装**：检索 / 工具结果作为 Context 注入，不要一股脑塞 system prompt；注意 token 预算。
- **可观测**：把 prompt 模板版本化，A/B 测试，配合 LangSmith 看哪个版本准确率更高。

**拓展双链**：[[Agent问题答案/Prompt工程#Q25]]、[[专栏/Agent/OpenClaw 笔记]]（System Prompt Builder）

---

## Q9 — 多轮对话的实现方案

> 原题：多轮对话的实现方案

**答题骨架**

- **简单方案**：把历史 messages 拼进 LLM 调用，按角色（user / assistant / tool）顺序排好；轮次少时直接喂。
- **窗口压缩**：达到 N 轮（西门子项目里是 10 轮）触发 summary，把前面所有对话压成一条 summary message + 保留最近 K 轮原文。
- **双层记忆**：window memory（最近 K 轮原文）+ summary memory（更早的总结）+ 长期 memory（向量库）。
- **OpenClaw 模式**（[[专栏/Agent/OpenClaw 笔记]]）：JSONL 转录 + MEMORY.md / `memory/*.md` 沉淀；`/new` / `/reset` 时 hook 把最近 N 条对话总结成新的 memory md。
- **Context Window Guard**：上下文快满时显式压缩 / 降级 / 优雅停，不能撑爆才知道。
- **token 估算**：单轮约 5000 token、10 轮 5 万（西门子真实数据），结合模型上下文窗选阈值。

**拓展双链**：[[专栏/Agent/OpenClaw 笔记]]（Memory 章）、[[微软/Bing图像视频业务实习一面面经]]（多轮压缩 Q）、[[西门子RAG]]（Q13）

---

## Q19 — 简历关键词提取的技术实现

> 原题：简历关键词提取的技术实现

**答题骨架**

- **结构化抽取**：先把简历切段（教育、实习、项目、技能），分别走 LLM JSON output 抽固定字段（公司、岗位、时间、技术栈）。
- **NER**：技术名词用细领域 NER 模型 / spaCy + 自建词表识别，输出 ESCO / O*NET 标签可对齐 JD。
- **Prompt 模板**：要求模型输出 `{ "skills": [...], "domain": [...], "tools": [...] }`，给 schema + 2 个示例。
- **去噪 / 同义合并**：用 embedding 把"k8s"、"Kubernetes"、"K8S"聚类合并；技能等级（熟练 / 了解）单独抽。
- **后处理**：和 JD 关键词做对齐打分（cosine + tf-idf 加权）→ 输出 match score 和缺口提醒。
> 来源说明：无直接面试出处，答案基于通用知识 + 行业代表系统（Cursor / Cody / Copilot Workspace）。

**拓展双链**：[[Agent问题答案/Prompt工程#Q8]]、[[Agent问题答案/RAG#Q26]]

---

## Q25 — Prompt 工程的实践经验

> 原题：Prompt 工程的实践经验

**答题骨架**

- **小步快跑**：一改一跑评测集，避免大改一次性回归；西门子项目里每次模型 / prompt 改动都跑 200+ 测试集。
- **System / User / Tool 分层**：System 写不变的角色与硬约束；User 放 query；Tool 结果作为 tool message 写回上下文。
- **结构化 + 指令清晰**：使用 XML tag 隔离段落（`<context>...</context>`）让模型抓 boundary；指令前置最重要的 1-2 条规则。
- **拒答 / 引用**：医疗场景明确要求"只能基于 retrieved_chunks 回答，否则回 '无法从已有知识获取相关回答'"。
- **Few-shot 选择**：example 用真实样本，覆盖正例 + 反例 + 边角 case；过多反而让模型 over-fit 到示例风格。
- **模板版本化**：和代码一起进 git，prompt 模板是工程资产不是 magic string。
- **观测 + 评估**：LangSmith trace + LLM judge + 人工抽样 double check。

**拓展双链**：[[Agent问题答案/Prompt工程#Q8]]、[[西门子RAG]]、[[专栏/Agent/OpenClaw 笔记]]

---

## Q40 — Prompt 设计示例

> 原题：Prompt 设计示例

**答题骨架**（医疗 RAG 模板示例）

```
你是西门子 CT 机操作助手。请严格基于 <context> 内的内容回答用户问题。

规则：
1. 答案必须从 <context> 推断，不允许引入外部知识。
2. 找不到相关信息时回答 "我无法从已有知识获取相关回答"。
3. 输出格式 JSON：{ "answer": "...", "sources": ["chunk_id1", ...] }
4. 答案语言跟用户提问一致；如果问题包含英文专业术语，answer 中保留原英文。

<context>
{retrieved_chunks_with_id}
</context>

用户问题：{user_question}
```

**要点解释**

- 角色 + 强约束 + 输出 schema + 拒答兜底，四件套都齐。
- `chunk_id` 用来溯源，下游可以渲染到 UI 让用户跳到原文。
- 温度 0、structured output（DeepSeek / 千问 都支持），减少格式偏移。
- 进阶：可以加 `<example>` 段做 few-shot，例子覆盖"找到答案"和"找不到答案"两种 case。

**拓展双链**：[[西门子RAG]]、[[Agent问题答案/Prompt工程#Q8]]

---

## 双链回到主索引

- [[Agent问题答案/README]]
- [[Agent相关问题]]
