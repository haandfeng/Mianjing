# JVM 内存与垃圾回收

> 目标：把 JVM 这一块面试常考的「运行时数据区 / 对象分配 / 垃圾回收 / 收集器 / 调参 / OOM 排查」按一条主线串起来，能写在简历八股本里直接背。
> 主题文章：[[JVM内存与GC]]；真题来源：[[快手/支付方向/我的快手支付一面]]、[[字节/我的字节一面]]、[[京东/京东零售一面]]、[[蚂蚁/蚂蚁一面]]、[[其他/银河智学]]。

---

## 一、为什么要单独学 JVM

Java 跨平台的根基不是语法，而是 **JVM**：源码编译成字节码，由 JVM 解释执行 / JIT 编译，运行期间所有对象的分配、回收、类的加载都在 JVM 里完成。

JVM 主要做四件事（在 [[快手/支付方向/我的快手支付一面]] 里被问得很细）：

1. **类加载机制**：Bootstrap → Ext / Platform → App → 自定义 ClassLoader，支持热部署、Spring Boot 模块化加载。
2. **内存管理**：把进程内存分成几个区域，对象统一在堆里分配。
3. **垃圾回收**：通过 GC Roots 判活，按分代算法回收。
4. **JIT 编译**：热点方法编译成机器码，提升性能。

后面我们逐项拆开。

---

## 二、运行时数据区（5 大区域）

| 区域 | 线程 | 作用 | 异常 |
|---|---|---|---|
| 程序计数器 | 私有 | 记录当前字节码指令地址，是唯一**不会 OOM** 的区域 | — |
| 虚拟机栈 | 私有 | 每个方法对应一个栈帧（局部变量表 / 操作数栈 / 动态链接 / 返回地址） | StackOverflowError、OOM |
| 本地方法栈 | 私有 | 服务于 JNI / Native 方法；HotSpot 里和虚拟机栈合二为一 | StackOverflowError、OOM |
| 堆 | 共享 | 所有对象实例和数组的分配地，GC 主战场 | OutOfMemoryError: Java heap space |
| 方法区（元空间） | 共享 | 类元数据、运行时常量池、字符串常量池（JDK 8+ 移到堆）、JIT 编译产物 | OOM: Metaspace |
| 直接内存（堆外） | 共享 | NIO 的 DirectByteBuffer、Netty | OOM: Direct buffer memory |

- **栈帧**包括四样：局部变量表、操作数栈、动态链接、方法返回地址。每次方法调用压栈，返回时弹栈（[[快手/支付方向/我的快手支付一面]]）。
- **方法区**在 JDK 8 起改为「元空间（Metaspace）」，使用本地内存而非 JVM 堆，避免传统 PermGen 容易 OOM 的问题。
- **直接内存**严格说不属于 JVM 规范，但 NIO 的 channel + buffer 大量使用，也是 Netty 性能的来源（[[字节/我的字节一面]]）。

### 堆的分代结构

```
                Young Gen                       Old Gen
     ┌──────────────┐ ┌────┬────┐         ┌──────────────────┐
     │     Eden     │ │ S0 │ S1 │   ────► │     Tenured      │
     └──────────────┘ └────┴────┘         └──────────────────┘
              ▲             ▲                       ▲
              │             │                       │
              新对象        晋升                  老年对象 / 大对象
```

- 默认比例 `Eden : S0 : S1 = 8 : 1 : 1`，每次只用 Eden + 一个 Survivor，「浪费 10%」而不是「浪费一半」。
- 对象优先分配在 Eden；Eden 满了 → Minor GC，存活对象拷到 Survivor，年龄 +1。
- 在 Survivor 每熬过一次 Minor GC 年龄 +1，达到阈值（默认 15）→ 晋升老年代。
- **大对象**（数组、长字符串）直接进 Old，避免在 Eden 与 Survivor 之间反复复制。
- **动态年龄判断**：Survivor 中同年龄对象大小总和超过 50%，则比该年龄大的全部直接晋升。

