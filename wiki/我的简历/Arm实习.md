---
title: Arm 实习
type: resume-section
period: 2026/01 – 至今
updated: 2026-05-04
---

# Arm 实习（2026/01 – 至今）

## 简历原文（逐条）

> 负责 Profiling 工具研发工作，重构开发 **Causal Profiling (Coz)** 工具，量化关键代码优化对整体系统吞吐量影响。

> 实现 Coz **程序预热后启动分析**、收集**完整的调用栈信息**等方式，并实现 **profile 内核级函数**，提高工具的兼容性和准确性。

> 发现 Coz(Perf) 在 **off-CPU 情形下测量不够精准**的问题，引入 **Block Sampling** 概念，修改 **Linux 内核 Perf 工具**，让其能够精准 Profile 多线程的 **on-CPU 执行热点**与 **off-CPU 等待瓶颈**（如锁竞争、I/O 排队）。

> 利用 Coz 对 **llama.cpp 和 MySQL** 进行性能剖析。验证团队对 llama.cpp 关于 Arm 平台上性能优化 issue 的准确性。将 **MySQL 的瓶颈定位到 CRC 校验函数**，指出 Arm 与 x86 指令差异造成的性能瓶颈。

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
- 这是当前在职岗位 → 面试时被深挖最多的项目（[[公司/快手]] [[公司/小红书]] [[公司/微软]] 都重点问了）。
- 详细 Q&A 库：[[ARM-Profiling]]
- 主题文章：[[Linux与IO模型]] · [[算法/README]]（DAG 拓扑相关）
