# RPC 框架知识梳理

---

## 一、序列化

### 1.1 速度排名

**Kryo > Protobuf > Hessian > JSON**

核心规律：**元数据越少、越偏二进制，就越快越小。**

### 1.2 各协议对比

**Kryo**

- 不需要 schema，直接按字段顺序写二进制，不写字段名/编号，数据最紧凑
- 基于类注册机制，用短整型 ID 代替类名，开销极小
- 只面向 JVM，不考虑跨语言，所以可以做更激进的优化
- 对类结构变化敏感（加个字段旧数据就可能反序列化失败）
- 适用场景：纯 Java 体系内的高性能场景，如 Spark 内部数据传输

**Protobuf**

- 需要提前写 `.proto` 文件定义 schema
- 序列化时写入字段编号（field tag），反序列化时做字段匹配查找
- 有版本兼容性（加减字段不会挂），跨语言支持好
- 适用场景：微服务间通信（gRPC 就用它）、需要长期演进的协议

**Hessian**

- 自描述协议，每个字段都带类型描述信息，反序列化要做大量字符串解析
- 跨语言、不需要预定义 schema
- Dubbo 早期默认的序列化方式，现在逐渐被替代
- Dubbo 3.x 主推 Triple 协议 + Protobuf，或升级到 Fastjson2

**JSON**

- 纯文本、自描述，人能直接读，几乎所有语言都支持
- 慢且大：字段名重复传输，数字用字符串表示，序列化/反序列化大量字符串解析
- 适用场景：对外 API、配置文件、前后端交互

**其他**

- **MessagePack**——"二进制的 JSON"，比 JSON 小且快，不需要 schema，介于 JSON 和 Protobuf 之间
- **Avro**——Hadoop 生态常用，schema 随数据一起传或单独存储

### 1.3 选型总结

对外给人看的用 JSON，微服务之间跨语言用 Protobuf，纯 Java 内部追求极致性能用 Kryo。

---

## 二、网络传输基础

### 2.1 MTU 与 MSS

**MTU（Maximum Transmission Unit）**——数据链路层的限制，一个以太网帧能承载的最大数据量，以太网默认 **1500 字节**。

**MSS（Maximum Segment Size）**——传输层（TCP）的概念，一个 TCP 段能携带的最大应用数据量。MSS = MTU - IP头(20B) - TCP头(20B) = **1460 字节**。

MTU 是数据链路层的限制，但数据链路层自己不会拆包（超过就丢弃）。所以由上一层——**IP 层**负责分片，确保每个分片都能装进一帧。

### 2.2 大文件传输：拆分与合并

**拆分**

- **传输层（TCP）做分段（Segmentation）**——按 MSS 把数据流切成一个个 segment，这是主力
- **网络层（IP）做分片（Fragmentation）**——兜底机制，现代网络通过 MSS 协商和 Path MTU Discovery 尽量避免

**合并**

- IP 分片 → 接收端 IP 层重组
- TCP 段 → 接收端 TCP 层按序拼回字节流

**TCP 保证有序正确的三个机制**

- **序列号（Sequence Number）**：每个段标记"第一个字节是整个流里的第几个字节"，接收端据此排序
- **确认号（ACK）+ 滑动窗口**：接收端告知"已连续收到第 N 字节之前的所有数据"，发送端据此判断重传
- **校验和（Checksum）**：验证数据完整性，损坏的段直接丢弃等重传

序列号是 32 位（最大约 4.29GB），超出后回绕从 0 重新开始。靠滑动窗口范围和 **PAWS（时间戳扩展）** 避免歧义。

**TCP 怎么知道文件发完了？**

TCP 不知道"文件"是什么，它只是字节流管道。应用层写完数据后调用 close()/shutdown()，TCP 发送 **FIN 标志**的段通知对方"我这个方向数据到此为止"，对方读到 **EOF** 即知收完。双方各发一次 FIN、各回一次 ACK，即**四次挥手**。

