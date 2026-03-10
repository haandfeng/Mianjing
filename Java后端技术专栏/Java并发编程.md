# Java 并发编程

## 一、多线程实现方式

### 1. 口语版回答（1 分钟）

> Java 里启动多线程大致有三类方式：
>
> 第一种是 **继承 Thread 类**，重写 run() 方法，然后 start() 启动。这种方式简单直观，但因为 Java 只能单继承，会限制类的继承层次，而且任务和线程强耦合，不利于复用。
>
> 第二种是 **实现 Runnable 接口**，把任务逻辑写在 run() 里，再把这个 Runnable 传给 new Thread(runnable)。这样任务和线程解耦，可以用同一个任务给多个线程执行，也保留了继承其他父类的空间，是实际项目中更推荐的方式。
>
> 更工程化的是第三种：**使用线程池（Executor 框架）**，比如 ExecutorService。我们只负责提交任务（Runnable / Callable），由线程池统一管理线程的创建、复用、队列、拒绝策略等。线程池可以避免频繁创建销毁线程带来的开销，也能更好地控制并发数量，是生产环境最常用的方式。

### 2. 展开说明

#### ① 继承 Thread

```java
class MyThread extends Thread {
    @Override
    public void run() {
        // 任务逻辑
    }
}

new MyThread().start();
```

- **优点**：写起来直观、demo 和小样例方便。
- **缺点**：
  - Java **单继承**，继承 Thread 后就不能再继承别的父类。
  - 任务逻辑写在 Thread 子类里，**任务 = 线程**，耦合度高，不利于复用和统一管理。

#### ② 实现 Runnable 接口

```java
class MyTask implements Runnable {
    @Override
    public void run() {
        // 任务逻辑
    }
}

Thread t = new Thread(new MyTask());
t.start();
```

- **优点**：
  - 可以同时继承其他父类：class MyTask extends SomeClass implements Runnable。
  - **任务逻辑**和**线程实现**解耦，一个 Runnable 可以交给不同线程执行，更利于复用。
- **缺点**：
  - Runnable.run() 没有返回值，如果需要结果，要自己设计回调或配合其他机制（如 FutureTask）。

（可以顺口提一句还有 **Callable + FutureTask** 这种带返回值的任务模型）

#### ③ Callable + FutureTask

##### 1. 最常规：自定义回调接口 + Runnable

**（1）定义一个泛型回调接口**

```java
public interface ResultCallback<T> {
    void onSuccess(T result);

    default void onError(Throwable t) {
        t.printStackTrace();
    }
}
```

**（2）在任务里注入回调**

```java
public class MyTask implements Runnable {

    private final int param;
    private final ResultCallback<Integer> callback;
    public MyTask(int param, ResultCallback<Integer> callback) {
        this.param = param;
        this.callback = callback;
    }

    @Override
    public void run() {
        try {
            // 1. 业务计算
            int result = doCompute(param);
            // 2. 通知回调（注意：这是在子线程里调用的）
            if (callback != null) {
                callback.onSuccess(result);
            }
        } catch (Exception e) {
            if (callback != null) {
                callback.onError(e);
            }
        }
    }
    private int doCompute(int x) {
        // 模拟计算
        return x * 2;
    }
}
```

**（3）提交任务时传入回调（可用 lambda）**

```java
ResultCallback<Integer> callback = new ResultCallback<Integer>() {
    @Override
    public void onSuccess(Integer result) {
        System.out.println("计算结果 = " + result);
        // 这里可以继续做后续处理
    }

    @Override
    public void onError(Throwable t) {
        System.err.println("任务失败: " + t.getMessage());
    }
};

// 用 Runnable + Thread
new Thread(new MyTask(10, callback)).start();
```

如果你用的是 Java 8+，回调接口也可以写成函数式接口，然后用 lambda 调：

```java
@FunctionalInterface
public interface SuccessCallback<T> {
    void onSuccess(T result);
}
```

##### 2. 如果项目里已经在用线程池，建议直接上 Callable / Future

**实话说**：只要你能控制线程创建方式，优先用 Callable，就不需要自己写回调接口了。

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
Callable<Integer> task = () -> {
    // 业务逻辑
    Thread.sleep(100);
    return 42;
};

