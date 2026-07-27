---
title: Python并发与GIL
type: topic
updated: 2026-07-20
---

# Python 并发与 GIL

> GIL 是 **CPython 实现**的一把全局互斥锁：同一时刻只有一个线程能执行 Python 字节码。根因是引用计数非原子。**2026 年它已从「不可逾越」变成「可选项」**——free-threading 与子解释器都已落地。

## 高频问法
- 「为什么有 GIL？多线程的锁有哪些？Lock 和 RLock 有啥区别？」—— 出处 [[老虎国际一面面经（资讯组）]]
- 「多线程情况下这个队列怎么保证正确性？」—— 出处 [[腾讯/微信事业群/腾讯微信支付一面_2026-07-20]]（手写环形队列的可选进阶项）
- 「信号量的底层实现原理」
- 「Python 多线程为什么快不起来？怎么绕过？」

## 答题骨架

### 1. GIL 是什么（一句话 + 比喻）

**GIL = Global Interpreter Lock**，CPython 解释器进程里的**一把 C 层互斥锁**（互斥量 + 条件变量 + 原子标志位）。规矩只有一条：**任何时刻只有持有 GIL 的线程能执行 Python 字节码**。

> **比喻**：会议室 8 个人只有一支麦克风，拿到才能说话。去倒水（I/O）就把麦克风放下 → I/O 可并发；一直演讲（CPU 密集）→ 麦克风成瓶颈，人再多也只有一个在说。

### 2. 为什么需要它（根因：引用计数非原子）

CPython 用**引用计数**管内存，每个对象有 `ob_refcnt`。`ob_refcnt++` 在机器层面是「读→加→写」三步，非原子：

```
线程A: 读到 5    线程B: 读到 5
线程A: 算出 6    线程B: 算出 6
线程A: 写回 6    线程B: 写回 6     ← 加了两次只涨 1
```

- 计数偏小 → **对象提前释放 → 悬垂指针 → 崩溃**
- 计数偏大 → **内存泄漏**

**为什么不给每个对象加锁**：几百万对象、每次访问都加解锁，开销爆炸 + 死锁风险。GIL 是「一把大锁保平安」的工程折中：实现简单、**单线程性能好**（省掉所有细粒度锁）、C 扩展作者不用操心线程安全。

### 3. 它怎么运转（释放时机）

**① 主动释放（并发的来源）**
- 执行 I/O 时（`socket.recv` / `file.read` / `time.sleep`）进系统调用前先放
- C 扩展主动放：`Py_BEGIN_ALLOW_THREADS`——**numpy 做大矩阵运算就是这么干的**

**② 被动释放（切换机制，CPython 3.2+ 新 GIL）**
- 等待线程 `cv_wait(切换间隔)`，默认 **5ms**（`sys.getswitchinterval()`）
- 超时后设置 **`gil_drop_request`** 标志
- 持有者在 eval loop 检查到标志 → 释放并让出

> ⚠️ **不是「每 5ms 自动切一次」**，是「**有人在等且等够 5ms 才发出让位请求**」。没人竞争时一个线程可以一直跑。
> 旧 GIL 是「每 100 条字节码检查一次」，导致 I/O 线程饥饿（**convoy effect**）。

### 4. 五个常见误解（面试高频陷阱）

| 误解 | 真相 |
|---|---|
| ❌ GIL 是 Python 语言特性 | **是 CPython 实现的特性**。Jython/IronPython 没有（它们用 GC 不用引用计数） |
| ❌ 有 GIL 就不用加锁 | **大错**。GIL 只保证**单条字节码**原子。`x += 1` 是三条（`dis.dis("x+=1")` 自己看），中间能被切走 |
| ❌ 多线程在 Python 里没用 | **I/O 密集完全有用**——I/O 时释放 GIL |
| ❌ GIL 是 Python 慢的原因 | 无关。单线程性能与 GIL 无关，**GIL 反而让单线程更快**。慢是因为解释执行+动态类型 |
| ❌ C 扩展也被锁住 | 可主动释放后做纯 C 计算 |

### 5. 同步原语与 Lock vs RLock

| 原语 | 用途 |
|---|---|
| `Lock` | 基本互斥，**不可重入** |
| `RLock` | 可重入（**owner 线程 id + 递归计数**） |
| `Condition` | Lock + wait/notify/notify_all |
| `Semaphore` / `BoundedSemaphore` | 计数信号量，限流/资源池 |
| `Event` | 广播式信号 |
| `Barrier` | N 个线程到齐才放行（**测并发神器**） |
| `queue.Queue` | 线程安全队列（内部 = deque + 两个 Condition） |

