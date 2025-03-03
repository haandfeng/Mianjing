更多面经请查看https://github.com/haandfeng/Mianjing 以后会陆续更新和完善，我会持续引用之前面经的内容，也会根据自己面的公司看之前的面经，然后写上答案。如果大家觉得有用请多多关注，点赞收藏star🥺🥺🥺
这些都是我基于gpt+小林+javaguide+其他杂七杂八的来源+自己思考的答案。欢迎大家来讨论

明天二面攒人品
面试公司：小鹅通

面试岗位：后端开发

# 有没有了解过PHP和Go
11

# 问Redis实现验证码Token验证中间发生的事
看这个代码吧，问gpt就好
```java
@Override
public Result login(LoginFormDTO loginForm, HttpSession session) {
    // 1.校验手机号
    String phone = loginForm.getPhone();
    if (RegexUtils.isPhoneInvalid(phone)) {
        // 2.如果不符合，返回错误信息
        return Result.fail("手机号格式错误！");
    }
    // 3.从redis获取验证码并校验
    String cacheCode = stringRedisTemplate.opsForValue().get(LOGIN_CODE_KEY + phone);
    String code = loginForm.getCode();
    if (cacheCode == null || !cacheCode.equals(code)) {
        // 不一致，报错
        return Result.fail("验证码错误");
    }

    // 4.一致，根据手机号查询用户 select * from tb_user where phone = ?
    User user = query().eq("phone", phone).one();

    // 5.判断用户是否存在
    if (user == null) {
        // 6.不存在，创建新用户并保存
        user = createUserWithPhone(phone);
    }

    // 7.保存用户信息到 redis中
    // 7.1.随机生成token，作为登录令牌
    String token = UUID.randomUUID().toString(true);
    // 7.2.将User对象转为HashMap存储
    UserDTO userDTO = BeanUtil.copyProperties(user, UserDTO.class);
    Map<String, Object> userMap = BeanUtil.beanToMap(userDTO, new HashMap<>(),
            CopyOptions.create()
                    .setIgnoreNullValue(true)
                    .setFieldValueEditor((fieldName, fieldValue) -> fieldValue.toString()));
    // 7.3.存储
    String tokenKey = LOGIN_USER_KEY + token;
    stringRedisTemplate.opsForHash().putAll(tokenKey, userMap);
    // 7.4.设置token有效期
    stringRedisTemplate.expire(tokenKey, LOGIN_USER_TTL, TimeUnit.MINUTES);

    // 8.返回token
    return Result.ok(token);
}
```

# 为什么要做RPC框架，出于什么目的
硬编，我主要说到一个java程序和python程序之间的交互


# 主要用什么数据库
Mysql


# Sql语法考察
你们也会有各种各样的一个考试吗？假设现在有这么一张表叫学生成绩表里面包含三主要的三个字段，你可以理解第一个学生ID字段，第二个是学生的科目，第三个是学生的分数。

现在我要找出所有的张三的学习，他最高的科目是哪一个，Sql怎么写，

**方法1：使用 ORDER BY 和 LIMIT**
```sql
SELECT subject
FROM student_scores
WHERE student_id = '张三'
ORDER BY score DESC
LIMIT 1;
```


**方法2：使用子查询查找最大分数**

```sql
SELECT subject
FROM student_scores
WHERE student_id = '张三'
  AND score = (SELECT MAX(score)
               FROM student_scores
               WHERE student_id = '张三');
```

# 假设我现在要从所有学生当中找出学生的有至少两门科目大于90大于等于90分的学生ID，这个时候怎么写？

```sql
SELECT student_id
FROM student_scores
WHERE score >= 90
GROUP BY student_id
HAVING COUNT(subject) >= 2;
```


# 对于单例模式，你是怎么理解他的
**单例模式**（Singleton Pattern），它确保 **某个类在整个程序运行期间** 只有 **一个实例**，并提供一个全局访问点来获取该实例。

**为什么要使用单例模式？**
1. **节省资源 & 提高性能**
	• 适用于数据库连接、日志记录、线程池等 **高消耗对象**，避免不必要的重复创建。
2. **确保全局唯一性**
	• 确保在整个程序运行期间，某个类只有 **一个实例**，防止数据不一致问题。
3. **方便管理 & 线程安全**
	• 全局只有 **一个实例**，避免多个实例导致的数据冲突。
