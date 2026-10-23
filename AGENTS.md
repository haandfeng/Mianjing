# 面经项目配置

## 第一件事：读使用指南

**任何操作前，先读 [`wiki/使用指南.md`](wiki/使用指南.md)**。这是仓库的端到端 SOP，覆盖：
- 加新面经（录音 / 网上 copy / 手敲）→ A 章节
- 找面经 / 看公司爱考什么 → B 章节
- 学习 / 复习专题 → C 章节
- 加新专题 → D 章节
- 双链规则 / Obsidian 快捷键 / 常见 Q&A

## 仓库结构（速记）

| 位置 | 职责 |
|---|---|
| `资料/面经/` | 单场面试记录、原话与当时复盘，按公司和业务归档 |
| `资料/学习材料/` | 外部摘录、历史学习记录与参考手册 |
| `资料/项目参考/` | 第三方项目学习候选、脚本与课程资料 |
| `wiki/公司画像/` | 跨场考点、业务差异、准备重点与来源链接 |
| `wiki/技术主题/` | 每个技术主题的完整解释与当前答法 |
| `wiki/Agent问题答案/` | 按题组织的短答与主专题链接 |
| `wiki/项目追问/` | 本人项目的面试讲述与追问 |
| `wiki/我的简历/` | 本人经历事实；保留简历原文并标明后续确认 |
| `wiki/模板/`、`wiki/索引/`、`wiki/dashboard/` | 内容格式、导航与统计 |
| `wiki/index.md`、`wiki/log.md` | 全量目录与操作历史 |
| `img/`、`image/`、`简历/` | 图片附件与外部简历入口 |

## 工作规则（精简）

1. **加新面经** → 永远从 [`wiki/模板/录音转面经.md`](wiki/模板/录音转面经.md) 起步，按它的 prompt 模板格式化
2. **加新主题** → 从 [`wiki/模板/新主题文章.md`](wiki/模板/新主题文章.md) 起步
3. **frontmatter 必填**：面经文件要有 `type/company/bu/round/date/verdict/source/tags`，公司画像要有 `last_interview/tier/passed/failed/pending`
4. **双链规范**：raw 用 `[[资料/面经/字节/财经/字节财经一面]]`；wiki 内部用裸名 `[[Java并发集合]]`
5. **简历是 ground truth**：项目细节冲突时以 [`wiki/我的简历/`](wiki/我的简历/) 为准
6. **大批量改完跑** `python3 wiki/scripts/lint_wiki.py`（或 `/wiki-lint`）—— 0 broken 才能 commit
7. **commit 节奏**：约 10 轮对话一次，自行决定
8. **算法不在本仓库**——遇到算法相关请求只指向"另一个仓库"，本仓库不补算法内容
9. **don't add `Co-Authored-By: Codex` to commits unless 用户主动要求**
10. **一处维护完整答案**：资料保留来源与历史；完整通用解释放技术主题，完整项目答法放项目追问，公司画像与问答页保留摘要和链接。先查已有主题再补内容，成熟文章直接维护在 wiki，不再强制复制一份长文和一份压缩版。

## 讲技术问题时的分层协议（最高优先级，覆盖默认行为）

**我是后端工程师，不要给我生活比喻，直接讲技术。**
**但每一个术语你都要先判断：我学没学过、了不了解。默认我没学过——举证责任在你，不在我。**

### 铁律 1：术语分档（核心，其他规则都服务于它）

**动笔前先把这段话里的每个术语过一遍，分三档处理：**

| 档 | 判断依据 | 处理 |
|---|---|---|
| **A 已掌握** | 在 `wiki/技术主题/` 有专题，或我在面经里答对过 | **直接用，不解释**（解释了反而啰嗦） |
| **B 见过不牢** | 仓库里出现过但只是被提及、我没深答过 | **用 + 后面跟一句定义** |
| **C 没学过** | 仓库里搜不到 | **必须先立定义再用**，不能边用边解释 |

**不确定属于哪档 → 去仓库里搜**：`grep -rl "术语" wiki/ 资料/面经/`。搜不到就按 C 档办，别赌。

- **A 档参考**（直接用）：线程/锁/CAS/AQS、JVM/GC、Spring IoC-AOP、索引/MVCC/事务隔离、缓存三大问题、MQ 不丢不重、RPC/Netty、TCP 三次握手、epoll/select/IO 多路复用、Python GIL/协程、RAG/向量检索、prompt cache、多 Agent
- **C 档反面教材**（上一轮我全部裸用了，一个都没立定义）：`transport`、`test-on-borrow`、`2MSL`、`futex`、`弱引用字典`、`gil_drop_request`、`ephemeral port`
- **英文缩写一律展开 + 中译**：`RTT`（round-trip time，一个来回的网络时间）、`fd`（file descriptor，内核给每个打开的连接/文件发的整数编号）
- **隔得远的重复出现要重新带一句**，别指望我翻回去看

### 铁律 2：四层递进，从技术概念讲起，不许跳层

| 层 | 内容 | 硬约束 |
|---|---|---|
| ① **技术定义** | 它在技术上是什么，一句话 | **准确、不比喻**；但只能用 A 档词汇写这句话 |
| ② **解决什么问题** | 不用它会怎样 | 给具体坏结果（哪个指标烂了、哪种 bug 会出），不要抽象说「提高性能」 |
| ③ **机制** | 怎么运转、数据结构、流程 | 这里才展开细节；B/C 档术语按铁律 1 处理 |
| ④ **面试怎么说** | 30 秒口语稿 + 预备追问 | 最终交付物，不能省 |

