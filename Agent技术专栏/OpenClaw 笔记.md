OpenClaw Tool System 的设计目标，就是在这个复杂空间内建立一个**结构化的决策框架**，让每一次工具调用都有迹可循、有理可依。


# 架构

```text
┌─────────────────────────────────────────────────────────────┐ 

│  用户查询层 (User Query Layer)                               │ 

│  "帮我总结一下这篇文章"                                       │ 

└───────────────────────┬─────────────────────────────────────┘ 

                        │ 解析实体引用、提取上下文 

                        ▼ 

┌─────────────────────────────────────────────────────────────┐ 

│  意图路由层 (Intent Routing Layer)                           │ 

│  Skill Router → Task Planner → Tool Selector                 │ 

│  "写作任务" → "总结操作" → "generateOverview + read"         │ 

└───────────────────────┬─────────────────────────────────────┘ 

                        │ 生成工具调用计划 

                        ▼ 

┌─────────────────────────────────────────────────────────────┐ 

│  执行层 (Execution Layer)                                    │ 

│  参数验证 → 调用执行 → 结果处理 → 上下文更新                   │ 

└─────────────────────────────────────────────────────────────┘
```

##  用户查询层：实体解析与上下文构建

在 OpenClaw 中，用户的每一次输入都不是孤立的。系统会首先解析查询中的**实体引用**，将其关联到用户知识库中的具体对象。

例如当用户输入包含 `@【文档标题】(id: xxx; type: material)` 这样的引用时，系统会：

1. **实体识别**：解析出这是一个 type 为 material、id 为 xxx 的对象
2. **元数据获取**：从材料存储中获取其元数据（文件类型、保存时间、内容摘要等）
3. **权限检查**：验证当前用户是否有权访问该对象
4. **内容加载**：对于需要读取内容的操作，预先加载材料全文注入上下文中

==这种实体引用机制解决了 LLM 长期以来的“幻觉”问题——当用户说“这篇文章”时，系统明确知道指的是哪一篇文章，而不是依赖 LLM 去猜测上下文。==



## 意图路由层：从模糊意图到精确指令

这是 Tool System 的核心层。OpenClaw 采用了一种**基于模式匹配和约束求解的混合路由策略**，而非简单地将所有决策交给 LLM。



###  Skill Router：任务类型分类器

Skill Router 是系统的第一道闸门，负责将用户查询分类到预定义的**任务模式**（Task Pattern）。

| 任务模式 | 特征信号           | 典型工具链                        |
| :------- | :----------------- | :-------------------------------- |
| 阅读理解 | 引用材料、询问内容 | `read` → `generateOverview`       |
| 内容创作 | 创建/撰写/生成文档 | `write` / `proxyWrite` / `edit`   |
| 信息检索 | 搜索/查找/有哪些   | `searchBoards` / `listBoard`      |
| 数据分析 | 对比/分析/统计     | `generateOverview` （多源）       |
| 外部探索 | 最新/新闻/研究     | `googleSearch` / `research`       |
| 创意生成 | 画/生成图片/视频   | `imageGenerate` / `videoGenerate` |


先关键词进行匹配，再用语义匹配。

Skill Router 使用**规则引擎 + 轻量 LLM 辅助**的混合策略：

- **硬规则优先**：如果查询包含明确的动作动词（“创建”、“搜索”、“生成”），直接匹配到对应任务模式
- **上下文增强**：如果查询中包含材料引用，优先考虑阅读相关任务模式
- **LLM 兜底**：当规则无法明确分类时，使用轻量模型进行意图识别

==这种设计的优势在于**可预测性**——常见场景走确定性路径，边缘 case 由模型兜底。==

### Task Planner：调用链编排器

确定任务类型后，Task Planner 负责生成具体的工具调用计划（Tool Call Plan）。

==调用工具的框架：怎么生成调用计划，有逻辑和调理的==

一个调用计划包含：

- **主工具**：完成核心任务的工具（如 `write`）
- **前置依赖**：必须在主工具之前调用的工具（如先 `read` 再 `generateOverview`）
- **后置处理**：主工具调用后需要进行的操作（如保存结果、更新上下文）
- **回退策略**：当主工具失败时的备选方案



Task Planner 通过**静态分析 + 动态规划**相结合的方式生成计划：

- 静态分析：检查工具间的依赖关系（如 `edit` 必须先 `read`）
- 动态规划：根据当前上下文状态决定哪些前置步骤可以跳过