### 对象分配（TLAB）

为了减少多线程在 Eden 上的竞争，HotSpot 默认开启 **TLAB（Thread Local Allocation Buffer）**：

- Eden 中预先给每个线程切出一小块私有缓冲。
- 分配新对象时先在 TLAB 里指针碰撞（bump-the-pointer），不需要锁。
- TLAB 满了或对象太大才回退到 Eden 共享分配（CAS）。

简历里如果被追问「你说对象在 Eden 分配，多线程会不会冲突」，可以补一句 TLAB。

---

## 三、GC Roots 与可达性分析

Java 不用引用计数（解决不了循环引用），用**可达性分析**：

> 从一组 **GC Roots** 出发，沿引用链遍历，能到达的对象存活，到不了的对象判死。

GC Roots 主要包括：

- 虚拟机栈中正在使用的局部变量、参数。
- 方法区中类的 **静态变量**。
- 方法区中常量引用（字符串常量池里的 String）。
- 本地方法栈里的 JNI 引用。
- 同步锁（synchronized）持有的对象。

> 经典追问：「为什么不用引用计数？」
> 答：A 引用 B、B 引用 A，互相计数都不为 0，但根本没人引用它们 → 永远回收不掉。可达性分析能正确判定。

---

## 四、四种引用类型

来自 [[快手/支付方向/我的快手支付一面]] 的高频题：

| 引用 | 类 | 回收时机 | 典型用途 |
|---|---|---|---|
| 强引用 | `T t = new T()` | 永不回收（除非显式置 null + 没人用） | 普通对象 |
| 软引用 | `SoftReference` | **内存不够时**回收 | 缓存（Guava 早期） |
| 弱引用 | `WeakReference` | **下次 GC 一定**回收 | `ThreadLocalMap` 的 key、防止内存泄漏 |
| 虚引用 | `PhantomReference` | 必须配 `ReferenceQueue`，对象**回收前**通知 | 堆外内存 / DirectByteBuffer 清理 |

注意点：

- ThreadLocalMap 的 Entry key 是 WeakReference 包装的，但 value 仍是强引用 → 长生命周期线程未 `remove()` 会泄漏 value。
- SoftReference 在「内存还宽裕」时就回收，会引发缓存抖动，生产环境少用。

---

## 五、垃圾回收算法

| 算法 | 思路 | 优缺点 | 适用代 |
|---|---|---|---|
| 标记 - 清除 | 标活、清死 | 有内存碎片 | 老年代候选 |
| 复制 | 把存活对象复制到另一半空间 | 没碎片，但浪费空间 | 年轻代 |
| 标记 - 整理 | 标活后压缩到一端 | 没碎片，但慢 | 老年代主力 |
| 分代收集 | 年轻代复制 + 老年代标记整理 | 兼顾吞吐和空间 | HotSpot 默认 |

为什么年轻代用复制？
- 年轻代对象**朝生夕灭**（IBM 数据 ~98% 第一次 GC 就死），存活的少 → 复制成本低。

为什么老年代用标记 - 整理 / 标记 - 清除？
- 老年代对象多、存活率高，复制不划算。

---

## 六、常见 GC 收集器

```
Serial ── ParNew ── CMS（已废弃）
   │         │         │
   ▼         ▼         ▼
Serial Old   Parallel Old   G1 ── ZGC ── Shenandoah
                                        │
                                        ▼
                                   超大堆 + 超低延迟
```

