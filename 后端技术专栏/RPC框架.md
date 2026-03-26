
# Kryo  为什么快

## 速度排名（从快到慢）

**Kryo > Protobuf > Hessian**

---

**Kryo 比 Protobuf 快：**

Protobuf 每个字段都写 field tag（字段编号 + 类型），反序列化要根据 tag 做字段匹配。Kryo 直接按顺序写字段值，没有任何元数据，字节数更少，解析更直接。

---

**Protobuf 比 Hessian 快：**

Hessian 是自描述协议，每个字段都携带类型描述字符串，反序列化需要大量字符串解析。Protobuf 是纯二进制 + 数字 tag，没有字符串，解析成本低得多。】

## Kryo 比 Protobuf 快



Protobuf 需要：

- 提前写 `.proto` 文件定义 schema
- 序列化时写入字段编号（field tag）用于跨语言识别
- 反序列化时做字段匹配查找

Kryo：

- 不需要 schema，直接按字段顺序写二进制
- 不写字段名/编号，数据更紧凑
- 基于类注册机制，用短整型 ID 代替类名，开销极小

## Kryo 比 Hessian 快

Hessian：

- 是文本/自描述协议，每个字段都带类型描述信息
- 反序列化要做大量字符串解析
- 设计目标是跨语言兼容，牺牲了性能

Kryo：

- 纯二进制，无自描述开销
- 直接操作字节，没有字符串解析
- 只面向 JVM，不考虑跨语言，所以可以做更激进的优化



## 你已经整理了二进制序列化的对比，现在加上 JSON 和其他常见的来看全貌。

------

**JSON**

JSON 是**纯文本、自描述**的格式。每个字段都带着字段名的字符串：

```json
{"name":"张三","age":25,"active":true}
```

优点很明显：人能直接读、几乎所有语言都支持、是 Web 领域的事实标准（REST API 基本都用它）。

缺点也很明显：**慢且大**。字段名重复传输，数字用字符串表示（`"25"` 占两个字节，二进制只要一个字节），序列化和反序列化都要做大量字符串解析和转义处理。

------

**把它们放在一起比较**

从速度和体积来排：

**Kryo > Protobuf > Hessian > JSON**

原因是一条清晰的链条——**元数据越少、越偏二进制，就越快越小：**

Kryo 什么元数据都不写，按顺序裸写字段值，最极端。

Protobuf 写字段编号（数字 tag），很小但有。

Hessian 写类型描述字符串，开销明显上升。

JSON 写完整字段名字符串，而且所有值都是文本编码，最慢最大。

------

**那为什么 JSON 还是用得最多？**

因为选序列化方案不只看速度。每种方案有自己适合的场景：

**JSON**——可读性最好、生态最广，适合对外 API、配置文件、前后端交互。性能不是瓶颈的场景下它就是最优选。

**Protobuf**——需要 schema（.proto 文件），有版本兼容性（加减字段不会挂），跨语言支持好。适合微服务间通信（gRPC 就用它）、需要长期演进的协议。

**Hessian**——Dubbo 早期默认的序列化方式，跨语言、不需要预定义 schema，但性能不如 Protobuf，现在逐渐被替代。

**Kryo**——最快，但**只能 Java 用**，没有跨语言能力，而且对类结构变化很敏感（加个字段旧数据就可能反序列化失败）。适合纯 Java 体系内的高性能场景，比如 Spark 内部数据传输。

------

**还有两个值得知道的：**

**MessagePack**——可以理解为"二进制的 JSON"，结构和 JSON 一样（键值对），但用二进制编码。比 JSON 小、快，同时保留了不需要 schema 的灵活性。介于 JSON 和 Protobuf 之间的折中选择。

**Avro**——Hadoop 生态常用，schema 随数据一起传或单独存储，适合大数据场景。

------

**一句话总结选型思路：** 对外给人看的用 JSON，微服务之间跨语言用 Protobuf，纯 Java 内部追求极致性能用 Kryo。其他的都是这几个的变体或折中。

常见的限流算法有什么常见的限流算法有什么




# 一台机器 最多能有多少个socket链接

## 理论上限

每个 socket 连接由四元组唯一标识：

```
(源IP, 源端口, 目标IP, 目标端口)
```

------

## 作为客户端

受本机端口号限制，端口范围 0~65535，去掉系统保留的，可用约 **28000~60000** 个端口。

所以连同一个目标服务器，单个 IP 最多约 **6万个连接**。

但如果有多个目标 IP，四元组不同，端口可以复用，连接数可以更多。

------

## 作为服务端

服务端只监听一个端口（如 80），客户端的 IP + 端口各不相同，所以四元组一直不重复，**理论上没有端口限制**。

真正的瓶颈在：

**1. 文件描述符（fd）** Linux 每个 socket 占一个 fd，系统默认限制 65535，可以通过修改 `ulimit` 和内核参数调大，上限约几百万。

**2. 内存** 每个 TCP 连接内核要维护收发缓冲区，默认约 **4KB~8KB**，100 万连接 ≈ 几个 GB 内存。

**3. CPU** 连接多了，上下文切换、内核处理开销上升。

------

## 实际结论

| 限制因素       | 默认值      | 可调整后          |
| -------------- | ----------- | ----------------- |
| 文件描述符     | 65535       | 百万级            |
| 内存           | 取决于机器  | 百万级连接需数 GB |
| 端口（客户端） | ~6万/目标IP | 多目标可复用      |





# 我的RPC自定义协议里的魔数是用来干嘛的。协议识别与魔数：讨论总结

### 1. 魔数是干什么的？

在你这个 RPC 协议里，魔数（magic，如 0x1） 的作用是：

- 不是用来决定「我们用的是不是 RPC」——那是端口和事先约定的事。

- 是在同一条 TCP 连接上的字节流里做校验：

- 解码时先看第一个字节是不是魔数；

- 是 → 认为这是一条合法 RPC 帧的开头，继续按 17 字节头 + body 解析；

- 不是 → 立刻报错/关连接，避免把脏数据、错位数据当 RPC 解析（防止错位、误读 bodyLength 等）。

所以：魔数 = 流内“帧起始”校验，提高健壮性，不是“协议类型识别”。

------

### 2. 协议识别是谁在做？

- “这是不是我的 RPC 服务 / 用不用这个协议” → 由 端口号 决定（例如连 8888 就约定用你的 RPC）。

- “这段字节是不是一条合法 RPC 帧” → 由 魔数 在解码时做快速校验。

其他协议对比：

- TCP / UDP：由 IP 头的 Protocol 字段（6=TCP，17=UDP）区分；

- HTTP、SMTP 等：由 端口（80、25…）+ 首行/首字节格式（如 GET 、220）识别；

- 你的 RPC：端口 负责“用 RPC”，魔数 负责“这段流是不是我的帧”。

------

### 3. 一句话

- 协议识别（用不用 RPC）→ 看 端口；

- 魔数 → 在已约定 RPC 的连接上，对 字节流做帧起始校验，防止错位和脏数据。







# 客户端发送消息，服务端返回，服务端怎么知道要返回给哪个客户端。客户端收到消息怎么知道是给自己的，如果客户端发送大量消息呢？怎么识别



## 1. 服务端怎么知道要返回给哪个客户端？

