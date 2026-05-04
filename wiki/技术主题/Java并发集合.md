---
title: Java并发集合
type: topic
updated: 2026-05-04
---

# Java并发集合

> HashMap 线程不安全（扩容死循环 / 数据覆盖）；ConcurrentHashMap 1.7 分段锁、1.8 CAS + synchronized 锁桶头节点；ThreadLocal 隔离线程数据但有内存泄漏。

## 高频问法
- "ConcurrentHashMap 怎么实现线程安全？1.7 vs 1.8" — [[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]、[[字节-今日头条-财经业务/我的字节一面]]、[[腾讯/数据平台/我的腾讯一面]]、[[小红书/小红书产品工程师一面面经]]、[[蚂蚁/蚂蚁一面]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
- "HashMap 为什么线程不安全？JDK 7 头插法死循环" — [[面经较少公司/银河智学]]
- "桶数量为什么是 2 的 n 次方" — [[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]
- "扩容时多线程怎么协作" — [[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
- "ThreadLocal 原理 + 内存泄漏" — [[小红书/小红书产品工程师一面面经]]、[[腾讯/数据平台/我的腾讯一面]]、[[蔚来/xhs]]
- "CAS 原理与 ABA" — [[小红书/小红书产品工程师一面面经]]

## 答题骨架

### 1. HashMap 结构与原理
- 数组 + 链表 / 红黑树（链表长 > 8 且数组长 ≥ 64 → 转红黑树；红黑树节点数降到 6 退回链表）
- `(table.length-1) & hash` 算下标
- 负载因子 0.75；超过则 2 倍扩容

### 2. HashMap 为什么线程不安全
- **JDK 1.7 头插法 + 多线程扩容**：链表反向 → 形成环 → `get` 死循环
- **JDK 1.8 改尾插**避免成环，但仍有：
  - 哈希冲突时，A 检查冲突时让出 CPU，B 写入后 A 继续写覆盖了 B
  - 多线程扩容时各自创建新数组，覆盖
  - `++size` 不原子 → 数据覆盖

### 3. ConcurrentHashMap JDK 1.7 vs 1.8
| | 1.7 | 1.8 |
|---|---|---|
| 结构 | Segment[] + HashEntry[] | Node[] + 链表 / 红黑树 |
| 锁 | ReentrantLock 锁 Segment | CAS + synchronized 锁桶头节点 |
| 锁粒度 | Segment 级（默认 16） | 桶级（数组多大就多少把锁） |
| 并发度 | 默认 16 | 等于数组长度 |

### 4. ConcurrentHashMap 1.8 put 流程
1. 算出桶下标
2. **桶为空**：用 CAS 写入头节点，成功就返回
3. **桶非空且不在迁移**：对头节点 `synchronized`，遍历链表 / 红黑树插入或替换
4. **桶在迁移**（看到 ForwardingNode）：当前线程协助扩容
5. 末尾 `addCount` 更新元素总数（用 CounterCell 避免单点竞争）

### 5. ConcurrentHashMap 1.8 get 无锁
- Node 的 val 和 next 都是 `volatile`，写入对其他线程可见
- 读取过程中扩容也不影响：碰到 ForwardingNode 自动转向新表查

### 6. 协作扩容
- 第一个线程 CAS 把 `sizeCtl` 改为负数，创建 2 倍新数组开始迁移
- 其他线程发现 sizeCtl 为负，按 stride 领一段桶帮忙迁移（默认每段 16 个桶）
- 迁移完一个桶放 `ForwardingNode` 标记
- 期间 get 转新表查；put 帮忙迁完再 put

### 7. 桶数为什么是 2 的 n 次方
1. **位运算取模**：`hash & (length-1)` ≡ `hash % length`，比除法快
2. **元素均匀分布**：`length-1` 全是 1，哈希值每位都参与；非 2 幂时部分位永远是 0，奇桶浪费
3. **扩容高效**：`(length-1)` 高位多一位 1，旧元素只需看哈希新增高位是 0 还是 1，决定留原位还是移到 `原位置 + 旧容量`，不必全部 rehash

### 8. ThreadLocal
- 每个 Thread 内部有 `ThreadLocalMap`，key 是 ThreadLocal 实例，value 是值
- `get()`：拿当前线程的 map，用 `this`（ThreadLocal 对象）查
- 线程隔离：A 线程的 map ≠ B 线程的 map
- **内存泄漏**：Entry 的 key 是弱引用（GC 时被回收），但 value 强引用
  - ThreadLocal 实例没有强引用 + 线程长存（线程池） → key=null 但 value 一直在
  - 用完一定 `remove()` 兜底；get/set/remove 内部会顺便清理 key=null 的 entry，但不可靠

### 9. CAS（Compare-And-Swap）
- 一条 CPU 指令：`if mem == expected then mem = new`
- 优点：无锁，避免阻塞 / 上下文切换
- 缺点：
  1. **ABA**：值从 A→B→A，CAS 检测不出 → 用 AtomicStampedReference（带版本号）
  2. **自旋开销**：高竞争下 CPU 空转 → LongAdder 分段累加缓解
  3. **只能保证单变量原子**：复合操作要 synchronized 或 ReentrantLock

## 易错点 & 追问
- ConcurrentHashMap 单个 get / put 原子，但 `if (!map.containsKey(k)) map.put(k, v)` 不原子 → 用 `putIfAbsent` / `computeIfAbsent`
- HashMap 1.8 改尾插仍不安全，只是不会成环
- ThreadLocal 不是给跨线程传值用的（要用 InheritableThreadLocal 或 TransmittableThreadLocal）
- `hashCode % length` 和 `hashCode & (length-1)` 等价仅在 length 是 2 的幂时成立

## 深入阅读
- 原始专栏 [[后端技术专栏/Java并发编程]]
- 原始专栏 [[后端技术专栏/Java多线程 并发]]
- 原始专栏 [[后端技术专栏/Java集合相关]]
- 真题来源 [[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]、[[字节-今日头条-财经业务/我的字节一面]]、[[腾讯/数据平台/我的腾讯一面]]、[[小红书/小红书产品工程师一面面经]]、[[蚂蚁/蚂蚁一面]]、[[面经较少公司/银河智学]]