Future<Integer> future = pool.submit(task);

// 需要结果时：
Integer result = future.get(); // 会阻塞到有结果
```

如果你又想要"回调风格"，可以在单独线程里或异步方式处理 Future：

```java
pool.submit(() -> {
    try {
        Integer result = future.get();
        // 回调逻辑
        onSuccess(result);
    } catch (Exception e) {
        onError(e);
    }
});
```

#### ④ 使用线程池（Executor / ExecutorService）

```java
ExecutorService pool = Executors.newFixedThreadPool(10);
pool.submit(new MyTask());  // Runnable 或 Callable
```

- **优点（重点）**：
  - **线程复用**：减少频繁创建/销毁线程的系统开销。
  - **统一管理**：方便设置线程数、队列、线程工厂、拒绝策略等，避免线程"野蛮生长"。
  - 更易做监控统计（活跃线程数、队列长度等）。
- **缺点 / 注意点**：
  - 需要合理配置线程池参数，不然可能导致任务堆积、OOM 或线程频繁上下文切换。
  - 不建议直接用 Executors.newFixedThreadPool 这类快捷方法，在真实项目中更推荐 **显式 new ThreadPoolExecutor**，自己指定参数。

---

## 二、synchronized 底层原理

### 1. 口语版回答（1–2 分钟）

> synchronized 是 Java 最基础的同步手段，它依赖的是对象的"监视器（Monitor）"和对象头里的锁标记。
>
> 编译之后，synchronized 块会变成字节码里的 monitorenter 和 monitorexit 指令，JVM 会通过对象的监视器来保证**同一时刻只有一个线程能持有这把锁**，从而实现互斥访问。
>
> 为了兼顾性能，HotSpot 对 synchronized 做了锁优化和"锁升级"的设计：
>
> - 初始是 **无锁状态**；
> - 当只有一个线程竞争时，会使用 **偏向锁**，把锁"偏向"当前线程，下次这个线程再进锁基本不用加锁操作；
> - 多线程竞争但冲突不激烈时，会升级为 **轻量级锁**，通过 CAS + 自旋的方式在用户态解决竞争；
> - 当竞争激烈、自旋失败时，会升级为 **重量级锁**，让线程挂起（park）和唤醒（unpark），底层会用到操作系统的互斥量和阻塞队列。
>
> 整体来说，synchronized 通过对象监视器保证互斥，通过偏向锁和轻量级锁减少真正阻塞，只有在竞争严重时才退化为重量级锁。

### 2. 展开说明

#### ① synchronized 怎么实现互斥？（Monitor + 字节码）

- 用在**同步代码块**时：

```java
synchronized (lock) {
    // 临界区
}
```

- 编译成字节码，会看到：
  - 进入时：monitorenter
  - 退出时：monitorexit（正常退出和异常退出都会有）
- 用在**同步实例方法**时，相当于给当前实例 (this) 加锁；
- 用在**同步静态方法**时，相当于给当前类的 Class 对象加锁。

**对象监视器（Monitor）**：
- 每个对象在 JVM 中都可以关联一个监视器；
- 当线程执行 monitorenter 时，会尝试获得该对象的监视器：
  - 没有线程持有 → 获得锁，进入临界区；
  - 已被其他线程持有 → 根据锁的状态，自旋或阻塞等待；
- monitorexit 之后，释放监视器，其他等待的线程才有机会获得锁。

synchronized 的**可重入性**：
- 同一线程可以多次进入同一把锁（方法递归调用时），监视器内部会维护一个"进入计数器"。

#### ② 对象头、Mark Word 和锁状态

HotSpot 里每个对象的头部通常包括：
- **Mark Word**：记录 hashCode、GC 分代信息、锁标志位等；
- **Class Pointer**：指向类元数据。

Mark Word 中有几位用于标识当前锁状态，比如：
- 01：无锁；
- 01 + "偏向标志"：偏向锁；
- 00：轻量级锁；
- 10：重量级锁（有 monitor 指针）。

（不需要死记具体二进制，只要知道：**锁的不同状态用 Mark Word 区分，并允许状态升级**。）

#### ③ 锁升级流程（偏向锁 → 轻量级锁 → 重量级锁）

不同 JDK 版本细节略有区别，但思路类似，面试说"总体步骤"就够了。

**1. 偏向锁（Biased Lock）**
- 适用场景：**绝大多数情况下只有一个线程访问这把锁**。
- 实现思想：
  - 第一次获取锁时，把当前线程 ID 写到对象的 Mark Word 中，表示对象"偏向"这个线程；
  - 以后这个线程再次进入同步块时，只需检查对象头是否已经偏向自己，无需真正加锁，**成本极低**。
- 如果有其他线程也尝试获取这把锁：
  - JVM 会撤销偏向锁（可能需要安全点、STW），然后升级为轻量级锁。

**2. 轻量级锁（Lightweight Lock）**
- 适用场景：多线程竞争但冲突不激烈，持锁时间短。
- 实现思想（大致流程）：
  1. 线程在自己的栈帧中创建一个 **Lock Record**；
  2. 用 CAS 尝试把对象的 Mark Word 更新为指向这个 Lock Record 的指针；
  3. 如果 CAS 成功 → 当前线程获得轻量级锁；
  4. 如果 CAS 失败：
     - 说明有其他线程持有锁；
     - 会通过 **自旋**再尝试一段时间；
     - 自旋仍失败，则锁升级为重量级锁。
- 优点：在冲突不大的情况下，自旋 + 用户态 CAS 比内核态阻塞/唤醒更快。

**3. 重量级锁（Heavyweight Lock）**
- 适用场景：竞争激烈、自旋成本过高。
- 实现思想：
  - 把锁对象关联到一个 Monitor，里面有一个阻塞队列；
  - 线程获取不到锁时，不再自旋，而是进入阻塞状态（park），等待唤醒；
  - 释放锁时，唤醒队列里的等待线程。
- 缺点：要从用户态陷入内核态，切换成本高。

**重要：锁可以升级但不能"降级"**
即：偏向锁 → 轻量级锁 → 重量级锁，这个方向只能越来越"重"，以保证实现简单、状态安全。

---

## 三、volatile 关键字

### 1. volatile 有什么作用？

**两个核心作用：可见性 + 有序性（禁止部分指令重排序）**

#### （1）保证可见性

- 普通变量在多线程下：
  每个线程可能把值缓存在线程工作内存 / CPU 缓存里，**改了之后别的线程不一定马上看到**。
- volatile 变量：
  - 线程对它的**写操作**，会立刻刷新到主内存；
  - 线程对它的**读操作**，每次都从主内存读最新值；
- JMM 规定：**对同一个 volatile 变量的写，对之后其他线程的读"happens-before"**，从而保证可见性。

典型例子：

```java
volatile boolean running = true;

