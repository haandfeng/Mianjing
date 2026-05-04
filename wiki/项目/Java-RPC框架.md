---
title: Java-RPC框架
type: project
updated: 2026-05-04
---

# Java-RPC框架

## 一句话介绍
基于 Etcd/Nacos + Netty 的自研 Java RPC 框架，含心跳、ShutdownHook、自定义协议头、requestId 异步映射、容错、限流、负载均衡。

## 项目级 STAR 自陈
- **S（场景）**：Java 程序与 Python 程序间需要远程调用，自建 RPC 框架学习核心组件。
- **T（目标）**：实现一套可注册发现、可容错、可监控的最小化 RPC 框架。
- **A（动作）**：1）注册中心 Etcd（Raft 强一致）/ Nacos（控制台 + 配置中心）双实现，本地缓存 + watch 推送；2）Netty TCP 服务端 + 自定义 17 字节协议头（魔数 + 版本 + 序列化方式 + type + status + requestId + bodyLength）；3）requestId（雪花算法）+ pendingRequests 映射做异步请求-响应匹配；4）心跳机制（Etcd 30s 租约 + 10s 重新注册续命；Nacos 客户端 SDK 自动心跳）+ JVM ShutdownHook 优雅下线；5）容错（FailFast / FailSafe / FailOver / FailBack） + 重试（NoRetry / FixedInterval）+ 限流（令牌桶/滑动窗口）+ 负载均衡（轮询 / 加权 / 随机 / 一致性哈希虚拟节点）。
- **R（结果）**：自研 demo 跑通服务注册发现、远程调用、容错、限流、心跳。

## 高频追问 Q&A

### Q1: 服务注册与发现流程
**出处**：[[快手日常实习面经]] · [[蚂蚁一面]] · [[银河智学]]

**答题骨架**：
- ServiceKey = ServiceName + ServiceVersion；NodeKey = ServiceKey + Host + Port
- 注册：本地注册器存 服务名 → Class 对象；连 Etcd，key 是 ETCD_ROOT_PATH + NodeKey，value 是 ServiceMetaInfo（服务名、IP、端口、协议版本号）的 JSON，30 秒租约；本地维护已注册节点 set，用于心跳重新注册
- 发现：先看本地缓存有没有；没有就根据 ServiceKey 前缀匹配 Etcd 拿到 List；watch 监听 key 变化；最后 ConcurrentHashMap 缓存 List
- Etcd 事件监听：监听 key 内容变化，DELETE 等事件触发本地缓存清理
- 为什么选 Etcd：Go 实现性能高、Raft 一致性算法、高可用强一致、完善的 watch 通知机制

---

### Q2: 心跳机制 + 优雅下线
**出处**：[[快手日常实习面经]] · [[Shopee DB Infra 北京平台实习面试问题总结]] · [[蚂蚁一面]]

**答题骨架**：
- Etcd：30 秒租约 + 用 Hutool CronUtil 每 10 秒跑定时任务，对本地 set 的每个 key get 后再 register（重新写一遍 key 续命）
- Nacos 2.x：客户端 SDK 内部定时（约 5 秒）发心跳到 /nacos/v1/ns/instance/beat；服务端超过 15 秒没心跳标记不健康，超过 30 秒删除实例
- ShutdownHook：`Runtime.getRuntime().addShutdownHook(new Thread(registry::destroy))` 在 JVM 关闭前清理 Etcd 数据
- 已经有 TCP Keep-Alive 为什么还要应用层心跳：TCP Keep-Alive 默认 2 小时太慢，应用层心跳几秒一次更快、可携带业务信息、能感知"实例还活着但服务已挂"
- 注册中心心跳维护「实例活不活」的元数据，TCP Keep-Alive 维护连接本身，是两件事

---

### Q3: 自定义协议头设计 / 魔数的作用
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]]

