---
title: Java RPC 框架项目
type: resume-section
period: 个人项目
updated: 2026-05-04
warning: 简历是 Nacos 注册中心，部分早期面经描述用了 Etcd —— 见下方说明
---

# Java RPC 框架（GitHub）

## 简历原文

> 基于 **TCP 的自定义协议和 Netty** 实现高性能 RPC 框架。利用 **JDK 动态代理**，实现无感透明远程调用。

> 基于统一 **SPI 与工厂模式**实现可插拔序列化、负载均衡与容错策略。

> 集成 **Nacos** 作为服务注册中心，使用线程安全的 **ConcurrentHashMap** 存储本地服务注册信息，实现服务注册与发现。

## ⚠ Nacos vs Etcd 不一致说明

简历最终版本使用 **Nacos** 注册中心。但仓库内部分早期面经文件（如 [[快手/支付方向/快手日常实习面经]]）描述时用了 **Etcd**。

可能原因：项目初期用 Etcd（基于 watch 机制 + 租约），后期重构为 Nacos（更适合 Java 生态、有 SDK 心跳）。

**面试时统一口径建议**：以简历为准说 Nacos；如被追问"为什么不用 Etcd / ZooKeeper"，可以讲：
- Nacos 自带 SDK 心跳和健康检查，集成成本低
- Etcd 需要自己管租约 + watch，适合 Go / 云原生场景
- ZooKeeper CP 强一致，对注册中心 AP 场景反而不利

## 关键数据 / 名词
- **栈**：Netty + 自定义 TCP 协议 + JDK 动态代理 + SPI + Nacos + ConcurrentHashMap
- **可插拔**：序列化（JSON/Hessian/Protobuf）+ 负载均衡（轮询/一致性哈希）+ 容错（Fail-over/Fail-back）
- **协议头**：魔数 + 版本号 + 序列化类型 + requestId + bodyLength

## 跨简历联动
- 详细 Q&A 库：[[Java-RPC框架]]
- 主题文章：[[RPC与Netty]] · [[Java并发集合]] · [[限流熔断容错]]
- 被深挖公司：[[公司/快手]] [[公司/蚂蚁]] [[公司/Cider]]
- raw 专栏：[[专栏/后端/RPC框架整理后]]
