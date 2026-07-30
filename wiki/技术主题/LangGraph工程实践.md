---
title: LangGraph 工程实践（State / Checkpoint / 流式 / 重试降级）
type: topic
updated: 2026-07-30
note: 本文是工程实践骨架。概念地图见 [[Agent设计模式与MCP]]，具体问答见 [[Agent问题答案/工程化]]。
---

# LangGraph 工程实践

> **一句话**：LangGraph 是把 Agent 的执行流程写成「图」的编排框架 —— 节点是函数、边是跳转规则、所有节点读写同一份 State。它换来的四个能力是：**循环、跨步骤共享状态、断点续跑、多粒度流式**，这四个 LCEL 链式写法一个都做不到。

## 术语先立定义

下面这些词后面会反复用，先定义清楚：

| 术语 | 定义 |
|---|---|
| **LCEL**（LangChain Expression Language） | LangChain 的链式写法，`prompt \| model \| parser`。用 `\|` 把组件串成一条**有向无环**的管道，数据单向流，每一步只能拿到上一步的输出 |
| **StateGraph** | LangGraph 的图构建器。`add_node` 加节点、`add_edge` 加固定跳转、`add_conditional_edges` 加条件跳转、`compile()` 编译成可执行对象 |
| **State** | 一个 `TypedDict`，全图共享的数据结构。节点只返回自己改动的字段（partial update），框架负责合并 |
| **reducer** | 声明「多个节点都往同一个字段写时怎么合并」的函数。写法 `Annotated[list, operator.add]`（追加）。**不声明 reducer 就是后写覆盖先写** |
| **superstep**（超步） | 一次调度批次。一个超步里可以有多个节点并行跑，跑完统一归并、再进下一个超步 |
| **BSP**（Bulk Synchronous Parallel，批量同步并行） | 一种并行计算模型：并行任务读同一份不可变快照 → 各自算 → 到栅栏处统一归并 → 进入下一轮。LangGraph 底层的 Pregel 引擎就是它 |
| **Checkpointer** | 把每个超步结束时的执行状态存下来的组件。按 `thread_id`（会话标识）分线程存 |
| **Store** | 跨会话的长期键值存储，按 namespace + key 存。和 Checkpointer 是两个东西 |
| **`Send`** | 运行时动态 fan-out（一变多）的 API。`return [Send("node", arg) for x in items]`，items 有几个就开几个并行分支 |
| **`Command`** | 一个返回值同时做两件事：改 State + 指定下一个跳哪。`Command(update={...}, goto="node_b")` |

---

## 一、State 与并发：为什么不需要加锁

### ① 技术上是什么

State 是全图共享的一个 `TypedDict`。节点函数签名是 `(state) -> dict`，返回的 dict 是**局部更新**，不是整个 state。

```python
class State(TypedDict):
    query: str
    docs:  Annotated[list, operator.add]   # reducer：多路写入时追加
    answer: str                            # 无 reducer：后写覆盖

def bm25_node(state: State) -> dict:
    return {"docs": bm25.search(state["query"])}     # 只返自己改的字段
```

### ② 不用它会怎样

LCEL 里没有共享状态。第 5 步想访问第 2 步的中间产物，只能一路手动透传字典——每个中间步骤都得原样带着别人的数据往下传，加一个字段要改沿途所有函数。

### ③ 机制：BSP 超步模型（面试满分点）

**「多个 agent 同时跑，状态竞争怎么避免」这题的正确答案是：LangGraph 里根本不存在传统 race condition（竞态条件，即多个执行流交错读改同一块内存导致结果不确定）。**

```
超步 N 开始
   │
   ├─ 快照（不可变）──→ node A 读快照 ─→ 返回值进 buffer
   │                └─→ node B 读快照 ─→ 返回值进 buffer
   │                └─→ node C 读快照 ─→ 返回值进 buffer
   │
   ▼ 栅栏：等 A/B/C 全部跑完
   框架按 reducer 统一归并 buffer → 原子产出超步 N+1 的 state
```

