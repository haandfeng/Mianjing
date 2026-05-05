# 自我介绍/个人信息

# 你的项目现在是一个什么样的状态？上线了吗？

是的，上线就是在我们那个官方那个学程上面，然后就是上线了一个。

# 为什么用RAG而不是把知识库封装成工具让大模型选择性调用？

我们 RAG 就是用了一个工具调用，不过就是说我们在这个检索知识库这一步的话，是一定要写死，让它进行一个检索知识库的一个调用的。

**设计思路**：

| **方案** | **优点** | **缺点** | **选择原因** |
|---------|---------|---------|------------|
| **固定调用RAG** | 避免模型跳过必要检索，保证答案来源可追溯 | 即使简单问题也要执行检索，增加延迟和成本 | 医疗行业准确性 > 效率 |
| **选择性工具调用** | 灵活，可以跳过不相关查询 | 可能出现"应该调用但没调用"的情况，产生幻觉 | 风险太高，不适合医疗场景 |

**实际效果**：
- 如果问无关问题，系统要么不回答，要么回答比较"正能量"
- 这个效果可以接受，因为医疗行业对准确性要求极高，不能容忍幻觉

# 如果问题不涉及私有知识库，也要调用吗？

会调一遍，然后不回答就说就是没有办法从已有的知识里面获取到相关的一个回答，然后我就说不回答就是这样子，因为我们当时一开始是有过想可以调可以不调，但是后来发现他这个调不调中间有比较大的一个问题，就是可能有些问题我希望他能调数据库回答，然后但他是没有调这个检索工具的，所以说我们就后来就把它改成一定会调。

# 项目效果怎么样？有定量或定性评价吗？

有的，我当时走的时候就是刚上线，然后就走了，然后我是不知道外部反馈，但是我自己内部这个进行测试的话。

**评估指标**：

| **指标** | **定义** | **优化前** | **优化后** | **说明** |
|---------|---------|----------|----------|---------|
| **准确率（Correctness）** | 模型回答与人工标准答案的一致性 | 76% | 92% | 主要优化方向 |
| **相关性（Relevance）** | 回答是否与问题相关 | - | 99%+ | 一直保持很高 |
| **幻觉率（Hallucination）** | 模型是否产生文档中没有的信息 | - | 99%+ | 几乎没有幻觉 |

**测试集**：
- 总数量：200+ 个测试用例
- 中文：180+ 个
- 英文：90+ 个
- 来源：测试中心提供

**上线后数据**：
- 使用量：每月几千个问题
- 特点：使用量不算特别高，因为是内部培训系统


# Agent的成功率、失败率有统计过吗？

这个的话百分百成功，没成功的主要是在。在那个没有余额，然后还有就是说我 Langsmith 追踪的时候，他那个超额度了，这是这回报错，然后另外的一个报错的话，主要就是看我用哪家的API。

**API选择对比**：

| **API提供商** | **稳定性** | **Structured Output** | **报错率** |
|------------|----------|---------------------|----------|
| **DeepSeek 官方** | ✅ 稳定 | ✅ 表现好 | 低 |
| **硅基流动** | ✅ 稳定 | ✅ 表现好 | 低 |
| **腾讯云** | ⚠️ 一般 | ❌ 不稳定 | 高 |

**失败场景**：
1. API 余额不足
2. Langsmith 超额度
3. Structured Output 失败（主要出现在腾讯云）

# 为什么不选国外的模型？比如ChatGPT？

我们当时是测试，首先我们在用开源模型，就是我们公司规定的就是模型应该用开源的，然后我们到时候要自己部署的，然后自己线上，因为它是比较机密的内容。

**模型测试对比**：

| **模型** | **参数量** | **中文表现** | **英文表现** | **问题** |
|---------|----------|------------|------------|---------|
| **Gemini** | - | ❌ 非常差 | ✅ 与DeepSeek差不多 | 无法理解中文语境下的操作术语 |
| **LLAMA** | - | ❌ 非常差 | ✅ 与DeepSeek差不多 | 同样无法很好理解中文专业术语 |
| **ChatGPT OSS** | 20B/120B | ✅ 不错 | ✅ 不错 | 参数量相对较小 |
| **DeepSeek** | 671B | ✅ 优秀 | ✅ 优秀 | - |

**最终选择：DeepSeek 671B**

**选择原因**：
1. 参数量最大，性能最强
2. 中文表现优秀，能理解专业术语
3. 符合开源要求，可以自己部署
4. 老板更信任大模型

**技术考量**：
- 部署方式：本地部署，保证数据安全
- 成本考虑：开源模型可以自己部署，不需要支付 API 费用
- 性能要求：医疗行业对准确性要求极高，需要选择性能最强的模型

# 你们用的哪个embedding模型？