服务端不用去“查客户端是谁”，由 TCP 连接决定。

- 请求是从 当前这条 Channel（TCP 连接） 读到的。

- 响应通过 同一条 Channel 写回：ctx.writeAndFlush(responseProtocolMessage)。

也就是说：谁发来的请求，就通过谁的连接把响应写回去。所以“返回给哪个客户端”是由 连接（Channel） 决定的，不是由服务端再去做“客户端寻址”。

```java
NettyTcpServerHandler.javaLines 42-46

​    // 发送响应，编码

​    header.setType((byte) ProtocolMessageTypeEnum.RESPONSE.getKey());

​    header.setStatus((byte) ProtocolMessageStatusEnum.OK.getValue());

​    ProtocolMessage<RpcResponse> responseProtocolMessage = new ProtocolMessage<>(header, rpcResponse);

​    ctx.writeAndFlush(responseProtocolMessage);
```



这里还做了一件事：响应的 header 直接复用了请求的 header（只改了 type/status），所以 requestId 会原样带回，下面客户端才能用 requestId 做匹配。

------

## 2. 客户端怎么知道这条消息是给自己的？

在单连接、多请求（连接池复用）的情况下，同一条连接上会交错收到很多响应，所以必须用 requestId 区分“这条响应对应哪一次请求”。

协议里已经带了 requestId：

```java
ProtocolMessage.javaLines 56-60

​    /**

​     \* 请求 id

​     */

​    private long requestId;
```



流程是：

1. 发请求时：生成唯一 requestId，把 requestId -> CompletableFuture\<RpcResponse> 放进 pendingRequests，并把 requestId 放进请求头一起发出去。

2. 收响应时：从响应头的 requestId 在 pendingRequests 里找到对应的 CompletableFuture，把 RpcResponse 填进去（complete），当初在等这个 Future 的调用就能拿到结果。

所以“是给自己的”在这里的含义是：是给「requestId 对应的那一次请求」的，由 requestId 唯一确定。

----

## 3. 客户端发大量消息时怎么识别？

靠 requestId 唯一 + 一张“未完成请求表”。

- 唯一 ID：每个请求用雪花算法生成一个 long 型 requestId，保证不同请求不会重复。

- 映射表：Map<Long, CompletableFuture\<RpcResponse>> pendingRequests，key 是 requestId，value 是“等这个请求结果”的 Future。

发请求时：

```java
NettyTcpClientPool.javaLines 149-169

​      // 2. 生成请求 ID

​      long requestId = IdUtil.getSnowflakeNextId();

​      // 3. 创建响应 Future

​      CompletableFuture<RpcResponse> responseFuture = new CompletableFuture<>();

​      pendingRequests.put(requestId, responseFuture);

​      // 4. 构造协议消息

​      ...

​      header.setRequestId(requestId);

​      ...

​      // 5. 发送请求

​      channel.writeAndFlush(protocolMessage);
```



收响应时：

```java
NettyTcpClientPoolHandler.javaLines 17-24

  protected void channelRead0(ChannelHandlerContext ctx, ProtocolMessage<RpcResponse> msg) throws Exception {

		 ProtocolMessage.Header header = msg.getHeader();

     RpcResponse rpcResponse = msg.getBody();

     long requestId = header.getRequestId();

     // 通过 requestId 匹配请求并完成 Future

    NettyTcpClientPool.handleResponse(requestId, rpcResponse);

  }
```



handleResponse 里会从 pendingRequests 中按 requestId 取出对应的 Future 并 complete。所以：

- 发 100 个请求 → 100 个不同的 requestId → 100 个 Future；

- 每个响应带自己的 requestId → 只会唤醒对应的那一个 Future。

小结：

| 问题                       | 机制                                                         |
| :------------------------- | :----------------------------------------------------------- |
| 服务端返回给谁？           | 谁发请求就用谁的 Channel（ctx）写回，不需要再查“客户端是谁”。 |
| 客户端怎么知道是给自己的？ | 响应头里带 requestId，客户端用 requestId 找到对应的 CompletableFuture 并完成。 |
| 大量并发请求怎么识别？     | 每个请求一个唯一 requestId + pendingRequests(requestId -> Future)，收到响应按 requestId 匹配即可。 |

- 注册中心确实会有很多“客户端”连到它（各 Provider 注册、心跳，各 Consumer 拉取/订阅），但那是注册中心自己的管理连接，不是你的 RPC 业务连接。

- RPC 业务数据是：Consumer 的 Netty 客户端 ↔ Provider 的 Netty 服务端，点对点直连，不经过注册中心。

# 服务注册与发现


按照这个说法Nacos不就是维护了所有客户端的链接吗？

Nacos 2.x

客户端和 Server 之间建 gRPC 长连接（每个进程通常一条到某一台 Server）。

订阅请求（subscribe）通过这条 gRPC 连接发给 Server；Server 记录“这个连接订阅了哪些服务”。

当某服务的实例列表变化时，Server 通过同一条 gRPC 连接向客户端发送“变更”请求（例如 NotifySubscriberRequest），客户端更新本地缓存并发布事件，触发你的 EventListener。

同时很多实现里还会保留定时拉取作为对账或兜底。

## Nacos 确实维护了“和所有客户端的连接”

在 Nacos 2.x 里：

- 每个连到 Nacos 的进程（不管是 Consumer 还是 Provider）都会和 Nacos Server 建 一条 gRPC 长连接。
- Server 端会持有这些连接，并且知道：
- 这条连接对应哪个客户端；
- 这个客户端注册了哪些服务（Provider 上报的实例）；
- 这个客户端订阅了哪些服务（Consumer 的 subscribe）。
- 当某服务的实例列表变化时，Server 就通过对应的那几条 gRPC 连接，给订阅了该服务的客户端推送变更（例如 NotifySubscriberRequest）。
## 之前说的“没管理连接”指的是另一类连接

之前说的“注册中心没有管理多个客户端的连接”，指的是你的 RPC 业务连接，不是指“客户端和 Nacos 之间的连接”。

可以这样区分：

| 连接类型      | 谁和谁                   | Nacos 是否维护？ | 上面跑的数据                             |
| --------- | --------------------- | ----------- | ---------------------------------- |
| 注册/发现协议连接 | 每个应用进程 ↔ Nacos Server | 是（gRPC 长连接） | 注册、心跳、订阅、服务列表推送                    |
| RPC 业务连接  | Consumer ↔ Provider   | 否           | 你的 RpcRequest / RpcResponse，实际方法调用 |

会，单机扛太多连接肯定有问题；所以 Nacos 用集群 + 客户端分散连接来扛一万、两万甚至更多客户端。

---

##  单机有上限，一万两万全连一台会有问题

- Nacos 1.x：单机（例如 8C16G）大致 6k～1w 个客户端实例，再往上（如 1.4w）容易不稳定。

- Nacos 2.x（gRPC 长连接）：同配置下能力明显提升，压测里 1.4w 实例 单机还能稳定；有资料给出约 4 万+ 客户端/单机（8C16G）的量级。

所以：如果真把一万、两万个客户端都连到同一台 Nacos 上，单机在连接数、FD、内存、推送时的 CPU/网络上都会吃紧，会有问题。

正确做法不是让一台“管理那么多连接”，而是多台一起分担。