四步：① 执行切成一个个超步；② 同一超步内并行的节点，读的都是**超步开始时的不可变快照**；③ 返回值**不立即写入**，先 buffer 住；④ 本超步全部跑完后框架统一按 reducer 归并。

**并发节点之间不共享可变内存，没有「读-改-写」交错，所以不需要锁。**

### ④ 真正要防的是副作用，不是内存竞态

节点里写库、发消息、扣额度如果不幂等，重试就会做两遍（幂等 = 同一操作执行多次和执行一次结果相同，见 [[消息队列不丢不重]]）。要用业务唯一键 upsert，或者把副作用单独拆成一个节点。

---

## 二、Checkpointer vs Store vs 自己建表存轨迹

三者常被混为一谈，这是高频追问。

| | **Checkpointer** | **Store** | **自建表存轨迹** |
|---|---|---|---|
| 作用域 | 线程内（按 `thread_id`） | 跨线程（namespace + key） | 全局日志 |
| 生命周期 | 短期，一次会话 | 长期 | 永久 |
| 存什么 | 执行快照 | 用户偏好、长期事实 | 调用记录、耗时、入参出参 |
| **能否恢复执行** | **✅ 可执行状态** | ❌ 只是数据 | **❌ 只读日志** |
| 典型用途 | 断点续跑 / 多轮对话 / time travel | 「下次换个会话还记得你」 | 排障、审计、计费 |

**Checkpoint 里存了三样东西：**

- `state` —— 当前的完整状态
- `next` —— 下一步该跑哪些节点
- `pending_writes` —— **已跑完但还没合并的写**

最后这个是「续跑不重复执行」的关键：同一超步里 A 跑完了、B 崩了，恢复时**不会重跑 A**。

**和自建表的本质区别**：自建表是只读日志，用来事后看；Checkpointer 是**可执行的状态**，能从任一 checkpoint 恢复继续跑，甚至改掉某个 checkpoint 的 state 再从那儿分叉（time travel）。

> ⚠ **控制 state 体积**：检索到的原文别整篇塞进 state —— 每个超步都会把 state 序列化存一次，几万字的正文会被反复写盘。放 `doc_id` / 引用，正文另存。

---

## 三、流式：怎么把图内部的执行捞出来推前端

### ① 问题在哪

`graph.invoke()` 是阻塞黑盒。内部跑了 5 个节点花 30 秒，对外只有「进去」和「30 秒后拿到结果」两个时刻。用户看着转圈圈 30 秒。

### ② 比普通 LLM 流式难在哪

图里节点性质不同：检索节点要花 3 秒但**一个 token 都没有**。前端要的信息横跨三层，而它们在完全不同的位置产生：

| 层次 | 例子 | `stream_mode` |
|---|---|---|
| 走到哪个节点了 | 「进入检索阶段」 | `updates` |
| 节点内部干到哪了 | 「BM25 命中 12 条」 | `custom` |
| 模型逐字输出 | 「根」「据」「您」 | `messages` |

### ③ 七种 stream_mode

| mode | 产出 | 用途 |
|---|---|---|
| `values` | 每步后的**完整 state** | 调试；生产别用，体积大 |
| `updates` | 每步的**增量**（哪个节点返回了什么） | 节点级进度，最常用 |
| `messages` | `(LLM token, metadata)` 二元组 | 打字机效果 |
| `custom` | `get_stream_writer()` 写进去的任意数据 | 业务语义进度 |
| `checkpoints` | checkpoint 事件（需 checkpointer） | time travel UI |
| `tasks` | 任务开始/结束，**带结果和错误** | 排障 |
| `debug` | checkpoints + tasks + 元数据 | 开发期 |

