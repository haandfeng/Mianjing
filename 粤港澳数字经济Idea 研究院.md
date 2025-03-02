
#### 对实习内容的询问
其实主要还是关注sql的优化方面

还有怎么用正则表达式处理数据（感觉是他们这种ai企业对数据处理比较关注）

#### 场景题1，解决效率和线程安全问题
考察的主要是java并发编程，异步的问题，不算很会。
```java
import java.util.Map;  
import java.util.concurrent.ConcurrentHashMap;  
  
public class Memoizer<A, V> implements Computable<A, V> {  
    private final Map<A, V> cache = new ConcurrentHashMap<A, V>();  
    private final Computable<A, V> c;  
  
    public Memoizer(Computable<A, V> c) {  
        this.c = c;  
    }  
  
    @Override  
    public V compute(A arg) throws InterruptedException {  
        V result = cache.get(arg);  
        {if (result == null) {  
            result = c.compute(arg);  // 耗时操作  
            cache.put(arg, result);  
        }}  
        return result;  
    }  
}
```

当前代码中，多个线程可能同时检测到 cache.get(arg) == null，然后多个线程都去执行 c.compute(arg) 这个耗时操作，最后只有一个线程的结果会被 cache.put(arg, result)，但多个线程仍然进行了冗余计算，浪费了资源。
**使用原子操作**：利用 ConcurrentHashMap 提供的原子方法（如 putIfAbsent 或 Java 8 的 computeIfAbsent）将“检查-更新”合并为原子步骤，避免并发竞态
```java
private final ConcurrentHashMap<A, V> cache = new ConcurrentHashMap<>();
public V compute(A arg) throws Exception {
    // 当键不存在时，原子地计算并放入缓存
    return cache.computeIfAbsent(arg, key -> {
        try {
            return c.compute(key);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);  // 将受检异常转换处理
        }
    });
}
```


**使用 FutureTask 防止重复计算**：将缓存的值由计算结果替换为表示计算过程的 Future。第一次计算时，由线程创建一个 FutureTask 执行实际计算，并将其 **立即** 放入缓存。其他线程发现缓存中已有对应的 Future，就直接通过 Future.get() 等待结果，而不重复执行计算
```java
public class Memoizer<A, V> implements Computable<A, V> {
    private final ConcurrentHashMap<A, Future<V>> cache = new ConcurrentHashMap<>();
    private final Computable<A, V> c;  // 实际计算逻辑接口

    public V compute(final A arg) throws InterruptedException {
        Future<V> f = cache.get(arg);
        if (f == null) {
            // 创建计算任务（Callable封装实际计算）
            Callable<V> eval = () -> c.compute(arg);
            FutureTask<V> ft = new FutureTask<>(eval);
            // 原子地将任务放入缓存，如果返回null表示成功放入
            Future<V> prior = cache.putIfAbsent(arg, ft);
            if (prior == null) {    
                f = ft;
                ft.run();           // 启动计算
            } else {
                f = prior;          // 有其他线程抢先放入，则复用已有任务
            }
        }
        try {
            // 等待任务执行结果（避免重复计算）
            return f.get();
        } catch (ExecutionException e) {
            throw new RuntimeException(e.getCause());
        }
    }
}
```

#### 讲讲Spring的IoC，优点是什么
- ﻿IoC容器(Inversion of Control)：Spring通过控制反转实现了对象的创建和对象间的依赖关系管理。开发者只需要定义好Bean 及其依赖关系，Spring容器负责创建和组装这些对象

Spring loC和AOP 区别：
- ﻿IoC：即控制反转的意思，它是一种创建和获取对象的技术思想，依赖注入（DI）是实现这种技术的一种方式。传统开发过程中，我们需要通过new关键字来创建对象。使用IoC思想开发方式的话，我们不通过new关键字创建对象，而是通过IoC容器来帮我们实例化对象。通过IoC的方式，可以大大降低对象之间的耦合度。


将对象之间的相互依赖关系交给 IoC 容器来管理，并由 IoC 容器完成对象的注入。这样可以很大程度上简化应用的开发，把应用从复杂的依赖关系中解放出来。 IoC 容器就像是一个工厂一样，当我们需要创建一个对象的时候，只需要配置好配置文件/注解即可，完全不用考虑对象是如何被创建出来的。


