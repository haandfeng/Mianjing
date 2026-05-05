---
title: PingCAP / 平凯星辰
type: company-profile
updated: 2026-05-04
---

# PingCAP / 平凯星辰

## 概览
- 方向：日常实习（数据库公司，但这场聊得几乎全是 AI 项目）
- 难度：项目深挖 —— Hackathon 改简历项目和西门子 RAG 都被反复追问
- 一句话画像：要把 LangChain vs LangGraph 的具体差异（resumable / traceable / human-in-the-loop）讲清楚；AI Coding 实战的痛点和应对要有

## 面经文件
- [[面试问题总结]] —— Hackathon 项目（鱼克松改简历，多 agent 协同，DeepSeek V3 + 硅基流动 + 拿 2000 块）+ Cursor 实际问题六大类（局部视角 / 改太多 / 风格不一致 / 不管测试 / 数据验证 / 工具选错 / Git 配合 / 可读性）+ 模型选型对比（DeepSeek 慢但好 vs Groq OSS 120B 快但差）+ Prompt 调优系统化方法（结构化设计 + 迭代 + Few-shot + 评估体系）+ LangChain vs LangGraph 详细对比（图编排 + 状态管理 + checkpoint）+ 西门子 RAG 优化
- [[面试问题总结]] —— 简化版问题列表

## 考察重点（按出现次数排序）
1. **AI Coding 实际问题** —— 局部视角局限、一改就改太多、代码风格不一致、不管测试边界、数据验证假设理想情况、工具选择不当（pydantic）、Git 冲突、可读性维护性
2. **Prompt 工程系统化** —— 结构化设计（角色 / 任务分解 / 输出格式 / Few-shot）+ 迭代优化（基准测试 / A/B 测试）+ 关键词覆盖率 / 格式正确率 / 用户满意度
3. **LangChain vs LangGraph** —— 链式 vs 图编排；resumable（中断后从 checkpoint 继续不重头）/ traceable（自动记录每节点输入输出耗时）/ human-in-the-loop（流程中暂停等人工审核）
4. **AI Hackathon 流程** —— Parser 解析 → 评价 → 修改 → 总结；招聘经理评分 ≥9 分通过否则循环
5. **模型选型权衡** —— DeepSeek 3.2 通过硅基流动调用慢（30 分钟跑完）但效果好；Groq OSS 120B 几秒跑完但效果差。GPT-4.5 太贵
6. **西门子 RAG**

## 真题摘录（值得背的）

> **你用 Cursor 遇到哪些实际问题？** 出处 [[面试问题总结]]
> 六类：①局部视角（monorepo 只看局部文件）；②一改就改太多（"优化下这个函数"会顺手改接口签名 + 调用方）；③代码风格不一致（绕过项目规范）；④不管测试边界；⑤数据验证假设理想（pydantic 字段默认 required，要手动改 Optional）；⑥Git 冲突 + 对构建系统不敏感（只改源码，不管 CI / 代码生成）。本质："文件层面聪明，工程化层面半懂不懂"。

> **LangChain vs LangGraph 关键差别？** 出处 [[面试问题总结]]
> LangChain = "组件库 + 简单链式"，没有 resumable / traceable / human-in-the-loop。LangGraph = "图编排 + 状态管理"，内置 checkpoint 可从中断节点继续 + 自动记录执行历史可回溯 + 支持节点暂停等人工审核。LangGraph 底层依赖 LangChain 组件，可配合使用。

## 复习清单（双链）
- [[RAG优化全链路]]
- [[Agent设计模式与MCP]]
- [[消息队列不丢不重]]
- [[西门子RAG]]
