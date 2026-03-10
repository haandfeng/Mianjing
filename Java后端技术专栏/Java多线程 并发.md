# 经典面试题：
手撕：实现一个并发任务处理器：给定一个包含100个任务ID的列表，要求控制最大并发数为3，模拟并发调用某个外部接口（如打印ID）
# 线程池
主要就是 1. 有多少个线程(稳定的，最大的) 2.怎么回收 3.排队队列 4.超出了怎么办

`ThreadPoolExecutor` 构造参数一共7个：
```java
new ThreadPoolExecutor(
    int corePoolSize,          // 核心线程数
    int maximumPoolSize,       // 最大线程数
    long keepAliveTime,        // 非核心线程空闲存活时间
    TimeUnit unit,             // 时间单位
    BlockingQueue workQueue,   // 任务队列
    ThreadFactory threadFactory,   // 线程工厂（可省，有默认）
    RejectedExecutionHandler handler  // 拒绝策略（可省，有默认）
);
```

---

**执行流程：**
```
提交任务
  → 核心线程数未满？创建核心线程执行
  → 核心线程满了？放入队列
  → 队列满了？创建非核心线程执行
  → 达到最大线程数且队列满？触发拒绝策略
```


**队列选择：**
- `LinkedBlockingQueue` — 无界队列（默认`Integer.MAX_VALUE`），注意OOM风险
- `LinkedBlockingQueue(n) `— 有界队列，推荐
- `SynchronousQueue` — 不存储任务，来一个必须立刻有线程接，`newCachedThreadPool` 用的就是这个
- `ArrayBlockingQueue(n)` — 有界，数组实现

**拒绝策略：**
- `AbortPolicy` — 抛 `RejectedExecutionException`（默认）
- `CallerRunsPolicy` — 由调用者线程执行，起到降速作用
- `DiscardPolicy` — 静默丢弃
- `DiscardOldestPolicy` — 丢掉队列头部最老的任务，再重试提交

## 实现经典面试题
```java
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolExecutor executor = new ThreadPoolExecutor(
            3, 3, 0, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>()
        );

        for (int i = 1; i <= 100; i++) {
            final int id = i;
            executor.submit(() -> {
                System.out.println("任务: " + id + " | 线程: " + Thread.currentThread().getName());
            });
        }

        executor.shutdown();
        executor.awaitTermination(1, TimeUnit.HOURS);
        System.out.println("完成");
    }
}
```


如果需要交替打印的

```java
public class Main {
    static int turn = 0;
    static final Object lock = new Object();

    public static void main(String[] args) {
        for (int id = 0; id < 3; id++) {
            final int threadId = id;
            new Thread(() -> {
                while (true) {
                    synchronized (lock) {
                        while (turn < 100 && turn % 3 != threadId) {
                            lock.wait();
                        }
                        if (turn >= 100) return;
                        System.out.println("Thread-" + threadId + ": " + turn);
                        turn++;
                        lock.notifyAll();
                    }
                }
            }).start();
        }
    }
}
```

输出严格交替：
```
Thread-0: 0
Thread-1: 1
Thread-2: 2
Thread-0: 3
Thread-1: 4
...
```

###  把 id 作为参数传递

不能直接用 lambda，因为 `Runnable` 的 `run()` 方法没有参数。但有几种方式可以实现：
方式1：封装成方法
```java
private static Runnable createTask(int id) {
    return () -> {
        System.out.println("任务: " + id + " | 线程: " + Thread.currentThread().getName());
        try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    };
}

// 使用
for (int i = 1; i <= 100; i++) {
    executor.submit(createTask(i));  // i 作为方法参数传入，天然就是值拷贝
}
```

####  Callable vs Runnable

两者都是用来定义线程任务的函数式接口，核心区别就两点：**有无返回值**和**能否抛异常**。

```java
@FunctionalInterface
public interface Runnable {
    void run();  // 无返回值，不能抛受检异常
}

@FunctionalInterface
public interface Callable<V> {
    V call() throws Exception;  // 有返回值，可以抛受检异常
}



// Runnable：只管执行，不关心结果
executor.submit(() -> {
    System.out.println("干活");
});

// Callable：执行完可以拿到结果
Future<String> future = executor.submit(() -> {
    Thread.sleep(1000);  // 可以直接抛异常，不用 try-catch
    return "干完了，这是结果";
});

String result = future.get();  // 阻塞等待结果
System.out.println(result);    // "干完了，这是结果"
```


# Future和CompleteFuture

# **Future**

`Future` 是 Java5 引入的，代表一个异步任务的结果。通过 `executor.submit()` 返回。

核心方法就三个：

- `get()` — 阻塞等待结果
- `get(timeout, unit)` — 带超时的阻塞
- `isDone()` — 判断是否完成

缺点很明显：`get()` 是阻塞的，多个 Future 只能逐个等待，没有回调机制，无法组合。

常用方法：

```java
Future<String> future = executor.submit(() -> {
    Thread.sleep(1000);
    return "结果";
});

future.isDone();                          // 是否完成，不阻塞
future.isCancelled();                     // 是否被取消
future.cancel(true);                      // 取消任务
future.get();                             // 阻塞等待结果
future.get(3, TimeUnit.SECONDS);          // 最多等3秒，超时抛异常
```



> **回调机制**是指任务完成后自动触发某段逻辑，而不是你主动去问"完成了吗"。Future 没有回调，你只能主动调 `get()` 阻塞等结果，任务完成了也不会通知你。CompletableFuture 的 `thenAccept` 就是回调，任务完成后自动执行。