| | Lock | RLock |
|---|---|---|
| 同线程重复 acquire | **死锁**（自锁死） | 允许，计数 +1 |
| release 要求 | 任意线程可 release | **只有 owner 能 release，次数要配平** |
| 性能 | 更快 | 略慢（查 owner + 维护计数） |

> **原则：能用 Lock 就用 Lock。需要 RLock 常说明锁的边界设计有问题**——更好的做法是把临界区抽成不加锁的私有方法 `_xxx_unlocked()`，外层统一加锁。

### 6. 信号量底层原理

**信号量 = 计数器 + 等待队列**。`P/acquire`: count--，<0 则入队阻塞；`V/release`: count++，有等待者则唤醒一个。

| | 互斥锁 | 信号量 |
|---|---|---|
| **所有权** | 有 owner，**谁加谁解** | **无 owner**，A 线程 P、B 线程 V 合法 |
| 计数 | 二元 | 任意 N |
| 用途 | 保护临界区 | 资源计数、限流、生产者-消费者同步 |

**三层实现：**
1. **计数器原子性** → CAS / `lock xadd`
2. **阻塞唤醒 → Linux futex**（精髓）：
   - **无竞争时完全在用户态**（CAS 成功直接走，零系统调用）
   - **有竞争才 `futex_wait` 进内核睡眠**
   - `futex_wait(addr, expected)` 在内核里**再检查一次 `*addr == expected` 才睡**——消除「检查完到睡下之间对方 release」的**丢失唤醒**竞态
3. **内核层**：按地址哈希的 futex 等待队列，线程 `RUNNING → INTERRUPTIBLE`，摘出就绪队列

**Python 的 `threading.Semaphore` 是纯 Python 实现**（Condition + 计数器），调用链：`Semaphore → Condition → Lock → pthread mutex → futex`。`BoundedSemaphore` 在 release 超过初值时抛 `ValueError`——**做资源池优先用它**，能抓出「release 多于 acquire」的 bug。

### 7. 阻塞队列的两个必背点（手写题常考）

```python
while self._size == self._cap and not self._closed:   # ← 必须 while 不能 if
    self._not_full.wait()
```
**为什么必须 while**：①**虚假唤醒**（futex/pthread 允许无故返回）②**竞争唤醒**（更常见——被 notify 后要**重新抢锁**，抢到前可能被别人插队）。**wait 返回只意味着「可能可以了」。**

```python
def close(self):
    with self._lock:
        self._closed = True
        self._not_full.notify_all()      # ⚠️ 必须 all
        self._not_empty.notify_all()     #    否则阻塞线程永久挂起
```

> 生产环境直接用 `queue.Queue(maxsize=n)`——**面试要能手写，工程上别重造**。

### 8. 2026 年怎么绕过 GIL

#### ① Free-threaded CPython（PEP 703）——真正的解法

**不是配置开关，是另一个可执行文件**：`python3.14`（有 GIL）vs **`python3.14t`**（t = threaded，无 GIL）。3.13 实验性，**3.14 官方支持（PEP 779）**。

```bash
uv python install 3.14t        # 或 pyenv install 3.14t / 官方安装包勾选框
python3.14t -c "import sys; print(sys._is_gil_enabled())"   # False
```

**代码一个字不用改**，`ThreadPoolExecutor` 直接吃满多核。

**实现三件事**：**偏向引用计数**（对象归属创建线程，本线程走非原子快路径）+ **不朽对象**（PEP 683，None/True/小整数引用计数根本不动）+ **内置容器细粒度锁**。

**三个坑**：①**C 扩展要重编译**并声明 `Py_MOD_GIL_NOT_USED`，不支持会自动把 GIL 打开（白装）②单线程略慢 ③**⚠️ 没了 GIL 更需要自己加锁**——以前因粗粒度调度碰巧没复现的竞态会立刻现形

#### ② 子解释器（PEP 734）——3.14 进标准库

**一个进程里开多个完整独立的解释器实例**，各有自己的 `sys.modules`、全局状态、**自己的一把 GIL**（PEP 684 在 3.12 已在 C 层实现）。

```python
from concurrent import interpreters
interp = interpreters.create()
interp.exec("x = sum(i*i for i in range(20_000_000))")
```

