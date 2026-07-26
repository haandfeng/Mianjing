OpenClaw 的工作区（默认 `~/.openclaw/workspace/`）主要包含两类内容：

### **1.2.1** **身份与配置文件**（通过 bootstrap 引导生成，见 1.3）：

- `IDENTITY.md` — Agent 的名字、类型、风格、专属 emoji；初始为空，在第一个session由用户与Agent一起填
- `USER.md` — 用户/所有者的背景信息
- `SOUL.md` — Agent 的行为哲学与灵魂内核，包括边界意识、自我定调等；系统鼓励Agent自我迭代这个文件
  
- `AGENTS.md` — 代理最核心的操作手册，规定了每次会话必做的事，记忆管理策略，各种规范等。
  
- `TOOLS.md` — 一个环境特定的本地备忘录，记录机器相关信息，不定义工具怎么用（这是Skills的定义）
  
- `HEARTBEAT.md` — 用户和Agent可编辑的待检清单，供Agent在心跳轮次时读取决定行为，为空则跳过心跳API调用





### **1.2.2** **记忆文件**（`MEMORY.md` 与 `memory/*.md`）

其中 `memory/*.md` 会在 Memory Flush 时按日期写入（`memory/YYYY-MM-DD.md`），已存在文件会追加而非覆盖，形成可追溯的时间线记忆。

值得注意的是即使MEMORY.md 并非始终载入。 也走的是按需语义检索。系统提示里有一段行为指令告诉代理："在回答任何涉及过往工作、决策、日期、人物、偏好或待办的问题之前，先对 MEMORY.md 和 memory/*.md 跑 memory_search，再用 memory_get 拉取需要的行。"。

‘

## 1.4 记忆写入与召回写入有两条路径，本质都是对以上文件的更新

- LLM 在对话中主动决定是否记录
- 接近压缩阈值时触发 Memory Flush，提醒保存关键信息。

同时记忆也会建立 embedding 索引，存在本地 SQLite 里。**在文件变更时**对记忆文件进行 chunk & embedding。默认每个 chunk 400 token，相邻 chunk 之间有 80 token 的重叠。





召回通过两个工具完成：

- `memory_get(path, from, lines)` 读取特定文件的指定行范围。
- `memory_search(query)` 做搜搜返回 top 片段（带路径、行号、相似度分数）

搜索使用 hybrid search。向量搜索（cosine similarity）占 70% 权重，BM25 关键词搜索（基于 SQLite FTS5 全文索引）占 30% 权重，两个分数加权融合排序