一开始是用这个 BGE-M3，然后它是有这个支持稠密向量，还有稀疏向量，还有多向量三种输出模式的。然后来我们发现它的一个稠密向量可能没有办法特别好的识别一些比较 trivial 的语义，就是在这个长的文段里面可能一两个关键词它有办法很好识别，然后当时千问三也出来了，然后它是有个更高的一个 embedding 的维度，然后感觉性能上也更强。然后我们就改用了一个千问三做这个稠密向量的一个检索，但是用，然后当时我们还是希望说用上一个更多的一个检索方式来提高我总体的性能，所以我们也是用了这个 BGE-M3 的一个稀疏检索。然后除了这个之外，我们就用了一个关键词检索来处理这些比较。在长文段里面的一些关键词是用了，再用了一个 BM25 的方法，然后最后这三个方法检索出来的文档，再进行放到一个重排序器里面，进行一个重排，然后得到最终结果，大概是这样。

**Embedding模型演进**：

| **阶段**   | **模型**       | **特点**              | **问题**                   |
| -------- | ------------ | ------------------- | ------------------------ |
| **第一阶段** | BGE-M3       | 支持稠密、稀疏、多向量三种模式     | 稠密向量在识别"trivial语义"方面表现不佳 |
| **第二阶段** | 千问3 + BGE-M3 | 千问3维度更高（4096维），性能更强 | -                        |

**混合检索策略**：

| **检索方式**   | **使用模型** | **优势**      | **适用场景**       |
| ---------- | -------- | ----------- | -------------- |
| **稠密向量检索** | 千问3      | 语义理解能力强     | 语义相似的问题        |
| **稀疏向量检索** | BGE-M3   | 关键词匹配能力强    | 包含特定关键词的问题     |
| **关键词检索**  | BM25     | 传统信息检索，精确匹配 | 包含专业术语、操作步骤名称等 |

**重排序（Reranking）**：
- 三种方法检索出的文档合并
- 使用重排序器对文档进行重新排序
- 选择最相关的文档作为最终结果

# 向量数据库是用的什么？

对，用的是Milvus，一开始是用Elasticsearch，但 Elasticsearch 它不太支持那个比较高维的向量，然后它也不支持什么稀疏向量。BM25 好像支持忘了，但是反正就比 Milvus 这些东西全部能支持，所以我们就改成了用Milvus。

**从 Elasticsearch 到 Milvus 的迁移**：

| **特性** | **Elasticsearch** | **Milvus** |
|---------|-----------------|-----------|
| **高维向量支持** | ❌ 最大1024维 | ✅ 支持4096维+ |
| **稀疏向量支持** | ❌ 不支持 | ✅ 原生支持 |
| **专业向量数据库** | ❌ 不是专门优化 | ✅ 专门为向量检索优化 |
| **增量更新** | ⚠️ 支持但不够好 | ✅ 支持良好 |

**迁移原因**：
- 千问3的 embedding 是 4096 维，Elasticsearch 无法存储
- 需要支持稀疏向量检索（BGE-M3的稀疏向量）
- Milvus 是专业向量数据库，性能更好

# 文档是在线还是离线？怎么更新知识库？

离线的。但是后面可能会再加。

**更新流程**：
1. **触发条件**：
   - 文档权限变更：某些文档从不可见变为可见
   - 新机型添加：需要添加新机型的文档
   - 文档内容更新：已有文档内容修改

2. **更新方式**：
   - 手动触发：当有文档更新时，手动调用更新 API
   - 定时更新：根据开放权限的时间表，定时更新文档

3. **技术实现**：
   - 在本地调用 embedding API
   - 将新文档或更新后的文档进行 embedding
   - 增量插入到 Milvus 数据库
   - 支持元数据过滤（如按机型分类）

**增量嵌入的优势**：
- 效率高：只处理新增或更新的文档，不需要全量重建
- 成本低：减少不必要的 embedding 计算
- 实时性：可以快速响应文档更新需求

# 你们调DeepSeek设置的温度是多少？

设置的温度一直都是0，就是我们是比较要求他这个。对，准确，就这个幻觉要求比较高的一个行业，所以温度一直都是零。

**温度 = 0 的原因**：

| **原因** | **说明** |
|---------|---------|
| **准确性要求** | 医疗行业对答案准确性要求极高，任何错误都可能带来严重后果 |
| **幻觉控制** | 温度越低，模型的输出越确定，越不容易产生幻觉 |
| **法律风险** | 如果模型回答了文档中没有的内容，可能产生法律风险 |

**温度 = 0 的副作用**：
- 当文档中没有相关信息时，模型可能直接回答"我无法回答"
- 用户体验可能不够友好

**权衡**：
- **准确性 > 用户体验**：在医疗行业，准确性比用户体验更重要
- **明确拒绝 > 错误回答**：宁愿不回答，也不能给出错误答案

# 温度是0会不会太不智能了？

会存在这个现象。对，他这个要求是严格的。对对，他我们就希望这样，就是说文档里面没有提到的，我们就不希望他能回答到用户，因为他是个医疗器械，医疗行业，肯定是不希望说文档里面没提到的，然后 AI 回答出来的，这肯定有法律风险。

我觉得它主要智能的地方可能就是怎么把文档搜出来，然后总结给你这一步，而不是说它有什么需求，我就回答它什么需求，因为就考还是考虑到这个法律的风险上面就是并不希望说我能够回答一些跟文档无关内容，这是我们并不需要它实现的嗯。

# 对agent设计模式有没有了解？

是的，我通过阅读 OpenManus 的源码，了解了多种设计模式的应用：

**1. 模板方法模式（Template Method Pattern）**