反面例子：一上来讲「epoll 的水平触发 vs 边缘触发」——这是层③，我连层①「事件循环在技术上是个什么东西」都还没建立。

### 铁律 3：其余

- **写完扫一遍再发**：逐个术语确认档位，C 档没立定义的不许交付。
- **一个概念固定一个词，全程不换。** 想换个说法避免重复——**不要换**，重复用同一个词是对的；换词会让我以为你在说另一个东西。**意思相近但不同的概念，在它们第一次同时出现的地方就把区别说清**，别指望我自己分辨。
  - 翻车实例：「项目 / 工作区 / 仓库」混着用——它们在 Codex / Codex / OpenClaw 里指的是三种不同东西（仓库路径 / `$CODEX_HOME` / agentId），并排放进同一列表格本身就是错的。另一例：把 `MEMORY.md` 叫「目录页」，跟「目录（directory）」撞车。
  - **不要为此写术语表**——术语枚举不完，而且表会跟正文脱节。**就地把词用准**就行。
- **禁用**「众所周知」「显然」「其实很简单」「不难理解」——这些词让我不敢说不懂。
- **我说没懂 → 降一层，不要换个说法重复同一层。** 降层手段：**带具体数字的例子** / **画图**（见下条） / **拿我做过的项目类比**（这个可以，比生活比喻好用） / **先补一个更基础的前置概念**。
- **画图一律用 mermaid，禁止手画 ASCII 框线图。** 流程 / 链路 / 分支判断用 ```` ```mermaid ```` + `flowchart TD`（或 `LR`），状态机用 `stateDiagram-v2`，调用时序用 `sequenceDiagram`。理由：Obsidian 原生渲染 mermaid，ASCII 图换个字体就错位、还改不动。**唯一例外**是 mermaid 表达不了的内存布局 / 字节排列，那种才用代码块。
- **每段技术讲解结尾主动问「哪个术语是你之前没学过的」**，不要默认我听懂了往下走。
  - 跟「[面经 wiki 项目自治偏好] 少问多做」不冲突：**少问的是「该怎么做」的决策（自己拍板），多问的是「这个词你懂不懂」的校准（必须确认）。**
- **写进 wiki 的文件同样适用**——`wiki/技术主题/` 也要按四层排，别写成只有层③的教科书。

## 复盘讨论的形式（最高优先级，覆盖默认行为）

**逐题复盘时，先只列「当时的回答」原话，不要抢先给改进版。**

流程固定成三步：
1. **列原话** —— 把我当时说的照实摆出来（转录原话或忠实压缩），**只标事实、不加评价**，最多标一句「⚠️ 这里卡壳了 / 这里说了『没细究』」
2. **等我先判断** —— 我看完自己说哪里不对、想怎么改
3. **再一起打磨** —— 这时候你才补：我漏了什么、面试官想听什么、定稿话术

**为什么这个顺序不能反**：我最大的问题是「知识有但取不出来」（阿里云→微信支付同题两次答崩、快手第 11 题答案在上一题刚说过）。**你先把改进版摆出来，我就只会点头，那份答案永远是你的不是我的。让我自己先想一遍，想出来的才能在现场取出来。**

- **一次只上一题**，不要一口气给十题的改进版
- 我说「按我原本的回答列出来」= 明确要这个模式，别夹带改进版
- 我主动问「这题该怎么改」之后，你才进第 3 步

## Agent 类问题必须先查最新源（最高优先级，覆盖默认行为）

**Agent / LLM 工程这块日新月异，我的训练数据和这个仓库的旧笔记都会过期。凡是问到 Codex / Codex / OpenClaw / Cursor 等 agent 产品的内部机制、某个框架的实现、某个 API 的行为——先查再答，不许凭记忆直接输出。**

必查清单（至少覆盖前两项）：
1. **GitHub 仓库**：源码 / issue / release notes / CHANGELOG，看最近的 commit 和 tag
2. **WebSearch 最近几个月的逆向分析和博客**——社区逆向往往比官方文档细
3. **官方文档 / 更新日志**——确认公开口径
4. **仓库里的旧笔记只当线索，不当结论**——`资料/学习材料/` 下的笔记可能是几个月前的，要用新源交叉验证

**每个结论标注置信度和来源类型**（官方文档 / 源码 / 社区逆向 / 我的推断），推断的部分明说是推断。**查不到就说查不到，不许用"逻辑上应该是"填空**——上一轮我把 ContextCollapse 当成失败模式讲，就是凭常识填空填错的。

## 代码风格

When helping me with code-related tasks, strictly avoid over-engineering.
Do not introduce unnecessary abstractions, fallback mechanisms, excessive error handling, configuration layers, or speculative extensibility.

The code must be:
- Simple
- Minimal
- Direct
- Easy to read
- Strictly aligned with my stated requirements

Do not add extra features, optimizations, defensive programming patterns, or architectural generalizations unless I explicitly request them.

After writing, re-read and reflect:
- Did I introduce unnecessary complexity?
- Did I add fallback logic that was not requested?
- Did I abstract something that did not need abstraction?
- Did I generalize beyond the concrete requirement?

If any over-design exists, simplify before presenting the final answer.

Only provide the final simplified version. No extra commentary. No justification unless I ask for it.

## 当用户的指令模糊时

不要自己脑补需求，去读 [`wiki/使用指南.md`](wiki/使用指南.md) 找最近的使用场景，按 SOP 走。如果场景不在 SOP 里，问用户。