#### Spring IoC的底层实现是怎么样的
==没有特别仔细的研究==
底层是：Map的数据结构
- ﻿﻿反射：Spring IOC容器利用Java的反射机制动态地加载类、创建对象实例及调用对象方法，反射允许在运行时检查类、方法、属性等信息，从而实现灵活的对象实例化和管理。
- ﻿﻿依赖注入：IOC的核心概念是依赖注入，即容器负责管理应用程序组件之间的依赖关系。Spring通过构造函数注入、属性注入或方法注入，将组件之间的依赖关系描述在配置文件中或使用注解。
- ﻿﻿设计模式- 工厂模式：SpringIOC容器通常采用工厂模式来管理对象的创建和生命周期。容器作为工厂负责实例化Bean并管理它们的生命周期，将Bean的实例化过程交给容器来管理。
- ﻿﻿容器实现：Spring IOC容器是实现IOC的核心，通常使用BeanFactory或ApplicationContext来管理Bean。BeanFactory是IOC容器的基本形式，提供基本的IOC功能；ApplicationContext是BeanFactory的扩展，并提供更多企业级功能。
- **Spring IoC 的底层实现流程**

1. **解析 BeanDefinition**（解析 XML、注解、Java 配置）
2. **存储到 BeanDefinitionMap**（ConcurrentHashMap）
3. **获取 Bean 时，先查缓存**（singletonObjects）
4. **如果没有，实例化 Bean**
5. **依赖注入（@Autowired）**
6. **执行 AOP 代理增强**
7. **执行 BeanPostProcessor**
8. **管理生命周期（@PostConstruct、@PreDestroy）**

#### 详细介绍一下我项目里的JDK动态代理+工厂模式
我的代码
```java
public static <T> T getProxy(Class<T> serviceClass) {  
    if (RpcApplication.getRpcConfig().isMock()) {  
        return getMockProxy(serviceClass);  
    }  
  
    return (T) Proxy.newProxyInstance(  
            serviceClass.getClassLoader(),// 类加载器  
            new Class[]{serviceClass},  // 代理的接口
            new ServiceProxy());   // 代理逻辑
}
```
JDK 动态代理的核心是 Proxy.newProxyInstance()，它会**在运行时生成一个代理类**，这个代理类会实现 serviceClass 接口，并在调用方法时转发到 InvocationHandler 进行处理。

• JDK 动态代理 **只能代理接口（Interface）**，如果目标类没有实现接口，无法使用 JDK 代理（可以使用 CGLIB 代理）。
• **代理对象不会直接调用目标对象的方法，而是通过 InvocationHandler 进行方法增强**。

1. **代理类在运行时生成**（Proxy 生成字节码，动态创建类）。
2. **代理类实现了目标接口**（所以只能代理**接口**）。
3. **方法调用时，会调用 InvocationHandler.invoke()**，然后**通过反射**调用目标对象的方法。
4. **生成的代理类名字类似 $Proxy0**

**示例：创建一个 UserService 接口及其动态代理**

**目标**：拦截 UserService 的方法调用，并在执行方法前后打印日志。
**Step 1: 定义一个接口**
```java
public interface UserService {
    void addUser(String name);
}
```

**Step 2: 实现接口**
```java
public class UserServiceImpl implements UserService {
    @Override
    public void addUser(String name) {
        System.out.println("正在添加用户：" + name);
    }
}
```

**Step 3: 创建 InvocationHandler 处理器**
InvocationHandler 负责**拦截方法调用**，并增强逻辑：
```java
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;

public class UserServiceInvocationHandler implements InvocationHandler {
    private final Object target; // 被代理的对象

    public UserServiceInvocationHandler(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("日志：调用 " + method.getName() + " 方法，参数：" + args[0]);
        Object result = method.invoke(target, args); // 调用目标方法
        System.out.println("日志：方法 " + method.getName() + " 执行完毕");
        return result;
    }
}
```