推荐构造方法
• **线程安全**（类加载机制保证只初始化一次）
• **懒加载**（Holder.INSTANCE 只有在 getInstance() 被调用时才会初始化）
```java
public class Singleton {
    private Singleton() {}
    private static class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }
    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```
# 关于数据库，你是怎么理解数据库引擎的
数据库引擎在数据库系统中主要负责以下功能：
1. **数据存储与管理** → 负责数据的**存储方式**、**文件组织**、**数据访问**等。
2. **事务处理（ACID）** → 确保数据库操作的**原子性（Atomicity）**、**一致性（Consistency）**、**隔离性（Isolation）** 和 **持久性（Durability）**。
3. **索引和查询优化** → 提高数据的检索速度，**优化 SQL 执行**。
4. **并发控制和锁机制** → 处理**多用户并发访问**，避免数据冲突。
5. **日志与恢复机制** → 记录**事务日志**，在数据库崩溃时提供恢复能力。
**1. InnoDB（默认 & 最常用）**
✅ **支持事务（ACID）**，强一致性，支持**行级锁**。
✅ **支持外键**，保证数据完整性。
✅ **支持 MVCC（多版本并发控制）**，提升查询效率。
✅ **采用 B+ 树索引**，查询性能优越。
**适用场景**：
• 高并发读写（**OLTP 事务型**），如**银行系统、电商订单、支付系统**。

**2. MyISAM（适用于读密集型场景）**
✅ **查询速度快**（适合**读操作**多的场景）。
✅ **支持表级锁，不支持事务**。
✅ **不支持外键**，数据一致性由应用层保证。
✅ **存储格式简单，占用空间小**。
**适用场景**：
• **日志系统**、**新闻网站**、**数据仓库（OLAP 分析型）**，如**大规模文本存储、搜索引擎**。

**3. Memory（适用于缓存）**  
✅ **数据存储在内存中，查询速度极快**。
✅ **适用于临时数据（重启丢失数据）**。
✅ **不支持事务**，仅适合存储临时数据。
**适用场景**：
• **高速缓存**（如 Redis 替代方案）。
• **会话数据存储**（如 Web Session ）。

 **4. Archive（适用于日志存储）**