文件完整性由应用层负责（如 HTTP 的 Content-Length、MD5 校验等）。

**TCP 连接不一定发完就关闭**，完全取决于应用层设计：HTTP/1.1 默认 Keep-Alive 长连接，HTTP/2 多路复用，数据库连接池可能从启动到关机一直开着。

### 2.3 UDP

UDP 头有 16 位 Length 字段，理论载荷最大约 **65507 字节**。UDP 自己不做拆分，超过 MTU 的包直接交给 IP 层分片。

IP 分片的问题：任何一个分片丢了整个数据报就废了（无重传）；没有拥塞控制；部分防火墙直接丢弃分片。

实际中使用 UDP 的应用会主动把数据控制在一个 MTU 以内（如 DNS 限制 512 字节），或在应用层自己做分段和排序（如 QUIC 协议在 UDP 之上实现了可靠传输）。

### 2.4 TCP Keep-Alive（心跳）

TCP 连接空闲时不会主动探测对方存活。Keep-Alive 机制：空闲一段时间后（Linux 默认 **2 小时**）发探测包，连续 **9 次**（每次间隔 **75 秒**）无回复则判定连接已死。

实际中 TCP Keep-Alive 太慢，大部分应用在**应用层自己实现心跳**（如 WebSocket Ping/Pong、HTTP/2 PING 帧），间隔几秒到几十秒，检测更快且可携带业务信息。

### 2.5 粘包与半包

TCP 是字节流，没有消息边界。应用层必须自己定义怎么切出完整消息，方案只有三种：**分隔符、固定长度头、固定长度消息**。

**HTTP/1.x（文本协议）**

- Header 结束：靠 `\r\n\r\n`（分隔符）
- Body 结束：靠 `Content-Length`（长度字段），或 `Transfer-Encoding: chunked`（每个 chunk 带长度，0 长度 chunk 表示结束）

**HTTP/2（二进制帧协议）**

- 每帧有固定 **9 字节帧头**，前 3 字节为 Length
- 解析：先读 9 字节帧头 → 取 Length → 精确读 Length 字节 payload → 循环
- 不需要分隔符和逐字节扫描，速度更快

其他协议：Redis RESP 用 `\r\n` 分隔；Dubbo 协议 16 字节固定帧头含 body 长度；Protobuf 用 varint 编码长度。**万变不离其宗：分隔符、固定长度头、或两者结合。**

---

## 三、Socket 连接上限

每个 socket 由四元组唯一标识：`(源IP, 源端口, 目标IP, 目标端口)`

**作为客户端**：受端口号限制（0~65535），可用约 28000~60000 个，连同一个目标服务器单 IP 最多约 **6 万连接**。多目标 IP 时端口可复用。

**作为服务端**：只监听一个端口，客户端的 IP + 端口各不相同，理论无端口限制。实际瓶颈在：

|限制因素|默认值|可调整后|
|---|---|---|
|文件描述符（fd）|65535|百万级|
|内存（每连接约 4~8KB 缓冲区）|取决于机器|百万连接需数 GB|
|端口（客户端）|~6万/目标IP|多目标可复用|

---

## 四、RPC 协议设计

| 字段         | 类型   | 长度   | 说明                                      |
| ---------- | ---- | ---- | --------------------------------------- |
| magic      | byte | 1 字节 | 魔数，用于校验协议/安全性，当前固定为 0x1（PROTOCOL_MAGIC） |
| version    | byte | 1 字节 | 协议版本，当前为 0x1（PROTOCOL_VERSION）          |
| serializer | byte | 1 字节 | 序列化方式：0=JDK，1=JSON，2=Kryo，3=Hessian     |
| type       | byte | 1 字节 | 消息类型：0=请求，1=响应                          |
| status     | byte | 1 字节 | 状态：20=OK，40=BadRequest，50=BadResponse   |
| requestId  | long | 8 字节 | 请求 ID，用于关联请求与响应                         |
| bodyLength | int  | 4 字节 | 消息体字节长度，解码时按此长度读 body                   |