| 收集器 | 代 | 算法 | 特点 | 适用 |
|---|---|---|---|---|
| Serial | 年轻 | 复制 | 单线程、STW，小堆 | 客户端、嵌入式 |
| ParNew | 年轻 | 复制 | Serial 多线程版，配 CMS | 服务端老搭档 |
| Parallel Scavenge | 年轻 | 复制 | 关注**吞吐量**（用户/总） | 后台批处理 |
| Serial Old / Parallel Old | 老 | 标记 - 整理 | 上面两者的老年代搭档 | — |
| **CMS**（JDK 9 已废弃） | 老 | 标记 - 清除 | 并发标记 + 并发清除，**低延迟**但有碎片、浮动垃圾 | 早期低延迟 |
| **G1**（JDK 9 默认） | 全 | Region + 标记 - 整理 / 复制 | 把堆拆 Region，可预测停顿 `MaxGCPauseMillis` | 大堆默认 |
| **ZGC / Shenandoah** | 全 | 染色指针 + 并发整理 | < 10ms 停顿，TB 级堆 | 超大堆、超低延迟 |

### G1 重点

- 把堆划分成几千个 Region（每个 1MB ~ 32MB），不再严格分代但仍有 Eden / Survivor / Old / Humongous 角色。
- 优先回收**垃圾最多**的 Region（Garbage First）→ 名字由来。
- 通过 `-XX:MaxGCPauseMillis=200` 设目标停顿，G1 自适应选择回收 Region 数量。
- 适合 4GB 以上堆，是 JDK 9+ 默认收集器。

### ZGC 染色指针

- 把 GC 状态（marked、relocated、remapped）打到 64 位指针的高几位。
- 不再依赖对象头存 GC 元信息 → 几乎所有 GC 阶段并发，停顿稳定 < 10ms。

---

## 七、Full GC / Minor GC / Major GC

来自 [[快手/支付方向/我的快手支付一面]]：

- **Minor GC（Young GC）**：只回收年轻代。Eden 满了就触发，频率高、停顿短。
- **Major GC**：只回收老年代（CMS 等并发收集器才有这个独立概念）。
- **Full GC**：年轻代 + 老年代 + 元空间一起回收，**STW 最长**，能不发生就别发生。

Full GC 触发条件：

1. 老年代不足（晋升空间不够 / 大对象直接进老年代分不到）。
2. 元空间 / 永久代不足。
3. `System.gc()`（生产环境一般禁用 `-XX:+DisableExplicitGC`）。
4. CMS Concurrent Mode Failure 退化成串行 Full GC。
5. 显式 `jmap -dump:live` 等触发。

排查思路：看 GC 日志频率、看晋升量、看老年代占用增长曲线。

---

## 八、JVM 启动参数（调参清单）

来自 [[蚂蚁/蚂蚁一面]]：

```
# 堆与栈
-Xms2g -Xmx2g                # 堆初始 / 最大；生产建议设一致避免 resize
-Xss512k                     # 单线程栈大小，默认 1M，调小可创建更多线程

# 元空间
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m

# 收集器
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=45  # G1 触发并发标记的占用阈值

# GC 日志（线上必开）
-XX:+PrintGCDetails
-XX:+PrintGCDateStamps
-Xloggc:/var/log/myapp/gc.log
-XX:+UseGCLogFileRotation
-XX:NumberOfGCLogFiles=5
-XX:GCLogFileSize=20M

# OOM 自动 dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/myapp/heap.hprof
```

线上一句话原则：

> 堆固定、参数明示、GC 日志必开、OOM 自动 dump。

---

## 九、OOM 排查流程

来自 [[蚂蚁/蚂蚁一面]] 和 [[京东/京东零售一面]]：

**第一步 看错误信息**
不同 OOM 对应不同区域：

| 错误 | 区域 | 常见原因 |
|---|---|---|
| `Java heap space` | 堆 | 大集合无限增长、缓存无 TTL |
| `GC overhead limit exceeded` | 堆 | 98% 时间在 GC 但回收 < 2% |
| `Metaspace` | 元空间 | ClassLoader 泄漏（热部署、动态代理刷类） |
| `Direct buffer memory` | 堆外 | DirectByteBuffer 没释放、Netty |
| `unable to create new native thread` | 系统 | 线程数超系统限制（ulimit） |

**第二步 拿堆 dump**

```bash
jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>
# 或者启动参数 -XX:+HeapDumpOnOutOfMemoryError
```