public void worker() {
    while (running) {
        // do something
    }
}

// 其他线程
running = false; // 能让 worker 线程及时退出循环
```

#### （2）一定程度上的有序性（禁止重排序）

- 编译器和 CPU 会对指令做重排序优化；
- 对于 volatile 变量的 **写**：
  - 之前的普通写入操作**不会被重排到它之后**；
- 对于 volatile 变量的 **读**：
  - 之后的普通读写操作**不会被重排到它之前**；
- 可以理解为：在 volatile 的读/写前后 JVM 会插入内存屏障，建立起一条"先行发生"关系。

典型用法就是 **双重检查单例** 中，防止 new 的指令被重排：

```java
class Singleton {
    private static volatile Singleton instance;
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton(); // 依赖 volatile 防止重排
                }
            }
        }
        return instance;
    }
}
```

### 2. volatile 能否保证原子性？

**结论：不能保证复合操作的原子性。**

- 对 volatile 变量的**单次读 / 单次写**是原子的（例如 volatile int x; x = 10;）。
- 但是像 i++ 这种是 **读 → 改 → 写** 三步操作，在多线程下仍然会有"丢更新"。

示例：

```java
volatile int count = 0;

public void incr() {
    count++;  // 不是原子操作
}
```

多个线程同时执行 count++ 时，可能都读到旧值，然后覆盖彼此结果，最终 count 明显小于预期。

**如果需要真正的原子性**：
- 可以用 synchronized、ReentrantLock；
- 或者用 AtomicInteger 这类原子类。

### 3. volatile 和 synchronized 的区别？

可以从几个角度对比：

#### （1）功能对比

- volatile：
  - 保证 **可见性**；
  - 提供一定的 **有序性（禁止部分重排序）**；
  - **不保证复合操作原子性**，不提供互斥。
- synchronized：
  - 保证 **可见性**（释放锁时刷新到主内存，获取锁时从主内存读）；
  - 保证 **原子性+互斥**（同一时刻只有一个线程能进入同步块）；
  - 也间接提供了有序性（临界区前后的代码顺序不会被随意重排）。

一句话：
> volatile 是"**轻量级的可见性+有序性工具**"，
> synchronized 是"**重量级的互斥锁（带可见性+原子性**）"。

#### （2）使用范围

- volatile：
  - **只能修饰变量**（成员变量、静态变量）；
  - 不能修饰方法、代码块。
- synchronized：
  - 可以修饰 **实例方法**、**静态方法**、**代码块**；
  - 需要一把"锁对象"（this、class 对象、任意 Object）。

#### （3）开销 & 特性

- volatile：
  - 不会阻塞线程，没有挂起 / 唤醒；
  - 只是在读写时多了内存屏障和缓存同步，开销很小；
  - **不支持重入、不支持条件等待**（没有 wait/notify 概念）。
- synchronized：
  - 在竞争激烈时可能导致线程上下文切换，有阻塞、唤醒的成本；
  - 但有自旋、偏向锁等优化后，轻度竞争场景下性能也不算差；
  - **可重入锁**，配合 wait()/notify()、notifyAll() 可以实现更复杂的同步协作。

### 4. 在什么情况下会考虑使用 volatile？

标准答案可以分两大类场景：

#### 场景一：状态标志 / 配置信号（最典型）

例子：

```java
public class Server {
    private volatile boolean running = true;