### 4.1 魔数的作用

魔数不是用来识别"是否是 RPC 协议"（那是端口的事），而是在已约定 RPC 的 TCP 连接上做**帧起始校验**：

- 解码时先看第一个字节是不是魔数
- 是 → 合法帧开头，按协议头 + body 解析
- 不是 → 报错/关连接，防止错位、脏数据被当 RPC 解析

#### 协议怎么做识别的
- TCP / UDP：由 IP 头的 Protocol 字段（6=TCP，17=UDP）区分；
- HTTP、SMTP 等：由 端口（80、25…）+ 首行/首字节格式（如 GET 、220）识别；

==**协议识别 → 看端口；帧起始校验 → 看魔数。**==

### 4.2 请求-响应匹配机制

**服务端返回给谁？** 由 TCP 连接（Channel）决定。请求从哪条 Channel 读到，响应就通过同一条 Channel 写回，不需要"客户端寻址"。

**客户端怎么识别响应？** 靠 **requestId**。协议头里带一个唯一的 requestId，流程：

1. 发请求时：生成唯一 requestId，存入 `Map<Long, CompletableFuture<RpcResponse>> pendingRequests`，requestId 放进请求头发出
2. 收响应时：从响应头取 requestId，在 pendingRequests 中找到对应 Future 并 complete

大量并发请求时，每个请求有唯一 requestId + pendingRequests 映射表，按 requestId 精确匹配。

---

## 五、服务注册与发现

### 5.1 注册中心的职责

注册中心**不管理 RPC 业务连接，不转发 RPC 数据**，只做两件事：

- 存元数据：服务名 → 提供者实例列表（host:port）
- 给消费端查/推：返回当前可用的提供者地址列表

|连接类型|谁和谁|注册中心是否维护|上面跑的数据|
|---|---|---|---|
|注册/发现连接|每个应用进程 ↔ 注册中心|是|注册、心跳、订阅、列表推送|
|RPC 业务连接|Consumer ↔ Provider|否|RpcRequest / RpcResponse|

### 5.2 服务发现流程

1. Provider 启动时把 ServiceMetaInfo（服务名、host、port）注册到注册中心，本机启动 Netty Server 监听
2. Consumer 调用前通过 `registry.serviceDiscovery(serviceKey)` 查实例列表
3. 负载均衡选一个实例，用 Netty Client 直连该 Provider 发 RPC

### 5.3 客户端怎么知道服务不活跃

**方式一：注册中心推送。** 注册中心检测到实例心跳超时后摘除，通过 watch/subscribe 推事件给客户端，客户端清掉本地缓存，下次发现用新列表。

**方式二：调用时发现。** 连接失败或超时，说明实例不可用。可在失败时清缓存或标记故障（当前项目只做了重试 + 容错，未反哺缓存）。

### 5.4 心跳机制

**Nacos**：客户端 SDK 内部自动每 ~5 秒向服务端发心跳请求。服务端超过 ~15 秒没心跳标记不健康，超过 ~30 秒删除实例。

**Etcd**：用 Lease（租约）机制，创建带 TTL（如 30 秒）的租约绑定到 key，客户端定时续约（或重新注册）。TTL 过期自动删 key。

注册中心的心跳和 TCP Keep-Alive 是两回事：TCP Keep-Alive 探测的是连接存活，注册中心心跳维护的是"这个服务实例是否还在提供服务"。

### 5.5 Nacos 集群承载能力

单机（8C16G）：Nacos 1.x 约 6k~1w 客户端实例；Nacos 2.x（gRPC 长连接）约 4w+ 客户端。超出需集群分担。

### 5.6 Zookeeper vs etcd vs Nacos