```python
# BaseAgent 定义算法骨架
class BaseAgent:
    async def run(self, request: Optional[str] = None) -> str:
        # 模板方法：定义执行流程
        while self.current_step < self.max_steps:
            step_result = await self.step()  # ⬅️ 调用子类实现
            # ...
    
    @abstractmethod
    async def step(self) -> str:  # ⬅️ 抽象方法，由子类实现
        pass

# ReActAgent 实现 step 模板
class ReActAgent(BaseAgent):
    async def step(self) -> str:
        should_act = await self.think()  # ⬅️ 调用子类实现
        if not should_act:
            return "Thinking complete"
        return await self.act()  # ⬅️ 调用子类实现
```

**特点**：
- 基类定义算法骨架（`run()` → `step()`）
- 子类实现具体步骤（`think()`、`act()`）
- 控制流程在基类中

**2. 策略模式（Strategy Pattern）**

不同的 Agent 实现不同的 `think()` 和 `act()` 策略：

```python
# 策略1：ToolCallAgent 的策略
class ToolCallAgent(ReActAgent):
    async def think(self) -> bool:
        # 策略：使用 LLM 进行工具调用决策
        response = await self.llm.ask_tool(...)
    
    async def act(self) -> str:
        # 策略：执行工具调用
        await self.execute_tool(...)

# 策略2：Manus 的策略（扩展）
class Manus(ToolCallAgent):
    async def think(self) -> bool:
        # 策略：动态调整 prompt（Context Engineering）
        if browser_in_use:
            self.next_step_prompt = await self.browser_context_helper.format_next_step_prompt()
        return await super().think()
```

**3. 继承/多态（Inheritance/Polymorphism）**

分层抽象结构：
```
BaseAgent (基础层)
  └── ReActAgent (ReAct模式层)
      └── ToolCallAgent (工具调用层)
          └── Manus (具体实现)
```

**4. 组合模式（Composition）**

Agent 组合多个组件：

```python
class Manus(ToolCallAgent):
    available_tools: ToolCollection  # 组合工具集合
    mcp_clients: MCPClients          # 组合 MCP 客户端
    browser_context_helper: BrowserContextHelper  # 组合浏览器助手
    llm: LLM                         # 组合 LLM
    memory: Memory                   # 组合内存
```

# ReAct模式你了解吗？是什么样的？

**ReAct = Reasoning（推理）+ Acting（行动）**

**ReAct 模式的核心思想**：
ReAct 是一种 AI Agent 的工作模式，通过推理和行动的循环来完成任务：

```
Think (推理) → Act (行动) → Observe (观察) → Think (推理) → ...
```

**ReAct 模式的四个阶段**：

| **阶段** | **说明** |
|---------|---------|
| **Reasoning（推理）** | 分析当前状态、决定下一步行动、使用 LLM 进行决策 |
| **Acting（行动）** | 执行决定的行动、调用工具或执行操作 |
| **Observing（观察）** | 观察行动结果、将结果存储到内存 |
| **Looping（循环）** | 基于新观察继续推理、重复直到任务完成 |

**ReAct 模式的示例**：

```
用户：帮我搜索"Python教程"并总结前3个结果

Step 1: Think
  LLM 分析：需要搜索信息，应该使用搜索工具
  → 决定：使用 web_search 工具

Step 2: Act
  → 执行：web_search("Python教程")
  → 结果：返回10个搜索结果

Step 3: Observe
  → 观察：获得了搜索结果
  → 存储：将结果添加到内存

Step 4: Think (基于新观察)
  LLM 分析：已经获得搜索结果，现在需要总结前3个
  → 决定：使用 python_execute 工具处理结果

Step 5: Act
  → 执行：python_execute(code="处理前3个结果...")
  → 结果：返回总结

Step 6: Observe
  → 观察：任务完成
  → 结束
```

# ReAct模式是怎么实现的？

基于 OpenManus 的代码，ReAct 模式的实现如下：

**1. ReActAgent 基类实现**：

```python
class ReActAgent(BaseAgent, ABC):
    @abstractmethod
    async def think(self) -> bool:
        """Process current state and decide next action"""
    
    @abstractmethod
    async def act(self) -> str:
        """Execute decided actions"""
    
    async def step(self) -> str:
        """Execute a single step: think and act."""
        should_act = await self.think()  # ⬅️ 推理阶段
        if not should_act:
            return "Thinking complete - no action needed"
        return await self.act()  # ⬅️ 行动阶段
```

**2. 执行循环（在 BaseAgent 中）**：

```python
async def run(self, request: Optional[str] = None) -> str:
    if request:
        self.update_memory("user", request)  # ⬅️ 初始观察
    
    async with self.state_context(AgentState.RUNNING):
        while self.current_step < self.max_steps:
            self.current_step += 1
            step_result = await self.step()  # ⬅️ 执行一步（Think + Act）
            # step() 内部会调用 think() 和 act()
            
            # 检查是否卡死
            if self.is_stuck():
                self.handle_stuck_state()
            
            results.append(f"Step {self.current_step}: {step_result}")
```

**3. ToolCallAgent 的具体实现**：

**Think 阶段（推理）**：