```python
from langgraph.config import get_stream_writer

def retrieve(state: State):
    writer = get_stream_writer()
    writer({"msg": "BM25 检索中"})              # 手动往流里塞
    hits = bm25.search(state["query"])
    writer({"msg": f"命中 {len(hits)} 条"})
    return {"docs": hits}

async for chunk in graph.astream(
    inputs,
    stream_mode=["updates", "messages", "custom"],   # 同时订阅多个
    subgraphs=True,                                   # 子图事件也要
):
    chunk["type"]   # 哪一层来的
    chunk["ns"]     # () 是主图，("node:task_id",) 是子图
    chunk["data"]
```

**`subgraphs=True` 必须开**：多 agent 场景下子 agent 通常是子图，不开这个参数子图内部执行对外完全不可见，前端只会看到父图那一个节点卡在那里。

### ④ FastAPI + SSE 的五个坑

（SSE = Server-Sent Events，一个永不结束的 HTTP 响应体，服务端可以持续往里追加数据；详见 [[专栏/Agent/MCP_SSE_文档]]）

| 坑 | 后果 | 处理 |
|---|---|---|
| **不做断连检测** | 用户关页面后图还在跑、还在烧 token | `if await request.is_disconnected(): break` |
| **直接 `json.dumps`** | `AIMessage` / `ToolMessage` 不可序列化直接抛异常；`updates` 里可能带几万字检索结果 | 手动抽字段，只发节点名和状态 |
| **异常抛出 generator** | HTTP 头已发、状态码改不了，前端只看到流莫名断掉 | catch 住，发 `event: error` |
| **不发心跳** | nginx `proxy_read_timeout` / ALB idle timeout 默认 60s，节点跑久了被中间设备掐断 | `EventSourceResponse(gen, ping=15)` |
| **nginx 缓冲** | `proxy_buffering on`（默认）会攒着响应体不转发，SSE 事件全卡住 | `proxy_buffering off` 或响应头 `X-Accel-Buffering: no`，并关 gzip |

> 🔴 **最隐蔽的一个**：Python < 3.11 的 async 环境下 `get_stream_writer()` 拿不到（contextvar —— Python 用来在同一协程链路里隐式传递上下文的机制 —— 在旧版本传不下去），要改成 `async def node(state, writer: StreamWriter)` 参数注入。同样地，旧版本 async 下调 LLM **必须手动把 `config` 透传下去**，否则 `messages` 模式一个 token 都收不到。**这是「流式不生效」最常见的原因。**

---

## 四、重试与降级：空结果不是异常

### ① 满分点

**`RetryPolicy` 只在抛异常时触发。** 接口 200 返回一个空数组，这是一次**成功的调用**，框架的重试机制根本不会启动。被问「数据抓回来是空的怎么办」时上来答「配个 RetryPolicy」就掉坑了。

| 类型 | 表现 | 谁来管 |
|---|---|---|
| **硬失败** | 抛异常：超时、5xx、连接拒绝 | 框架的 `RetryPolicy` |
| **软失败** | 正常返回但没数据：空数组、"未查询到" | **应用层判断 + 条件边路由** |
| **语义失败** | 有数据但不对：全是 0、时间过期、不相关 | 校验节点 |

### ② 硬失败

```python
from langgraph.types import RetryPolicy

builder.add_node("fetch", fetch, retry_policy=RetryPolicy(
    max_attempts=3, initial_interval=0.5, backoff_factor=2.0,
    max_interval=8.0, jitter=True,
    retry_on=(httpx.TimeoutException, httpx.ConnectError),   # 一定要收窄
))
```

两个必讲的点：

- **`retry_on` 要收窄。** 默认全量重试的话，参数错误（400）也会被白重试三次。4xx 不该重试，5xx 和超时才该。
- **重试是重跑整个节点函数，不是从中断处继续。** 节点内有副作用必须幂等。
- `jitter=True`（随机抖动）不加的话，并发的几十个节点会同时退避、同时重试，形成脉冲把上游打死。