|       | Zookeeper         | etcd              | Nacos                     |
| ----- | ----------------- | ----------------- | ------------------------- |
| 定位    | 分布式协调服务           | 分布式 KV 存储（K8s 底座） | 注册中心 + 配置中心               |
| 一致性协议 | ZAB（CP）           | Raft（CP）          | Raft(CP) + Distro(AP)，可切换 |
| 健康检查  | 临时节点 + 心跳         | Lease 租约 TTL      | 主动探活 + 客户端心跳              |
| 易用性   | 无 UI，需 Curator 封装 | 无原生 UI，KV API     | 自带 Web 控制台，接入成本最低         |
| 配置管理  | 原始（节点写数据 + watch） | 类似（KV + watch）    | 原生支持，有命名空间/分组/灰度/回滚       |
| 语言生态  | Java 最好           | Go/K8s 最好         | Spring Cloud / Dubbo 最好   |
| 性能    | 大规模 watch 是瓶颈     | 小规模最均衡            | AP 模式吞吐量最高                |

---

## 六、负载均衡

### 6.1 常见算法

- **轮询（Round Robin）**：按顺序分配，严格均匀，但不考虑服务器性能差异
- **加权轮询（Weighted Round Robin）**：权重越高分配越多，但权重是预设的，运行时不变
- **随机 / 加权随机**：随机选择，请求量小时可能不均匀，量大时趋近均匀
- **最少连接（Least Connections）**：当前连接数最少的优先，能感知忙碌程度
- **一致性哈希（Consistent Hash）**：根据请求特征（如用户 ID）哈希到固定节点，保证同一特征的请求总打到同一台机器，适合有状态或需要缓存亲和的场景

### 6.2 一致性哈希

将 0 到 2^32 组成虚拟环，服务器节点和请求分别哈希映射到环上，请求顺时针找到第一个节点。增删节点只影响相邻一小段请求。

**虚拟节点**解决物理节点过少时分布不均的问题：每台物理机映射出多个虚拟节点分散到环上。

可以结合响应时间动态调整虚拟节点数量：响应快的多分虚拟节点（多分流量），响应慢的少分。但每次调整会导致部分请求重映射（缓存失效），不宜过于频繁。

### 6.3 基于响应速度的负载均衡

记录每台实例的响应时间，反向计算权重。例如 A:100ms、B:200ms、C:400ms，总 700ms，权重分别为 600、500、300（用总时间减各自时间），归一化后 A 约 43%、B 约 36%、C 约 21%。

实际框架：Dubbo 的 ShortestResponse（预估响应时间 = 平均响应时间 × 活跃数）、Ribbon 的 WeightedResponseTimeRule、Nginx 的 least_time。

注意事项：新实例用默认权重（冷启动）；响应时间用滑动窗口统计；用 EWMA 平滑避免抖动。

---

## 七、限流算法

### 7.1 算法对比

|算法|特点|缺点|
|---|---|---|
|固定窗口|最简单，窗口内计数|临界突发问题|
|滑动窗口|细分小格子，窗口滑动|实现稍复杂|
|漏桶|出口速率恒定，严格平滑|不能应对突发|
|令牌桶|允许突发，控制平均速率|—|

实际中**令牌桶和滑动窗口**最常用。

### 7.2 固定窗口计数器

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class FixedWindowRateLimiter {
    private final int maxRequests;
    private final long windowSizeMs;
    private final AtomicInteger counter = new AtomicInteger(0);
    private final AtomicLong windowStart = new AtomicLong(System.currentTimeMillis());

    public FixedWindowRateLimiter(int maxRequests, long windowSizeMs) {
        this.maxRequests = maxRequests;
        this.windowSizeMs = windowSizeMs;
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        if (now - windowStart.get() >= windowSizeMs) {
            windowStart.set(now);
            counter.set(0);
        }
        return counter.incrementAndGet() <= maxRequests;
    }
}
```

### 7.3 滑动窗口计数器

```java
import java.util.concurrent.ConcurrentLinkedQueue;