##  注册中心不管 RPC 业务连接

服务发现中心不会“管理许多客户端的连接然后转发 RPC 数据”。

它只做两件事：

- 存元数据：服务名 → 提供者实例列表（host:port）

- 给消费端查：根据服务名返回「当前可用的提供者地址列表」

也就是说：注册中心只反馈“去哪连”的元数据，不承载、不转发你的 RPC 请求/响应。

| 角色               | 和注册中心的关系                                            | 和 Netty 的关系                                              |
| :----------------- | :---------------------------------------------------------- | :----------------------------------------------------------- |
| Provider（服务端） | 启动时把 ServiceMetaInfo（服务名、本机 host、port）注册上去 | 本机起 Netty Server，监听 serverPort，等别人连过来           |
| Consumer（调用方） | 调用前用 registry.serviceDiscovery(serviceKey) 查提供者列表 | 根据查到的地址，用 Netty Client 直连某个 Provider 的 host:port 发 RPC |


## 2. 你项目里的实际角色划分

|角色|和注册中心的关系|和 Netty 的关系|
|---|---|---|
|Provider（服务端）|启动时把 ServiceMetaInfo（服务名、本机 host、port）注册上去|本机起 Netty Server，监听 serverPort，等别人连过来|
|Consumer（调用方）|调用前用 registry.serviceDiscovery(serviceKey) 查提供者列表|根据查到的地址，用 Netty Client 直连某个 Provider 的 host:port 发 RPC|
|注册中心（Nacos/Etcd/ZK）|-|只和注册中心自己的协议打交道（如 Nacos 的 gRPC、ZK 的 session），不建、不持有一个个 RPC 的 Netty 连接|

所以：

- 注册中心确实会有很多“客户端”连到它（各 Provider 注册、心跳，各 Consumer 拉取/订阅），但那是注册中心自己的管理连接，不是你的 RPC 业务连接。

- RPC 业务数据是：Consumer 的 Netty 客户端 ↔ Provider 的 Netty 服务端，点对点直连，不经过注册中心。



## 3. 用你现有代码串一下流程

服务端（Provider）

启动时在 ProviderBootstrap / RpcProviderBootstrap 里：

- 本地：LocalRegistry.register(serviceName, implClass)

- 远程：registry.register(serviceMetaInfo)

这里 serviceMetaInfo 里带着本机的 serverHost、serverPort，也就是本机 Netty Server 的地址。

消费端（Consumer）

在 ServiceProxy.invoke() 里（你项目里目前仍用 VertxTcpClient，若改成 Netty 也是同样逻辑）：

```java
ServiceProxy.javaLines 52-61

    // 从注册中心获取服务提供者请求地址

    RpcConfig rpcConfig = RpcApplication.getRpcConfig();

    Registry registry = RegistryFactory.getInstance(rpcConfig.getRegistryConfig().getRegistry());

    ServiceMetaInfo serviceMetaInfo = new ServiceMetaInfo();

    serviceMetaInfo.setServiceName(serviceName);

    serviceMetaInfo.setServiceVersion(RpcConstant.DEFAULT_SERVICE_VERSION);

    List<ServiceMetaInfo> serviceMetaInfoList = registry.serviceDiscovery(serviceMetaInfo.getServiceKey());

    if (CollUtil.isEmpty(serviceMetaInfoList)) {

      throw new RuntimeException("暂无服务地址");

    }
```



- registry.serviceDiscovery(serviceKey)：向注册中心查该服务名下的所有实例 → 得到 List\<ServiceMetaInfo>（多个 host:port）。

- 再用负载均衡从列表里选一个 selectedServiceMetaInfo。

- 然后 Netty（或 Vertx）客户端 用 selectedServiceMetaInfo.getServiceHost()、getServicePort() 直连 那个 Provider，发请求、收响应。

所以：“反馈数据”的是注册中心只反馈「服务地址列表」；真正传 RPC 请求/响应的是 Consumer 和 Provider 之间的 Netty 直连。



## 客户端怎么知道“服务已经不活跃”？

### 方式一：注册中心推送 → 清空本地缓存（已有）

客户端在第一次做 serviceDiscovery(serviceKey) 时会：

1. 从注册中心拉列表并 writeCache(serviceKey, list)

1. 对该服务 watch / subscribe

当注册中心发现某个实例不活跃（心跳超时或主动下线）并更新实例列表后，会推事件给订阅者，回调里会清掉该服务的本地缓存：

- Nacos（你项目里已有）：

```java
NacosRegistry.javaLines 168-175

​        namingService.subscribe(serviceName, getGroupName(serviceVersion), event -> {

​          if (event != null) {

​            log.info("服务列表发生变化，服务名：{}", serviceName);

​            // 清理注册服务缓存

​            registryServiceMultiCache.clearCache(serviceNodeKey);

​          }

​        });
```



- Etcd：watch 到 DELETE 等事件时同样会 registryServiceMultiCache.clearCache(serviceNodeKey)。

所以：一旦注册中心认为实例不活跃并推了变更，客户端会清掉该服务的缓存；下次再 serviceDiscovery(serviceKey) 会重新从注册中心拉，拿到的是更新后的列表，就不会再拿到已下线的那个实例（在“注册中心侧”已经摘掉的前提下）。

也就是说：“客户端知道服务不活跃”的第一种方式，就是：注册中心通知 → 清缓存 → 下次发现用新列表。



### 方式二：真正发 RPC 时连不上 / 超时（当前未反哺缓存）

另一层是调用时才发现不活跃：

客户端从缓存里拿到 List\<ServiceMetaInfo>，负载均衡选出一个 selectedServiceMetaInfo，用 Netty/Vertx 去连这个 host:port。如果对方已经挂了或网络不通，就会：

- 连接失败、或

- 读超时 / 写失败

这时客户端已经知道“这个实例当前不可用”，但当前实现里：

- 只做了 重试 和 容错（返回默认/抛异常），

- 没有在失败时对“该服务”做 clearCache(serviceKey)，也没有在本地把“这个实例”标记为不可用。

所以：本地缓存里确实会在一段时间内仍然保留已经不活跃的实例，直到：

- 注册中心检测到该实例心跳超时并摘除，然后通过 watch 触发你这边的 clearCache，或

- 你主动增加“调用失败时清缓存/标记故障”的逻辑。

## 注册中心不“管 RPC 连接”，而是“推送变更”

- 注册中心：不管理“多个 RPC 客户端到 Provider 的业务连接”，只做两件事：

- 存「服务名 → 实例列表」的元数据；

- 在实例列表变化时，用某种方式通知订阅了该服务的客户端（“推送”变更）。

- 所以：是“推送（或拉取+推送）机制把变更消息/数据推给客户端”，而不是注册中心替你管理多条 RPC 链接。

你项目里就是：Nacos 通知“某服务实例列表变了” → 客户端回调里 clearCache → 下次发现时再拉最新列表。





# Nacos和ETCD怎么分别实现心跳机制的？

由 Nacos 客户端 SDK 内部自动发心跳，你的业务代码不用自己写定时任务。

你在项目里只做了两件事：

- 调用 namingService.registerInstance(serviceName, group, instance) 做服务注册；

- heartBeat() 里没有实际逻辑，只是打日志说明“心跳由 Nacos 客户端管理”。

