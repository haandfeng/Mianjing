---
title: Java锁体系
type: topic
updated: 2026-05-04
---

# Java锁体系

> synchronized 自动加解锁、JVM 锁升级（无锁→偏向→轻量级→重量级）；ReentrantLock 显式 + 可中断 + 公平 + 条件变量；volatile 只保证可见性 + 有序性，不原子。

## 高频问法
- "synchronized 底层原理 + 锁升级" — [[蚂蚁/蚂蚁一面]]、[[小红书/小红书产品工程师一面面经]]
- "synchronized vs ReentrantLock 对比" — [[蚂蚁/蚂蚁一面]]、[[字节-今日头条-财经业务/字节财经一面]]
- "volatile 作用 + 双重检查锁为什么需要 volatile" — [[快手/支付方向/快手日常实习面经]]、[[快手/支付方向/我的快手支付一面]]
- "锁的分类（可重入 / 公平 / 读写 / 自旋）" — [[蚂蚁/蚂蚁一面]]、[[小红书/小红书产品工程师一面面经]]
- "死锁四个必要条件、怎么避免、怎么排查" — [[字节-今日头条-财经业务/字节财经一面]]
- "Java 中的锁有哪些，分别什么场景" — [[蚂蚁/蚂蚁一面]]

## 答题骨架

### 1. synchronized 底层
- **代码块**：编译成 `monitorenter` / `monitorexit`，对象 Monitor 互斥
- **方法**：方法标志位 `ACC_SYNCHRONIZED`，JVM 看到该标志直接获取对象 / Class 锁
- **可重入**：Monitor 内部有计数器，同一线程重入计数 +1，归零才释放
- 对象头 Mark Word 存锁状态：01 无锁 / 偏向、00 轻量级、10 重量级

### 2. 锁升级（HotSpot 优化）
| 状态 | 适用 | 实现 |
|---|---|---|
| 无锁 | 没人加 | — |
| 偏向锁 | 仅一个线程 | 把线程 ID 写 Mark Word，下次进来直接通过 |
| 轻量级锁 | 多线程低竞争 | 栈帧建 Lock Record + CAS 改 Mark Word；失败自旋 |
| 重量级锁 | 高竞争 | OS 互斥量 + 阻塞队列，park / unpark |

- 锁只能升级不能降级
- JDK 15+ 偏向锁默认禁用（维护成本 > 收益）

### 3. synchronized vs ReentrantLock
| | synchronized | ReentrantLock |
|---|---|---|
| 加解锁 | JVM 自动 | 手动 lock / unlock（必须 finally） |
| 可重入 | ✓ | ✓ |
| 公平性 | 非公平 | 默认非公平，可构造公平锁 |
| 可中断 | ✗ | `lockInterruptibly()` |
| 超时 | ✗ | `tryLock(timeout)` |
| 条件变量 | wait / notify（单条件） | Condition（多个条件队列） |
| 性能 | 中（JVM 优化） | 略好（高竞争下） |

### 4. volatile 三大作用 + 限制
- **可见性**：写立即刷主内存，读每次都从主内存（通过内存屏障）
- **有序性**：禁止指令重排（写前面的写不被排到后面，读后面的读不被排到前面）
- **❌ 原子性**：`i++` 仍然不安全（读-改-写三步）
- 单变量需要原子用 `AtomicInteger`（CAS）

### 5. 双重检查单例为什么 instance 要 volatile
```java
class Singleton {
    private static volatile Singleton instance;
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) instance = new Singleton(); // 这里
            }
        }
        return instance;
    }
}
```
- `new Singleton()` 不原子：①分配内存 ②初始化对象 ③把引用赋给 instance
- 没 volatile 时 ② 和 ③ 可能重排 → 别的线程拿到未初始化对象（外层 if 直接看到非空）
- volatile 禁止 ② 和 ③ 重排

### 6. 死锁四要素 + 避免 + 排查
- 四要素：互斥 / 占有且等待 / 不可抢占 / 循环等待
- **避免**：统一加锁顺序（破坏循环）；缩小锁粒度 + 减少嵌套；`tryLock(timeout)` 超时放弃；用 J.U.C 容器
- **排查**：`jstack <pid>` 看是否有 "Found one Java-level deadlock"，里面会列出哪个线程持哪个锁等哪个

### 7. 锁分类速记
- 可重入 vs 不可重入
- 公平 vs 非公平
- 独占（synchronized / ReentrantLock）vs 共享（ReadWriteLock）
- 悲观（synchronized）vs 乐观（CAS）
- 自旋（CAS while 循环）vs 阻塞

## 易错点 & 追问
- synchronized 是非公平锁；ReentrantLock 默认也是非公平
- 读写锁 `ReentrantReadWriteLock`：读读不互斥，写写 / 读写互斥；写锁可降级为读锁
- ReentrantLock 必须 `try { ... } finally { unlock() }`
- volatile 不能保证 `i++` 原子
- 偏向锁在新 JDK 默认关闭

## 深入阅读
- 原始专栏 [[后端技术专栏/Java并发编程]]
- 原始专栏 [[后端技术专栏/Java并发编程#六、经典并发工具]]
- [[wiki/技术主题/Java并发集合]]
- 真题来源 [[蚂蚁/蚂蚁一面]]、[[快手/支付方向/快手日常实习面经]]、[[字节-今日头条-财经业务/字节财经一面]]、[[小红书/小红书产品工程师一面面经]]