    public void start() {
        while (running) {
            // do work
        }
    }

    public void shutdown() {
        running = false; // 其他线程调用后能"立刻被看到"
    }
}
```

**特点：**
- 写入很少，读很多；
- 多线程之间只是要"看到最新值"，**不会有复合操作依赖这个变量**；
- 不需要加锁互斥，只是一个"开关信号"。

#### 场景二：发布-订阅 / 配置刷新 / 双重检查锁

1. **双重检查单例**（上面说过）：
   - instance 用 volatile 防止 new 的指令重排。

2. **配置缓存刷新**：

```java
volatile Config config;

void reload() {
    // 主线程重新加载配置
    config = loadFromDb();
}

void handle() {
    // 工作线程每次直接用最新的 config
    Config c = config;
    // 使用 c
}
```

所有线程都能看到最新的配置对象，不用加锁。

3. **简单的"一写多读"共享变量**
   - 数据结构本身是不可变的，例如把 volatile 用在 volatile List\<String> configList，每次修改都是**重新 new 一个 List** 赋值回去，而不是在原 List 上增删改；
   - 那么读线程只需要看到"指针指向的新对象"，就够了。

#### 场景三：配合原子类或 CAS 做一些框架级优化（了解即可）

- 在一些底层并发类里，volatile 会和 CAS / 原子类搭配使用；
- 面试时如果你提到 volatile 常出现在 **J.U.C 包**源码中（比如 AtomicInteger 的 value 字段），说明你看过一些源码，会加分。

### 5. 面试用一句话总结

你可以最后补一句收尾：

> 我一般把 volatile 看成"多线程下的带内存语义的普通变量"，只在**不需要互斥、只需要保证可见性和有序性**的场景用它，比如状态开关、配置引用、双检锁里的单例变量；一旦涉及到复合操作或业务逻辑比较复杂，就会用 synchronized 或显式锁 / 原子类来保证原子性和线程安全。

---

## 四、线程池

### 1. 线程池是什么？

一句话：

**线程池就是"预先创建好一批可复用的工作线程，用来统一接收和执行任务的组件"。**

好处：
- 复用线程，**减少频繁创建/销毁线程的开销**；
- 能**限制并发数量**，避免"开太多线程把机器打爆"；
- 集中管理：可统计、监控、定制线程名、异常处理等。

### 2. ThreadPoolExecutor 的核心参数含义

常见构造方法（简化版）：

```java
public ThreadPoolExecutor(
    int corePoolSize,              // 核心线程数
    int maximumPoolSize,           // 最大线程数
    long keepAliveTime,            // 非核心线程空闲存活时间
    TimeUnit unit,                 // 时间单位
    BlockingQueue<Runnable> workQueue,     // 任务队列
    ThreadFactory threadFactory,          // 创建线程的工厂
    RejectedExecutionHandler handler      // 拒绝策略
)
```

你提到的几个重点参数：

#### ① 核心线程数（corePoolSize）

- 线程池**会尽量维持的线程数量**，就算空闲也不回收（除非设置了 allowCoreThreadTimeOut(true)）。
- 当有新任务到来：
  - 如果当前运行的线程数 < corePoolSize → **直接创建新线程**来执行任务；
  - 不会先入队列。

#### ② 最大线程数（maximumPoolSize）

- 线程池中允许存在的**最大线程数量**（核心 + 非核心）。
- 当队列满了且当前线程数 < maximumPoolSize 时：
  - 会继续创建**非核心线程**来执行任务；
- 超过 maximumPoolSize 后再有新任务 → 触发**拒绝策略**。

#### ③ 队列（workQueue）及队列长度

BlockingQueue\<Runnable> workQueue，常见几种：
- **有界队列**：ArrayBlockingQueue（有固定容量，如 1000）
  - 可以控制排队任务个数，防止 OOM；
- **无界队列**：LinkedBlockingQueue（默认 Integer.MAX_VALUE）
  - 队列几乎"无限大"，一旦核心线程数满了，新任务全进队列，**maximumPoolSize 基本失效**；
- **同步移交队列**：SynchronousQueue
  - 没有容量，每个 put 必须等一个 take，适合"直接交给线程，不排队"的高并发场景。

"队列长度"其实就是**任务能堆积多少个**，配合 core/maximumPoolSize 决定整体吞吐和内存占用。

#### ④ 拒绝策略（RejectedExecutionHandler handler）

当满足 **"线程数已达 maximumPoolSize 且队列已满"** 时，再有新任务提交：
- 就会走到 RejectedExecutionHandler，常见几种默认策略：
  - AbortPolicy（默认）：直接抛 RejectedExecutionException；
  - CallerRunsPolicy：交给**提交任务的那个线程**自己同步执行；
  - DiscardPolicy：悄悄丢弃这个任务；
  - DiscardOldestPolicy：丢弃队列中最旧的任务，然后尝试重新提交当前任务。

通常生产环境会**自定义拒绝策略**，至少要打日志或做降级，而不是悄悄丢。

### 3. 线程池的工作流程（非常适合面试时画个流程）

假设使用 execute() / submit() 提交任务，整体流程是：

1. **如果当前工作线程数 < corePoolSize**
   → 直接创建新线程执行任务（不进队列）。

2. **否则，如果线程数 ≥ corePoolSize**
   → 尝试把任务 **放入队列 workQueue**：
   - 如果队列没满 → 入队等待，由现有线程从队列中取任务执行。

3. **如果队列满了，并且当前线程数 < maximumPoolSize**
   → 创建**非核心线程**执行任务。

4. **如果线程数已达 maximumPoolSize 且队列也满了**
   → 调用 **拒绝策略** RejectedExecutionHandler 处理。

5. **非核心线程空闲超过 keepAliveTime**
   → 会被回收（核心线程默认不会被回收）。

一句话总结流程（可以背）：

> 先看核心线程够不够，不够就新建线程；
> 核心线程满了就排队；
> 队列满了再看最大线程，不够就再建线程；
> 最大线程也满了，任务就交给拒绝策略处理。

---

## 五、死锁

### 1. 什么是死锁（Deadlock）？

定义：

**多个线程互相持有对方所需要的锁/资源，导致各自都在等待对方释放，最终都无法继续执行的一种"永久等待"状态。**

简单例子（两个锁，两条线程交叉拿）：

```java
Object lockA = new Object();
Object lockB = new Object();