✅ **存储空间占用小，适合归档数据**。
✅ **不支持索引（只能支持 PRIMARY KEY）**。
✅ **只支持 INSERT 和 SELECT（不支持 DELETE 和 UPDATE）**。
**适用场景**：
• **日志存储**、**历史数据归档**（如银行流水、监控日志）。
# Mysql的主从同步原理了解过吗
没有。。
[小林coding有讲](https://xiaolincoding.com/interview/mysql.html#mysql%E4%B8%BB%E4%BB%8E%E5%A4%8D%E5%88%B6%E4%BA%86%E8%A7%A3%E5%90%97)
# 场景题
可能我是在大四的时候，我想查一下，我张三这个人这4年以来，他的以前考的比如说线性代数，因为当时他的科目分数多少，想做这么一个查询，比如说我在在我自己的学生的教务系统，他做了这么一个工具，想查出他的张三这个人线性代数他的科目分数是多少，针对于这么一个使用场景，你的那张表的所以会怎么去创建？怎么创建索引，加那些索引，实际搜的场景就是学生的ID加学生的科目

由于 **查询模式是按 student_id + subject 查询**，我们应该创建**联合索引**：
```sql
CREATE INDEX idx_student_subject ON student_scores (student_id, subject);
```

**覆盖索引**
如果查询中 **只需要 subject, score, exam_date 这些字段**，可以 **直接创建覆盖索引**，提高查询效率：
```sql
CREATE INDEX idx_cover_student_subject ON student_scores (student_id, subject, exam_date, score);
```


# 你这里后面秒杀描述的优化了秒杀的业务流程，平均耗时从400毫秒降低到100毫秒，主要是哪一块降低了300秒毫秒的延时，

黑马，使用消息队列，异步创建订单，使用redis判断库存和一人一单
然后异步线程在后台操作数据库，创建订单


# 会不会导致一个问题，比如说我下单之后我看不到自己的订单了？
消息队列的ack机制确保了每个订单都会被处理到

# 比如说一些大平台，它有会出现一些什么我订单，比如说下单之后订单看不到，还要过很久的时间看到了一些情况

**Redis 先存“订单占位”，避免用户误以为失败**  
**思路：**
• **下单成功后，先在 Redis 记录订单占位**（orderId = “处理中”）。
• **用户查询订单时，先查 Redis，如果有订单则返回“正在处理”**。
• **等数据库落盘后，用户再次查询，就能查到订单信息**。
1. **先查 Redis**
	• 如果订单状态是 "pending"，告诉用户“订单处理中”。
2. **如果 Redis 没有订单，再查数据库**
	• 如果数据库有订单，返回订单信息。
	• 如果数据库也没有，说明订单失败。
# 比如说你的队列积压到那里了，你咋办

当**消息队列（MQ）积压**时，意味着**消费者消费速度跟不上生产者的生产速度**
  
从 **生产者（限流）、消费者（扩容）、队列优化（降级 & 死信队列）** 角度入手，找到合适的方案。
**1. 限流（生产者限流，减少消息堆积）**
**📌 问题：**
	• 如果生产者**无限制发送消息**，但消费者处理能力有限，队列很快会**积压消息**，导致高延迟甚至系统崩溃。
**📌 解决方案：**
	✅ **生产端限流**，使用 **令牌桶 / 漏桶算法** 控制请求速率。
	✅ **削峰填谷**，高峰期**限流 & 拒绝低优先级请求**。
📌 **示例：使用 RateLimiter（限流生产者发送消息速度）**
```java
RateLimiter rateLimiter = RateLimiter.create(1000); // 每秒最多 1000 个请求
public void sendMessage(String message) {
    if (rateLimiter.tryAcquire()) { 
        rabbitTemplate.convertAndSend("exchange", "queue", message);
    } else {
        log.warn("生产者限流，消息被丢弃！");
    }
}
```
**令牌桶（Token Bucket）** 是一种 **流量控制（Rate Limiting）** 算法，它用于 **限制系统的请求速率**，防止流量突增导致系统崩溃。
它的核心思想是：
1. **以固定速率向“桶”中添加令牌**（比如每秒 100 个令牌）。
2. **请求到来时，必须消耗令牌才能被处理**。
3. **如果桶里没有令牌，请求被丢弃或延迟**。


**2. 扩容（消费者扩容，提高消费速度）**
**📌 问题：**
	• 消费者消费不过来，导致队列积压。
**📌 解决方案：**
✅ **增加消费者数量（水平扩展）**
	• 让多个消费者**并发消费**，减少单个消费者的压力。
📌 **示例：RabbitMQ 增加并发消费者**

```java
@RabbitListener(queues = "order.queue", concurrency = "10") // 增加并发消费者数量
public void processOrder(Message message) {
    // 处理订单逻辑
}
```

✅ **优化消费者逻辑（减少处理时间）**
	• **异步处理**（比如先存入数据库，再异步计算）。
	• **批量消费**，例如一次处理 10 条消息，而不是逐条消费。
📌 **示例：批量消费 Kafka 消息**
```java
@KafkaListener(topics = "order_topic", groupId = "order_group", batch = "true")
public void processOrders(List<ConsumerRecord<String, String>> records) {
    records.forEach(record -> {
        processOrder(record.value()); // 批量处理
    });
}
```

**3. 降级（丢弃 & 降低优先级）**
**📌 问题：**

• 如果队列堆积严重，可能导致**核心业务受影响**，甚至导致系统崩溃。
**📌 解决方案：**
	✅ **丢弃低优先级消息**（比如**非核心日志、统计数据**）。
	✅ **延迟处理低优先级任务**，如**非核心业务进入延迟队列**。
📌 **示例：RabbitMQ 使用 TTL 让低优先级消息自动过期**

```java
MessageProperties properties = new MessageProperties();
properties.setExpiration("60000"); // 60秒后过期丢弃
Message message = new Message(msgContent.getBytes(), properties);
rabbitTemplate.convertAndSend("queue", message);
```

**✅ 作用：**
• **避免低优先级任务占满队列**
• **优先保证核心业务（订单、支付等）执行**


**🔥 总结**

| **优化方向**  | **方法**            | **效果**          |
| --------- | ----------------- | --------------- |
| **生产者限流** | 令牌桶算法、RateLimiter | **削峰填谷，防止流量过载** |
| **消费者扩容** | 增加消费者并发数、批量消费     | **提升消费速度**      |
| **消息降级**  | 丢弃低优先级消息、延迟消费     | **优先保证核心业务**    |

# 你想来小鹅通希望获取到什么，能给公司带来什么激励

自己编

# 你是什么性格
他们喜欢e人，喜欢喜欢沟通的人


# 介绍工作内容