public class SlidingWindowRateLimiter {
    private final int maxRequests;
    private final long windowSizeMs;
    private final ConcurrentLinkedQueue<Long> timestamps = new ConcurrentLinkedQueue<>();

    public SlidingWindowRateLimiter(int maxRequests, long windowSizeMs) {
        this.maxRequests = maxRequests;
        this.windowSizeMs = windowSizeMs;
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        while (!timestamps.isEmpty() && now - timestamps.peek() >= windowSizeMs) {
            timestamps.poll();
        }
        if (timestamps.size() < maxRequests) {
            timestamps.offer(now);
            return true;
        }
        return false;
    }
}
```

### 7.4 漏桶算法

> **注意**：下面的代码本质上是准入控制（判断能不能进桶），不是真正的漏桶语义。真正的漏桶应该是请求入队排队，消费端按固定间隔取出处理。大部分实现（包括网上的）都是这种"假漏桶"，因为真漏桶需要队列 + 定时消费，会引入延迟。真正需要严格平滑流量的场景（如 Linux `tc` 流量整形）才会用真漏桶。

```java
public class LeakyBucketRateLimiter {
    private final int capacity;
    private final double leakRatePerMs;
    private double currentWater;
    private long lastLeakTime;

    public LeakyBucketRateLimiter(int capacity, int leakPerSecond) {
        this.capacity = capacity;
        this.leakRatePerMs = leakPerSecond / 1000.0;
        this.currentWater = 0;
        this.lastLeakTime = System.currentTimeMillis();
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        double leaked = (now - lastLeakTime) * leakRatePerMs;
        currentWater = Math.max(0, currentWater - leaked);
        lastLeakTime = now;
        if (currentWater < capacity) {
            currentWater++;
            return true;
        }
        return false;
    }
}
```

### 7.5 令牌桶算法

```java
public class TokenBucketRateLimiter {
    private final int capacity;
    private final double tokensPerMs;
    private double currentTokens;
    private long lastRefillTime;

    public TokenBucketRateLimiter(int capacity, int tokensPerSecond) {
        this.capacity = capacity;
        this.tokensPerMs = tokensPerSecond / 1000.0;
        this.currentTokens = capacity;
        this.lastRefillTime = System.currentTimeMillis();
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        double newTokens = (now - lastRefillTime) * tokensPerMs;
        currentTokens = Math.min(capacity, currentTokens + newTokens);
        lastRefillTime = now;
        if (currentTokens >= 1) {
            currentTokens--;
            return true;
        }
        return false;
    }
}
```

漏桶和令牌桶的实现技巧一样：**不用定时器，用时间差懒计算。**

### 7.6 Redis 实现限流

|算法|Redis 数据结构|说明|
|---|---|---|
|固定窗口|**String**（INCR + EXPIRE）|key 带时间戳，过期自动清理|
|滑动窗口|**ZSet**（score 存时间戳）|ZREMRANGEBYSCORE 清旧记录，ZCARD 统计|
|漏桶|**Hash**（water + last_time）|Lua 脚本惰性计算漏水量|
|令牌桶|**Hash**（tokens + last_time）|Lua 脚本惰性计算补充令牌量|

所有涉及多步操作的都必须用 **Lua 脚本**保证原子性。

### 7.7 消息队列实现限流

请求先入队，消费端控制消费速率，天然就是漏桶模型。

- 优点：天然削峰填谷、解耦、有序、可堆积
- 缺点：引入延迟（不适合同步场景）、增加组件复杂度、不能精确控速、不能快速拒绝

适合异步任务（短信通知、日志处理、秒杀下单）；不适合需要实时响应的 API 限流。

---

## 八、服务保护

### 8.1 保护被调方（B 端）：限流 + 降级

- **限流**：控制接口最大 QPS，超出直接拒绝（Sentinel、Guava RateLimiter）
- **降级**：压力大时关掉非核心逻辑，返回默认数据

### 8.2 保护调用方（A 端）：超时 + 熔断 + 隔离

**超时（Timeout）**：调 B 设超时时间，超时就放弃。不设超时是雪崩的最常见起因。

**熔断（Circuit Breaker）**：三状态机——

- **CLOSED**（正常）：放行请求，滑动窗口统计失败率，超标则切 OPEN
- **OPEN**（熔断）：所有请求直接拒绝，启动冷却计时器，到期切 HALF_OPEN
- **HALF_OPEN**（试探）：放少量请求试探，成功回 CLOSED，失败回 OPEN

```java
public class CircuitBreaker {
    enum State { CLOSED, OPEN, HALF_OPEN }

