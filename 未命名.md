


在 Agent 模式下，你需要引入一个**控制中枢（Reasoning Core）**。

- **不再预设顺序**：Agent 看到问题后，由它决定是先去 `Search_Manual`（查手册），还是先 `Clarify_User_Intent`（反问用户），或者发现信息不足时调用 `Check_Error_Codes`。
    
- **引入 ReAct 模式**：通过 `Thought -> Action -> Observation` 的循环，让 LLM 自主决定何时停止检索并生成答案。




既然你提到了 **Clawbot**（通常指具有强自主性的工具调用者）和 Anthropic 的思路，你可以引入 **Plan-and-Execute** 模式：

1. **Planner 节点**：Agent 接收复杂指令（如：“对比 A 型号和 B 型号的维护周期并制定检查计划”），先生成一份待执行的任务清单。
    
2. **Executor 节点**：逐条执行工具调用。
    
3. **Reflector 节点（关键）**：这是你目前 92% 正确率继续突破的关键。在生成答案前，由一个 Self-Correction 节点根据 `Groundedness` 准则自检：_“我引用的文档真的支持这个结论吗？”_ 如果不支持，重新进入 Loop




在 LangGraph 中，你的 `State` 对象需要承载更多的“记忆”而非仅仅是“变量”：

- **Shared Memory**：记录 Agent 之前的尝试。例如：_“我已经尝试过检索‘球管过热’，但没有找到解决方案，下一步我应该尝试检索‘冷却系统故障’。”_





考虑使用memory的方式，记录做过什么样子的尝试。

能够对检索web，查询，生成search语句

能够对文档进行学习理解，，生成回答，改写query和查询