### Tool Selector：精确工具匹配

在某些任务模式下，存在多个功能相似的工具（如 `write` vs `proxyWrite`）。Tool Selector 负责在最后一公里做出精确选择。



选择逻辑基于以下维度：

1. **用户显式偏好**：如果用户明确说“用 GPT 写”，优先选择 `proxyWrite` 并指定 gpt-5
2. **内容类型适配**：某些工具对特定内容类型有优化（如 `proxyWrite` 支持特定模型的风格适配）
3. **成本-质量权衡**：在简单场景使用轻量工具，复杂场景使用专业工具
4. **状态依赖**：如果上下文已包含某个工具的输出，优先使用兼容的后续工具



##  执行层：安全、可靠的工具调用


执行层负责将调用计划转化为实际的工具调用，并处理结果。

### 参数验证与补全

每个 OpenClaw 工具都有严格的参数规范：

- **必需参数**：调用前必须提供，缺失则阻止调用
- **可选参数**：有默认值，可根据上下文自动补全
- **约束参数**：必须满足特定条件（如 `id` 必须是有效的 UUID）

参数补全逻辑：

1. 从用户查询中直接提取
2. 从引用的实体元数据中推断
3. 从当前上下文中继承
4. 使用智能默认值

#### 调用执行与错误处理

工具调用采用**同步执行 + 超时控制**的模式：

- 大多数工具在数秒内返回结果
- 长时间运行的工具（如 `research`）有专门的进度反馈机制
- 超时后自动触发回退策略

错误处理遵循**优雅降级**原则：

- 可恢复错误：自动重试（如网络超时）
- 业务错误：返回友好提示，提供替代方案
- 系统错误：记录日志，通知用户

#### 上下文更新

每次工具调用后，系统会更新上下文状态：

- 将工具输出添加到对话历史
- 更新实体引用列表
- 维护工具调用计数（用于成本追踪）



# 从发消息到执行的流程

整体数据流：从“发一条消息”到“操作电脑”