Thread t1 = new Thread(() -> {
    synchronized (lockA) {
        Thread.sleep(100);
        synchronized (lockB) {
        }
    }
});

Thread t2 = new Thread(() -> {
    synchronized (lockB) {
        Thread.sleep(100);
        synchronized (lockA) {
        }
    }
});
```

t1 先拿了 A 等 B，t2 先拿了 B 等 A → 互相等 → 就死了。

### 2. 产生死锁的四个必要条件

这是标准八股，面试可以一口气背出来：

1. **互斥条件（Mutual Exclusion）**
   - 资源一次只能被一个线程占用（典型就是锁）。

2. **占有且等待（Hold and Wait）**
   - 线程已经持有至少一个资源，同时又在请求新的资源，并且对已占有的资源不释放。

3. **不可抢占（No Preemption）**
   - 资源（锁）不能被强制抢占，只能由持有线程主动释放。

4. **循环等待（Circular Wait）**
   - 存在一个线程等待环：
     T1 等 T2 的资源，T2 等 T3 的资源，…，Tn 又等 T1 的资源。

**只有这四个条件都满足时，才会形成死锁。**

要避免死锁，就要**破坏其中至少一个条件**。

### 3. 实际开发中如何避免死锁？

更偏实战，可以从"设计上避免 + 代码习惯 + 工具排查"三方面讲。

#### ① 统一加锁顺序（最实用）

- 约定所有线程**获取多把锁的顺序是一致的**，比如：
  - 先锁 Account ID 小的，再锁大的；
  - 先锁 A 再锁 B，任何地方都不能先锁 B 再锁 A。
- 这样就能破坏"循环等待条件"，非常有效。

#### ② 减少锁的粒度和持有时间

- 尽量**缩小 synchronized 的范围**，锁内不要做：
  - IO 操作、网络调用、sleep、复杂计算等；
- 持锁时间越短，发生死锁和性能问题的概率都越小。

#### ③ 尽量避免"嵌套锁"

- 尽量避免在持有一把锁的同时，还去获取另一把锁；
- 如果确实需要多把锁，务必统一顺序 + 明确注释。

#### ④ 使用显式锁 + tryLock + 超时（如 ReentrantLock）

```java
Lock lockA = new ReentrantLock();
Lock lockB = new ReentrantLock();