**Step 4: 使用 Proxy 生成动态代理**
```java
import java.lang.reflect.Proxy;

public class Main {
    public static void main(String[] args) {
        // 1. 创建目标对象
        UserService userService = new UserServiceImpl();

        // 2. 创建 InvocationHandler 代理逻辑
        UserServiceInvocationHandler handler = new UserServiceInvocationHandler(userService);

        // 3. 创建代理对象
        UserService proxyInstance = (UserService) Proxy.newProxyInstance(
            userService.getClass().getClassLoader(),  // 类加载器
            new Class[]{UserService.class},           // 代理的接口
            handler                                   // 代理逻辑
        );

        // 4. 调用代理方法
        proxyInstance.addUser("Alice");
    }
}
```



#### 针对上千万用户这种类型的查询，如何发现有问题的查询语句，如有优化这些查询语句

##### 1.发现有问题的语句
建议看[黑马mysqlP75-78](<【黑马程序员 MySQL数据库入门到精通，从mysql安装到mysql高级、mysql优化全囊括】https://www.bilibili.com/video/BV1Kr4y1i7ru?p=75&vd_source=f2a07ad9f0a74c5a938b94aa1877394b>)比较详细
 **1.1 使用 SQL 执行日志分析慢查询**
 
 **1.2 使用 EXPLAIN 分析查询执行计划**
 现索引未命中、全表扫描、排序等性能问题
• type = ALL → **全表扫描（非常慢）**
• possible_keys = NULL → **没有使用索引**
• rows → **扫描的行数，过大会影响查询速度**
• Extra → **是否出现 “Using filesort”、“Using temporary”（性能差的标志）**

**使用 SHOW PROFILE 分析 SQL 执行性能**
可以分析哪个操作比较耗时，比较占用cpu
• **关注 CPU / I/O 开销**
• **“Sending data” 高 → 可能是未优化的查询**
• **“Creating sort index” → 可能是 ORDER BY 未优化**


##### **2. 如何优化 SQL 查询**

 **2.1 索引优化**
• **主键 / 唯一索引**：针对 WHERE 条件中的 **主键（id）** 进行查询
• **普通索引**：针对高频查询字段创建索引，例如 email
• **覆盖索引**：让查询的字段全部在索引中，避免 SELECT \*（减少回表查询）

**避免索引失效**->见[[广州兴业#Mysql 索引失效的场景]]

**2.2 SQL 语句优化**
使用 EXISTS 替代 IN

**IN** 用于检查左边的表达式是否存在于右边的列表或子查询的结果集中。如果存在，则IN返回TRUE否则返回 FALSE
```sql
SELECT column_name (s)
FROM table_name
WHERE column_name IN (valuel, valuez, ...);
```

**EXISTS** 用于判断子查询是否至少能返回一行数据。它不关心子查询返回什么数据，只关心是否有结果。如果子查询有结果，则 EXISTS 返回 TRUE，否则返回 FALSE。
```sql
SELECT column_name (s)
FROM table_name
WHERE EXISTS (SELECT column_name FROM another_table WHERE condition);
```

- ﻿﻿性能差异：在很多情况下，EXISTS 的性能优于 IN，特别是当子查询的表很大时。这是因为EXISTS一旦找到匹配项就会立即停止查询，而 IN 可能会扫描整个子查询结果集。
- ﻿使用场景：如果子查询结果集较小且不频繁变动，IN 可能更直观易懂。而当子查询涉及外部查询的每一行判断，并且子查询的效率较高时，EXISTS 更为合适。
- ﻿﻿NULL值处理：IN 能够正确处理子查询中包含NULL值的情况，而 EXISTS不受子查询结果中NULL值的影响，因为它关注的是行的存在性，而不是具体值。

 **2.3 数据库架构优化**

**垂直拆分**
• **拆分大表，避免单表数据量过大**
• 例如 users 表拆分：
• users_basic (id, name, email)
• users_profile (id, address, age)

**水平分库分表**
• **按 user_id 取模分库**
• **按时间范围分表**（如 users_202401, users_202402）

**2.4 缓存优化**
**Redis 预加载热门查询**



#### 优化这个sql语句
```sql
SELECT * FROM USER AS A 
INNER JOIN 
USER_INFO AS B 
ON A.ID=B.USER_ID 
WHERE A.GENDER=1 AND B.TIMESTAMP>1605078745 AND B.SCORE=16798416
```

**JOIN 的效率问题**
	• INNER JOIN 需要匹配 USER.ID = USER_INFO.USER_ID，如果 USER.ID 和 USER_INFO.USER_ID 没有索引，查询效率会很低。
	• 直接 JOIN **大表 USER_INFO**，导致 MySQL 需要扫描 USER_INFO 的所有行后再进行过滤，开销大。
	• **WHERE 过滤条件较多**（B.TIMESTAMP > 1605078745 AND B.SCORE = 16798416），但过滤是在 JOIN 之后发生的，造成不必要的计算。
优化：
```sql
EXPLAIN SELECT A.ID, A.NAME, A.GENDER, B.TIMESTAMP, B.SCORE 
FROM USER A
INNER JOIN (
    SELECT USER_ID, TIMESTAMP, SCORE 
    FROM USER_INFO 
    WHERE TIMESTAMP > 1605078745 
    AND SCORE = 16798416
) B 
ON A.ID = B.USER_ID 
WHERE A.GENDER = 1;
```

**WHERE 条件可能导致索引失效**
	• 不建议针对性别字段加索引。实际上与索引创建规则之一区分度有关，性别字段假设有100w数据，50w男、50w女，区别度几乎等于。
	• 联合索引中，出现范围查询(>,<)，范围查询右侧的列索引失效。
		• B.TIMESTAMP > 1605078745 是范围查询，可能无法利用索引高效查询。(使用覆盖索引/联合索引的位置)
		• B.SCORE = 16798416 需要检查索引是否有效。
优化
```sql
-- 为 USER 表添加索引
CREATE INDEX idx_user_gender ON USER (GENDER);
CREATE INDEX idx_user_id ON USER (ID);  -- 主键索引通常已存在

-- 为 USER_INFO 表添加索引
CREATE INDEX idx_user_info_userid ON USER_INFO (USER_ID);
CREATE INDEX idx_user_info_timestamp ON USER_INFO (TIMESTAMP);
CREATE INDEX idx_user_info_score ON USER_INFO (SCORE);

-- TIMESTAMP 和 SCORE 组合索引 可能更优：
-- 因为 SCORE=16798416 是等值查询，放在索引的前面，TIMESTAMP > 1605078745 是范围查询，MySQL 能利用索引进行高效查询。
CREATE INDEX idx_user_info_score_timestamp ON USER_INFO (SCORE, TIMESTAMP);

```

**返回 SELECT * 可能导致性能下降**
	• SELECT * 返回所有字段，可能导致查询读取过多无关数据，影响性能。
	**避免 SELECT \*，只查询必要字段**

优化：
```sql
SELECT A.ID, A.NAME, A.GENDER, B.TIMESTAMP, B.SCORE 
FROM USER AS A 
INNER JOIN USER_INFO AS B 
ON A.ID = B.USER_ID 
WHERE A.GENDER = 1 
AND B.TIMESTAMP > 1605078745 
AND B.SCORE = 16798416;
```





#### 场景题2，设计架构，这个系统有一个API，可以返回当前用户所有关注的用户的动态，然后支持对所有的一些动态，按照时间的顺序做一个聚合和分页。

和黑马点评的关注消息推送类似，把推，拉，推拉结合说一下

**拉模式**：也叫做读扩散

该模式的核心含义就是：当张三和李四和王五发了消息后，都会保存在自己的邮箱中，假设赵六要读取信息，那么他会从读取他自己的收件箱，此时系统会从他关注的人群中，把他关注人的信息全部都进行拉取，然后在进行排序

优点：比较节约空间，因为赵六在读信息时，并没有重复读取，而且读取完之后可以把他的收件箱进行清楚。

缺点：比较延迟，当用户读取数据时才去关注的人里边去读取数据，假设用户关注了大量的用户，那么此时就会拉取海量的内容，对服务器压力巨大。
![[1653809450816.png]]


**推模式**：也叫做写扩散。

推模式是没有写邮箱的，当张三写了一个内容，此时会主动的把张三写的内容发送到他的粉丝收件箱中去，假设此时李四再来读取，就不用再去临时拉取了

优点：时效快，不用临时拉取

缺点：内存压力大，假设一个大V写信息，很多人关注他， 就会写很多分数据到粉丝那边去
![[1653809875208.png]]


**推拉结合模式**：也叫做读写混合，兼具推和拉两种模式的优点。

推拉模式是一个折中的方案，站在发件人这一段，如果是个普通的人，那么我们采用写扩散的方式，直接把数据写入到他的粉丝中去，因为普通的人他的粉丝关注量比较小，所以这样做没有压力，如果是大V，那么他是直接将数据先写入到一份到发件箱里边去，然后再直接写一份到活跃粉丝收件箱里边去，现在站在收件人这端来看，如果是活跃粉丝，那么大V和普通的人发的都会直接写入到自己收件箱里边来，而如果是普通的粉丝，由于他们上线不是很频繁，所以等他们上线时，再从发件箱里边去拉信息。
![[1653812346852.png]]



#### 追问，从系统的可靠性和可用性角度呢，要怎么设计
==不是很会==
**2.1 高可用架构**
**（1）服务层高可用**
• **API 网关**：
	• 采用 **Nginx+Consul** 进行负载均衡。
	• **限流**（防止恶意请求）。
	• **鉴权**（避免无效查询）。
• **微服务架构**
	• 关注消息推送、拉取、存储等**独立微服务**，可水平扩展。
	• **异步解耦**：推送服务、存储服务、查询服务通过 **Kafka** 消息队列进行解耦。
• **流量削峰**
	• **请求队列**（如 Kafka）：避免瞬间高并发导致数据库崩溃。
	• **Redis 预缓存**：活跃用户直接读取缓存。
**（2）数据存储高可用**
• **MySQL 读写分离**
	• **主库写，多个从库读**，提高查询性能。
	• 使用 **Binlog+Canal** 进行数据同步。
• **Redis 高可用**
	• **Redis Cluster（主从+分片）**，防止单点故障。
	• **持久化（RDB + AOF）**，防止数据丢失。
• **ElasticSearch 查询优化**
	• 大规模数据查询采用**分片索引**。
	• 预计算 **聚合数据**，避免实时计算压力。

**2.2 数据一致性**
**（1）保证消息不丢失**
	• **Kafka 采用 acks=all 机制**，保证消息写入**至少两个副本**。
	• **MySQL Binlog 双写**，确保数据库和缓存数据一致。
**（2）缓存一致性**
	• **写消息时，先更新数据库，再删除 Redis 缓存**
	• **拉模式采用 Cache Aside 模型**
**（3）分布式事务**
	• **使用 RocketMQ 或 Kafka 事务消息**
	• **采用 TCC（Try-Confirm-Cancel）模型**
	• **事务补偿机制**
**2.3 故障恢复 & 降级**
**（1）消息丢失恢复**
	• Kafka **配置 log.retention.hours=72**，如果 Redis 或 MySQL 崩溃，可**重新消费 Kafka** 消息进行恢复。
**（2）服务降级**
	• **大V用户大量推送**时，优先**活跃用户推送**，普通用户使用拉模式减少存储压力。
	• **流量过载时**：
		• **限流**（大V限制 1 秒最多 10 条）。
		• **降级策略**（推送失败可回落到拉模式）。
**（3）故障转移**
	• **Redis Sentinel** 监控故障自动切换主库。
	• **MySQL 双主架构**，故障自动转移。
**2.4 监控与报警**
	• **Prometheus + Grafana** 监控服务健康状态
	• **日志收集（ELK：Elasticsearch + Logstash + Kibana）**
	• **服务熔断（Hystrix）** 防止雪崩

####  算法题：很难是一个01背包变种，具体看代码

```java
/*  
1. 背景描述  
       假设你在一家AI公司负责分布式模型训练。公司需要训练一个大型神经网络模型，但由于单机资源（内存、计算能力）有限，必须将模型切分到多个计算节点上进行模型并行化训练。每个计算节点的资源如下：  
        * 内存限制：每个节点有固定的内存容量，不能加载超过其内存的模型部分。  
        * 计算速度：每个节点的计算速度不同（例如，节点A的每层计算时间是1秒，节点B是2秒）。  
       模型由多个层（如卷积层、全连接层等）组成，层之间必须按顺序执行。当相邻层被分配到不同节点时，会产生跨节点通信开销（例如数据传输时间）。  
2. 问题  
       设计一个算法，将模型的所有层分配到不同的计算节点上，满足以下条件：  
        * 内存约束：每个节点加载的层总内存不超过其容量。  
        * 最小化总训练时间：总时间由最慢节点的计算时间（所有分配到该节点的层的计算时间之和）和跨节点通信时间决定。  
3. 输入  
       model_layers: 模型各层信息列表，每层包含：  
        * layer_id（唯一标识）  
        * memory（内存占用）  
        * compute_time（单次计算时间）  
        * prev_layers（依赖的前置层列表，确保层必须按顺序执行）。  
       nodes: 计算节点列表，每个节点包含：  
        * node_id（唯一标识）  
        * memory_capacity（内存容量）  
        * compute_speed（计算速度系数，例如1.0表示基准速度，实际计算时间=单层时间/速度）。  
4. 输出  
        * 一个分配字典，键为node_id，值为该节点分配的层ID列表（按执行顺序排列）。  
        * 总训练时间的估算值。  
5. 示例  
        model_layers = [            {"layer_id": 1, "memory": 4, "compute_time": 5, "prev_layers": []},    
            {"layer_id": 2, "memory": 3, "compute_time": 3, "prev_layers": [1]},    
            {"layer_id": 3, "memory": 2, "compute_time": 4, "prev_layers": [2]},    
        ]    
        nodes = [    
            {"node_id": "A", "memory_capacity": 6, "compute_speed": 1.0},    
            {"node_id": "B", "memory_capacity": 5, "compute_speed": 0.5},    
        ]  
6. 可能的输出  
        {"A": [1, 2],  # 内存4+3=7？但节点A容量为6 → 此分配无效！需重新调整              "B": [3]    
        }  
7. 正确分配可能为  
        {"A": [1],     # 内存4 ≤6，计算时间5/1.0=5    
"B": [2, 3]   # 内存3+2=5 ≤5，计算时间3/0.5 +4/0.5=6+8=14    
}  // 总时间 = max(5, 14) + 通信开销（层1→层2跨节点，假设通信时间为2） → 14 + 2 = 16*/  
import java.util.*;  
  
class Layer {  
    String layerId;  
    int memory;  
    double computeTime;  
    List<String> prevLayers;  
  
    public Layer(String layerId, int memory, double computeTime, List<String> prevLayers) {  
        this.layerId = layerId;  
        this.memory = memory;  
        this.computeTime = computeTime;  
        this.prevLayers = prevLayers;  
    }  
}  
  
class Node {  
    String nodeId;  
    int memoryCapacity;  
    double computeSpeed;  
    int usedMemory = 0;  
    double totalComputeTime = 0;  
    List<String> layers = new ArrayList<>();  
  
    public Node(String nodeId, int memoryCapacity, double computeSpeed) {  
        this.nodeId = nodeId;  
        this.memoryCapacity = memoryCapacity;  
        this.computeSpeed = computeSpeed;  
    }  
}  
  
public class ModelParallelAllocator {  
  
    public static Map<String, List<String>> allocateLayers(  
            List<Layer> modelLayers, List<Node> nodes, double communicationCost) {  
        // 请在此填写代码，并详细注释思路  
  
        return null;  
    }  
  
    // 示例测试  
    public static void main(String[] args) {  
        List<Layer> layers = Arrays.asList(  
                new Layer("1", 4, 5, Collections.emptyList()),  
                new Layer("2", 3, 3, Collections.singletonList("1")),  
                new Layer("3", 2, 4, Collections.singletonList("2"))  
        );  
  
        List<Node> nodes = Arrays.asList(  
                new Node("A", 6, 1.0),  
                new Node("B", 5, 0.5)  
        );  
  
        Map<String, List<String>> allocation = allocateLayers(layers, nodes, 2.0);  
        System.out.println("分配结果：");  
        allocation.forEach((k, v) -> System.out.println(k + " : " + v));  
    }  
}
```