**答题骨架**：
- 17 字节固定头：magic(1) + version(1) + serializer(1) + type(1) + status(1) + requestId(8) + bodyLength(4)
- 解码：先读 17 字节头 → 取 bodyLength → 精确读 bodyLength 字节 body
- 魔数 ≠ 协议识别（协议识别是端口的事），魔数是流内"帧起始"校验，防止错位、脏数据被当 RPC 解析
- 粘包/半包：靠 bodyLength 字段（固定长度头方案），第一个字节先校验魔数

---

### Q4: 客户端怎么知道响应是给自己的？requestId 异步映射
**出处**：[[快手日常实习面经]]

**答题骨架**：
- 协议头携带 requestId（雪花算法生成的 long）
- 发请求：生成 requestId → 创建 CompletableFuture<RpcResponse> → 放到 `Map<Long, CompletableFuture> pendingRequests` → requestId 放进请求头发出
- 收响应：从响应头取 requestId → 在 pendingRequests 找到对应 Future → complete
- 服务端响应：直接复用请求 header（只改 type/status），requestId 原样带回；通过同一条 Channel writeAndFlush 写回
- 大量并发：每个请求唯一 requestId + pendingRequests 映射表精确匹配

---

### Q5: 容错策略
**出处**：[[快手日常实习面经]]

**答题骨架**：
- FailFast 快速失败：包装成 RuntimeException 抛出
- FailSafe 静默失败：打日志，返回空 RpcResponse
- FailOver 故障转移：换节点再调（待实现）
- FailBack 失败回退：降级逻辑（待实现）
- 重试：NoRetry / FixedInterval（基于 Guava Retrying）
- 流程：rpcRequest → RetryStrategy.doRetry → 失败进 catch → TolerantStrategy.doTolerant
- A 端保护自己：超时 + 熔断（Hystrix/Sentinel/Resilience4j，关闭→打开→半开三态）+ 隔离（每个下游独立线程池/信号量，舱壁模式）
- B 端保护自己：限流 + 降级

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

**答题骨架**：
- 固定窗口：简单但有临界突发问题
- 滑动窗口：把固定窗口细分小格子，临界问题缓解，Sentinel 用这个
- 漏桶：固定速率流出，严格平滑，不允许突发
- 令牌桶：固定速率生成令牌，允许突发，Guava RateLimiter / Nginx limit_req 用这个
- 实际项目中：令牌桶 + 滑动窗口最常见

---

### Q8: Netty 线程模型 / BIO NIO AIO 区别
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]] · [[字节跳动中国商业化一面面经]] · [[快手日常实习面经]]

**答题骨架**：
- BIO：一个连接一个线程，所有 I/O 操作阻塞等待，连接多线程多
- NIO：基于 Selector 多路复用，一个线程通过 Selector 同时监听多个连接，事件就绪才处理；不是完全不阻塞，是阻塞在 Selector 而非单个连接
- Netty 线程模型：Reactor 模式，channel + Selector，线程把感兴趣的事件注册到 channel，事件触发后处理对应内容
- TCP 粘包拆包：协议头带 bodyLength 字段，按长度读对应字节
- decoder：JSON 编解码器（不是二进制），ProtocolMessage 包含 header + body

---

### Q9: 序列化协议选型
**出处**：[[Shopee DB Infra 北京平台实习面试问题总结]] · [[银河智学]]

**答题骨架**：
- 速度：Kryo > Protobuf > Hessian > JSON（元数据越少越偏二进制越快）
- Kryo：无 schema、按字段顺序写、纯 Java、对类结构变化敏感
- Protobuf：需 .proto schema、字段编号、跨语言、版本兼容
- Hessian：自描述协议、跨语言、性能不如 Protobuf
- JSON：纯文本可读、生态最广、慢且大
- 选型：对外用 JSON，跨语言微服务用 Protobuf，纯 Java 高性能用 Kryo

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
- [[索引/主题索引]]
- [[后端技术专栏/RPC框架]]
- [[后端技术专栏/RPC框架整理后]]
- [[公司画像/快手]]
- [[公司画像/蚂蚁]]
- [[公司画像/Cider]]
- [[公司画像/其他公司|银河智学]]