void doWork() {
    if (lockA.tryLock(100, TimeUnit.MILLISECONDS)) {
        try {
            if (lockB.tryLock(100, TimeUnit.MILLISECONDS)) {
                try {
                    // 临界区
                } finally {
                    lockB.unlock();
                }
            } else {
                // 获取 lockB 失败，放弃或重试
            }
        } finally {
            lockA.unlock();
        }
    } else {
        // 获取 lockA 失败
    }
}
```

- 利用 tryLock(timeout)，**获取不到锁就放弃 / 重试 / 记录日志**，从而**避免无限期等待**。

#### ⑤ 使用更高级的并发工具

- 尽量用 java.util.concurrent 提供的容器和工具：
  - ConcurrentHashMap、ConcurrentLinkedQueue、Semaphore、CountDownLatch、CyclicBarrier 等；
- 避免自己频繁手写 "synchronized + 多把锁" 的复杂逻辑。

### 4. 如何排查死锁？

面试时说"线程 dump + 工具"就行：

- **拿线程 dump（Thread Dump）**：
  - Linux 上用 jstack \<pid>；
  - 或者用各种图形化工具（JConsole / VisualVM 等）；
- 在线程 dump 中，JVM 会直接帮你标记出 **Found one Java-level deadlock**；
  - 会列出：哪些线程，分别持有哪些锁，又在等待哪些锁；
- 根据这些信息，定位到代码中的锁顺序问题或嵌套锁问题。

你可以总结一句：

> 实战里，我更倾向于在设计阶段就统一锁顺序、减少嵌套锁，并在关键模块加上日志和监控。如果真的怀疑有死锁，就会先打线程 dump，看有没有"Found one Java-level deadlock"，再顺着锁和线程的关系回到代码里修。
