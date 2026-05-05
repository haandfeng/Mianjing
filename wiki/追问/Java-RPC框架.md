---
title: Java-RPC框架
type: project
updated: 2026-05-04
---

# Java-RPC框架

## 一句话介绍
基于 **Nacos** + Netty 的自研 Java RPC 框架，含心跳、ShutdownHook、自定义协议头、requestId 异步映射、容错、限流、负载均衡。

> ⚠ **简历 vs 早期面经口径不一致**：简历最新版用 **Nacos**（见 [[我的简历/RPC框架项目]]）；早期部分面经（如 [[快手/支付方向/快手日常实习面经]]）用了 **Etcd**。面试时统一以 Nacos 为准。被追问 Etcd / Nacos / ZK 选型差异的话术见 [[我的简历/RPC框架项目#⚠ Nacos vs Etcd 不一致说明]]。

> 通用 RPC / Netty 原理（协议字段、序列化对比、注册中心对比、Reactor、粘包半包）→ 见 [[wiki/技术主题/RPC与Netty]]
> 通用限流 / 熔断 / 容错 → 见 [[wiki/技术主题/限流熔断容错]]

## 项目级 STAR 自陈
- **S（场景）**：Java 程序与 Python 程序间需要远程调用，自建 RPC 框架学习核心组件。
- **T（目标）**：实现一套可注册发现、可容错、可监控的最小化 RPC 框架。
- **A（动作）**：1）注册中心 Etcd（Raft 强一致）/ Nacos（控制台 + 配置中心）双实现，本地缓存 + watch 推送；2）Netty TCP 服务端 + 自定义 17 字节协议头（魔数 + 版本 + 序列化方式 + type + status + requestId + bodyLength）；3）requestId（雪花算法）+ pendingRequests 映射做异步请求-响应匹配；4）心跳机制（Etcd 30s 租约 + 10s 重新注册续命；Nacos 客户端 SDK 自动心跳）+ JVM ShutdownHook 优雅下线；5）容错（FailFast / FailSafe / FailOver / FailBack） + 重试（NoRetry / FixedInterval）+ 限流（令牌桶/滑动窗口）+ 负载均衡（轮询 / 加权 / 随机 / 一致性哈希虚拟节点）。
- **R（结果）**：自研 demo 跑通服务注册发现、远程调用、容错、限流、心跳。

## 高频追问 Q&A

### Q1: 服务注册与发现流程（项目特定实现）
**出处**：[[快手日常实习面经]] · [[蚂蚁一面]] · [[银河智学]]

> 通用注册发现流程见 [[wiki/技术主题/RPC与Netty#5. 服务注册与发现]]；下面是本项目 Etcd 路径与 key 设计。

- ServiceKey = ServiceName + ServiceVersion；NodeKey = ServiceKey + Host + Port
- 注册：本地注册器存 服务名 → Class 对象；连 Etcd，key 是 `ETCD_ROOT_PATH + NodeKey`，value 是 ServiceMetaInfo（服务名、IP、端口、协议版本号）的 JSON，30 秒租约；本地维护已注册节点 set，用于心跳重新注册
- 发现：先看本地缓存有没有；没有就根据 ServiceKey 前缀匹配 Etcd 拿到 List；watch 监听 key 变化；最后 ConcurrentHashMap 缓存 List
- Etcd 事件监听：监听 key 内容变化，DELETE 等事件触发本地缓存清理

---

### Q2: 心跳机制 + 优雅下线（项目特定细节）
**出处**：[[快手日常实习面经]] · [[Shopee DB Infra 北京平台实习面试问题总结]] · [[蚂蚁一面]]

> 应用层心跳为何不靠 TCP Keep-Alive、Nacos / Etcd 心跳机制对比 → 见 [[wiki/技术主题/RPC与Netty#11. 心跳为什么自己写而不靠 TCP Keep-Alive]]

- Etcd（本项目实现）：30 秒租约 + 用 Hutool CronUtil 每 10 秒跑定时任务，对本地 set 的每个 key get 后再 register（重新写一遍 key 续命）
- Nacos（备选实现）：客户端 SDK 内部定时（约 5 秒）发心跳到 `/nacos/v1/ns/instance/beat`；服务端超过 15 秒没心跳标记不健康，超过 30 秒删除实例
- ShutdownHook：`Runtime.getRuntime().addShutdownHook(new Thread(registry::destroy))` 在 JVM 关闭前清理 Etcd 数据

---

### Q3: 自定义协议头设计 / 魔数的作用（项目特定 17 字节布局）
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]]

> 通用协议字段含义 / 魔数 vs 协议识别 / 粘包半包通解 → 见 [[wiki/技术主题/RPC与Netty#1. 自定义协议字段（17 字节固定头 + body）]]

本项目采用 17 字节固定头：
```
magic(1) + version(1) + serializer(1) + type(1) + status(1) + requestId(8) + bodyLength(4)
```
解码：先读 17 字节头 → 取 bodyLength → 精确读 bodyLength 字节 body。

---

### Q4: 客户端怎么知道响应是给自己的？requestId 异步映射
**出处**：[[快手日常实习面经]]

> 通用 requestId 匹配机制 → 见 [[wiki/技术主题/RPC与Netty#3. 请求 / 响应匹配]]

本项目特定：
- requestId 用雪花算法生成的 long
- 发请求：生成 requestId → 创建 `CompletableFuture<RpcResponse>` → 放到 `Map<Long, CompletableFuture> pendingRequests` → requestId 放进请求头发出
- 收响应：从响应头取 requestId → 在 pendingRequests 找到对应 Future → complete
- 服务端响应：直接复用请求 header（只改 type/status），requestId 原样带回

---

### Q5: 容错策略
**出处**：[[快手日常实习面经]]

> FailFast / FailSafe / FailOver / FailBack 四种策略含义 → 见 [[wiki/技术主题/RPC与Netty#10. 容错策略与重试]]
> A 端保护（超时 + 熔断 + 隔离）/ B 端保护（限流 + 降级）→ 见 [[wiki/技术主题/限流熔断容错]]

本项目实现：
- FailFast：包装成 RuntimeException 抛出
- FailSafe：打日志，返回空 RpcResponse
- FailOver / FailBack：待实现
- 重试：NoRetry / FixedInterval（基于 Guava Retrying）
- 流程：rpcRequest → RetryStrategy.doRetry → 失败进 catch → TolerantStrategy.doTolerant

---

### Q6: 负载均衡怎么实现？
**出处**：[[快手日常实习面经]] · [[蚂蚁一面]]

**答题骨架**：
- 工厂模式获取负载均衡选择器
- 算法：轮询 / 加权轮询 / 随机 / 加权随机 / 最少连接 / 一致性哈希
- 一致性哈希：服务信息列表 + 虚拟节点构造哈希环 → 用请求参数算 hash → 顺时针找第一个 ≥ 该 hash 的虚拟节点
- 一致性哈希解决普通哈希在节点增删时大量请求路由到不同机器（缓存失效雪崩）的问题；引入虚拟节点解决物理节点少时分布不均

---

### Q7: 限流算法
**出处**：[[快手日常实习面经]]

> 4 种算法对比 / 漏桶 vs 令牌桶 / Redis 实现 → 见 [[wiki/技术主题/限流熔断容错]]

本项目用：令牌桶 + 滑动窗口。

---

### Q8: Netty 线程模型 / BIO NIO AIO 区别
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]] · [[字节跳动中国商业化一面面经]] · [[快手日常实习面经]]

> 通用 BIO / NIO / AIO 对比 + Netty 主从 Reactor + 粘包半包三种解法 → 见 [[wiki/技术主题/RPC与Netty#7. Netty 为什么快]] / [[wiki/技术主题/RPC与Netty#9. BIO / NIO / AIO]]

本项目特定：decoder 用 JSON 编解码器（不是二进制），ProtocolMessage 包含 header + body；TCP 粘包拆包靠协议头 bodyLength 字段。

---

### Q9: 序列化协议选型
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]] · [[银河智学]]

> Kryo / Protobuf / Hessian / JSON 速度排名 + 选型建议 → 见 [[wiki/技术主题/RPC与Netty#4. 序列化对比]]

---

### Q10: SPI / 动态代理 / 工厂模式
**出处**：[[银河智学]] · [[小红书产品工程师一面面经]]

**答题骨架**：
- SPI：load 函数读固定路径文件 → forName 拿 Class → 存 keyClassMap → getInstance 时根据 key 拿 Class 初始化
- JDK 动态代理：基于接口，Proxy.newProxyInstance + InvocationHandler.invoke 拦截，反射调用
- CGLIB：基于继承，生成目标类子类重写方法，FastClass 直接调用，比 JDK 反射快
- RPC 中：调用方法时不真正执行本地函数，而是 InvocationHandler 拦截后发消息到服务器、接收结果、返回，实现无感远程调用
- Spring Boot 2.x 默认用 CGLIB

---

### Q11: ConcurrentHashMap 怎么用 / 为什么线程安全
**出处**：[[蚂蚁一面]] · [[小红书产品工程师一面面经]] · [[字节跳动中国商业化一面面经]] · [[银河智学]]

**答题骨架**：
- 项目里用来并发写 Cache：多个线程查 etcd → 写 cache，保证 cache 内容一定是最后一次查的内容，防止数据相互覆盖
- 锁粒度低保持高性能
- JDK 1.7 用 Segment 分段锁，每个 Segment 是小 HashTable 有自己的锁
- JDK 1.8 改为 CAS + synchronized：桶为空 CAS 初始化，桶非空 synchronized 锁桶头，锁粒度细化到每个桶；链表长度 ≥ 8 且数组 ≥ 64 转红黑树

## 双链
- [[索引/主题]]
- [[wiki/技术主题/RPC与Netty]]
- [[wiki/技术主题/限流熔断容错]]
- [[后端技术专栏/RPC框架]]
- [[后端技术专栏/RPC框架整理后]]
- [[公司/快手]]
- [[公司/蚂蚁]]
- [[公司/Cider]]
- [[公司/其他公司|银河智学]]
