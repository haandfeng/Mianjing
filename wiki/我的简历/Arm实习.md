---
title: Arm 实习
type: resume-section
period: 2026/01 – 2026/04
updated: 2026-07-19
---

# Arm 实习（2026/01 – 2026/04）

## 简历原文（逐条，2026-07 版）

> 重构 **Causal Profiling (Coz)** 性能剖析工具，通过因果实验量化关键代码段优化对系统整体**吞吐量**的影响。

> 支持**程序预热后延迟启动分析**与**完整调用栈采集**，并实现**内核级函数 Profiling**，将工具适用范围从用户态扩展至内核态。

> 发现 Coz/Perf 在 **off-CPU** 场景下测量失准的问题，设计 **Block Sampling** 采样机制并**修改 Linux 内核 Perf 工具**，实现对多线程 **on-CPU 执行热点**与 **off-CPU 等待瓶颈**（锁竞争、I/O 排队）的统一精准剖析。

> ⚠️ 旧版简历第 4 条（用 Coz 剖析 **llama.cpp 和 MySQL**，MySQL 瓶颈定位到 CRC 校验函数）**已从 2026-07 版简历删除**，但仍是真实经历，可作口述案例："工具做出来后怎么用"。

## STAR 自陈

- **S**：Causal Profiling (Coz, SOSP 2015 best paper) 工具能量化"如果某段代码加速 X%，整体吞吐提升多少"，但开源版本只能采 on-CPU 热点，不能采 off-CPU 等待，且需要程序启动一段时间后才能稳定采样。
- **T**：把 Coz 改造成生产可用的 Arm 平台 profiler，覆盖 on-CPU + off-CPU，验证团队优化 issue。
- **A**：(1) 加预热启动机制（避开冷启动噪声）；(2) 加完整调用栈采集；(3) 修改 Linux Perf 让它能 sample 内核级函数；(4) 引入 Block Sampling 概念修改 Linux 内核 Perf 工具，把 sleep / 阻塞时间也纳入 trace；(5) 用改造后的 Coz 跑 llama.cpp 和 MySQL 验证。
- **R**：MySQL 瓶颈定位到 CRC 校验函数，发现 Arm SIMD 指令集缺少对应优化（vs x86 SSE4.2 CRC32 指令）；validated llama.cpp 性能优化 issue。

## 关键数据 / 名词
- **Causal Profiling (Coz)**：来源 SOSP 2015 论文，2024 年也有跟进；AMD LCM 已用类似方案。
- **Block Sampling**：自创概念，让 perf 在线程 sleep / wake 时也打点。
- **off-CPU**：线程 sleep / 阻塞 / 等待 IO 的时间。
- **on-CPU**：线程实际占 CPU 计算的时间。
- **内核版本**：从 Linux 5.x 迁移到 6.8 内核。
- **Profile 目标**：llama.cpp、MySQL；落点是 CRC 校验函数（MySQL）。

## 跨简历联动
- 已于 2026/04 结束（后续：[[字节实习]] → [[谷歌实习]]）。曾是面试被深挖最多的项目（[[公司/快手]] [[公司/小红书]] [[公司/微软]] 都重点问了）。
- 详细 Q&A 库：[[ARM-Profiling]]
- 主题文章：[[Linux与IO模型]] · _算法/README_（已移除）（DAG 拓扑相关）