```java
    @Override
    public void register(ServiceMetaInfo serviceMetaInfo) throws Exception {
        // 创建服务实例
        Instance instance = new Instance();
        ...
        // 注册服务（SDK 内部会启动心跳）
        namingService.registerInstance(serviceMetaInfo.getServiceName(), 
                getGroupName(serviceMetaInfo), instance);
      
    @Override
    public void heartBeat() {
        // Nacos客户端会自动处理心跳，这里不需要额外实现
        log.info("Nacos注册中心心跳检测已启动（由Nacos客户端自动管理）");
    }
```

### 1.2 Nacos 客户端内部大致怎么做的？

（这是 Nacos 官方客户端的通用行为，不是你这套代码里的实现，但能解释“心跳是谁发的”。）

- 注册时：除了把实例信息上报到服务端，还会在客户端启动一个定时任务（默认约每 5 秒一次）。

- 定时任务会向 Nacos 服务端发心跳请求（例如 /nacos/v1/ns/instance/beat），带上服务名、分组、ip、port 等。

- 服务端收到心跳后会更新该实例的最后心跳时间。

### 1.3 服务端怎么判断“死了”？

- 服务端有健康检查逻辑，会看每个实例的“最后心跳时间”：

- 超过约 15 秒没心跳 → 标记为不健康（可能不再被负载均衡选中）；

- 超过约 30 秒没心跳 → 从实例列表中删除该实例。

所以：Nacos 的心跳 = 客户端 SDK 定时向服务端“报活”，服务端根据最后心跳时间做健康检查和自动摘除。

## 2. Etcd 的“心跳”机制（租约 + 续约）

Etcd 没有“心跳接口”这个概念，而是用 Lease（租约）：带 TTL 的 key，到期自动删；要“保活”就要在 TTL 内续约。

### 2.1 你项目里的做法：定时“重新注册”当续约

当前 Etcd 注册实现是：

- 注册时：为每个服务创建一个 30 秒 的租约，把服务信息以 key-value 形式存到 Etcd，并和该租约绑定；key 记到 localRegisterNodeKeySet。

- “心跳”：用 CronUtil 每 10 秒跑一次任务，对 localRegisterNodeKeySet 里的每个 key：

- 先 get(key) 看 Etcd 里是否还存在；

- 若存在（说明还没过期），就再调一次 register(serviceMetaInfo)，相当于用新的 30 秒租约重新写一遍同一个 key，起到“续命”效果。

## 已经有 TCP 的心跳了，为什么还需要再自己写个心跳？



TCP 本身其实**没有"心跳"这个术语**，但有一个相关机制叫 **TCP Keep-Alive**，通常大家说的"TCP 心跳"就是指它。

------

**为什么需要它？**

TCP 连接建立后，如果双方都不发数据，这条连接可以**永远沉默下去**，TCP 协议本身完全不会主动探测对方还在不在。

这就会出问题：假设对方进程崩溃了、网线断了、机器关机了，你这边完全不知道，连接资源一直占着。

Keep-Alive 就是为了解决这个问题——**在空闲时定期发一个探测包，看对方还活着没有。**

------

**怎么工作的？**

连接空闲一段时间后（Linux 默认 **2 小时**），一端发送一个探测包，这个包本质上是一个**没有数据的 TCP 段**，序列号故意设为对方已经确认过的值。

如果对方还活着，会回一个 ACK，说明连接正常，计时器重置。

如果连续发了若干次探测（Linux 默认 **9 次**，每次间隔 **75 秒**）都没收到回复，就判定连接已死，本地内核关闭这条连接，应用层读写时会收到错误。

------

**但实际中很少只靠它**

TCP Keep-Alive 有几个问题：默认 2 小时才开始探测，太慢了；而且它是操作系统内核层面的机制，不够灵活。

所以大部分应用会在**应用层自己实现心跳**。比如 WebSocket 有 Ping/Pong 帧，HTTP/2 有 PING 帧，很多 RPC 框架也有自己的心跳消息。这些应用层心跳间隔短（几秒到几十秒），检测更快，还能携带业务信息。





## 2. 注册中心的“心跳”是干什么的？

注册中心（Nacos/Etcd）维护的是：“哪些服务实例还活着，可以对外提供这个服务”。

它和你的 RPC 服务是两个不同的系统：

- 注册中心：只和你进程里的“注册客户端”通信（HTTP/gRPC 等）。

- 你的 RPC 服务：和别的 RPC 客户端之间用 TCP（上面说的 TCP keepalive 是在这里）。

所以：

- Nacos 的心跳：你的进程定期向 Nacos 说“我还活着”，Nacos 更新这个实例的“最后心跳时间”；超时没收到就认为实例挂了，从列表里摘掉。

- Etcd 的续约：你的进程定期续约（或你写的定时“重新注册”），否则租约过期，Etcd 自动删 key，相当于从服务列表里消失。

也就是说：“谁在提供这个服务、要不要从注册表里删掉” 这件事，只能由 “你的进程 ↔ 注册中心” 的这类心跳/续约来维护，TCP keepalive 做不到。





# 负载均衡策略



负载均衡的核心目标是把流量合理分配到多台服务器上，避免单点过载。

**常见的算法主要有以下几种**：

1）轮询算法：按顺序把请求依次分给后端服务器，比如第一个请求给 Serverl，第二个给 Server2，循环往复。适合后端服务器处理能力相当的场景，但如果服务器性能差异大，4 核的机器和 32核的机器分到一样多的请求，显然不合理。

2）加权轮询算法：在轮询基础上给每个服务器设置权重，权重越高被选中概率越大。比如一台8 核的机器权重设8，一台4核的设 4，让高性能机器多扛点活。Nginx 的 upstream 默认就支持 weight 配置。

3）随机算法：像掷骰子一样随机挑一台服务器处理请求，每台被选中的概率相等。缺点和轮询类似，不考虑服务器性能差异。

4）加权随机算法：随机算法的升级版，根据权重调整被选中的概率，减少高性能服务器的闲置。

5）最少连接算法：选择当前连接数最少的服务器来处理请求。适合请求处理时间差异大的场景，比如有些请求 10ms 就返回了，有些要跑5 秒才能出结果，这时候按连接数分配比轮询靠谱得多。

6）哈希算法：根据请求的某个特征算哈希值，比如客户端IP 或 URL，将同一特征的请求路由到同一台服务器。RedisCluster 和 Nginx的 ip_hash 都是这种方式，能保证同一个用户的请求始终落到同一台机器上，对有状态服务很重要。



##  一致性哈希

一致性哈希（Consistent Hashing）是一种经典的哈希算法，用于将请求分配到多个节点或服务器上，所以非常适用于负载

均衡。

它的核心思想是将整个哈希值空间划分成一个环状结构，每个节点或服务器在环上占据一个位置，每个请求根据其哈希值映射到环上的一个点，然后顺时针寻找第一个大于或等于该哈希值的节点，将请求路由到该节点上。



