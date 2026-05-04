---
title: RPC与Netty
type: topic
updated: 2026-05-04
---

# RPC与Netty

> 自定义 RPC = 协议（魔数 + 头 + body）+ 序列化 + 注册中心 + 负载均衡 + Netty 主从 Reactor；Netty 快靠 NIO + epoll + 主从多线程 + 零拷贝。

## 高频问法
- "讲讲你的 RPC 框架（协议字段、请求响应匹配、注册发现）" — [[腾讯/数据平台/我的腾讯一面]]、[[蔚来/xhs]]、[[Cider面经/1]]
- "请求响应怎么对应？多个请求并发怎么区分" — [[腾讯/数据平台/我的腾讯一面]]、[[蔚来/xhs]]
- "魔数干什么用的；协议识别 vs 帧起始校验" — 后端专栏 [[后端技术专栏/RPC框架整理后]]
- "BIO / NIO / AIO 区别" — [[快手/支付方向/快手日常实习面经]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]
- "Netty 为什么快 / 主从 Reactor / 零拷贝" — 后端专栏 [[后端技术专栏/Netty]]
- "粘包半包怎么解决；HTTP/1.x / HTTP/2 怎么读边界" — 后端专栏 [[后端技术专栏/RPC框架整理后]]
- "Kryo / Protobuf / Hessian / JSON 性能对比" — 后端专栏 [[后端技术专栏/RPC框架整理后]]
- "服务注册发现：Nacos / Etcd / ZK 对比；心跳实现" — [[蚂蚁/蚂蚁一面]]、[[快手/支付方向/快手日常实习面经]]

## 答题骨架

### 1. 自定义协议字段（17 字节固定头 + body）
| 字段 | 长度 | 作用 |
|---|---|---|
| magic | 1B | 帧起始校验，防错位脏数据 |
| version | 1B | 协议版本，方便升级 |
| serializer | 1B | 0=JDK 1=JSON 2=Kryo 3=Hessian |
| type | 1B | 0=请求 1=响应 |
| status | 1B | OK / BadRequest / BadResponse |
| requestId | 8B | long，雪花算法生成，用于异步匹配 |
| bodyLength | 4B | 解码器按此长度读 body，避免粘包 |

### 2. 魔数 ≠ 协议识别
- 协议识别（这个端口跑什么协议）→ 端口号决定（80 HTTP、443 HTTPS、自定 RPC 端口约定俗成）
- 魔数 → 在 TCP 流里做"帧起始校验"，第一个字节是不是约定值，不是就关连接

### 3. 请求 / 响应匹配
- 服务端：从哪条 Channel 读到的请求就用哪条 Channel 写回，不需"客户端寻址"
- 客户端：每个请求生成唯一 requestId，存入 `Map<Long, CompletableFuture<RpcResponse>> pendingRequests`
- 收到响应取 requestId → 找到 Future → complete
- 多请求并发用 requestId 一对一匹配

### 4. 序列化对比
**速度排名 Kryo > Protobuf > Hessian > JSON**：元数据越少越偏二进制就越快越小
- **Kryo**：纯 JVM、按字段顺序写、最紧凑、对类结构变化敏感（加字段就坏）
- **Protobuf**：跨语言、需 .proto schema、字段编号 → tag → 有版本兼容
- **Hessian**：自描述、跨语言但带类型字符串
- **JSON**：纯文本、人类可读、最慢最大

### 5. 服务注册与发现
- 注册中心**只存元数据 + 推送变更**，不承载业务连接
- Provider 启动 → register（serviceName + host:port） → 本机起 Netty Server
- Consumer 调前 → discover（拿实例列表）→ 负载均衡 → Netty 直连 Provider
- **心跳**：Nacos 客户端每 5s 报活；Etcd 用 lease + 续约
- 服务变更：Nacos / Etcd watch 推送 → 客户端 clearCache → 下次发现拿新列表

### 6. Nacos / Etcd / ZK 对比（节选，详见 [[wiki/技术主题/RPC与Netty]] 与原专栏）
| | Nacos | etcd | ZK |
|---|---|---|---|
| 一致性 | AP / CP 可切换 | Raft（CP） | ZAB（CP） |
| 健康检查 | 主动探活 + 客户端心跳 | Lease 租约 | 临时节点 + 心跳 |
| 易用性 | 自带 Web 控制台 | 仅 KV API | 需 Curator |
| 配置中心 | ✅ 原生 | KV + watch | KV + watch |

### 7. Netty 为什么快
1. **NIO 非阻塞**：Selector 一线程管 N 连接
2. **主从 Reactor 多线程**：BossGroup（accept）+ WorkerGroup（read/write），Channel 与 EventLoop 一对一绑定，单 Channel 操作天然线程安全
3. **epoll**（Linux）：O(1) 事件通知；Netty 还自己 JNI 调 epoll，使用 `EPOLLRDHUP`
4. **修复 Selector 空轮询**：select 返回 0 超过阈值就重建 Selector
5. **零拷贝**：
   - 系统层 `FileRegion / sendfile`：内核直接到 socket
   - 应用层 `CompositeByteBuf` / `slice` / `wrap`：多个 ByteBuf 逻辑合并不拷贝
   - DirectByteBuf：堆外内存，少一次堆 → 直接内存的拷贝
6. **Pipeline**：双向链表 Handler，事件顺序流转，无线程切换

### 8. 粘包半包 → 三种解法
- 分隔符（HTTP/1.x：`\r\n\r\n`；Redis RESP：`\r\n`）
- 固定长度头（HTTP/2：9B 帧头中 3B Length；Dubbo：16B 头）
- 固定长度消息（极少见）

### 9. BIO / NIO / AIO
- BIO：每连接 1 线程，所有 IO 阻塞
- NIO：Selector 多路复用，1 线程管多连接，事件就绪才处理
- AIO：异步 IO，OS 完成后回调（Linux 实现弱，多用 Reactor 模拟）

### 10. 容错策略与重试
- FailFast：快速失败抛异常
- FailSafe：静默忽略，返回空 / 默认值
- FailOver：换节点重试
- FailBack：失败回退，走降级逻辑

### 11. 心跳为什么自己写而不靠 TCP Keep-Alive
- TCP Keep-Alive 默认 2 小时才探测，太慢；内核层不灵活
- 应用层心跳：几秒~几十秒，可携业务信息（节点状态 / 版本 / Tags）

## 易错点 & 追问
- 注册中心**不**转发 RPC 数据，业务连接是 Consumer ↔ Provider 直连
- requestId 需要全局唯一，雪花算法 / UUID 都行
- HTTP/2 二进制帧不需要扫分隔符，直接按偏移读 → 比 HTTP/1.x 快得多
- Kryo 慎在跨服务版本演进的场景使用
- ZK 用 ZAB；etcd / Nacos CP 模式用 Raft

## 深入阅读
- 原始专栏 [[后端技术专栏/RPC框架]]
- 原始专栏 [[后端技术专栏/RPC框架整理后]]
- 原始专栏 [[后端技术专栏/Netty]]
- 真题来源 [[腾讯/数据平台/我的腾讯一面]]、[[蚂蚁/蚂蚁一面]]、[[快手/支付方向/我的快手支付一面]]、[[Cider面经/1]]、[[蔚来/xhs]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]