### Future实现经典面试题

```java

import java.util.*;
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(3);
        List<Future<?>> futures = new ArrayList<>();

        for (int i = 1; i <= 100; i++) {
            final int id = i;
            futures.add(executor.submit(() -> {
                System.out.println("任务: " + id + " | 线程: " + Thread.currentThread().getName());
                return null;
            }));
        }

        for (Future<?> f : futures) {
            f.get();
        }

        executor.shutdown();
        System.out.println("完成");
    }
}
```



## **CompletableFuture**

Java8 引入，解决了 Future 的缺点，支持回调、组合、异步链式调用。

常用方法：

```java
// 提交异步任务
CompletableFuture.runAsync(() -> {...}, executor);        // 无返回值
CompletableFuture.supplyAsync(() -> return xxx, executor); // 有返回值

// 任务完成后回调
.thenRun(() -> {...})          // 不关心上一步结果
.thenAccept(result -> {...})   // 接收上一步结果
.thenApply(result -> {...})    // 接收并转换结果

// 组合
CompletableFuture.allOf(f1, f2, f3).join();  // 等所有任务完成
CompletableFuture.anyOf(f1, f2, f3).join();  // 等任意一个完成
```

### CompleteFuture 实现经典面试题

```java
import java.util.*;
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(3);
        List<CompletableFuture<Void>> futures = new ArrayList<>();

        for (int i = 1; i <= 100; i++) {
            final int id = i;
            futures.add(CompletableFuture.runAsync(() -> {
                System.out.println("任务: " + id + " | 线程: " + Thread.currentThread().getName());
            }, executor));
        }

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        executor.shutdown();
        System.out.println("完成");
    }
}
```





# CountDownLatch



`CountDownLatch` 是一个计数器，初始化一个数字，每次调用 `countDown()` 减1，调用 `await()` 的线程会阻塞直到计数器归零。



```java
CountDownLatch latch = new CountDownLatch(3);

for (int i = 0; i < 3; i++) {
    final int id = i;
    new Thread(() -> {
        System.out.println("任务 " + id + " 完成");
        latch.countDown();
    }).start();
}

latch.await(); // 主线程阻塞，等3个任务都完成
System.out.println("全部完成");
```


# ThreadLocal

比如我们在同一个线程中声明了两个 ThreadLocal 对象的话， Thread内部都是使用仅有的那个ThreadLocalMap 存放数据的，ThreadLocalMap的 key 就是 ThreadLocal对象，value 就是 ThreadLocal 对象调用set方法设置的值。



ThreadLocal 实现线程隔离的关键在于：数据不是存在 ThreadLocal 对象里，而是存在每个 Thread 对象自己的 Map里。

每个 Thread 对象内部有一个 threadLocals 字段，类型是 ThreadLocalMap。当你调用 threadLocal.get（）的时候，它先拿到当前线程的 ThreadLocalMap，再用 ThreadLocal 对象自身作为 key 去查。所以同一个 ThreadLocal 对象，线程 A调用 get 查的是A的 Map，线程B 调用 get 查的是 B 的 Map，各找各的，自然就隔离了。


![](https://oss.javaguide.cn/github/javaguide/java/concurrent/threadlocal-data-structure.png)



## 内存泄露

`ThreadLocal` 的 `set()` 方法源码如下：

```java
public void set(T value) {
    Thread t = Thread.currentThread(); // 获取当前线程
    ThreadLocalMap map = getMap(t);   // 获取当前线程的 ThreadLocalMap
    if (map != null) {
        map.set(this, value);         // 设置值
    } else {
        createMap(t, value);          // 创建新的 ThreadLocalMap
    }
}
```

`ThreadLocalMap` 的 `set()` 和 `createMap()` 方法中，并没有直接存储 `ThreadLocal` 对象本身，而是使用 `ThreadLocal` 的哈希值计算数组索引，最终存储于类型为`static class Entry extends WeakReference<ThreadLocal<?>>`的数组中。

`ThreadLocalMap` 的 `Entry` 定义如下：

```java
static class Entry extends WeakReference<ThreadLocal<?>> {
    Object value;

    Entry(ThreadLocal<?> k, Object v) {
        super(k);
        value = v;
    }
}
```



`ThreadLocalMap` 的 `key` 和 `value` 引用机制：

- **key 是弱引用**：`ThreadLocalMap` 中的 key 是 `ThreadLocal` 的弱引用 (`WeakReference<ThreadLocal<?>>`)。 这意味着，如果 `ThreadLocal` 实例不再被任何强引用指向，垃圾回收器会在下次 GC 时回收该实例，导致 `ThreadLocalMap` 中对应的 key 变为 `null`。
- **value 是强引用**：即使 `key` 被 GC 回收，`value` 仍然被 `ThreadLocalMap.Entry` 强引用存在，无法被 GC 回收。

当 `ThreadLocal` 实例失去强引用后，其对应的 value 仍然存在于 `ThreadLocalMap` 中，因为 `Entry` 对象强引用了它。如果线程持续存活（例如线程池中的线程），`ThreadLocalMap` 也会一直存在，导致 key 为 `null` 的 entry 无法被垃圾回收，即会造成内存泄漏。

也就是说，内存泄漏的发生需要同时满足两个条件：

1. `ThreadLocal` 实例不再被强引用；
2. 线程持续存活，导致 `ThreadLocalMap` 长期存在。

虽然 `ThreadLocalMap` 在 `get()`, `set()` 和 `remove()` 操作时会尝试清理 key 为 null 的 entry，但这种清理机制是被动的，并不完全可靠。