![image6.png](https://pic.code-nav.cn/mianshiya/question_picture/1772087337535152129/image6_mianshiya.webp)





与普通的轮询算法相比，一致性哈希还解决了 节点下线 和 倾斜问题。

1）节点下线：当某个节点下线时，其负载会被平均分摊到其他节点上，而不会影响到整个系统的稳定性，因为只有部分请求会受到影响。

2）倾斜问题：通过虚拟节点的引入，将每个物理节点映射到多个虚拟节点上，使得节点在哈希环上的分布更加均匀，减少了节点间的负载差异。







普通哈希算法有个致命问题：服务器数量变了，哈希结果就全乱了。

比如原来 3台服务器，hash % 3算下标；加一台变成 hash % 4，大量请求会被路由到不同的机器，如果后端有本地缓存，瞬间缓存失效率能到75％，直接把数据库打爆。

一致性哈希就是为了解决这个问题设计的。

它把•到2^32组成一个虚拟的圆环，服务器节点根据IP 或名称算出哈希值，映射到环上的某个位置。请求过来也算哈希值，然后顺时针找到第一个服务器节点。这样增删节点只影响相邻的一小段请求，不会引发雪崩。

Memcached、Redis 的一些客户端库、Dubbo 都支持一致性哈希负载均衡。

一致性哈希还有个虚拟节点的概念。如果物理节点太少，比如就 3 台服务器，可能分布不均匀导致某台机器压力特别大。

虚拟节点就是把一台物理机映射成多个虚拟节点分散到环上，比如 Server1 映射出 Server1#1、Server1#2、Server1#3 三个虚拟节点，让数据分布更均匀。



![image.png](https://pic.code-nav.cn/mianshiya/question_picture/1783388929455529986/9zkKhFyN_image_mianshiya.webp)



# 容错策略



## 2. 重试策略（RetryStrategy）

| 配置值        | 实现类                     | 含义                                |
| :------------ | :------------------------- | :---------------------------------- |
| no            | NoRetryStrategy            | 不重试，失败直接抛异常              |
| fixedInterval | FixedIntervalRetryStrategy | 固定间隔重试（基于 Guava Retrying） |

SPI 定义在：META-INF/rpc/system/com.naive.rpc.fault.retry.RetryStrategy。

------

## 3. 容错策略（TolerantStrategy）

重试仍失败后，会进入容错（在 ServiceProxy 的 catch 里）：

| 配置值   | 实现类                   | 含义                                                    |
| :------- | :----------------------- | :------------------------------------------------------ |
| failFast | FailFastTolerantStrategy | 快速失败：包装成 RuntimeException 抛出                  |
| failSafe | FailSafeTolerantStrategy | 静默失败：打日志，返回空的 RpcResponse                  |
| failOver | FailOverTolerantStrategy | 故障转移：预留扩展，当前返回 null（待实现“换节点再调”） |
| failBack | FailBackTolerantStrategy | 失败回退：预留扩展，当前返回 null（待实现降级逻辑）     |

SPI 定义在：META-INF/rpc/system/com.naive.rpc.fault.tolerant.TolerantStrategy。

```java
        // rpc 请求
        // 使用重试机制
        RpcResponse rpcResponse;
        try {
            RetryStrategy retryStrategy = RetryStrategyFactory.getInstance(rpcConfig.getRetryStrategy());
            rpcResponse = retryStrategy.doRetry(() ->
                    VertxTcpClient.doRequest(rpcRequest, selectedServiceMetaInfo)
            );
        } catch (Exception e) {
            // 容错机制
            TolerantStrategy tolerantStrategy = TolerantStrategyFactory.getInstance(rpcConfig.getTolerantStrategy());
            rpcResponse = tolerantStrategy.doTolerant(null, e);
        }
```



# Zookeeper vs etcd vs Nacos



**定位不同**

Zookeeper 最早是 Hadoop 的子项目，本质是分布式协调服务，被"借用"来做注册中心。etcd 是 Kubernetes 的底座，核心是分布式 KV 存储。Nacos 是阿里开源的，从一开始就是为注册中心 + 配置中心设计的，开箱即用。

**一致性协议**

Zookeeper 用 ZAB 协议，etcd 用 Raft 协议，两者都是 CP 系统（强一致性，网络分区时可能牺牲可用性）。Nacos 比较灵活，它同时支持 CP（Raft）和 AP（Distro 协议）两种模式，临时实例默认用 AP，持久实例用 CP。

**健康检查**

Zookeeper 靠临时节点 + 心跳，服务挂了临时节点自动删除。etcd 靠 lease（租约）机制，TTL 过期自动删除。Nacos 内置了主动健康检查（HTTP/TCP 探活），也支持客户端心跳上报，功能最丰富。

**易用性**

Zookeeper 没有 UI，API 是树形节点操作（create/get/set），做注册中心需要自己封装（或用 Curator）。etcd 也没有原生 UI，提供 KV 的 gRPC/HTTP API，同样需要上层封装。Nacos 自带 Web 控制台，提供专门的服务注册/发现/配置管理 API，接入成本最低。

**配置管理**

Zookeeper 可以做但很原始，就是往节点写数据 + watch。etcd 类似，KV + watch。Nacos 原生支持配置管理，有命名空间、分组、灰度发布、配置历史回滚，这块远强于前两者。

**语言生态**

Zookeeper 是 Java 写的，Java 生态最好。etcd 是 Go 写的，Go/K8s 生态最好。Nacos 是 Java 写的，对 Spring Cloud / Dubbo 生态支持最好，有现成的 starter 直接集成。

**性能**

etcd 在读写延迟上通常优于 Zookeeper（Raft 比 ZAB 更简洁高效）。Nacos 在 AP 模式下吞吐量很高，适合大规模服务注册场景。Zookeeper 在节点数很多时 watch 的性能会成为瓶颈。

**小规模、强一致 → etcd 性能最均衡。大规模服务注册（万级实例以上）→ Nacos AP 模式吞吐量和扩展性最好。Zookeeper 在大规模场景下 watch 是明显短板，性能最先遇到瓶颈。**





 



# 一个很大的文件例如几tb，是如何在网络传输的。在网络里一个包最大是多少，这个概念是叫MSS吗？如果数据太大，在哪一层做拆分，在哪一层做合并。怎么保证他的合并是有序的正确的？

**包的大小限制**

网络中有两个关键概念：

**MTU（Maximum Transmission Unit）**——这是数据链路层（第二层）的限制，指一个以太网帧能承载的最大数据量，以太网默认是 **1500 字节**。

**MSS（Maximum Segment Size）**——这是传输层（第四层，TCP）的概念，指一个 TCP 段能携带的最大应用数据量。它等于 MTU 减去 IP 头（20字节）和 TCP 头（20字节），所以通常是 **1460 字节**。

你说的没错，MSS 就是 TCP 层面"一个包最多装多少数据"的那个概念。

**拆分发生在哪一层？**

拆分主要发生在两个地方：

**传输层（TCP，第四层）做分段（Segmentation）。** 应用层把一个几 TB 的文件通过 socket 写下来，TCP 会按 MSS 把数据流切成一个个 segment。一个 1TB 的文件大概会被切成约 7 亿个 TCP 段。这是最主要的拆分。

**网络层（IP，第三层）可以做分片（Fragmentation）。** 如果某个 TCP 段加上头部仍然超过了链路的 MTU，IP 层会再切一次。但现代网络基本通过 MSS 协商和 Path MTU Discovery 来避免 IP 分片，因为 IP 分片效率很低且容易出问题。

所以实际上，**TCP 分段是主力，IP 分片是兜底但尽量避免。**

------

**合并发生在哪一层？**

对称地：

如果发生了 IP 分片，**接收端的 IP 层**负责把分片重组成完整的 IP 数据报，然后交给 TCP。

TCP 段的重组由**接收端的 TCP 层**完成，它把收到的段按序拼回连续的字节流，再交给应用层。

------

**怎么保证合并是有序且正确的？**

TCP 靠三个机制：

**序列号（Sequence Number）。** TCP 连接建立时双方协商一个初始序列号，之后每个段都带一个序号，表示"这个段的第一个字节是整个流里的第几个字节"。接收端根据序号把乱序到达的段排回正确位置。

**确认号（ACK）+ 滑动窗口。** 接收端告诉发送端"我已经连续收到了第 N 个字节之前的所有数据"。发送端据此知道哪些数据已安全送达，哪些需要重传。

**校验和（Checksum）。** 每个 TCP 段都带校验和，接收端验证数据完整性，损坏的段直接丢弃，等发送端超时重传。

对于 IP 分片的场景，IP 头里有 **Identification（标识）** 和 **Fragment Offset（偏移量）** 两个字段来保证同一个数据报的分片能正确拼回去。

### MTU不是数据链路层的吗，为什么会在IP成分片

**MTU 确实是数据链路层的限制**，它定义的是"这条链路一帧最多能装多大的载荷"。以太网是 1500 字节，Wi-Fi 是 2304 字节，不同链路技术 MTU 不同。

**但数据链路层自己不会拆包。** 它的态度很简单：你给我的数据超过我的 MTU，我装不下，要么你别给我，要么我直接丢掉报错。数据链路层没有分片能力。

------

**那谁来解决这个问题？只能是上一层——IP 层。**

IP 层在发送数据报时，会查看出口链路的 MTU。如果这个 IP 数据报比 MTU 大，IP 层就把它拆成多个小于 MTU 的分片，每个分片各自加上 IP 头，然后分别交给数据链路层。这样每个分片都能装进一帧，数据链路层就满意了。

打个比方：数据链路层是一辆卡车，限载 1500 公斤。卡车司机不会帮你拆货，他只告诉你"超重不拉"。IP 层就是装货的工人，他知道卡车的限载，所以提前把大件货物拆成小件，分批装车。

## UDP

**UDP 的大小限制**

UDP 头里有一个 16 位的 Length 字段，所以一个 UDP 数据报理论最大是 **65535 字节**（含 UDP 头 8 字节和 IP 头），实际载荷最大约 **65507 字节**。

但这只是理论上限。实际中你发一个 65000 字节的 UDP 包，它会超过链路的 MTU（1500），这时候会发生什么？

------

**UDP 大包怎么处理？**

UDP 自己不管拆分。它把整个数据报原封不动交给 IP 层，**IP 层发现超过 MTU，就会做分片（Fragmentation）**。

比如你发一个 3000 字节的 UDP 数据报，IP 层会把它拆成两个 IP 分片，到达接收端后由接收端的 IP 层重组，再交给 UDP，最后交给应用层。

------

**这为什么是个问题？**

IP 分片有几个很大的缺陷：

**任何一个分片丢了，整个数据报都废了。** IP 层没有重传机制，UDP 也没有。假设一个 UDP 包被切成 10 个 IP 分片，丢了 1 个，剩下 9 个全部白传。

**没有拥塞控制。** 大量大 UDP 包导致大量 IP 分片，很容易加剧网络拥塞和丢包。

**有些网络设备或防火墙会直接丢弃 IP 分片。**



# 粘包 半包问题，http是怎么读消息头中的字段(分隔符)，二进制帧又是怎么分割的



**粘包和半包**

TCP 是字节流，没有"消息边界"的概念。发送端调两次 write，分别写了消息 A 和消息 B，接收端 read 的时候可能一次就读到了 A+B 粘在一起（**粘包**），也可能只读到了 A 的前半截（**半包**）。TCP 不管你的消息在哪里结束，它只负责把字节流完整有序地送到。

所以**应用层必须自己定义怎么从字节流里切出一条完整的消息**。常见的方案就三种：分隔符、固定长度头、固定长度消息。

------

**HTTP/1.x——文本协议，靠分隔符 + Content-Length**

HTTP/1.x 是纯文本协议，一条 HTTP 消息长这样：

```
GET /index.html HTTP/1.1\r\n
Host: example.com\r\n
Content-Length: 13\r\n
\r\n
Hello, World!
```

它用**两层机制**来确定消息边界：

**请求头/响应头的结束：靠 `\r\n\r\n`（连续两个换行）。** 接收端从字节流里一个字节一个字节地读，看到 `\r\n\r\n` 就知道头部结束了。在这之前，每一行 header 都是用 `\r\n` 分隔的，所以解析 header 就是按 `\r\n` 逐行读，每行再按冒号分割出字段名和值。

**Body 的结束：靠头部里声明的 `Content-Length`。** 头部解析完了，从中取出 Content-Length 的值（比如 13），然后从字节流里再精确读 13 个字节，就是完整的 body。

如果没有 Content-Length（比如流式响应），就用 **Transfer-Encoding: chunked**，每个 chunk 前面带一个十六进制的长度，最后用一个长度为 0 的 chunk 表示结束：

```
4\r\n
Wiki\r\n
5\r\n
pedia\r\n
0\r\n
\r\n
```

所以 HTTP/1.x 本质上是：**分隔符（\r\n\r\n）定位头部结束，长度字段（Content-Length 或 chunk size）定位 body 结束。**

------

**HTTP/2——二进制帧协议，靠固定长度头**

HTTP/2 不再是文本协议，所有数据被封装成**帧（Frame）**，每个帧有一个固定 9 字节的帧头：

```
+-----------------------------------------------+
|                Length (3 字节)                   |
+---------------+-------------------------------+
|  Type (1字节)  |  Flags (1字节)                  |
+---------------+-------------------------------+
|R|          Stream Identifier (4 字节)           |
+-----------------------------------------------+
|              Frame Payload (变长)                |
+-----------------------------------------------+
```

接收端的解析逻辑非常简单：

先读固定的 **9 个字节**，这是帧头，永远不会变。从前 3 个字节取出 Length 值，知道后面的 payload 有多长。再精确读取 Length 个字节，就是完整的一帧。然后下一个 9 字节又是下一帧的帧头，如此循环。

不需要任何分隔符，不需要逐字节扫描，**直接按偏移量读固定位置的字段**，解析速度比文本协议快得多。

------

**对比一下两种方式**

HTTP/1.x（文本 + 分隔符）：要逐字节扫描找 `\r\n`，遇到大 header 扫描成本高，而且分隔符本身如果出现在内容里还需要转义处理。好处是人能直接读，调试方便。

HTTP/2（二进制 + 固定长度头）：永远先读固定字节数，拿到长度再读 payload，不需要扫描。快、紧凑、没有歧义。但人看不懂，调试要靠工具。







# 限流算法

**简单对比：**

固定窗口——最简单，有临界突发问题。滑动窗口——修复了临界问题，实际中常用。漏桶——严格平滑，不允许任何突发。令牌桶——允许突发但控制平均速率，最灵活，用得最多。

实际项目中，**令牌桶和滑动窗口**是最常见的选择。

## 固定窗口计数器（Fixed Window Counter）

把时间切成固定的窗口，比如每秒一个窗口，窗口内计数，达到阈值就拒绝。

简单直接，但有**临界问题**：假设限制每秒 100 次，在第一秒的最后 100ms 来了 100 个请求，第二秒的前 100ms 又来了 100 个，两个窗口都没超限，但实际上 200ms 内涌入了 200 个请求，是预期的两倍。

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 固定窗口计数器限流
 */
public class FixedWindowRateLimiter {

    private final int maxRequests;       // 窗口内最大请求数
    private final long windowSizeMs;     // 窗口大小（毫秒）
    private final AtomicInteger counter = new AtomicInteger(0);
    private final AtomicLong windowStart = new AtomicLong(System.currentTimeMillis());

    public FixedWindowRateLimiter(int maxRequests, long windowSizeMs) {
        this.maxRequests = maxRequests;
        this.windowSizeMs = windowSizeMs;
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        // 如果当前时间超出窗口，重置
        if (now - windowStart.get() >= windowSizeMs) {
            windowStart.set(now);
            counter.set(0);
        }
        return counter.incrementAndGet() <= maxRequests;
    }

    public static void main(String[] args) throws InterruptedException {
        FixedWindowRateLimiter limiter = new FixedWindowRateLimiter(5, 1000);
        for (int i = 1; i <= 8; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
    }
}
```

## 滑动窗口计数器（Sliding Window Counter）

把固定窗口再细分成多个小格子，比如 1 秒分成 10 个 100ms 的小窗口。统计时把当前时间往前推一整个窗口的所有小格子加起来。

这样窗口是"滑动"的，临界突发问题大幅缓解。实现上比固定窗口稍复杂，但效果好很多。Sentinel 用的就是这个思路。

```java
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * 滑动窗口计数器限流
 * 用队列记录每个请求的时间戳，统计窗口内的请求数
 */
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
        // 移除窗口外的旧时间戳
        while (!timestamps.isEmpty() && now - timestamps.peek() >= windowSizeMs) {
            timestamps.poll();
        }
        if (timestamps.size() < maxRequests) {
            timestamps.offer(now);
            return true;
        }
        return false;
    }

    public static void main(String[] args) throws InterruptedException {
        SlidingWindowRateLimiter limiter = new SlidingWindowRateLimiter(5, 1000);
        for (int i = 1; i <= 8; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
        System.out.println("等待1秒...");
        Thread.sleep(1000);
        System.out.println("请求9: " + (limiter.tryAcquire() ? "通过" : "拒绝"));
    }
}

```



## 漏桶算法（Leaky Bucket）

想象一个底部有小孔的桶。请求进来就往桶里倒水，水以**固定速率**从底部漏出（被处理）。桶满了，新的水直接溢出（拒绝）。

核心特点是**出口速率恒定**，不管进来多少请求，处理速度始终平稳。适合需要严格平滑流量的场景，但缺点是即使系统有余力，突发流量也没法加速处理，不够灵活。

**错误代码：**你说得完全对。我给的这个实现**本质上更像令牌桶**，只是换了个说法，并没有真正实现漏桶"固定速率流出"的语义。

------

**真正的漏桶应该是什么样的？**

真正的漏桶不是"判断能不能进来"，而是**请求进桶排队，以固定间隔一个一个放出去处理**。如果每秒漏2个，那就是严格的每500ms处理一个，不管桶里攒了多少。

这意味着漏桶需要一个**队列**，请求进来先排队，然后有一个消费机制按固定节奏取出处理。

------

**两种语义的区别**

我之前写的那个（大部分网上的实现也是这样）：只是在做"准入控制"——判断请求能不能进桶。进了桶之后立刻就处理了，根本没有"排队等着按节奏流出"这回事。所以你看到的就是瞬间涌入5个都立刻通过了。

真正的漏桶：请求进桶后**不会立刻被处理**，而是排队等，消费端严格按固定速率取。这才是"平滑流量"的真正含义。

------

**为什么大部分实现都是"假漏桶"？**

因为真漏桶需要排队 + 定时消费，实现复杂，而且会引入**延迟**——请求进了桶还要等着被处理，响应时间变长。大多数业务场景不需要这么严格的平滑，只需要控制总量，所以实际中几乎都用令牌桶的思路，管它叫什么名字。

真正需要严格平滑的场景，比如网络流量整形（Traffic Shaping），才会用真漏桶，而且通常是在操作系统或网络设备层面实现的，比如 Linux 的 `tc`（traffic control）。

------

**所以结论是：** 我之前给的漏桶和令牌桶代码，逻辑上其实是同一个东西的两种写法。真正的漏桶要有队列和固定间隔消费，实际业务开发中很少这么做。面试时知道这个区别是加分项。

```java
/**
 * 漏桶算法限流
 * 水（请求）以任意速率流入，以固定速率流出
 * 桶满则拒绝
 */
public class LeakyBucketRateLimiter {

    private final int capacity;          // 桶容量
    private final double leakRatePerMs;  // 每毫秒漏出多少
    private double currentWater;         // 当前水量
    private long lastLeakTime;           // 上次漏水时间

    public LeakyBucketRateLimiter(int capacity, int leakPerSecond) {
        this.capacity = capacity;
        this.leakRatePerMs = leakPerSecond / 1000.0;
        this.currentWater = 0;
        this.lastLeakTime = System.currentTimeMillis();
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        // 先漏水：计算这段时间漏掉了多少
        double leaked = (now - lastLeakTime) * leakRatePerMs;
        currentWater = Math.max(0, currentWater - leaked);
        lastLeakTime = now;

        // 尝试加水
        if (currentWater < capacity) {
            currentWater++;
            return true;
        }
        return false; // 桶满，拒绝
    }

    public static void main(String[] args) throws InterruptedException {
        // 桶容量5，每秒漏出2个
        LeakyBucketRateLimiter limiter = new LeakyBucketRateLimiter(5, 2);
        for (int i = 1; i <= 8; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
        System.out.println("等待2秒（漏出4个）...");
        Thread.sleep(2000);
        for (int i = 9; i <= 12; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
    }
}
```





## 令牌桶算法（Token Bucket）

系统以固定速率往桶里放令牌，桶有容量上限。每个请求来了先拿一个令牌，拿到就通过，拿不到就拒绝或排队。

和漏桶的关键区别：**允许一定程度的突发**。桶里攒了一堆令牌时，短时间内可以一口气放过很多请求，但长期平均速率还是受令牌生成速率限制。这在实际场景中更实用，因为现实流量本来就有波动。

Guava 的 RateLimiter、Nginx 的 limit_req 底层都是令牌桶的思路。

```java
/**
 * 令牌桶算法限流
 * 以固定速率生成令牌，请求来了消耗令牌
 * 桶里有积攒的令牌时允许突发
 */
public class TokenBucketRateLimiter {

    private final int capacity;              // 桶容量（最多攒多少令牌）
    private final double tokensPerMs;        // 每毫秒生成多少令牌
    private double currentTokens;            // 当前令牌数
    private long lastRefillTime;             // 上次补充令牌时间

    public TokenBucketRateLimiter(int capacity, int tokensPerSecond) {
        this.capacity = capacity;
        this.tokensPerMs = tokensPerSecond / 1000.0;
        this.currentTokens = capacity;       // 初始满桶
        this.lastRefillTime = System.currentTimeMillis();
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        // 先补充令牌
        double newTokens = (now - lastRefillTime) * tokensPerMs;
        currentTokens = Math.min(capacity, currentTokens + newTokens);
        lastRefillTime = now;

        // 尝试消耗一个令牌
        if (currentTokens >= 1) {
            currentTokens--;
            return true;
        }
        return false; // 没令牌了，拒绝
    }

    public static void main(String[] args) throws InterruptedException {
        // 桶容量5，每秒生成2个令牌
        TokenBucketRateLimiter limiter = new TokenBucketRateLimiter(5, 2);

        // 突发：初始有5个令牌，可以瞬间放过5个
        for (int i = 1; i <= 8; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
        System.out.println("等待2秒（生成4个令牌）...");
        Thread.sleep(2000);
        for (int i = 9; i <= 14; i++) {
            System.out.println("请求" + i + ": " + (limiter.tryAcquire() ? "通过" : "拒绝"));
        }
    }
}
```



# A服务调用B服务，怎么实现对B的保护？如何在A端实现服务保护

**在 B 端保护自己（不被打垮）**

B 作为被调用方，核心是**限流**——控制自己能接受多少请求，超了就拒绝。

就是我们前面聊的那些限流算法。B 给自己的接口设一个阈值，比如每秒最多处理 1000 次调用，超出的直接返回错误码，保证自己不会因为流量太大而崩掉。Sentinel、Guava RateLimiter 都可以做这件事。

另外 B 还可以做**服务降级**——当自己压力大时，主动关掉一些非核心逻辑，比如关掉推荐算法直接返回默认列表，把资源留给核心功能。

------

**在 A 端保护自己（不被 B 拖垮）**

这是更容易被忽略的问题。B 如果变慢或者挂了，A 的线程会阻塞在等 B 的响应上，线程池被占满，A 自己也跟着挂，然后 A 的上游也挂……这就是**雪崩**。

A 端的保护手段主要有三个：

**超时（Timeout）。** 最基本的。调 B 的时候设一个超时时间，比如 500ms 没响应就放弃。不设超时，线程会一直卡着，这是雪崩的最常见起因。

**熔断（Circuit Breaker）。** 思路类似家里的保险丝。A 记录调 B 的失败率，当失败率超过阈值（比如连续 10 次有 5 次失败），A 直接**不再调 B**，立刻返回错误或兜底数据。过一段时间后放几个请求试探，如果 B 恢复了就恢复调用。熔断器有三个状态：

关闭（正常调用）→ 失败率超标 → 打开（直接拒绝，不调B）→ 等一段时间 → 半开（放少量请求试探）→ 试探成功 → 回到关闭。

Hystrix、Sentinel、Resilience4j 都能做熔断。

**隔离（Isolation）。** A 可能调 B、C、D 三个服务。如果调 B 的线程和调 C 的线程共享同一个线程池，B 挂了会把线程池占满，连 C 也调不了。解决办法是给每个下游服务分配**独立的线程池或信号量**，B 出问题只影响调 B 的那个池子，不波及其他服务。这叫舱壁模式（Bulkhead），像船的水密隔舱一样，一个舱进水不会沉整条船。

------

**总结一下：**

保护 B（被调方）：**限流 + 降级**——控制进来的量，扛不住就简化处理。

保护 A（调用方）：**超时 + 熔断 + 隔离**——别被下游拖死，下游出问题就快速失败，而且把影响范围隔开。

两端都要做，缺一不可。只保护 B 不保护 A，B 虽然没挂但响应变慢，A 的线程还是会被耗尽。只保护 A 不保护 B，A 是安全了但 B 可能被打垮。

# 对比一下jdk和cglib的动态代理

JDK 动态代理也会生成新类，也有可能导致元空间溢出，只是机制不同。

------

**JDK 动态代理**

基于**接口**。运行时生成一个实现了目标接口的代理类，类名长这样：`$Proxy0`、`$Proxy1`。底层是 `java.lang.reflect.Proxy`，通过拼接字节码生成新类，然后用反射调用 InvocationHandler 的 invoke 方法。

```java
UserService proxy = (UserService) Proxy.newProxyInstance(
    classLoader,
    new Class[]{UserService.class},  // 必须传接口
    invocationHandler
);
```

限制很明确：**目标类必须实现接口**，代理的是接口方法，没有接口就用不了。

**CGLIB 动态代理**

基于**继承**。运行时通过 ASM 字节码框架生成目标类的子类，重写父类的方法来插入代理逻辑。类名长这样：`UserService$$EnhancerByCGLIB$$a1b2c3d4`。

```java
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);  // 直接传类，不需要接口
enhancer.setCallback(methodInterceptor);
UserService proxy = (UserService) enhancer.create();
```

不需要接口，但因为是继承，**final 类和 final 方法无法代理**。

------

**关于元空间溢出**

两者都会生成新类，都有可能导致元空间溢出。但实际中 **CGLIB 更容易出问题**，原因是：

JDK 代理有内置缓存，相同接口组合只会生成一次代理类，`Proxy.newProxyInstance` 内部会先查缓存，命中就复用。所以正常使用很难生成大量不同的代理类。

CGLIB 的缓存机制依赖 Enhancer 实例的配置，如果每次都 new 一个新的 Enhancer 并且配置有细微差异（比如不同的 Callback），就会被当成不同的代理需求，生成不同的类。而且 CGLIB 生成的类比 JDK 代理的类**更大**（包含父类方法的重写、FastClass 索引等），单个类占用的元空间更多。

------

**性能对比**

JDK 代理的 invoke 走的是**反射调用**，每次方法调用都要通过 Method.invoke()，有反射开销。

CGLIB 用的是 **FastClass 机制**，生成代理类的同时还生成了一个 FastClass，通过方法索引直接调用，避免了反射，所以方法调用本身比 JDK 代理快。

不过 JDK 高版本对反射做了很多优化（比如生成 MethodAccessor 字节码），差距已经很小了。**创建代理对象的速度则是 JDK 更快**，因为 CGLIB 要生成子类 + FastClass，字节码生成本身比较重。

------

**Spring 怎么选的**

Spring Boot 2.x 开始默认使用 **CGLIB**，不管目标类有没有实现接口。原因是统一行为——用 JDK 代理时注入的类型必须是接口，用 CGLIB 注入的可以是具体类，很多开发者踩过"注入具体类报错"的坑，所以 Spring 干脆默认 CGLIB 省事。

如果你想强制用 JDK 代理，可以配置 `spring.aop.proxy-target-class=false`。

------

**总结**

|              | JDK 动态代理    | CGLIB                  |
| ------------ | --------------- | ---------------------- |
| 基于         | 接口            | 继承                   |
| 限制         | 必须有接口      | 不能代理 final 类/方法 |
| 生成类大小   | 小              | 大（含 FastClass）     |
| 方法调用     | 反射            | FastClass 直接调用     |
| 创建代理速度 | 快              | 慢                     |
| 元空间风险   | 低（缓存好）    | 较高                   |
| Spring 默认  | Spring MVC 时代 | Spring Boot 2.x 起     |



# Netty 相关