```python
async def think(self) -> bool:
    """Process current state and decide next actions using tools"""
    
    # 1. 添加下一步提示
    if self.next_step_prompt:
        user_msg = Message.user_message(self.next_step_prompt)
        self.messages += [user_msg]
    
    # 2. 调用 LLM 进行推理（包含对话历史和可用工具）
    response = await self.llm.ask_tool(
        messages=self.messages,  # ⬅️ 包含所有观察结果
        system_msgs=[Message.system_message(self.system_prompt)],
        tools=self.available_tools.to_params(),  # ⬅️ 可用工具列表
        tool_choice=self.tool_choices,
    )
    
    # 3. 解析 LLM 的决策
    self.tool_calls = response.tool_calls  # ⬅️ LLM 选择的工具
    content = response.content  # ⬅️ LLM 的思考内容
    
    # 4. 将决策添加到内存（作为观察）
    assistant_msg = Message.from_tool_calls(
        content=content, 
        tool_calls=self.tool_calls
    )
    self.memory.add_message(assistant_msg)  # ⬅️ 存储推理结果
    
    return bool(self.tool_calls)  # 返回是否需要行动
```

**Act 阶段（行动）**：

```python
async def act(self) -> str:
    """Execute tool calls and handle their results"""
    
    if not self.tool_calls:
        return "No content or commands to execute"
    
    results = []
    for command in self.tool_calls:
        # 1. 执行工具
        result = await self.execute_tool(command)
        
        # 2. 将结果添加到内存（观察阶段）
        tool_msg = Message.tool_message(
            content=result,
            tool_call_id=command.id,
            name=command.function.name,
        )
        self.memory.add_message(tool_msg)  # ⬅️ 存储观察结果
        
        results.append(result)
    
    return "\n\n".join(results)
```

**4. 完整的 ReAct 循环流程**：

```
┌─────────────────────────────────────────────────┐
│ 1. 初始化                                        │
│    - 用户请求添加到内存（初始观察）                  │
│    - 状态设置为 RUNNING                           │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 2. Think (推理阶段)                              │
│    - 读取内存中的对话历史（包含所有观察）        │
│    - 调用 LLM，传入：                            │
│      • 对话历史（观察）                          │
│      • 可用工具列表                              │
│      • 系统提示                                  │
│    - LLM 分析当前状态，决定下一步行动            │
│    - 返回工具调用决策                            │
│    - 将决策添加到内存                            │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 3. Act (行动阶段)                                │
│    - 执行 LLM 选择的工具                         │
│    - 获取工具执行结果                            │
│    - 将结果添加到内存（观察）                    │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 4. Observe (观察阶段)                            │
│    - 工具结果已存储在内存中                      │
│    - 成为下一次 Think 的输入                     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 5. Loop (循环)                                    │
│    - 回到步骤 2（Think）                         │
│    - 基于新的观察继续推理                        │
│    - 重复直到任务完成或达到最大步数              │
└─────────────────────────────────────────────────┘
```

**5. 内存管理（观察的存储）**：

```python
class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    
    def add_message(self, message: Message) -> None:
        self.messages.append(message)
```

内存中的消息序列：
```
1. user: "帮我搜索Python教程"
2. assistant: (tool_calls: [web_search("Python教程")])
3. tool: "搜索结果：..."
4. assistant: (tool_calls: [python_execute(...)])
5. tool: "总结结果：..."
```

每次 `think()` 时，LLM 都能看到完整的对话历史（所有观察结果）。

**关键代码位置**：
- ReAct 基类：`app/agent/react.py`
- 执行循环：`app/agent/base.py` 的 `run()` 方法
- Think 实现：`app/agent/toolcall.py` 的 `think()` 方法
- Act 实现：`app/agent/toolcall.py` 的 `act()` 方法
- 内存管理：`app/schema.py` 的 `Memory` 类

# LangChain和LangGraph有什么区别？


