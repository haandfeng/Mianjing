---
title: JVM内存与GC
type: topic
updated: 2026-05-04
---

# JVM内存与GC

> 堆按代分（Eden / Survivor / Old）；分代收集 = 年轻代复制 + 老年代标记整理；GC Roots + 可达性分析判活；OOM 排查 = 堆 dump + MAT。

> ⚠️ TODO：[[后端技术专栏/JVM]] 文件为空，本页内容来自面试真题，待补充正式专栏。

## 高频问法
- "GC 是怎么回收对象的？什么时候触发 Full GC？" — [[快手/支付方向/我的快手支付一面]]、[[字节-今日头条-财经业务/我的字节一面]]
- "JVM 内存区域 / 运行时数据区" — [[快手/支付方向/我的快手支付一面]]
- "JVM 启动参数（-Xmx / -Xss / GC 选择）" — [[蚂蚁/蚂蚁一面]]
- "OOM 怎么排查？什么场景会发生" — [[蚂蚁/蚂蚁一面]]、[[京东/京东零售一面]]
- "Eden / Survivor 算法选择" — [[快手/支付方向/我的快手支付一面]]
- "Java 应用提升并发吞吐量从哪几个层面" — [[京东/京东零售一面]]
- "引用类型（强软弱虚）区别" — [[快手/支付方向/我的快手支付一面]]
- "类加载机制（JVM 除了字节码解释还能做什么）" — [[快手/支付方向/我的快手支付一面]]、[[面经较少公司/银河智学]]

## 答题骨架

### 1. 运行时数据区
| 区域 | 线程 | 作用 |
|---|---|---|
| 程序计数器 | 私有 | 记录当前字节码地址 |
| 虚拟机栈 | 私有 | 方法调用栈帧（局部变量、操作数栈、动态链接） |
| 本地方法栈 | 私有 | Native 方法 |
| 堆 | 共享 | 对象 / 数组 |
| 方法区 / 元空间 | 共享 | 类元数据、常量、静态变量、JIT 缓存 |
| 直接内存 | 共享 | NIO 堆外内存 |

### 2. 堆分代结构
```
Young Gen          Old Gen
┌────────┐ ┌──┬──┐ ┌────────┐
│  Eden  │ │S0│S1│ │  Tenured│
└────────┘ └──┴──┘ └────────┘
```
- 对象优先在 Eden 分配；Eden 满 → Minor GC
- 复制算法：存活对象 Eden → Survivor；Survivor 不够 → 直接进 Old
- 在 Survivor 每熬过一次 Minor GC 年龄 +1，达到阈值（默认 15）→ 晋升 Old
- 大对象直接进 Old；动态年龄判断（Survivor 同年龄对象超 50% → 直接晋升）

### 3. 主流 GC 算法
- **可达性分析**（GC Roots：栈引用、静态变量、常量、JNI 引用 等）→ 判活
- **复制算法**：Eden → Survivor，没碎片但浪费一半空间，年轻代用
- **标记 - 清除**：会有碎片
- **标记 - 整理**：标记后压缩，老年代用
- **分代收集**：年轻代复制，老年代标记 - 整理 / 标记 - 清除

### 4. 常见 GC 收集器
| 收集器 | 适用 | 特点 |
|---|---|---|
| Serial | 客户端、小堆 | 单线程，STW |
| Parallel Scavenge / Old | 高吞吐 | 多线程并行，关注吞吐 |
| CMS（已废弃） | 老年代低延迟 | 并发标记 + 并发清除，碎片多 |
| G1 | 大堆默认 | 分 Region，可预测停顿 |
| ZGC / Shenandoah | 超大堆 + 超低延迟 | 染色指针、并发整理，<10ms |

### 5. 引用类型
- **强**：普通赋值，永不被回收
- **软（SoftReference）**：内存不够时回收，做缓存
- **弱（WeakReference）**：下次 GC 必回收，ThreadLocalMap key 用
- **虚（PhantomReference）**：必须配 ReferenceQueue，对象回收前通知，可用于堆外内存清理

### 6. JVM 启动参数清单
- `-Xms` / `-Xmx`：堆初始 / 最大
- `-Xss`：单线程栈大小
- `-XX:MetaspaceSize` / `-XX:MaxMetaspaceSize`：元空间
- `-XX:+UseG1GC` / `-XX:MaxGCPauseMillis=200`
- `-XX:+PrintGCDetails -Xloggc:/path/gc.log`
- `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=...`：OOM 时自动 dump 堆

### 7. OOM 排查流程
1. **看错误**：`Java heap space` / `Metaspace` / `Direct buffer memory` / `unable to create new native thread` / `GC overhead limit`
2. **拿堆 dump**（启动参数自动 dump，或运行时 `jmap -dump`）
3. **MAT / VisualVM** 分析：Dominator Tree 找大对象，看是否有 ClassLoader 泄漏、Map 无限增长、ThreadLocal 没清理等
4. **GC 日志**：用 GCViewer / GCEasy 看是否频繁 Full GC、回收不动
5. **运行时工具**：`jps` / `jstat -gc` / `jmap -histo` / `jstack` / `jconsole` / `jvisualvm`

### 8. 常见 OOM 原因
- 大集合（List / Map）无限增长 + 没清理
- 缓存（Caffeine / 自写）无 TTL 与容量上限
- ThreadLocal 长生命周期线程未 remove
- ClassLoader 泄漏（热部署、动态代理频繁生成类）
- DirectByteBuffer 没释放（Netty / NIO）
- 线程数过多

### 9. 提升 Java 并发吞吐 4 层（[[京东/京东零售一面]]）
1. **定位瓶颈**：profiler，判断 CPU / 锁 / IO / GC
2. **线程模型**：线程池分组、有界队列、超时熔断限流
3. **并发设计**：减少共享和锁竞争（分段、LongAdder、ConcurrentHashMap、避免 EventLoop 阻塞）
4. **IO / 资源**：连接池、批量、缓存、降低对象分配率减 GC

## 易错点 & 追问
- "Full GC = Old + Young + 元空间一起回收"，触发条件：老年代不足、Metaspace 不足、System.gc()、CMS 失败回退
- 复制算法不是"只用一半"，是 Eden:S0:S1 = 8:1:1，每次只用 Eden + 1 个 Survivor，浪费 10%
- 元空间用本地内存，而不是 JVM 堆
- ZGC 染色指针：把 GC 状态打到指针上而非对象头

## 深入阅读
- 原始专栏 [[后端技术专栏/JVM]]（// 待补全 stub，文件为空）
- 真题来源 [[快手/支付方向/我的快手支付一面]]、[[字节-今日头条-财经业务/我的字节一面]]、[[蚂蚁/蚂蚁一面]]、[[京东/京东零售一面]]、[[面经较少公司/银河智学]]
