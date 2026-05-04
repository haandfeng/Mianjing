---
title: RAG优化全链路
type: topic
updated: 2026-05-04
---

# RAG优化全链路

> 链路：文档预处理 → 切片 → 多路嵌入（dense + sparse + BM25）→ HNSW 向量索引 → 多路召回 → Reranker 精排 → 上下文压缩 → LLM 生成。每环节都有可优化点。

## 高频问法
- "RAG 系统流程；准确率怎么从 76% 提到 92%" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[小红书/小红书产品工程师一面面经]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "Embedding 模型怎么选 / 切换；BGE-M3 vs 千问3" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "为什么用 Milvus 不用 Elasticsearch" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "HNSW 是什么；KNN vs ANN；FLAT 索引和 KNN 的关系" — [[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "混合检索（dense + sparse + BM25）+ Reranker；RRF" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "Chunk 切分策略；语义分块 / 滑动窗口 / 层次化" — [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[蔚来/蔚来一面RAG深挖]]
- "RAG 评估方案 + LangSmith trace" — [[面经较少公司/PingCAP 平凯星辰/面试问题总结]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
- "为什么不用大窗口模型直接喂全文档" — [[蔚来/蔚来一面RAG深挖]]

## 答题骨架

### 1. 端到端链路
```
文档 → ETL（XML→Markdown）→ Chunk 切分
   → 多路嵌入：dense（千问3）+ sparse（BGE-M3）+ BM25
   → Milvus 存储（HNSW + 倒排索引）
   → Query Refine（多语言 / 同义词扩写）
   → 多路召回（向量 + 稀疏 + 关键词，Top 20）
   → Reranker 精排（Top 10）
   → 上下文压缩 / Reorder
   → LLM 生成
```

### 2. ETL 与 Chunk
- **XML → Markdown**：开源库不支持嵌套 / 合并表格 → 自己改库；用相同信息填合并表格的每行每格让 LLM 能理解
- **Chunk 策略选型**：
  - 固定长度：简单但断语义
  - **语义分块**：按句子 / 段落语义边界切，相邻嵌入相似度低于阈值时切
  - **滑动窗口**：相邻 chunk 重叠 10-20%，避免边界丢失
  - **层次化**：章节 → 小节 → 段落多粒度
  - **基于标记符**：Markdown `#`、代码 `function` 切
  - 推荐：技术文档 = 层次化 + 语义 + 滑动窗口

### 3. Embedding 选型
| 模型 | 维度 | 输出 |
|---|---|---|
| BGE-M3 | 1024（dense）+ sparse + multi-vector | 三模式都有，关键词强 |
| 千问3 | 4096（dense） | 维度高语义强，但只 dense |

- 实战组合：dense 用千问3、sparse 用 BGE-M3、关键词 BM25 → 三路召回
- Embedding 模型微调：用领域数据做 domain fine-tune 提升专业术语效果

### 4. 向量索引：HNSW vs FLAT
- **FLAT** = 暴力搜索（精确 KNN，O(N·d)）
- **HNSW** = 分层小世界图（近似 ANN，O(logN)）
  - 顶层稀疏快速导航 → 中层 → 底层精确搜索
  - 关键参数：M（每层最大连接数 16-32）、efConstruction（构建宽度 200）、ef_search（查询宽度 100-200）
  - 召回率 95%+，延迟 ms 级
- **概念区分**：KNN 是算法 / 目标，FLAT / HNSW 是实现方式
- **稀疏向量**用倒排索引（关键词 → 文档列表）

### 5. 为什么用 Milvus 不用 Elasticsearch
- ES 最大向量维度 1024，千问3 是 4096 维放不下
- ES 不支持稀疏向量（BGE-M3 sparse）
- Milvus 专门优化向量检索，原生 HNSW + 稀疏倒排索引

### 6. 多路召回 + Reranker
**召回三路**：
- Dense（千问3）：语义相似
- Sparse（BGE-M3）：关键词 + 部分语义
- BM25：精确关键词

**Reranker 选型**：
- 基于大模型（千问 / BGE-M3 reranker）：准但慢，30 个文档约 2 秒
- **RRF（Reciprocal Rank Fusion）**：每路排名取倒数 + 相加，几十毫秒，但单路才出现的关键文档可能被埋没
- 实战：业务能等就用 LLM reranker，业务对延迟敏感用 RRF

### 7. Query 优化
- **Query Refine**：把问题生成中英多语言 + 同义词版本，分别检索后合并
- **Query Decomposition**：复杂问题拆子问题分别检索
- **HyDE**：让 LLM 先生成假设答案，用答案做嵌入检索

### 8. 评估体系（LangSmith）
- 评估三维度：
  - **Correctness**：模型回答 vs 标准答案一致性
  - **Relevance**：回答是否相关
  - **Groundedness（关联准确性）**：回答有没有基于检索文档（防幻觉）
- 用 LLM judge（如 DeepSeek V3）打分；先和人工标注做 AB 测试，F1 ~0.8 才采信
- LangSmith trace：每个节点的输入输出 + 耗时；定位是哪一步出错

### 9. 上下文压缩 / 多模态处理
- LongContextReorder：把最相关的放头尾，模型注意力集中
- 上下文压缩：先用一个小模型筛选最相关片段
- 多模态文档转文本：OCR（图片）/ Markdown 表格 / LaTeX 公式 / 流程图描述

### 10. 进阶方向
- **GraphRAG**：实体 / 关系建图，多跳推理
- **Dynamic RAG**：高质量 QA 入库做长期记忆
- **CoT / ToT**：让 LLM 一步步思考多文档信息

### 11. 为什么不用大窗口模型直接读全部文档
- 成本：百万 token 调一次贵
- 效率：长上下文响应慢
- 注意力分散：250 万 token 模型也抓不住关键信息
- 可扩展性：文档增长后大窗口仍有上限
- RAG 灵活：可结合多种检索策略

## 易错点 & 追问
- "FLAT 是不是 KNN 算法" → 不是，FLAT 是**实现 KNN 的索引**之一
- "ANN 是 HNSW 吗" → ANN 是一类目标，HNSW 是其中一种实现
- 混合检索的 Reranker 是必要的，不能直接合并三路结果
- 评估 RAG 别只看 LLM judge，必须有人工 ground truth
- Chunk 切太大噪声多，太小丢上下文；500-1000 token 是常见折中

## 深入阅读
- 原始专栏 [[后端技术专栏/向量索引-HNSW和KNN-ANN区别]]
- Agent 专栏 [[Agent技术专栏/MCP_SSE_文档]]
- 真题来源 [[蔚来/蔚来CICD组AI agent实习生一面面经-详细版]]、[[面经较少公司/PingCAP 平凯星辰/面试问题总结]]、[[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]、[[小红书/小红书产品工程师一面面经]]、[[蔚来/蔚来一面RAG深挖]]
