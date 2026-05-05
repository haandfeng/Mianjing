---
title: MCP与Tool管理
tags:
  - Agent
  - MCP
  - 面试八股
date: 2026-03-11
---

# MCP 与 Tool 管理

## MCP（Model Context Protocol）是什么

Anthropic 开源的协议，定义了 LLM 应用与外部工具/数据源之间的标准通信接口。

**核心架构：Client-Server 模式**
- **Host**（如 Claude Desktop、IDE 插件）内嵌 MCP Client
- MCP Client 通过标准协议连接多个 MCP Server
- 每个 Server 暴露三类能力：**Tools**（可调用的函数）、**Resources**（可读取的数据）、**Prompts**（预定义的提示模板）

**类比：** USB-C 统一了充电口，MCP 统一了 AI Agent 连接工具的方式。之前每接入一个新工具就要写一套适配代码，MCP 让工具提供方只需实现一个标准 Server，所有支持 MCP 的 Host 都能直接用。

**与 LangChain Tool 的关系：** LangChain 的 Tool 机制解决的是同一个问题——让 LLM 动态调用外部能力。区别在于 LangChain Tool 是框架内的抽象，MCP 是跨框架、跨应用的开放协议。LangChain 也已支持接入 MCP Server。

## 常见的 MCP Server 类型

- 文件系统读写（Filesystem）
- 数据库查询（PostgreSQL、MySQL）
- 搜索引擎（Brave Search、Google）
- 知识库检索（如 [[RAG混合检索|Milvus 混合检索]]）
- 代码仓库操作（GitHub）
- 日历/邮件（Google Calendar、Gmail）

## Tools 过多的问题

当 Agent 接入几十个 tools 时会出现两个核心问题：
1. **Token 消耗大：** 每个 tool 的 schema 描述都要放进 system prompt，几十个 tool 可能占掉几千 token。
2. **选择准确率下降：** LLM 在 5-6 个 tool 里选对的概率远高于在 50 个里选。tool 越多，语义重叠越大，越容易选错。

## 解决方案（从简单到复杂）

### 1. Tool 分组 + 按需加载

不把所有 tool 一次性塞给 LLM，而是按场景分组。先让 LLM 判断用户意图属于哪个类别，再只加载该类别的 tools。

类似 [[RAG混合检索|RAG 的两阶段检索]]——先粗筛再精排。

### 2. Tool 描述优化

- 把每个 tool 的 name 和 description 写得足够区分，减少语义重叠
- 描述要写"什么时候该用"和"什么时候不该用"，帮 LLM 做排除法
- 避免模糊描述如"处理数据"，要具体到"从 PostgreSQL 执行 SQL 查询并返回结果"

### 3. RAG 选 Tool

把所有 tool 的描述做 embedding 存起来，用户 query 进来后先做语义检索，只取 top-k 相关的 tool 放进 prompt。

本质上是把 tool selection 变成了一个检索问题。

### 4. 多级 Agent 架构（Supervisor 模式）

一个 supervisor agent 负责路由，把任务分发给专门的 sub-agent，每个 sub-agent 只持有自己领域的几个 tools。这样每一层 LLM 看到的 tools 数量都很少。

在 [[LangGraph]] 中对应 supervisor 模式：supervisor 节点根据用户意图把控制权交给对应的 sub-graph。

### 5. Fine-tune / Few-shot

对 tool calling 能力做微调或者在 prompt 里给几个 tool 选择的示例，提高选择准确率。适合 tool 集合相对固定的生产场景。

## 面试回答模板

> 用过文件系统、数据库查询、搜索引擎、知识库检索等类型的 MCP/Tool。Tools 过多的核心问题是 token 占用和选择准确率下降。解决思路：一是 Tool 分组按需加载，先判断意图再加载对应组的 tools；二是用 RAG 的思路做 tool 检索，把 tool 描述 embedding 化，按语义相关性只取 top-k；三是多级 Agent 架构，supervisor 路由到持有少量 tools 的 sub-agent。