    private State state = State.CLOSED;
    private int failCount = 0;
    private int successCount = 0;
    private final int failThreshold = 5;
    private final int halfOpenMaxAttempts = 3;
    private final long cooldownMs = 10000;
    private long openedAt;

    public synchronized boolean allowRequest() {
        switch (state) {
            case CLOSED: return true;
            case OPEN:
                if (System.currentTimeMillis() - openedAt >= cooldownMs) {
                    state = State.HALF_OPEN;
                    successCount = 0;
                    failCount = 0;
                    return true;
                }
                return false;
            case HALF_OPEN:
                return (successCount + failCount) < halfOpenMaxAttempts;
            default: return false;
        }
    }

    public synchronized void recordSuccess() {
        switch (state) {
            case HALF_OPEN:
                successCount++;
                if (successCount >= halfOpenMaxAttempts) {
                    state = State.CLOSED;
                    failCount = 0;
                }
                break;
            case CLOSED:
                failCount = 0;
                break;
        }
    }

    public synchronized void recordFailure() {
        switch (state) {
            case CLOSED:
                failCount++;
                if (failCount >= failThreshold) {
                    state = State.OPEN;
                    openedAt = System.currentTimeMillis();
                }
                break;
            case HALF_OPEN:
                state = State.OPEN;
                openedAt = System.currentTimeMillis();
                break;
        }
    }
}
```

**隔离（Bulkhead）**：给每个下游服务分配独立的线程池或信号量，一个下游出问题不波及其他服务。

两端都要做：只保护 B 不保护 A，B 响应变慢 A 线程照样耗尽；只保护 A 不保护 B，B 可能被打垮。

---

## 九、容错策略

### 9.1 重试策略（RetryStrategy）

|配置值|实现类|含义|
|---|---|---|
|no|NoRetryStrategy|不重试，失败直接抛异常|
|fixedInterval|FixedIntervalRetryStrategy|固定间隔重试（基于 Guava Retrying）|

### 9.2 容错策略（TolerantStrategy）

重试仍失败后进入容错：

|配置值|实现类|含义|
|---|---|---|
|failFast|FailFastTolerantStrategy|快速失败：包装成 RuntimeException 抛出|
|failSafe|FailSafeTolerantStrategy|静默失败：打日志，返回空 RpcResponse|
|failOver|FailOverTolerantStrategy|故障转移：换节点再调（待实现）|
|failBack|FailBackTolerantStrategy|失败回退：执行降级逻辑（待实现）|

```java
// 使用方式
try {
    RetryStrategy retryStrategy = RetryStrategyFactory.getInstance(rpcConfig.getRetryStrategy());
    rpcResponse = retryStrategy.doRetry(() ->
            VertxTcpClient.doRequest(rpcRequest, selectedServiceMetaInfo));
} catch (Exception e) {
    TolerantStrategy tolerantStrategy = TolerantStrategyFactory.getInstance(rpcConfig.getTolerantStrategy());
    rpcResponse = tolerantStrategy.doTolerant(null, e);
}
```

---

## 十、动态代理：JDK vs CGLIB

|           | JDK 动态代理            | CGLIB                         |
| --------- | ------------------- | ----------------------------- |
| 基于        | 接口                  | 继承                            |
| 限制        | 必须有接口               | 不能代理 final 类/方法               |
| 生成类大小     | 小                   | 大（含 FastClass）                |
| 方法调用      | 反射（Method.invoke）   | FastClass 直接调用（方法索引）          |
| 创建代理速度    | 快                   | 慢（要生成子类 + FastClass）          |
| 元空间风险     | 低（内置缓存，相同接口组合只生成一次） | 较高（缓存依赖 Enhancer 配置，易生成大量不同类） |
| Spring 默认 | Spring MVC 时代       | Spring Boot 2.x 起             |

**动态代理为什么可能导致元空间溢出？** 两者都在运行时生成新类，类的元数据存在元空间。类只有其 ClassLoader 被 GC 回收时才能卸载，如果 ClassLoader 一直被引用，动态生成的类就越积越多。CGLIB 更容易出问题，因为生成的类更大、缓存机制更容易失效。

## 十一、Netty相关

### Netty 为什么快


这是一个很好的系统性问题，我从你提到的几个维度以及一些额外角度来展开。

####  1. NIO 非阻塞 I/O 模型
[[Netty#BIO NIO AIO]]
传统 BIO（Blocking I/O）模式下，每个连接需要一个独立线程，线程在 `read()`/`write()` 时会阻塞等待，导致大量线程被挂起浪费资源。NIO 的核心变化是引入了 **Channel + Buffer + Selector** 三件套：一个线程通过 Selector 可以监听多个 Channel 上的事件（连接就绪、可读、可写），不需要阻塞等待某一个连接。这让单线程就能管理成千上万的连接，线程利用率大幅提升。

Netty 在 Java 原生 NIO 之上做了大量封装，屏蔽了 NIO 编程中非常繁琐且容易出错的细节（比如半包读写、Selector 空轮询等）。

#### 2. Reactor 线程模型
[[Netty#Reactor 和 Proactor]]

这里需要澄清一点：Netty 采用的是 **Reactor 模式**，而非 Proactor。两者的区别在于，Reactor 是"事件就绪通知"——内核告诉你数据准备好了，由应用程序自己去读；Proactor 是"事件完成通知"——内核帮你把数据读完了再通知你。Linux 下主流实现是 Reactor（Windows 的 IOCP 才是真正的 Proactor）。

Netty 实现的是 **主从 Reactor 多线程模型**：

- **BossGroup（主 Reactor）**：通常 1 个线程，专门负责 `accept` 新连接，把建立好的连接注册到 WorkerGroup。
- **WorkerGroup（从 Reactor）**：多个线程（默认 CPU 核心数 × 2），每个线程绑定一个 Selector，负责处理已连接 Channel 上的读写 I/O 事件。
- 每个 Channel 在其生命周期内只绑定到一个 EventLoop 线程，所以对于单个 Channel 的操作天然是线程安全的，避免了锁竞争。

这种分工让连接接入和 I/O 处理互不干扰，Worker 线程之间也因为 Channel 绑定关系而几乎没有共享状态，并发性能极高。

#### 3. epoll 与 Linux 平台优化
[[Netty#Select Poll Epoll]]
Java NIO 的 `Selector` 在 Linux 上底层使用 `epoll`。相比早期的 `select`/`poll`，epoll 的优势在于：

- **O(1) 的事件通知**：epoll 只返回有事件就绪的 fd，不需要遍历全部连接。
- **没有 fd 数量限制**：select 默认上限 1024，epoll 理论上只受系统内存限制。
- **边缘触发（ET）模式**：减少不必要的事件通知次数。

Netty 更进一步，提供了自己的 **`EpollEventLoop`**，直接通过 JNI 调用 Linux epoll 系统调用，绕过了 Java NIO 的 Selector 抽象层，减少了一层开销，并且能使用一些 Java NIO 未暴露的 epoll 特性（如 `EPOLLRDHUP` 用于更精确地检测连接断开）。

#### 4. 读写事件驱动与 Pipeline 机制
[[Netty#Netty的具体调用路径]]
Netty 的 `ChannelPipeline` 是一个双向链表结构的处理器链，InboundHandler 处理读事件（数据进来），OutboundHandler 处理写事件（数据出去）。这种设计的好处是：

- 每个 Handler 只做一件事（解码、业务逻辑、编码），职责清晰，处理高效。
- 事件在 Pipeline 中流转，没有不必要的线程切换——同一个 EventLoop 线程依次调用链上的 Handler。
- 写操作不会直接发到 Socket，而是先写入 `ChannelOutboundBuffer`，等到 Channel 可写时再 flush，避免了写阻塞。

#### 5. 修复的 Java NIO Bug —— Selector 空轮询

[[Netty#Netty 为什么不用JDK 原生的 NIO，要自己封装一层？]]
这是 Netty 非常著名的一个贡献。JDK 存在一个长期未彻底修复的 bug（[JDK-6670302](https://bugs.openjdk.org/browse/JDK-6670302)）：在 Linux 上，epoll 在某些条件下会错误地报告事件就绪，导致 `Selector.select()` 本应阻塞却立即返回 0，CPU 被空转打满到 100%。

Netty 的解决方案很巧妙：它统计在一定时间窗口内 `select()` 返回 0 的次数，当超过阈值（默认 512 次）时，判定发生了空轮询，然后**重建一个新的 Selector**，把所有 Channel 重新注册上去，废弃有问题的旧 Selector。这个 workaround 在 `NioEventLoop` 的 `select` 方法中可以看到。

#### 6. 零拷贝（Zero-Copy）

[[Netty#Netty的零拷贝]] 更加细节的在这里
Netty 的零拷贝体现在多个层面：

**操作系统层面：** Netty 的 `FileRegion` 封装了 `FileChannel.transferTo()`，底层调用 Linux 的 `sendfile` 系统调用，数据直接从内核缓冲区传到 Socket 描述符，不经过用户态缓冲区，省去了内核态到用户态再到内核态的两次拷贝。

**应用层面（更重要的优化）：**
- **CompositeByteBuf**：把多个 ByteBuf 逻辑上组合成一个，不需要真正地内存拷贝合并。比如 HTTP 协议头和协议体可以各自生成后直接组合发送。
- **slice() / duplicate()**：对同一块内存创建不同的视图，多个引用共享底层数据，无需拷贝。
- **DirectByteBuf（堆外内存）**：数据分配在直接内存中，Socket 读写时不需要再从 JVM 堆拷贝到直接内存，少了一次拷贝。JVM 堆内存写入 Socket 时，JDK 底层会先拷贝到临时的直接内存缓冲区，DirectByteBuf 直接跳过了这一步。
- **wrap()**：可以把 byte 数组直接包装成 ByteBuf，不产生拷贝。


### 多个线程调用 channel.writeAndFlush 会不会有线程安全问题

不会，Netty 的 `channel.writeAndFlush()` 是线程安全的。

**原因**

每个 Channel 绑定一个 **EventLoop**（单线程事件循环）。调用 writeAndFlush 时，Netty 内部判断当前线程是不是该 Channel 的 EventLoop 线程：

- **是** → 直接执行写操作
- **不是** → 封装成 task 提交到 EventLoop 的任务队列，由 EventLoop 线程稍后执行

java

```java
// Netty 源码核心逻辑（简化）
public void writeAndFlush(Object msg) {
    if (eventLoop.inEventLoop()) {
        doWrite(msg);
    } else {
        eventLoop.execute(() -> doWrite(msg));
    }
}
```

不管多少个线程同时调，**最终都串行化到同一个 EventLoop 线程执行**，天然无并发问题。