### ③ 软失败：判断结果写进 state

```python
def fetch(state: State) -> dict:
    rows = client.query(state["query"])
    return {"rows": rows,
            "fetch_status": "ok" if rows else "empty",
            "attempt": state.get("attempt", 0) + 1}    # 计数器必须在 state 里

def route(state: State) -> str:
    if state["fetch_status"] == "ok":  return "process"
    if state["attempt"] >= 3:          return "degrade"
    return "relax_query"

builder.add_conditional_edges("fetch", route)
builder.add_edge("relax_query", "fetch")               # 回环
```

**`attempt` 必须放在 state 里**——图里有环就必须有终止条件。`recursion_limit`（默认 25，超了抛 `GraphRecursionError`）只是保险丝，不是设计。

### ④ 降级阶梯

| 层级 | 做法 |
|---|---|
| 1. 放宽查询 | 扩大时间窗口、去掉次要过滤条件、精确匹配改模糊 |
| 2. 换数据源 | 备用源 / 本地缓存 / 历史快照 |
| 3. 降低精度 | 日频拿不到拿周频；个股拿不到拿行业均值 |
| 4. 部分成功 | `Send` 分发的并行分支各自成败，用 reducer 分别收集 `results` / `failures`，按成功率决定继续还是降级 |
| 5. **显式告知模型** | 明确说「XX 数据未获取到，原因是 YY」 |

> 🔴 **第 5 条最容易漏也最重要**：给模型一个空数组，它会当作「这部分没什么好说的」然后继续编。给它 `{"rows": [], "note": "该标的自 2026-07-15 起停牌"}`，它才会在最终回答里如实标注。**空数组诱发幻觉，明确的缺失说明抑制幻觉。**

### ⑤ 什么不该重试

- **参数错误**（模型把日期格式填错）→ 把错误信息**回灌给模型让它自己改**，重试同样的调用一百次还是错
- **鉴权失败** → 重试无意义，走告警
- **合法的空结果**（今天确实停牌）→ 这不是失败

---

## 五、为什么用 LangGraph 而不是 LangChain

**先纠正问题前提：这不是二选一。** LangGraph 本身就是 LangChain 生态的一部分，`create_agent` 就构建在 LangGraph 上，middleware 的钩子也跑在它返回的编译图里。真正的对比是 **LCEL 链式编排 vs 图编排**。

| LCEL 做不到 | LangGraph 的机制 |
|---|---|
| **循环**（agent 本质是 while 循环） | 节点回环 + `recursion_limit` 兜底 |
| **分支后再汇合** | 条件边 / `Command` |
| **跨步骤共享状态** | State + reducer |
| **中断和恢复** | Checkpointer + `interrupt()` |
| **自定义并行归并**（`RunnableParallel` 只有固定字典合并） | reducer |
| **动态并行**（运行时才知道开几路） | `Send` |
| **多粒度流式** | 七种 `stream_mode` |

**判据**：需要环、需要跨步骤共享状态、需要中途暂停 → LangGraph；单向数据变换管道 → LCEL 够了。

**收尾金句**：

> **LCEL 管「一步怎么算」，LangGraph 管「步与步之间怎么走」。**

节点内部照样用 LCEL，两者不冲突：

```python
chain = prompt | model | parser              # 节点内部：LCEL
def analyze(state): return {"r": chain.invoke({"input": state["query"]})}
builder.add_node("analyze", analyze)         # 节点之间：LangGraph
```

### v1 之后的分层现状（说出来加分）

- `create_agent()` 是新的高层入口，返回的就是一个编译好的 LangGraph
- **Middleware** 是新扩展点，钩子挂在 agent loop 各处（模型调用前后、工具调用前后），内置 `SummarizationMiddleware`（上下文超长自动摘要）、`HumanInTheLoopMiddleware`（指定工具触发人工确认）、工具重试、模型 fallback、限流、PII 检测
- `create_agent` 建的 agent 可以直接作为节点嵌进更大的 `StateGraph`，middleware 照常生效