![Image](https://pbs.twimg.com/media/G_2oRYXXgAENMWP?format=jpg&name=medium)





![Image](https://mmbiz.qpic.cn/mmbiz_png/sXiaukvjR0RBZheYRxR7ALicjcPNFveBJYIQPuINgsRPQ7yt4lNAhHDw8X33ux5RB6cWtmhvhLP4icrjASXV4amsQ/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)


它是一个在你的机器上运行的进程，具体来说：

- 暴露一个网关服务器来处理所有渠道连接（Telegram、WhatsApp、Slack 等）
- 调用 LLM API（Anthropic、OpenAI、本地模型等）
- 在本地执行工具
- 在你的电脑上执行任何你想做的操作


 **一条主链路讲清楚：消息进来之后发生了什么**

1. **Channel Adapter**：把不同渠道的输入统一成标准消息，并提取附件。
2. **Gateway Server**：会话协调器，决定这条消息应该进入哪个会话、排到哪个队列。
3. **Lane Queue**：每个会话默认串行；确实低风险的任务才允许并行。
4. **Agent Runner**：拼上下文、选模型、发起调用，驱动工具循环。
5. **Agentic Loop**：模型提出 tool call → 执行 → 结果回填 → 下一轮，直到输出或触达上限。
6. **Response Path**：把最终内容流式回写到渠道，同时把全过程写入可回放的转录（JSONL）。



原帖里提到 LLM 调用是流式输出，最终响应通过渠道回到用户；同时会话会被持久化成 JSONL（每行一个 JSON，对应用户消息、工具调用、执行结果、模型响应等）。

为了更简单地解释架构，下面举一个例子：从你给 Clawd 发送消息开始，一直到你收到输出的完整过程。

## Channel Adapter

渠道适配器接收你的消息并进行处理（标准化、提取附件）。不同的通讯工具和输入流都有各自专用的适配器。


## Gateway Server

网关服务器是任务/会话的协调器，它接收你的消息并将其分发到正确的会话中。这是 Clawd 的核心。它处理多个重叠的请求。为了实现操作的序列化，Clawd 使用了**基于通道（lane）的命令队列**。每个会话有自己专属的通道，而低风险的可并行任务则可以在并行通道中运行（定时任务）。

这与使用 async/await 意大利面条式代码形成对比。过度并行化会损害可靠性，并引发大量调试噩梦。

==Default to Serial, go for Parallel explicitly==

**默认串行，显式并行**

如果你做过 Agent 开发，你多少已经意识到了这一点。这也是 Cognition 的 [Don’t Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)博客文章的核心观点。

简单地给每个 Agent 用 async 会让你得到一堆交错混乱的垃圾输出。日志将无法阅读，如果它们共享状态，竞态条件将成为开发中时刻需要防范的噩梦。

Lane 是对队列的一层抽象，序列化是默认架构，而非事后补救。作为开发者，你正常写代码，队列替你处理竞态条件。

mental model从"我需要锁什么？"转变为"什么可以安全地并行？"



-  每个会话有自己的"泳道"（lane）。
-  泳道里默认 **串行执行**。
-  只有你明确标注"低风险、可并行"的任务，才会进入并行泳道（例如某些定时任务）。
- ![Image](https://mmbiz.qpic.cn/mmbiz_png/sXiaukvjR0RBZheYRxR7ALicjcPNFveBJYJ6Yx9GliaUpWwHLsbZ5ia4I3dxPuWfldntoZAuF0DLJ5QVph455ElFCw/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

## Agent Runner



这是真正的 AI 介入的地方。它决定使用哪个模型，选择 API 密钥（如果都不可用，就将配置标记为冷却状态并尝试下一个），如果主模型失败则回退到其他模型。

Agent Runner会动态组装系统提示词，包含可用工具、技能、记忆，然后添加会话历史（来自 `.jsonl` 文件）。

接着传递给context window gaurd，确保有足够的context空间。如果context快满了，要么压缩会话（总结上下文），要么优雅地失败。



真正能跑起来的系统，往往把提示词当成装配线上的一环，而不是宗教。

在 OpenClaw 的描述里，Runner 做的事很具体：

- **Model Resolver**：决定用哪个模型；Key 失效标记冷却并切换；主模型失败自动换备用。
-  **System Prompt Builder**：动态拼装系统提示词，把工具、技能、记忆整合进去。
-  **Session History Loader**：加载会话历史（来自 `.jsonl` 转录）。
- **Context Window Guard**：上下文快满时压缩（总结）或降级/停止，避免"撑爆以后才知道"。





LLM 调用本身以流式方式返回响应，并对不同提供商做了抽象。如果模型支持，还可以请求扩展思考。



##  Agentic Loop

如果 LLM 返回的是工具调用响应，Clawd 会在本地执行并将结果添加到对话中。这个过程反复进行，直到 LLM 返回最终文本或达到最大轮次（默认约 20 轮）。

这也是魔法发生的地方：**计算机操控（Computer Use）**——我后面会讲到。

工具循环大家都懂：tool call → 执行 → 回填 → 下一轮，直到输出或触达轮次上限（例如 20 轮）。





但工程上真正需要盯住的是三件事：

- • **终止条件**：什么时候该停？停得是否可解释？
- • **工具输出的格式**：工具返回是"日志"，还是"可被模型消费的证据"？
- • **回填策略**：回填太多撑爆上下文，回填太少模型又失明。

Context Window Guard 的价值也在这里：把"上下文爆炸"做成显式组件，而不是靠经验拍脑袋。

你可以不追求每次都成功，但你不能接受失败时无从定位。



## Response Path



比较标准。响应通过channel返回给你。==会话也通过一个基本的 jsonl 文件进行持久化，每一行是一个 JSON 对象，包含用户消息、工具调用、结果、响应等。这就是 Clawd 记忆的方式（基于会话的记忆）。==

以上涵盖了基本架构。

接下来让我们看看一些更关键的组件。





# Memory

没有合适的记忆系统，AI 助手和金鱼没什么区别。Clawd 通过两个系统来处理记忆：

1.  JSONL 格式会话记录：每一行一个 JSON 对象，包含用户消息、工具调用、执行结果、模型响应。
2. 以 Markdown 形式存储的记忆文件，位于 `MEMORY.md` 或 `memory/` 文件夹中。



这相当于把记忆拆成两类：

- "发生过什么"（转录，偏事实、偏审计）
-  "应该记住什么"（摘要与沉淀，偏经验、偏复用）



.md 记忆（主存储）：

- MEMORY.md：长期、人工整理的事实与偏好。

- memory/YYYY-MM-DD.md：按天的追加日志。

- 存在工作区（默认 ~/.openclaw/workspace），是唯一的事实来源，模型只“记住”写到这些文件里的内容。

JSONL“记忆”（会话记录）

- 会话转录存在 ~/.openclaw/agents/\<agentId>/sessions/*.jsonl。

- 每行一条 JSON（type: "message"，含 role + content），是对话的原始日志，不是和 .md 并列的另一种“记忆格式”，而是可被索引的会话数据。



## MD和Jsonl怎么写作

### ① 统一检索：一起被搜到

- 内置索引：

- .md 被分块、嵌入，写入 SQLite。

- 若开启 memorySearch.sources: ["memory", "sessions"]（或 experimental.sessionMemory: true），JSONL 也会被读：解析出 user/assistant 文本 → 转成「User: … / Assistant: …」的纯文本 → 再分块、嵌入，写进同一个 SQLite，并打上 source: "sessions"。

- 一次 memory_search：同时查 .md 块和会话块，结果里带 path / source，能区分是来自 memory/2026-01-15.md 还是 sessions/sess-main.jsonl。

- 所以：协作 = 共用同一套向量/关键词索引，一起参与召回；不是“两个独立系统”，而是一个检索入口、两类数据源。

### ② 会话沉淀为 .md：JSONL → 新 md 文件

- session-memory hook（/new 或 /reset 时）：

- 用当前会话的 JSONL 最近若干条消息，让 LLM 生成一个摘要 slug。

- 在工作区写一个新文件：memory/YYYY-MM-DD-\<slug>.md。

- 效果：这段 JSONL 对话被固化成一条 .md 记忆，之后和别的 MEMORY.md、memory/*.md 一样被索引、被 memory_search / memory_get 使用。

- 协作关系：JSONL 是原料，.md 是沉淀结果；同一段对话先只在 JSONL 里，经过 hook 后多了一份 .md，长期记忆就主要靠 .md。



总结

- JSONL = 对话日志，更全、更原始。解析成「User: … / Assistant: …」再分块、嵌入，也进同一索引（并标 source: "sessions"）。

- .md = 长期记忆，更摘要、更精炼；有时会从 JSONL 里总结出一段，写成新的 .md（例如 session-memory hook），但 .md 本身不是 JSONL 的索引，而是另一类主数据。按文件分块、嵌入，直接进索引；





协作：

1）检索：JSONL 解析/导出后和 .md 进同一索引，一次 memory_search 同时搜到两者；

2）沉淀：用 session-memory hook 把某段 JSONL 对话变成新的 memory/…md，之后这段“记忆”就主要活在 .md 里，和别的 .md 一起被索引和引用。



### 是什么jsonL都写进md吗，每次生成一个jsonL都写进md里，有判断筛选吗

只有一种情况会把会话内容写进 .md 文件：

- 你发了 /new 或 /reset

- 且 session-memory 这个 hook 是启用状态（openclaw hooks enable session-memory）

这时会为刚才结束的那段对话写一个新的 .md 文件，不是“每生成一段 JSONL 就写一个 .md”。

也就是说：

- 平时对话只会往 JSONL 里追加，不会自动写 .md。

- 只有在你用 /new 或 /reset 时，hook 才会把上一段会话整理后写成一个 .md。



Hook 从会话的 JSONL 里取内容时，会做这些筛选（见 handler.ts）：

| 筛选                 | 说明                                                         |
| :------------------- | :----------------------------------------------------------- |
| 只处理 /new / /reset | 只有这两种命令会触发写 .md，其它消息不触发。                 |
| 只取最近 N 条        | 默认用最近 15 条 user/assistant 消息（可配置 session-memory.messages），不是整份 JSONL。 |
| 只要“消息”           | 只解析 type == " message" 且 role == "user" 或 role == "assistant" 的条目。 |
| 去掉命令             | 内容以 / 开头的（如 /new、/reset）不会放进要写进 .md 的摘要里。 |

会生成类似这样一个文件（例如 memory/2026-03-01-1430.md）：

```markdown
# Session: 2026-03-01 14:30:00 UTC

- **Session Key**: agent:main:main
- **Session ID**: ...
- **Source**: ...

## Conversation Summary

User: 第一条用户消息
Assistant: 第一条回复
User: 第二条用户消息
...
```



## 检索 Retrieve

搜索方面，它采用了**向量搜索和关键词匹配的混合方式**，兼取两者之长。



同一套索引里既有 .md 的块，也有从 JSONL 抽出来的文本；一次 memory_search 同时查这两类内容。

- memory：MEMORY.md、memory/**/*.md（及 memorySearch.extraPaths）按块切分、嵌入，写入 SQLite。
- jsonl:  1. 用 src/memory/session-files.ts 里的 buildSessionEntry() 读每个 *.jsonl。2. 解析出 role === "user" | "assistant" 的 message，抽出文本，打成 User: ...\nAssistant: ... 的纯文本。3.再按与 .md 相同的分块/嵌入流程写入同一个 SQLite，并在表里打上 source = "sessions"。

 检索

- memory_search 查的是这一套 SQLite（向量 + 可选 BM25）。

- 结果里每条都带 path、source（"memory" 或 "sessions"），所以既有来自 memory/2026-01-15.md 的片段，也有来自 sessions/sess-main.jsonl 的会话片段，一次查询就混合了两者。

 



它还受益于** **Smart Synching****，当文件监视器检测到文件变更时触发:

记忆文件更新也不需要一套"专用记忆 API"。更朴素的方式就够了：Agent 用"写文件工具"写入 `memory/*.md`，文件监控器检测到变化后触发同步与索引更新。

一个细节：新对话开始时，会有一个钩子把上一轮对话抓出来，写一份 Markdown 总结。你可以把它理解成"把经验沉淀变成默认动作"，而不是全靠用户手动整理。==会话 → 长期记忆 某段会话（JSONL）在 /new 或 /reset 时经 LLM 摘要，写成 memory/YYYY-MM-DD-slug.md，变成正式 .md 记忆==

Clawd 的记忆系统出奇地简单，与 **@CamelAIOrg** 中实现的工作流记忆非常相似。没有记忆合并，没有按月/按周的记忆压缩。

这种简单性是优势还是缺陷取决于你的视角，但我始终倾向于**可解释的简单性**，而非复杂的意大利面条式代码。

它的记忆会长期保存，旧记忆与新记忆权重接近，也就意味着"它不太会自然遗忘"。

这既是优势也是风险：

-  优势：可追溯、可解释，复盘方便。

-  风险：过期经验可能持续被召回；你需要显式的版本化、有效期或冲突解决策略。

  

# Clawd 的爪子：它如何使用你的电脑

这是 Clawd 的**护城河**之一：你给它一台电脑，让它自由使用。那么它是怎么用的呢？基本上和你想的差不多。

Clawd 给予 Agent 大量的计算机访问权限，风险由你自己承担。它使用 exec 工具在以下环境中运行 shell 命令：

- **沙箱**：默认方式，命令在 Docker 容器中运行
- **直接在宿主机上**运行
- **在远程设备上**运行

除此之外，Clawd 还有文件系统工具（读取、写入、编辑）、基于 Playwright 的**浏览器工具**（带语义快照），以及用于后台长时间运行命令、终止进程等的**进程管理工具**。

**安全性（或者说缺乏安全性？）**

与 Claude Code 类似，有一个允许列表，用户可以对命令进行审批（允许一次、始终允许、拒绝并提示用户）。

json

```json
// ~/.clawdbot/exec-approvals.json
{
  "agents": {
    "main": {
      "allowlist": [
        { "pattern": "/usr/bin/npm", "lastUsedAt": 1706644800 },
        { "pattern": "/opt/homebrew/bin/git", "lastUsedAt": 1706644900 }
      ]
    }
  }
}
```

安全命令（如 jq、grep、cut、sort、uniq、head、tail、tr、wc）已预先批准。

危险的 shell 构造默认被阻止：

bash

```bash
# 这些在执行前就会被拒绝：
npm install $(cat /etc/passwd)     # 命令替换
cat file > /etc/hosts              # 重定向
rm -rf / || echo "failed"          # 用 || 链接
(sudo rm -rf /)                    # 子 shell
```

安全机制与 Claude Code 非常相似。核心理念是**在用户允许的范围内尽可能自主**。

**浏览器：语义快照**

浏览器工具主要不使用截图，而是使用**语义快照**——即基于页面无障碍树（ARIA）的文本表示。

Agent 看到的是这样的内容：

bash

```bash
- button "Sign In" [ref=1]
- textbox "Email" [ref=2]
- textbox "Password" [ref=3]
- link "Forgot password?" [ref=4]
- heading "Welcome back"
- list
  - listitem "Dashboard"
  - listitem "Settings"
```

这带来了四个显著优势。正如你可能已经猜到的，浏览网站本质上并不一定是视觉任务。

一张截图可能有 5 MB，而一个语义快照不到 50 KB，token 成本只是图片的一个零头。