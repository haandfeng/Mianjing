> 📌 **2026-08-04 复核并补写**。原笔记（约 2026-05 记的）只覆盖了「文件结构 + 检索」，**缺了整个 dreaming 子系统**，且有两个数字在新官方文档里查不到。补写部分来源：[OpenClaw 官方 memory 文档](https://docs.openclaw.ai/concepts/memory)、[memory-config 参考](https://docs.openclaw.ai/reference/memory-config)、dreaming 配置 gist、GitHub issue。
> 三家横向对比见 [[Agent记忆四家实现对比]]。

## 1.1 工作区

默认 `~/.openclaw/workspace/`，主要包含三类内容。

### 1.2.1 身份与配置文件（通过 bootstrap 引导生成）

- `IDENTITY.md` — Agent 的名字、类型、风格、专属 emoji；初始为空，在第一个 session 由用户与 Agent 一起填
- `USER.md` — 用户/所有者的背景信息，**作为指令性指导加载**
- `SOUL.md` — Agent 的行为哲学与灵魂内核，包括边界意识、自我定调；系统鼓励 Agent 自我迭代这个文件
- `AGENTS.md` — 最核心的操作手册，规定每次会话必做的事、记忆管理策略、各种规范
- `TOOLS.md` — 环境特定的本地备忘录，记录机器相关信息（不定义工具怎么用，那是 Skills 的事）
- `HEARTBEAT.md` — 用户和 Agent 可编辑的待检清单，供 Agent 在心跳轮次时读取决定行为；为空则跳过心跳 API 调用

### 1.2.2 记忆文件：`MEMORY.md` vs `memory/YYYY-MM-DD.md`

**这两个是不同的层，不是同一层的两个文件。** 区别有四条：

| | `MEMORY.md` | `memory/YYYY-MM-DD.md` |
|---|---|---|
| **定位** | **curated 精炼层** | **working 工作层** |
| **内容** | 持久事实、偏好、**长期成立的决策**、短摘要 | 当天的流水上下文、观察、会话摘要、原始记录 |
| **加载** | **每次主会话（DM session）开始时加载** | **只有今天和昨天的自动加载**，更早的靠检索 |
| **衰减** | **不衰减（evergreen）** | builtin 引擎对带日期的日记应用**固定 30 天 recency 半衰期** |
| **谁能写** | dreaming 的 **Deep 阶段是唯一自动写入方**；人工可改 | Light 阶段、agent 自己、session-memory hook 都能写 |

> ⚠️ 官方文档明确说 `MEMORY.md` **不是**原始转录、不是日记、不是穷举归档——它是「该在主会话开场就拿到手」的那一小撮东西。**日记是原料，MEMORY.md 是成品。**

文件名还有带 slug 的变体 `memory/YYYY-MM-DD-<slug>.md`（session-memory hook 在 `/new` / `/reset` 时写的），会和纯日期文件一起被拾取。已存在的文件**追加而非覆盖**，形成可追溯的时间线。

值得注意的是 `MEMORY.md` **并非始终载入**（除主会话开场外），也走按需检索。系统提示里有一段行为指令告诉 Agent：「在回答任何涉及过往工作、决策、日期、人物、偏好或待办的问题之前，先对 `MEMORY.md` 和 `memory/*.md` 跑 `memory_search`，再用 `memory_get` 拉取需要的行。」

### 1.2.3 dreaming 的产物

- `DREAMS.md` — **纯给人看**的叙事式梦境日志
- `memory/.dreams/short-term-recall.json` — 机器状态：候选条目 + 分数
- `memory/.dreams/phase-signals.json` — 机器状态：light / REM 阶段命中计数
- `memory/.dreams/events.jsonl` — **审计日志**（跟会话转录的 jsonl 不是一回事，见 §1.6）

---

## 1.4 记忆写入：三条路径

1. **LLM 在对话中主动决定是否记录**
2. **接近压缩阈值时触发 Memory Flush** —— 压缩总结前跑一个「无声轮次」提醒 Agent 保存重要上下文。默认启用，可配置禁用。**这是三家里唯一把压缩和记忆写入耦合起来的设计**（Claude Code / Codex 都不耦合）
3. **session-memory hook**（`/new` / `/reset` 时）—— 用当前会话 JSONL 最近若干条消息让 LLM 生成摘要 slug，固化成一个新的 `.md`

---

## 1.5 检索

召回通过两个工具完成：

- `memory_get(path, from, lines)` — 读取特定文件的指定行范围
- `memory_search(query)` — 搜索并返回 top 片段（**带路径、行号、相似度分数**）

搜索使用 **hybrid search**：向量搜索（cosine similarity）+ BM25 关键词搜索（基于 SQLite FTS5 全文索引），两个分数加权融合排序。记忆会建立 embedding 索引，**在文件变更时**做 chunk & embedding。

> ⚠️ **原笔记记的具体参数：向量 70% + BM25 30%，chunk 400 token / overlap 80。**
> **2026-08-04 复核：新官方文档只说「向量相似性结合关键词匹配」，没给权重，也没提 chunk 参数。** 可能是版本变更，也可能是当时的实现细节现已不公开。**面试引用这几个数字要说清是旧版本信息。**
> <!-- 来源: 原笔记来源不可考 ・ 新官方文档未确认 ・ 复核于 2026-08-04 -->

**存储后端可选**（这是新增的）：
- **Builtin（默认）** — SQLite 基础，无额外依赖
- **QMD** — 本地优先，支持目录索引
- **Honcho** — 跨会话 AI 原生记忆
- **LanceDB** — 支持本地 Ollama 嵌入

---

## 1.6 JSONL 与 MD 的分工

**会话转录 jsonl** 存在 `~/.openclaw/agents/<agentId>/sessions/<session-id>.jsonl`（同目录还有 `sessions.json` 做索引），每行一个 JSON 对象：用户消息、工具调用、执行结果、模型响应，带 type / timestamp / role / content / usage cost。另有 `$OPENCLAW_STATE_DIR/transcripts/YYYY-MM-DD/<session>/` 下的 `transcript.jsonl` + `metadata.json` + `summary.json` + `summary.md`。

**一句话分工：JSONL 是原料（"发生过什么"，偏事实偏审计），`.md` 是沉淀结果（"该记住什么"，偏摘要偏精炼）。**

**详细机制（含 `memorySearch.sources` 把 JSONL 也纳入同一索引、`source: "sessions"` 标签、session-memory hook 的固化流程）已写在 [[专栏/Agent/OpenClaw 笔记]] 的「MD 和 Jsonl 怎么协作」一节，不重复。**

⚠️ **别把三种 jsonl 搞混**：
| 文件 | 是什么 |
|---|---|
| `sessions/<id>.jsonl` | 会话转录，崩溃恢复 + 可被索引的原料 |
| `transcripts/.../transcript.jsonl` | 按日期归档的转录 |
| `memory/.dreams/events.jsonl` | **dreaming 的审计日志**，跟对话内容无关 |

---

## 1.7 Dreaming：后台整合（原笔记完全缺失的一半）

**默认 cron `"0 3 * * *"`（每天凌晨 3 点），`dreaming.enabled` 默认 false。** 三阶段串行：

| 阶段 | 做什么 | 写哪 |
|---|---|---|
| **Phase 1 · Light Sleep**<br/>摄入与暂存 | 读近期日记 + 会话转录；**Jaccard 相似度 0.9 判重**去掉重复；候选进短期召回库；记 light 信号 | **只写日记文件，绝不写 `MEMORY.md`** |
| **Phase 2 · REM Sleep**<br/>模式提取 | 分析 lookback 窗口（默认 7 天）内的短期召回条目；**概念标签词频分析**找复现主题；识别高置信候选真相；记 REM 信号 | **也绝不写 `MEMORY.md`** |
| **Phase 3 · Deep Sleep**<br/>晋升 | 六信号加权打分 + light/REM 阶段强化加成 + 阈值门过滤 | **唯一会往 `MEMORY.md` 追加的阶段**（按日期分节） |

**Deep 阶段的六个打分信号**：

| 信号 | 权重 | 含义 |
|---|---|---|
| Relevance | 0.30 | 历次召回中的检索质量 |
| Frequency | 0.24 | 累积到的短期信号总数 |
| **Query Diversity** | 0.15 | **有多少个不同的查询语境命中过它** |
| Recency | 0.15 | 时间衰减，**14 天半衰期**（注意跟 §1.2.2 检索侧那个 30 天不是一回事） |
| Consolidation | 0.10 | 跨天复现强度 |
| Conceptual Richness | 0.06 | 概念标签密度 |

Light 阶段命中额外加最多 **+0.05**，REM 阶段 **+0.08**（都按时间衰减）。

**三重阈值门，全部通过才晋升**：`minScore ≥ 0.8`、`minRecallCount ≥ 3`、`minUniqueQueries ≥ 3`。

关键配置：
```json
{ "dreaming": {
    "enabled": false,
    "frequency": "0 3 * * *",
    "phases.light.lookbackDays": 2,      "phases.light.limit": 100,
    "phases.rem.lookbackDays": 7,
    "phases.deep.minScore": 0.8,         "phases.deep.minRecallCount": 3,
    "phases.deep.minUniqueQueries": 3,   "phases.deep.recencyHalfLifeDays": 14,
    "phases.deep.maxAgeDays": 30,        "phases.deep.limit": 10 } }
```

> 💡 **`minUniqueQueries ≥ 3` 是这套设计里最值得学的一条**：要求一条记忆被**至少 3 个不同的问题**命中过才算真知识。只被同一个问题反复命中说明它是孤立事实，不是可复用经验。**这跟 [[追问/谷歌Memory]] 里「按历史成功率联合排序」是同一类思路——都在解决「语义相似度高 ≠ 真有用」。**
> <!-- 来源: OpenClaw 官方 dreaming 文档 + 配置 gist ・ 查证于 2026-08-04 -->

---

## 1.8 已知问题（2026）

**dreaming 污染日记文件，导致 heartbeat 跳过记录** —— [#66947](https://github.com/openclaw/openclaw/issues/66947)、[#65652](https://github.com/openclaw/openclaw/issues/65652)

dreaming 把 Light Sleep / REM Sleep 阶段的块**直接写进 `memory/YYYY-MM-DD.md`**，于是 heartbeat agent 看到「今天的日记文件已存在」就跳过扫描真实会话活动——**结果是有对话的日子反而零条 agent 记录**。另有 2026.4.11 版本里 dreaming 在每次 heartbeat 都触发、产生空的 light/rem/heartbeat 会话。

> 🎯 **面试价值很高**：被问「记忆系统有什么坑」时，这比抽象地说「记忆会腐化」具体得多——**根因是后台整合和前台写入共用同一个文件，没做写入源隔离**。

---

## 双链

- wiki 主题：[[Agent记忆四家实现对比]]（Claude Code / Codex / OpenClaw 五维对比）· [[Agent记忆系统]]（七个设计维度）· [[Agent上下文压缩链路]]
- 追问库：[[追问/谷歌Memory]]
- raw：[[专栏/Agent/OpenClaw 笔记]]（Tool System / Skill Router / JSONL 与 MD 协作全文）· [[专栏/Agent/记忆压缩]]