```
单步数据变换                    → LCEL
标准 ReAct agent + 常见需求      → create_agent + middleware
复杂多 agent 编排 / 自定义拓扑    → 手写 StateGraph
```

---

## 高频问法（真题出处）

| 问法 | 出处 |
|---|---|
| State 管理和 Checkpoint 怎么实现？多 agent 并行的状态竞争怎么避免？ | [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]] |
| LangGraph 图里怎么捕获每个节点结果实时推前端？ | [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]] |
| 子任务失败（数据抓回来是空的）怎么重试降级？ | [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]] |
| 为什么用 LangGraph 而不是简单的 LangChain？ | [[公司/淘天/AI Agent/淘天AI-Agent一面_2026-07-30]] · [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]] · [[其他/PingCAP/面试问题总结]] |
| 你对 LangChain / LangGraph 的理解？框架解决了什么、不解决什么？ | [[微软/Bing图像视频业务实习一面面经]] |
| 你们当时为什么选择用 LangGraph 去写？对比过哪些框架？ | [[其他/PingCAP/面试问题总结]] |
| LangGraph 复用连接池 + 事件循环被外部 SDK 关掉，导致跨 loop 报错 | [[公司/点点互动/AI Agent方向/点点互动AI Agent一面_2026-07-27]] |
| 想借 LangGraph 的 human-in-the-loop 让人审核模型计划 | [[微软/Bing图像视频业务实习一面面经]] |

## 易错点（高频追问）

- **多 agent 并行要加锁吗？** —— 不用。BSP 超步模型下并发节点读不可变快照、写入 buffer 后统一归并，不存在读-改-写交错。要防的是**副作用不幂等**
- **Checkpointer 和自己建表存轨迹是一回事吗？** —— 不是。自建表是只读日志；Checkpointer 是可执行状态，能从任一点恢复甚至分叉
- **Checkpointer 就是长期记忆吗？** —— 不是。Checkpointer 是线程内短期（按 `thread_id`），跨会话长期记忆是 Store
- **数据抓回来是空的，配个 RetryPolicy 就行？** —— 不行。空结果不抛异常，RetryPolicy 不触发，必须应用层判断 + 条件边路由
- **RetryPolicy 是断点续跑吗？** —— 不是，重跑**整个节点函数**，节点内副作用必须幂等
- **图里加了回环就完事？** —— 必须把重试计数器放进 state，`recursion_limit` 只是保险丝
- **流式为什么一个 token 都收不到？** —— Python < 3.11 async 下没把 `config` 透传给 LLM 调用；或者忘了开 `subgraphs=True` 导致子图全黑
- **拿不到数据就返空数组给模型？** —— 会诱发幻觉。必须给明确的缺失说明
- **LangGraph 比 LangChain 好？** —— 问题前提就错了，LangGraph 是 LangChain 生态的一部分；真正的对比是 LCEL vs 图编排，固定单向流程用图是过度设计

## 深入阅读

- 概念地图：[[Agent设计模式与MCP]]
- 答题分册：[[Agent问题答案/工程化]]（Q48 流式 / Q49 重试降级 / Q50 选型）· [[Agent问题答案/Agent设计]]
- 相关主题：[[RAG优化全链路]] · [[限流熔断容错]] · [[消息队列不丢不重]]（幂等）· [[Python并发与GIL]]（事件循环 / 协程）
- raw 专栏：[[专栏/Agent/RAG到Agent进阶]] —— RAG → ReAct → Plan-Execute → LangGraph State 演化路径 · [[专栏/Agent/什么时候选择多智能体]] —— Anthropic 多 Agent 决策准则 · [[专栏/Agent/MCP_SSE_文档]] —— SSE 与流式
- 公司画像：[[公司/淘天]] · [[蔚来]] · [[微软]] · [[PingCAP]]