**第三步 分析 dump**

- **MAT（Eclipse Memory Analyzer）**：Dominator Tree 找占用最大的对象、Leak Suspects 自动报告。
- **VisualVM / JProfiler**：可视化堆快照、对比两次 dump。

**第四步 看 GC 日志**

- GCViewer / GCEasy 可视化 → 看 Full GC 频率、吞吐、停顿。
- 频繁 Full GC 但回收不动 → 老年代有不能回收的强引用堆积。

**第五步 运行时观测工具**

| 工具 | 用途 |
|---|---|
| `jps` | 列出 Java 进程 |
| `jstat -gcutil <pid> 1000` | 实时看各区域占用、GC 次数 |
| `jmap -histo:live <pid>` | 当前对象数量与大小 |
| `jstack <pid>` | 线程 dump，找死锁 / 阻塞 |
| `jconsole` / `jvisualvm` | 图形化 |
| `arthas` | 阿里开源，热诊断神器 |

### 常见 OOM 原因清单

1. 大集合（List / Map）无限增长 + 没清理。
2. 自写缓存 / Caffeine 没有 TTL 与容量上限。
3. ThreadLocal 长生命周期线程未 `remove()`（Tomcat 线程池 + ThreadLocal 是经典坑）。
4. ClassLoader 泄漏（动态代理频繁生成新类）。
5. DirectByteBuffer 没释放（Netty 没正确 release）。
6. 线程数过多（每个线程要 1M 栈）。

---

## 十、提升 Java 应用并发吞吐量的 4 个层面

[[京东/京东零售一面]] 的高频题，可以把 JVM 调优放在第 4 层：

1. **定位瓶颈**：用压测 + profiler（async-profiler / arthas）判断 CPU、锁竞争、IO 等待还是 GC。
2. **线程模型**：线程池分组隔离、有界队列、超时熔断（[[Java 并发编程]]）。
3. **并发设计**：减少共享状态和锁竞争 —— 分段、`LongAdder`、`ConcurrentHashMap`、避免 EventLoop 阻塞。
4. **IO 与资源**：连接池、批量、缓存、降低对象分配率减 GC（**这一层属于 JVM 调优**）。

---

## 十一、口语化背诵段（面试可以直接说）

> JVM 我大致按四块讲：
>
> 第一是**运行时数据区**：程序计数器、虚拟机栈、本地方法栈是线程私有的；堆和方法区（元空间）是共享的；NIO 还会用堆外的直接内存。对象绝大多数在堆里分配，并且可能走 TLAB 减少竞争。
>
> 第二是**分代和 GC**：堆按 Eden、Survivor、Old 分代，Eden 满了触发 Minor GC，存活对象走复制算法到 Survivor，熬过几轮升老年代。GC 用 GC Roots 的可达性分析判活，不用引用计数因为解决不了循环引用。
>
> 第三是**收集器**：Serial / ParNew 是单线程或多线程的复制收集器；CMS 是老年代低延迟，已经废弃；JDK 9+ 默认 G1，把堆拆 Region 可预测停顿；超大堆超低延迟用 ZGC，靠染色指针几乎全程并发。
>
> 第四是**调优和排查**：堆设固定大小、GC 日志必开、OOM 自动 dump；线上排查靠 `jstat`、`jstack`、`jmap`，离线用 MAT 分析堆 dump，重点找 ClassLoader 泄漏、ThreadLocal 没清理、缓存无上限这些点。

---

## 十二、深入阅读 / 双链

- 主题文章：[[JVM内存与GC]]
- 关联章节：[[Java 并发编程]]、[[Java集合相关]]、[[Java语法基础]]
- 真题来源：[[快手/支付方向/我的快手支付一面]]、[[字节/我的字节一面]]、[[京东/京东零售一面]]、[[蚂蚁/蚂蚁一面]]、[[其他/银河智学]]
- 项目联动：[[专栏/Agent/OpenClaw 笔记]]（讲到内存模型时可以类比）
