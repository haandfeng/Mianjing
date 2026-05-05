---
title: 虾皮 / Shopee
type: company-profile
updated: 2026-05-04
---

# 虾皮 / Shopee

## 概览
- 方向：Shopee 数据平台部 AI Agent 实习生（北京 DB Infra）
- 难度：单场面经覆盖面极广 —— RAG 全链路（embedding/向量库/HNSW/重排/分层/递归/评测）+ Spring Starter / Profile / Nacos 热配置 + Redis Lua 原子性
- 一句话画像：把西门子 RAG 讲到能聊 1 小时；八股要会 Spring Starter 不是注解、Nacos 长轮询热配置原理、Lua 单线程不是 Redis 单线程

## 面经文件
- [[虾皮/Shopee DB Infra 北京平台实习面试问题总结]] —— RAG 系统架构（接手框架 + 测评不好 + 重构 ETL）+ embedding 流水线（XML→Markdown 改开源库表格嵌套 + 千问3 4096 维 + ES→Milvus）+ HNSW 索引（vs FLAT 延迟 -80%）+ Milvus 混合索引（dense + sparse + BM25 一张表）+ BGE-M3 reranker（30 文档 2 秒 vs 千问 10 文档 2 秒 vs RRF）+ 分层/递归检索（最后没用）+ LangSmith 评测（200+ 中英文，三维度）+ 用友实习（统一异常 + 慢查询优化 + 事务回滚 + 幂等）+ 秒杀 Lua 原子性（不是 Redis 单线程，是 Lua 整个脚本作为一个命令）+ Spring Starter（不是注解，是依赖包，自动配置）+ 多环境配置（Profile vs Nacos）+ Nacos 热配置长轮询原理

## 考察重点（按出现次数排序）
1. **RAG 全链路（最大头）** —— XML 表格嵌套合并的 trick（每行用同样信息表示）；Milvus HNSW 索引 vs FLAT；Milvus 一张表存 dense + sparse + BM25 实现混合索引；BGE-M3 reranker 在 30 文档下比千问还快 3 倍；分层/递归检索测试效果差最终没上线
2. **LangSmith 评测三维度** —— Correctness（学生 vs 老师对比，AI 多内容 OK 少内容不 OK，事实矛盾打错）/ Relevance / Groundedness；用 DeepSeek V3.1 跑生成和评测（MoE 架构激活神经元不一样合理）
3. **Spring Starter** —— 不是注解是依赖包；包含自动配置类（META-INF/spring.factories）+ 条件注解（@ConditionalOnClass 等）；命名规范官方/第三方
4. **多环境配置：Profile vs Nacos** —— Profile 适合单体应用；Nacos 适合微服务（集中管理 + 动态刷新 + 命名空间隔离 + 配置版本管理）
5. **Lua 脚本原子性的本质** —— 不是因为 Redis 单线程，而是整个脚本作为一个命令，执行期间不切换其他命令（脚本时间要 <1s，不能有阻塞操作）
6. **秒杀完整方案补充** —— 限流（前端置灰/网关令牌桶）+ 库存预热 + Redis SET 记录已购用户 + DECR 原子扣减 + RabbitMQ 削峰解耦持久化 + Redis 主从/MQ ACK 异常处理
7. **慢查询优化 + 事务管理** —— 统一异常处理 + 事务回滚 + 断点续跑 + 幂等写入 + 分批写入

## 真题摘录（值得背的）

> **Lua 脚本为什么在 Redis 中执行是原子性的？** 出处 [[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
> 关键点：不是因为 Redis 单线程，而是整个 Lua 脚本被 Redis 视为一个完整的命令。执行期间 Redis 不会处理其他命令，所有 redis.call 在同一线程顺序执行。注意脚本时间要 <1s，不能有 BLPOP/网络/文件 IO 等阻塞操作；脚本错误不会回滚已执行的 Redis 命令。

> **Milvus HNSW vs FLAT 的对比基线？** 出处 [[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
> FLAT = 全部进行比较的精确暴力检索；HNSW = 分层导航小世界 ANN（近似最近邻），延迟 -80% 同时召回准确率几乎不损失。HNSW 是 ANN 算法的一种，ANN 是所有近似最近邻搜索算法的统称。

> **Spring Boot Starter 是什么？** 出处 [[虾皮/Shopee DB Infra 北京平台实习面试问题总结]]
> Starter 不是注解，是预配置的依赖包。作用：①简化依赖管理（一个 starter 自动引入相关依赖并解决版本兼容）；②自动配置（包含自动配置类 + META-INF/spring.factories 注册 + @ConditionalOnClass 等条件注解）；③约定优于配置（合理默认 + 开箱即用）。命名：官方 spring-boot-starter-{name}，第三方 {name}-spring-boot-starter。

## 复习清单（双链）
- [[RAG优化全链路]]
- [[Agent设计模式与MCP]]
- [[Redis分布式锁]]
- [[Redis数据结构与大Key]]
- [[Redis缓存三大问题]]
- [[Spring核心]]
- [[消息队列不丢不重]]
- [[MySQL索引与执行计划]]
- [[InnoDB事务与锁]]
- [[西门子RAG]]
- [[用友数据迁移]]
- [[黑马点评秒杀]]