| | 多线程 | **子解释器** | 多进程 |
|---|---|---|---|
| 同一 OS 进程 | ✅ | ✅ | ❌ |
| 共享 Python 对象 | ✅ | **❌ 不共享** | ❌ |
| 各有 GIL | ❌ | ✅ | ✅ |
| 启动开销 | 最小 | **中等** | 最大 |
| 数据竞争风险 | 高 | 低（无共享无竞争） | 无 |

**定位：比进程轻，比线程安全。** 传数据用 `interpreters.create_queue()`。

#### ③ 多进程 —— 最成熟

代价是 **pickle 序列化开销**（见下）+ 内存翻倍。大数组用 `multiprocessing.shared_memory` 绕开序列化。

#### ④ 把热点推到 C/Rust（最常被低估）

numpy / polars / torch 底层大运算**主动释放 GIL**；**PyO3** 的 `py.allow_threads(|| {...})`；**Cython** 的 `with nogil:`；**numba** 的 `@njit(parallel=True, nogil=True)`。

> **判断标准**：profile 显示 80% 时间在少数几个函数里 → **换 native 实现比重构并发模型划算得多**。

#### 决策表

| 场景 | 选择 |
|---|---|
| I/O 密集 | `asyncio`（高并发）/ `threading`（简单）——**不用绕** |
| CPU 密集，热点集中 | **换 native 库 / Rust 扩展** ← 性价比最高 |
| CPU 密集，任务独立 | `ProcessPoolExecutor` |
| CPU 密集 + 需共享大量状态 | **free-threaded 3.14t**（先验证依赖兼容） |
| 需并行 + 强隔离 | **子解释器** |

### 9. pickle（多进程绕不开的配套知识）

**pickle = Python 内置的「对象 ↔ 字节流」转换器**。多进程必须用它，因为**进程间内存隔离**——对象只能拍扁成字节传过去再还原。

```
进程A: {"a":1} ─dumps→ b'\x80\x05...' ─管道→ 进程B ─loads→ {"a":1}
```

**三个代价：**
1. **CPU + 内存开销**——大数据时是主要瓶颈，「多进程处理大数组反而更慢」的原因
2. **有些东西 pickle 不了**：lambda、文件句柄、socket、锁——**规律：绑定 OS 资源的都不行**（换个进程毫无意义）
3. **⚠️ 安全红线：绝不 unpickle 不可信数据**——反序列化会执行 `__reduce__`，等价于任意代码执行。**pickle ≠ json**：json 只表达数据，pickle 表达「怎么重建对象」。跨系统/接收外部数据一律用 JSON / msgpack / Protobuf / Arrow

## 易错点 & 追问

- ❌ **「有 GIL 所以不用加锁」**——最高频错误。`dis.dis("x += 1")` 亲手看三条字节码
- ❌ **把 GIL 当语言特性**——是 CPython 实现特性
- ❌ **条件等待用 `if` 不用 `while`**——虚假唤醒 + 竞争唤醒
- ❌ **close 时用 `notify` 而非 `notify_all`**——阻塞线程永久挂起（关闭时死锁）
- ⚠️ **反直觉**：去掉 GIL 之后**更需要**加锁，不是更不需要

**60 秒口语版：**
> 「GIL 是 CPython 里的全局互斥锁，同一时刻只有一个线程能执行字节码。根因是引用计数增减非原子，多线程并发改会导致对象提前释放或泄漏；给每个对象加锁开销太大，所以用一把大锁。它在 I/O 和部分 C 扩展调用时主动释放，所以 I/O 密集多线程有效，CPU 密集才受限。切换是等待线程等够 5ms 后设 drop request，持有者在 eval loop 检查到就让出。**关键是有 GIL 也必须自己加锁**——它只保证单条字节码原子。另外 2026 年已经有解了：3.14 的 free-threading 官方支持，子解释器进了标准库，最实用的还是把 CPU 热点推到 C/Rust 里让它主动释放 GIL。」

## 深入阅读
- 实战出处：[[腾讯/微信事业群/腾讯微信支付一面_2026-07-20]]（手写线程安全队列）· [[老虎国际一面面经（资讯组）]]（GIL/协程对比）
- 并发测试怎么写：[[测试设计方法论]] §④并发层
- 相关：[[Linux与IO模型]]（epoll / futex 同源）· [[Java锁体系]]（对照 synchronized/AQS）