**详细对比和代码示例**：[[其他/PingCAP 平凯星辰/面试问题总结#你们当时为什么选择用 LangGraph 去写？|PingCAP面经中有详细的LangChain vs LangGraph对比和代码示例]]

# 你了解MCP吗？

是的，MCP（Model Context Protocol）是一个标准协议，用于 AI 应用与外部工具服务器之间的通信。

**MCP 的核心概念**：

MCP 允许 AI Agent 连接到外部工具服务器，并使用服务器提供的工具：

```
AI Agent (客户端)  ←→  MCP 协议  ←→  MCP 服务器 (工具提供者)
```

**在 OpenManus 中的实现**：

OpenManus 实现了完整的 MCP 客户端和服务器：

| **组件** | **位置** | **功能** |
|---------|---------|---------|
| **MCP 客户端** | `app/tool/mcp.py` | 连接 MCP 服务器、获取服务器提供的工具、将远程工具转换为本地工具代理 |
| **MCP 服务器** | `app/mcp/server.py` | 将本地工具暴露为 MCP 工具、支持工具注册和管理 |
| **Agent 集成** | `app/agent/manus.py` | 在 Agent 中集成 MCP 工具、支持连接多个 MCP 服务器 |

**MCP 的工作流程**：

```
1. 客户端连接到 MCP 服务器
   ├─→ 建立传输连接（SSE 或 stdio）
   └─→ 初始化会话

2. 获取工具列表
   ├─→ 调用 session.list_tools()
   └─→ 服务器返回可用工具列表

3. 创建工具代理
   ├─→ 为每个工具创建 MCPClientTool 实例
   └─→ 添加到工具集合

4. 执行工具
   ├─→ Agent 调用工具
   ├─→ MCPClientTool 转发到服务器
   └─→ 返回执行结果
```

**MCP 的价值**：
- ✅ 统一接口：不同厂商的工具通过统一协议暴露
- ✅ 解耦设计：工具服务器与 AI Agent 分离，便于扩展
- ✅ 标准化：遵循标准协议，易于集成和维护

# MCP的传输协议有哪些？

OpenManus 实现了两种传输协议：

**1. SSE (Server-Sent Events) - HTTP 长连接**

**实现代码**：

```python
async def connect_sse(self, server_url: str, server_id: str = "") -> None:
    """Connect to an MCP server using SSE transport."""
    streams_context = sse_client(url=server_url)  # ⬅️ HTTP SSE 客户端
    streams = await exit_stack.enter_async_context(streams_context)
    session = await exit_stack.enter_async_context(ClientSession(*streams))
    self.sessions[server_id] = session
```

**特点**：
- 基于 HTTP 长连接
- 支持跨网络通信
- 服务器需要预先运行
- 配置简单（只需 URL）

**使用场景**：
- 连接远程 MCP 服务器
- 连接云服务提供的 MCP 工具
- 跨机器通信

**配置示例**：

```json
{
  "mcpServers": {
    "remote_api": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**2. stdio (Standard Input/Output) - 进程间通信**

**实现代码**：

```python
async def connect_stdio(
    self, command: str, args: List[str], server_id: str = ""
) -> None:
    """Connect to an MCP server using stdio transport."""
    server_params = StdioServerParameters(command=command, args=args)
    stdio_transport = await exit_stack.enter_async_context(
        stdio_client(server_params)  # ⬅️ 启动子进程
    )
    read, write = stdio_transport  # ⬅️ 标准输入输出流
    session = await exit_stack.enter_async_context(ClientSession(read, write))
    self.sessions[server_id] = session
```

**特点**：
- 基于标准输入输出管道
- 客户端自动启动服务器进程
- 仅支持本地通信
- 低延迟

**使用场景**：
- 本地 MCP 服务器
- 需要自动启动的服务器
- 开发测试环境

**配置示例**：

```json
{
  "mcpServers": {
    "local_tools": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

**两种协议对比**：

| **特性** | **SSE (HTTP)** | **stdio (进程)** |
|---------|---------------|-----------------|
| **连接方式** | HTTP 长连接 | 标准输入输出管道 |
| **通信范围** | 跨网络 | 仅本地 |
| **服务器启动** | 需要预先启动 | 客户端自动启动 |
| **延迟** | 可能有网络延迟 | 极低延迟 |
| **配置** | 需要 URL | 需要命令和参数 |
| **适用场景** | 远程服务、云服务 | 本地工具、开发环境 |

# 你开发过MCP吗？配置过MCP客户端吗？

基于 OpenManus 的代码，我了解了 MCP 服务器和客户端的开发与配置：

**1. MCP 服务器开发**

**服务器实现（`app/mcp/server.py`）**：

```python
class MCPServer:
    """MCP Server implementation with tool registration and management."""
    
    def __init__(self, name: str = "openmanus"):
        self.server = FastMCP(name)  # ⬅️ 使用 FastMCP 框架
        self.tools: Dict[str, BaseTool] = {}
        
        # 初始化标准工具
        self.tools["bash"] = Bash()
        self.tools["browser"] = BrowserUseTool()
        self.tools["editor"] = StrReplaceEditor()
        self.tools["terminate"] = Terminate()
    
    def register_tool(self, tool: BaseTool, method_name: Optional[str] = None) -> None:
        """Register a tool with parameter validation and documentation."""
        tool_name = method_name or tool.name
        tool_param = tool.to_param()
        
        # 创建异步包装函数
        async def tool_method(**kwargs):
            result = await tool.execute(**kwargs)
            return json.dumps(result.model_dump())
        
        # 注册到 MCP 服务器
        self.server.tool()(tool_method)
    
    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server."""
        self.register_all_tools()
        self.server.run(transport=transport)
```

**启动服务器**：

```python
# run_mcp_server.py
from app.mcp.server import MCPServer

if __name__ == "__main__":
    server = MCPServer()
    server.run(transport="stdio")  # 或 "sse"
```

**2. MCP 客户端配置**

**配置文件（`config/mcp.json`）**：

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_filesystem"]
    },
    "remote_api": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**配置类（`app/config.py`）**：

```python
class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server"""
    type: str = Field(..., description="Server connection type (sse or stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(default_factory=list, description="Arguments for stdio command")

class MCPSettings(BaseModel):
    """Configuration for MCP (Model Context Protocol)"""
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )
    
    @classmethod
    def load_server_config(cls) -> Dict[str, MCPServerConfig]:
        """Load MCP server configuration from JSON file"""
        config_path = PROJECT_ROOT / "config" / "mcp.json"
        # 加载并解析配置...
```

**3. 在 Agent 中使用 MCP**

**初始化 MCP 服务器（`app/agent/manus.py`）**：

```python
async def initialize_mcp_servers(self) -> None:
    """Initialize connections to configured MCP servers."""
    for server_id, server_config in config.mcp_config.servers.items():
        try:
            if server_config.type == "sse":
                if server_config.url:
                    await self.connect_mcp_server(
                        server_config.url, 
                        server_id
                    )
            elif server_config.type == "stdio":
                if server_config.command:
                    await self.connect_mcp_server(
                        server_config.command,
                        server_id,
                        use_stdio=True,
                        stdio_args=server_config.args,
                    )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
```

**连接 MCP 服务器**：

```python
async def connect_mcp_server(
    self,
    server_url: str,
    server_id: str = "",
    use_stdio: bool = False,
    stdio_args: List[str] = None,
) -> None:
    """Connect to an MCP server and add its tools."""
    if use_stdio:
        await self.mcp_clients.connect_stdio(
            server_url, stdio_args or [], server_id
        )
    else:
        await self.mcp_clients.connect_sse(server_url, server_id)
    
    # 获取新工具并添加到可用工具集合
    new_tools = [
        tool for tool in self.mcp_clients.tools 
        if tool.server_id == server_id
    ]
    self.available_tools.add_tools(*new_tools)
```

**4. 完整配置示例**

**示例 1：混合配置（SSE + stdio）**：

```json
{
  "mcpServers": {
    "local_filesystem": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_filesystem"]
    },
    "remote_database": {
      "type": "sse",
      "url": "http://db-server.example.com:8000/sse"
    },
    "cloud_api": {
      "type": "sse",
      "url": "https://api.cloud.com/mcp"
    }
  }
}
```

**示例 2：开发环境配置**：

```json
{
  "mcpServers": {
    "dev_tools": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_dev_server", "--debug"]
    }
  }
}
```

**5. 实际开发流程**

**开发 MCP 服务器**：

```python
# 1. 创建工具
from app.tool.base import BaseTool

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"
    parameters = {...}
    
    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return self.success_response("Done")

# 2. 创建 MCP 服务器
from app.mcp.server import MCPServer

server = MCPServer()
server.tools["my_tool"] = MyCustomTool()
server.register_all_tools()
server.run(transport="stdio")
```

**配置客户端**：

```json
{
  "mcpServers": {
    "my_server": {
      "type": "stdio",
      "command": "python",
      "args": ["my_mcp_server.py"]
    }
  }
}
```

**在 Agent 中使用**：

```python
# Agent 会自动加载配置并连接
agent = await Manus.create()

# MCP 工具已经可用
# 工具名称会被重命名为：mcp_my_server_my_tool
```



# 用友网络项目是做什么的？

当时是后端项目，当时就是说我们要帮助中国电信国际那边升级一个新系统，就从旧升级到新。然后我当时作为实习生的话，主要就是要帮他们把数据迁移到新系统，符合这个数据格式，然后再帮他们这个提高一下他们这个查询效率，大概就这样。

# 怎么识别PostgreSQL中的慢查询SQL语句？

我采用三种方法来识别慢查询：

**1. 开启慢查询日志（log_min_duration_statement）**

最常用的方式：让 PostgreSQL 自动把超过 N ms 的 SQL 打到日志里。

```sql
-- 记录所有超过 500ms 的语句
ALTER SYSTEM SET log_min_duration_statement = '500ms';

-- 确保打开通用日志
ALTER SYSTEM SET logging_collector = on;
ALTER SYSTEM SET log_directory = 'pg_log';
ALTER SYSTEM SET log_filename = 'postgresql-%Y-%m-%d.log';

SELECT pg_reload_conf();
```

然后到日志目录里用 grep / rg / ELK 等工具就能搜出慢 SQL。

**2. 使用 pg_stat_statements 找"平均慢、总耗时多"的 SQL**

日志是按"单条语句"看，pg_stat_statements 则是帮你聚合统计：

```sql
-- 1. 在 postgresql.conf 里打开扩展
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
SELECT pg_reload_conf();

-- 2. 在目标数据库里创建扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 3. 查询统计视图
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    (total_time / calls) AS avg_time,
    (total_time / 1000 / 60) AS total_time_min
FROM pg_stat_statements
ORDER BY avg_time DESC
LIMIT 20;
```

**分析指标**：
- **avg_time 高** → 每次都慢
- **total_time 高** → 总体耗时大（高频 + 不算快）

**3. 实时监控（pg_stat_activity）**

查看当前有哪些查询在跑、跑了多久：

```sql
SELECT
    pid,
    now() - query_start AS duration,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY duration DESC;
```

可以看到哪些 SQL 正在挂着、锁等待等。

**二、拿到慢 SQL 之后：怎么分析？**

**首选工具：EXPLAIN (ANALYZE, BUFFERS)**

对慢 SQL 跑一遍：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
FROM ...
WHERE ...
ORDER BY ...;
```

**参数说明**：
- **ANALYZE**：让它真跑一遍，显示真实耗时、行数
- **BUFFERS**：显示读写的是 shared buffers 还是磁盘（IO 情况）

**执行计划关注点**：

| **关注点**        | **说明**                              | **问题信号**                                         |
| -------------- | ----------------------------------- | ------------------------------------------------ |
| **最耗时的节点**     | 通常看 actual time=... 最大、rows 特别多的那一层 | Seq Scan（顺序扫描）要特别留意：是不是应该有索引？                    |
| **估算 vs 实际行数** | rows vs actual rows                 | 差距很大 → 统计信息不准 → 需要 ANALYZE                       |
| **常见耗时节点**     | Seq Scan、Nested Loop、Hash Join、Sort | Sort Method: external merge → 说明用了磁盘，work_mem 不够 |

**常见问题信号**：

1. **WHERE 条件列没有索引**
   - `Seq Scan on table + Filter: (xxx)`
   - 如果这个条件选择性好（过滤掉很多行），应该考虑建索引

2. **ORDER BY / GROUP BY 很慢**
   - 执行计划里有 Sort 或 GroupAggregate
   - 排序字段上没有合适的索引
   - 或者出现 `Sort Method: external merge Disk`（说明写磁盘）

3. **JOIN 顺序不佳 / 缺索引**
   - 大表之间通过没有索引的字段 JOIN
   - 执行计划显示 Nested Loop + Seq Scan

4. **统计信息不准**
   - 执行计划里的 `rows=xxx` 和 `actual rows=yyy` 差几个数量级
   - 需要：`ANALYZE table_name;` 或 `VACUUM ANALYZE;`

**三、优化手段：从易到难**

**1. 优化索引（最常见 & 最有效）**

**WHERE 条件中常用的列**：

```sql
-- 查询
SELECT ... FROM orders 
WHERE user_id = 123 AND created_at > now() - interval '30 days';

-- 适合的索引
CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at);
```

**原则**：
- WHERE 里一起经常出现的列 → 组合索引（注意列顺序：过滤性更强 / 等值条件优先放前面）
- 区分度低的字段（比如 status 小枚举值）单列索引用处有限

**JOIN 列**：
- 两个表按 `A.id = B.a_id` join，就要确保：
  - `A.id` 是主键 / 唯一索引
  - `B.a_id` 上也有索引（特别是多对一关系的"多"那一侧）

**ORDER BY / GROUP BY**：

```sql
-- 查询
SELECT ... FROM logs 
WHERE project_id = 1 
ORDER BY created_at DESC 
LIMIT 100;

-- 可以考虑
CREATE INDEX idx_logs_project_created_at
ON logs (project_id, created_at DESC);
```

这样既能利用 WHERE，又能利用 ORDER BY，避免额外排序。

**2. 优化 SQL 写法**

| **问题** | **错误写法** | **正确写法** |
|---------|------------|------------|
| **避免不必要的 SELECT *** | `SELECT * FROM ...` | 只选你真的要用的列 |
| **用合适的写法触发索引** | `WHERE date(created_at) = '2025-12-01'` | `WHERE created_at >= '2025-12-01'::date AND created_at < '2025-12-02'::date` |
| **避免在索引列上做函数** | `WHERE lower(email) = 'xxx'` | 用表达式索引：`CREATE INDEX idx_users_lower_email ON users (LOWER(email));` |
| **拆分过长、过复杂的 SQL** | 很多 join + 子查询 + 聚合 | 先把核心过滤结果放到临时表 / CTE，再进一步聚合 |

**3. 调整表结构 / 归档历史数据**

- **历史表归档**：可以建分区表按时间分区（`PARTITION BY RANGE (created_at)`）
- **合适的数据类型**：用 INTEGER/BIGINT 而不是 TEXT 做主键 / join key

**4. 调整 PostgreSQL 配置（适度）**

| **配置项** | **说明** | **调整建议** |
|---------|---------|------------|
| **work_mem** | 排序 / HASH / JOIN 内存 | 如果执行计划里经常看到 `Sort Method: external merge Disk`，需要调大 work_mem：`SET work_mem = '64MB';` |
| **shared_buffers** | 缓存大小 | 一般设置成物理内存的 25% 左右 |
| **autovacuum** | 自动 VACUUM / ANALYZE | 确保 autovacuum 开着，对更新特别频繁的表可以调高 aggressiveness |

**四、实战案例：订单查询优化**

**场景**：电商网站「订单列表」接口很慢，查询某个用户最近 30 天的订单，按时间倒序取 50 条。

**原始 SQL**：

```sql
SELECT
    o.id,
    o.user_id,
    o.created_at,
    o.total_amount
FROM orders o
WHERE o.user_id = 123
  AND o.created_at >= now() - interval '30 days'
ORDER BY o.created_at DESC
LIMIT 50;
```

**问题**：orders 表有几百万行，没有合适索引，接口响应时间常年在 1~2 秒。

**优化步骤**：

**1. 用 pg_stat_statements 确认问题**：

```sql
SELECT
    query,
    calls,
    total_time,
    mean_time AS avg_ms_per_call
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**2. 执行 EXPLAIN (ANALYZE, BUFFERS)**：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id, o.user_id, o.created_at, o.total_amount
FROM orders o
WHERE o.user_id = 123
  AND o.created_at >= now() - interval '30 days'
ORDER BY o.created_at DESC
LIMIT 50;
```

**执行计划问题**：
- `Seq Scan on orders`：全表扫描，扫描了 500 万行
- `Sort`：对 150 万行进行排序
- 总耗时：~1200ms

**3. 创建索引**：

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_created
ON orders (user_id, created_at DESC);
```

**说明**：
- `user_id` 放前面 → 对应等值过滤
- `created_at DESC` 放后面 → 对应 range + 排序
- 使用 `CONCURRENTLY` → 线上建索引时不锁写（速度慢一点但安全）

**4. 更新统计信息**：

```sql
ANALYZE orders;
```

**5. 再次 EXPLAIN 验证优化效果**：

优化后的执行计划：
- `Index Scan using idx_orders_user_created`：使用索引扫描
- `rows` 从几百万 → 几千
- `actual time` 从 ~1200ms → 5ms 左右
- **性能提升两个数量级**

**6. 验证效果**：

```sql
SELECT
    query,
    calls,
    mean_time AS avg_ms_per_call
FROM pg_stat_statements
WHERE query LIKE 'SELECT o.id, o.user_id, o.created_at, o.total_amount FROM orders%'
ORDER BY mean_time DESC
LIMIT 5;
```

看到 `avg_ms_per_call` 从 1200ms 降到 8ms，说明优化成功。

**完整优化流程总结**：

| **步骤** | **操作** | **工具/方法** |
|---------|---------|------------|
| **1. 发现问题** | 用户反馈接口慢 / 监控告警 | pg_stat_statements / 日志 |
| **2. 锁定 SQL** | 拿到 SQL 模板和具体参数 | pg_stat_statements |
| **3. 分析执行计划** | EXPLAIN (ANALYZE, BUFFERS) | 找最耗时的节点、Seq Scan、统计信息 |
| **4. 设计索引** | 分析 WHERE / JOIN / ORDER BY | 设计合适的复合索引（注意列顺序） |
| **5. 执行优化** | 创建索引（CONCURRENTLY）+ ANALYZE | 线上安全建索引 |
| **6. 验证效果** | 再次 EXPLAIN | 确认变成 Index Scan，耗时明显下降 |
| **7. 应用层验证** | 接口响应时间、pg_stat_statements | 确认 avg_time / total_time 明显变好 |


# 对CICD和DevOps了解吗？

了解的话就是我在西门子那一边部署，就是测部署模型部署应用的时候用过这个 GitLab 的一个CICD，然后主要就。就是当时就是分成多个链路，首先是先测试，我记得有四个节点先测试，但第有一个好像第三个节点是测试整个功能，其余齐全，然后第一第二好像是部署，最后是在正式上线。我忘了，因为我当时也是用过，只能说用过，没有说我们这自己是没有说参与这个编写这个 CICD 的这个链路的。

**当前经验**：
- 在西门子实习时使用过 GitLab CI/CD
- 了解基本流程：测试 → 部署 → 正式上线（4个节点）
- 只是使用过，没有参与编写 CICD 链路

**团队背景**：
- 在 AI agent 出现之前，一直做 DevOps 平台开发
- 有自研的 DevOps 产品
- 基于 Jenkins 做二次开发
- 希望通过 AI agent 在 DevOps 方面找落地场景

**学习方向**：
1. Jenkins 深入学习：Pipeline as Code、插件开发、分布式构建
2. AI Agent 在 DevOps 中的应用：代码审查自动化、测试用例生成、部署决策辅助、故障诊断




# 如果想继续做agent开发，需要关注或学习什么内容？

**面试官建议**：
可能需要一些项目经验，我觉得你的这个学历，还有你的这个知识广度什么是没问题的？后面可能需要一些实际的一些整体开发经验。因为相对来说，你在西门子做的这个其实是，就是我个人感觉还是比较简单的，现在 agent 它其实发展很快。对吧？它的一些，你比如说我们在互联网上用的那些，比如说那个腾讯元宝，还有什么 Kimi 这种，它们内部绝对不仅仅是简单是做了一个这个 RAG 嵌入或者调了一些工具这么简单的。还有一些，比如说长期记忆、短期记忆还有什么是那些大文档的一些处理什么的。TOKEN 超限这种很多异常场景处理之类的。对，这个还是就是说我建议就是可能是需要多一些项目经验吧。

**当前优势**：
- ✅ 学历背景好
- ✅ 知识广度足够

**需要提升**：
- ❌ 实际项目开发经验不足
- ❌ 当前项目相对简单

**复杂 Agent 系统的特点**：

| **特性** | **说明** |
|---------|---------|
| **长期记忆** | 用户会话历史持久化、知识图谱构建、用户偏好学习 |
| **短期记忆** | 对话上下文管理、多轮对话状态维护、上下文窗口优化 |
| **大文档处理** | 文档分块策略优化、长文档摘要与压缩、多文档信息整合 |
| **异常场景处理** | TOKEN超限处理、API调用失败重试、限流与降级、错误恢复 |

**学习方向**：
- 多做实际项目，积累复杂场景经验
- 关注业界最佳实践（如腾讯元宝、Kimi 等产品）
- 深入学习 Agent 的高级特性



