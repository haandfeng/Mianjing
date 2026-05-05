在面对著名的C10K（一万个并发连接）甚至C10M问题时，线程的创建与销毁开销、海量线程带来的内核上下文切换（Context Switch）损耗以及每个线程私有栈对物理内存的极度消耗，会迅速导致系统资源枯竭并引发内核崩溃。操作系统为此引入了==I/O多路复用技术（I/O Multiplexing），允许单一线程同时监控多个文件描述符（File Descriptor, FD）的读写就绪状态==，从而以极低的资源消耗实现海量并发连接的管理。


[快手日常实习面经，也考到了RPC Netty相关的内容 可以看看](obsidian://open?vault=%E9%9D%A2%E7%BB%8F&file=%E5%BF%AB%E6%89%8B%2F%E6%94%AF%E4%BB%98%E6%96%B9%E5%90%91%2F%E5%BF%AB%E6%89%8B%E6%97%A5%E5%B8%B8%E5%AE%9E%E4%B9%A0%E9%9D%A2%E7%BB%8F)
#  Select Poll Epoll



| **核心特性与考察维度**    | **select机制**                    | **poll机制**                 | **epoll机制**                           |
| ---------------- | ------------------------------- | -------------------------- | ------------------------------------- |
| **底层数据结构支持**     | 定长数组（Bitmap结构）                  | 链表结构                       | 红黑树（存储FD） + 双向链表（就绪队列）                |
| **最大连接数限制**      | 存在严格限制（受限于`FD_SETSIZE`，通常为1024） | 无硬性限制（仅受限于系统可用物理内存）        | 无硬性限制（仅受限于系统可用物理内存）                   |
| **用户态与内核态数据拷贝**  | 每次调用均需将庞大的FD集合从用户态全量拷贝至内核态      | 每次调用均需将庞大的FD集合从用户态全量拷贝至内核态 | 仅在`epoll_ctl`注册时发生一次拷贝，内核态长效维护        |
| **就绪事件检测与时间复杂度** | $O(N)$（需线性遍历整个FD集合以查找就绪状态）      | $O(N)$（需线性遍历整个FD集合以查找就绪状态） | $O(1)$（网卡硬中断直接触发回调，将就绪FD写入双向链表）       |
| **工作触发模式支持**     | 仅支持水平触发（Level Triggered, LT）    | 仅支持水平触发（LT）                | 全面支持水平触发（LT）与边缘触发（Edge Triggered, ET） |





总的来说：

Poll相对于Select的进化就是用了链表结构，允许更大的链接（FD）

Epoll相对于Poll来说的进化：

1. 用红黑树+双向链表管理FD，不需要每次都把FD从用户态拷贝到内核态里面

2. epoll使用回调函数管理就绪事件，一旦发生中断把就绪FD写入链表里。而select和poll是每次返回就绪的FD的时候，都需要便利所有的FD找到可读可写的FD返回。 

   **详细版**：（这epoll使用事件驱动的机制，内核里维护了一个链表来记录就绪事件，当某个 socket 有事件发生时，通过回调函数内核会将其加入到这个就绪事件列表中，当用户调用 epoll_wait（）函数时，只会返回有事件发生的文件描述符的个数，不需要像 select/poll 那样轮询扫描整个 socket 集合，大大提高了检测的效率。）

   ![img](https://cdn.xiaolincoding.com/gh/xiaolincoder/ImageHost4@main/%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F/%E5%A4%9A%E8%B7%AF%E5%A4%8D%E7%94%A8/epoll.png)

## Epoll 红黑树和链表的协作
### 红黑树和就绪链表是两个东西，干两件不同的事

```
epoll 内部有两个核心数据结构：

┌─────────────────────────────────────────────┐
│              epoll 实例                      │
│                                             │
│   红黑树（rbr）              就绪链表（rdllist） │
│   ┌───────┐                 ┌──┬──┬──┐      │
│   │  fd=5 │                 │3 │7 │12│      │
│   │ / \   │                 └──┴──┴──┘      │
│   │3   7  │                                 │
│   │   / \ │                 这里面放的是      │
│   │  6  12│                 "已经有事件就绪"   │
│   └───────┘                 的 fd            │
│                                             │
│   这里面放的是                                │
│   "所有你让我监听"                             │
│   的 fd                                     │
└─────────────────────────────────────────────┘
```

### 红黑树：管理"监听哪些 fd"

当你调用 `epoll_ctl` 增删改 fd 时，操作的是红黑树：

```c
// 添加一个 fd 到 epoll 监听
epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &event);  // O(log N)，插入红黑树

// 删除一个 fd
epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client_fd, NULL);    // O(log N)，从红黑树删除

// 修改一个 fd 关注的事件
epoll_ctl(epoll_fd, EPOLL_CTL_MOD, client_fd, &event);  // O(log N)，红黑树查找后修改
```

为什么用红黑树？因为需要**频繁地增删查 fd**。连接建立就 ADD，连接断开就 DEL，改监听事件就 MOD。红黑树保证这些操作都是 O(log N)，比链表的 O(N) 查找快，又不像哈希表那样有扩容和冲突的问题。

### 就绪链表：O(1) 事件通知

这是你说的 O(1) 部分，它和红黑树无关：

```
数据到达的完整路径：

网卡收到数据
  → 触发硬中断
  → 内核协议栈处理，数据放入 Socket 接收缓冲区
  → 内核检查：这个 fd 有没有被某个 epoll 监听？
  → 有！调用注册好的回调函数 ep_poll_callback()
  → 回调做了一件事：把这个 fd 挂到就绪链表（rdllist）上
  → O(1)，就是往双向链表尾部追加一个节点
```

然后你调用 `epoll_wait` 时：

```c
// 应用层调用
int n = epoll_wait(epoll_fd, events, max_events, timeout);

// 内核做的事（简化）：
if (rdllist 不为空) {
    // 直接把就绪链表里的 fd 拷贝到用户空间的 events 数组
    // 返回就绪的数量
    return 就绪数量;
} else {
    // 链表为空，没有就绪事件，阻塞等待
    // 等到有回调把 fd 挂上来，就醒来
}
```

所以 **epoll_wait 不做任何遍历和检测**，它只是去看就绪链表里有没有东西。

### 对比 select/poll 就明白了

```
select/poll 的做法（O(N)）：
  用户态：把所有 fd（比如1万个）传给内核
  内核：  遍历这1万个 fd，逐个检查有没有事件
  返回：  告诉你哪些有事件
  每次调用都要遍历全部，不管有几个就绪

epoll 的做法：
  注册时：epoll_ctl 把 fd 插入红黑树，O(log N)，只做一次
  运行时：数据到了 → 内核回调 → fd 挂到就绪链表，O(1)
  获取时：epoll_wait 直接取就绪链表，O(就绪数量)
  不需要遍历所有 fd
```

## 一句话总结

红黑树是为了**高效管理"我要监听哪些 fd"**（增删改 O(log N)），就绪链表是为了**高效获取"哪些 fd 有事件了"**（内核回调挂入 O(1)，取出 O(就绪数量)）。两个数据结构各管各的，分工明确。

## LT 水平触发 和 ET 边缘触发



LT: 只要满足事件的条件，比如内核中有数据需要读，就一直不断地把这个事件传递给用户。
ET: 边缘触发的意思是只有第一次满足条件的时候才触发，之后就不会再传递同样的事件了。

## 红黑树原理

### 先从二叉搜索树（BST）说起

红黑树本质上是一棵**自平衡的二叉搜索树**，所以先理解 BST：

```
BST 的规则：左子节点 < 父节点 < 右子节点

比如存 [5, 3, 7, 1, 4, 6, 8]：

        5
       / \
      3   7
     / \ / \
    1  4 6  8

查找 6：5→右→7→左→6，三步找到，O(log N)
```

但 BST 有个致命问题，如果按顺序插入 [1, 2, 3, 4, 5]：

```
    1
     \
      2
       \
        3
         \
          4
           \
            5

退化成链表了！查找变成 O(N)
```

所以需要"自平衡"机制，红黑树和 AVL 树都是解决这个问题的。

### 红黑树的规则

红黑树通过给节点染色，加上五条约束，保证树**大致平衡**：

```
规则1：每个节点非红即黑
规则2：根节点是黑色
规则3：叶子节点（NIL空节点）是黑色
规则4：红色节点的两个子节点必须是黑色（不能连续两个红）
规则5：从任意节点到其所有叶子的路径上，黑色节点数量相同
```

规则 5 是核心。它保证了**最长路径不超过最短路径的两倍**：

```
最短路径：全黑          黑 → 黑 → 黑          长度 3
最长路径：黑红交替      黑 → 红 → 黑 → 红 → 黑 → 红  长度 6

所以树高最多是 2 * log(N)，查找还是 O(log N)
```

举个例子：

```
        8(黑)
       /     \
     4(红)    12(红)
    / \       / \
  2(黑) 6(黑) 10(黑) 14(黑)
  /\   /\    /\     /\
 1  3 5  7  9  11  13 15
(红)          (全红，省略颜色标注)
```

### 红黑树怎么保持平衡

插入或删除后如果违反了规则，通过两种操作修复：

#### 变色：把节点红变黑或黑变红

```
插入 节点X（新节点默认红色）后，父节点也是红色，违反规则4

      10(黑)                    10(红) ← 变红
     /    \                    /    \
   5(红)   15(红)   →       5(黑)   15(黑) ← 变黑
   /                        /
 3(红) ← 新插入           3(红)

父和叔都是红 → 父、叔变黑，祖父变红
```

#### 旋转：调整树的结构

```
左旋（以节点X为支点）：

    X                Y
     \      →      /
      Y            X

右旋（以节点Y为支点）：

      Y            X
     /      →       \
    X                Y
```

实际的修复场景：

```
插入后发现：父红，叔黑，需要旋转

      10(黑)                   5(黑)
     /            右旋         /   \
   5(红)          →         3(红)  10(红)
   /
 3(红)
```

关键点在于：**修复操作最多沿着树往上走到根，最多 O(log N) 次变色，最多 2-3 次旋转**。

### AVL 树的规则

AVL 树更严格，要求**每个节点的左右子树高度差不超过 1**：

```
AVL 合法：               AVL 不合法：
    5  (左高2,右高1)         5  (左高3,右高1)
   / \  差值=1              / \  差值=2 ← 违规！
  3   7                    3   7
 /                        /
1                        2
                        /
                       1
```

AVL 违规后也通过旋转修复，但因为平衡要求更严格，修复时旋转次数更多。

### 红黑树 vs AVL 树的核心区别

```
              红黑树                    AVL树
平衡标准    黑色节点数相同（宽松）      左右高度差 ≤ 1（严格）
树高       最高 2*log(N)              最高 1.44*log(N)
查找       稍慢一点点                  稍快一点点（树更矮）
插入       最多 2 次旋转               最多 2 次旋转
删除       最多 3 次旋转               最多 O(log N) 次旋转 ← 关键区别
综合       增删多的场景更快             查找多的场景更快
```

### 删除操作是决定性差距

这是红黑树被广泛采用的根本原因。

AVL 删除一个节点后，可能需要**从删除点一路旋转到根节点**，每层都要调整：

```
AVL 删除最坏情况：

删除节点后，层层不平衡，每层都要旋转

      层1 → 旋转
     /
   层2 → 旋转
   /
  层3 → 旋转
  /
 层4 → 旋转       总共 O(log N) 次旋转
```

红黑树删除后，**最多 3 次旋转**就能搞定，剩下的只需要变色（变色比旋转代价小得多）：

```
红黑树删除最坏情况：

最多 3 次旋转 + O(log N) 次变色

旋转涉及指针修改、可能的缓存失效
变色只是改一个标志位
```

### 为什么 epoll 用红黑树

回到 epoll 的场景：

```
epoll 的操作模式：
  - 高频地 ADD/DEL fd（连接不断建立和断开）
  - 偶尔 MOD（修改监听事件）
  - 增删操作远多于纯查找

红黑树：增删都是 O(log N)，删除最多 3 次旋转  ← 适合
AVL树：删除可能 O(log N) 次旋转               ← 没必要
哈希表：增删 O(1)，但无序，且扩容有延迟抖动    ← 不稳定
```

epoll 需要的是**稳定的、增删高效的有序存储**，红黑树正好满足。

## 一句话总结

红黑树用"大致平衡"换来了**删除时极少的旋转次数**（最多 3 次），而 AVL 树为了追求"严格平衡"在删除时可能旋转 O(log N) 次。在频繁增删的场景下（比如 epoll 管理 fd、Java 的 TreeMap、Linux 进程调度），红黑树的综合性能更优。

# BIO NIO AIO

BIO、NIO、AIO 是 Java 里三种不同的I/O模型，核心区别在于线程在等待数据时的行为。

BIO 是同步阻塞模型，线程发起 read 调用后就卡在那，数据没来之前啥也干不了。一个连接配一个线程，1000个连接就得开1000个线程，线程切换开销直接把CPU 拖垮。

NIO 是同步非阻塞模型，线程可以先去干别的，通过 Selector 轮询哪些Channel 有数据可读。一个线程能管几千个连接，Netty、Tomcat 的 NIO 模式都是这个套路。

AIO 是异步非阻塞模型，发起读请求后直接返回，操作系统把数据拷贝完了再通过回调通知你。听起来最牛，但Linux 下AIO 支持一般，实际生产环境用得不多。



![](https://pic.code-nav.cn/mianshiya/question_picture/1783388929455529986/1Ue6bEo6_javaio.drawio_mianshiya.webp)


**同步阻塞：** 调用后线程卡住，什么都不能做，等结果回来才继续。

```java
String result = future.get(); // 线程卡在这，等结果
```

**同步非阻塞：** 调用后立刻返回，但你需要自己不断去轮询问"好了吗？"

```java
while (!future.isDone()) {
    // 可以做其他事，但要不断来问
}
String result = future.get();
```

---

两者都是"同步"，意思是你需要主动去等或去问结果。区别是阻塞会卡住线程，非阻塞不卡但要轮询。

真正解放线程的是**异步**，也就是 CompletableFuture 的回调，任务完成后自动通知你，主线程完全不用管。

## BIO

BIO 最典型的实现就是 ServerSocket：

```java
ServerSocket server = new ServerSocket(8080);
while (true) {
    Socket client = server.accept(); // 阻塞，等待连接
    new Thread(() -> {
        InputStream in = client.getInputStream();
        byte[] buf = new byte[1024];
        int len = in.read(buf); // 阻塞，等待数据
        // 处理数据...
    }).start();
}
```

问题很明显：每来一个连接就得新开一个线程，线程在 read 的时候阻塞着，啥也不干，纯占资源。假设系统能撑 2000 个线程，那最多就只能处理 2000个并发连接。更要命的是线程栈默认 1MB，2000 个线程光栈空间就要 2GB内存。

![img](https://pic.code-nav.cn/mianshiya/question_picture/1843904816956411905/InPMqbrN_44k58wr7S4_mianshiya.webp)

## NIO



NIO 引入了三个核心概念：

1） Channel 是双向通道，可以读也可以写，比 Stream 灵活。SocketChannel、FileChannel 都属于这类。

2） Buffer 是数据缓冲区，NIO 读写都要通过 Buffer 中转。ByteBuffer 用得最多，有 capacity、position、limit 三个指针控制读写位置。

3） Selector 是多路复用器，一个 Selector 能同时监听多个 Channel 的事件。底层在 Linux 上用 epoll，Windows 上用select.



> JDK 原生 NIO 有个臭名昭著的 Selector 空轮询 Bug，在 Linux 的epoll 实现上，即使没有任何事件就绪，select（）也可能直接返回 0，导致死循环把 CPU 跑到100%。这个 Bug 从JDK 1.6 就有，官方一直没彻底修复。

```java
Selector selector = Selector.open();
ServerSocketChannel serverChannel = ServerSocketChannel.open();
serverChannel.bind(new InetSocketAddress(8080));
serverChannel.configureBlocking(false);
serverChannel.register(selector, SelectionKey.OP_ACCEPT);

while (true) {
    selector.select(); // 阻塞，直到有事件就绪
    Set<SelectionKey> keys = selector.selectedKeys();
    for (SelectionKey key : keys) {
        if (key.isAcceptable()) {
            // 处理新连接
        } else if (key.isReadable()) {
            // 处理读事件
        }
    }
    keys.clear();
}
```

![img](https://pic.code-nav.cn/mianshiya/question_picture/1843904816956411905/FpvvL5EG_gJSEGQLqHM_mianshiya.webp)



## 为什么 NIO 比 BIO 性能好

关键在于线程利用率。BIO 模式下线程大部分时间在 sleep等数据，CPU 空转。NIO 用一个线程轮询所有连接，只有真正有数据可读的时候才处理，线程利用率能到 90％以上。

Netty 的 Reactor 模型就是 NIO 的最佳实践：1-2个 Boss 线程负责 accept 新连接，CPU 核心数 × 2个 Worker 线程负责读写。4 核机器配 8个 Worker 线程，轻松扛住几万并发。





### NIO 的 Selector 底层在 Linux上是怎么实现的？

回答：Linux上用的是 epoll。JDK 早期版本用select/poll，但这两个每次调用都要把fd 集合从用户态拷贝到内核态，连接多了性能很差。epoll用 epoll_create 创建句柄，epoll_ctl 注册事件，epoll_wait 等待就绪，fd 集合常驻内核，不用每次拷贝，而且用红黑树管理 fd，就绪事件用链表返回，时间复杂度 O（1）。



### 直接内存和堆内存在 NIO 里有什么区别？



回答：NIO 的 ByteBuffer 有两种，HeapByteBuffer 在堆上分配，DirectByteBuffer 在堆外分配。==堆内存读写要先拷贝到直接内存再做系统调用，多一次拷贝。直接内存省掉这次拷贝，但分配和回收成本高，适合缓冲区复用的场景。==Netty默认用池化的 DirectBuffer，既省拷贝又省分配开销。

### 什么场景下 BIO 反而比 NIO 合适？

回答：连接数少、请求处理时间短的场景。比如内部管理后台，同时在线就几十个人，用BIO 代码简单、调试方便。NIO 的优势在高并发，如果并发量上不去，Selector 的轮询开销反而是负担。另外文件1/0 用 NIO 的 FileChannel 配合MappedByteBuffer 做内存映射才有意义，普通小文件读写 BIO 的 FilelnputStream 就够了。

# Reactor 和 Proactor
==一个线程管理多个线程，一个线程轮询所有事件，然后分发给不同的线程==，能一对多的根据不同请求做出不同响应，这就是 Reactor 的核心。

Reactor 是一种处理并发 I/O事件的设计模式，特别适合网络服务器开发。它的核心思想是把 I/O 事件和处理程序解耦，通过一个事件分发器来管理事件和响应操作。

说白了就是有一个 selector 线程管着一大堆连接，只要某个连接上有事件产生，就会唤醒这个线程，然后根据事件类型找到对应的处理逻辑去执行。

Reactor 的工作方式有三个特点：
1. ﻿﻿﻿事件驱动，通过监听多个事件源，有事件发生时调用对应的 Handler
2. ﻿﻿非阻塞 I/O，单个或少数线程就能处理大量I/O 操作，避免线程频繁切换
3. ﻿﻿﻿事件分发与处理，把收到的事件分发给对应的处理器去执行

Reactor 线程通过多路复用器监听多个连接，当连接上有事件发生时，Reactor 被唤醒。

Reactor 根据事件类型找到对应的 Handler,Handler 执行读取数据、写入数据或业务逻辑处理。处理完成后 Reactor 继续监听其他事件。

![](https://pic.code-nav.cn/mianshiya/question_picture/1783388929455529986/prDb6hMl_image_mianshiya.webp)

大学做图书管理系统这种大作业的时候，点击一个按钮就会弹出对应的弹框。不同的按钮弹不同的框，这就是”反应"。
把这个抽象一下，就是针对不同的事件需要有不同的处理逻辑。
两个概念出来了：
- ﻿﻿事件是点击按钮
- ﻿﻿处理逻辑是弹对应的框。
那到底是谁在监听按钮被点击然后弹框呢？

两种思路：

1. ﻿﻿一个按钮派一个线程守着，只要按钮被点击了，这个线程就执行弹框
2. ﻿﻿==一个线程轮询所有按钮的情况，死循环查看只要有一个按钮被点击了，就找出按钮绑定的框然后弹(Reactor)==

### 单 Reactor 与多 Reactor 模型

1）单 Reactor 单线程模型：所有操作都在一个I/O线程里完成。系统资源消耗少，但扛不住高并发，连接数上去之后一个线程根本顶不住。

2）单Reactor多线程模型：一个线程负责接收连接和处理I/O读写，业务逻辑甩给线程池跑。大部分场景够用了，但并发量大的时候，单个线程负责所有事件的接收和分发，容易成瓶颈。

3） 主从 Reactor 多线程模型：主Reactor 线程专门负责接收连接，从 Reactor 线程处理I/O读写，业务逻辑还是线程池来跑。能扛住几十万连接的高并发，Netty 默认就是这种模型。代价是实现复杂度更高，资源管理要求也更高。

#### 代码示例

代码已经是 NIO 了。你用的 `SocketChannel` + `ByteBuffer` + `Selector` 就是 Java NIO 的三板斧。NIO 的"非阻塞"体现在整体架构上：Selector 通过事件通知告诉你哪个 Channel 可读/可写，你才去读写，而不是一个线程死等一个连接。单看 `channel.read()` 这一行，它确实是"读到数据就返回"的非阻塞调用。

跟 BIO 的 `inputStream.read()` 最大的区别就是：BIO 没数据时会**卡住等**，NIO 没数据时**直接返回 0 不等**。但我们的代码能走到 `read()` 方法，是因为 Selector 已经告诉我们"这个 Channel 有数据可读了"（OP_READ 事件就绪），所以实际上几乎不会返回 0。



#### **单 Reactor 单线程：**

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;

/**
 * 模型一：单 Reactor 单线程
 *
 * 所有操作（accept、read、decode、compute、encode、send）都在同一个线程里完成。
 * 优点：系统资源消耗少，实现简单。
 * 缺点：扛不住高并发，一个线程处理所有事情，容易阻塞。
 *
 * 使用方式：启动后用 telnet localhost 8080 测试
 */
public class SingleReactorSingleThread implements Runnable {

    private final Selector selector;
    private final ServerSocketChannel serverChannel;

    public SingleReactorSingleThread(int port) throws IOException {
        selector = Selector.open();
        serverChannel = ServerSocketChannel.open();
        serverChannel.socket().bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);
        // 注册 ACCEPT 事件，附带 Acceptor 作为回调
        serverChannel.register(selector, SelectionKey.OP_ACCEPT, new Acceptor());
        System.out.println("[单Reactor单线程] 启动，监听端口: " + port);
    }

    @Override
    public void run() {
        try {
            while (!Thread.interrupted()) {
                selector.select(); // 阻塞等待事件
                Set<SelectionKey> keys = selector.selectedKeys();
                Iterator<SelectionKey> it = keys.iterator();
                while (it.hasNext()) {
                    dispatch(it.next());
                    it.remove();
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /** 事件分发：取出 attachment 直接在当前线程执行 */
    private void dispatch(SelectionKey key) {
        Runnable handler = (Runnable) key.attachment();
        if (handler != null) {
            handler.run();
        }
    }

    // ==================== Acceptor ====================
    // 负责接收新连接，并为每个连接创建 Handler
    // =================================================
    class Acceptor implements Runnable {
        @Override
        public void run() {
            try {
                SocketChannel channel = serverChannel.accept();
                if (channel != null) {
                    System.out.println("[Acceptor] 新连接: " + channel.getRemoteAddress());
                    new Handler(selector, channel);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // ==================== Handler ====================
    // read → decode → compute → encode → send
    // 全部在 Reactor 单线程中串行执行
    // ================================================
    static class Handler implements Runnable {

        private final SocketChannel channel;
        private final SelectionKey key;
        private final ByteBuffer readBuffer = ByteBuffer.allocate(1024);
        private final ByteBuffer writeBuffer = ByteBuffer.allocate(1024);

        private static final int READING = 0, SENDING = 1;
        private int state = READING;

        public Handler(Selector selector, SocketChannel channel) throws IOException {
            this.channel = channel;
            channel.configureBlocking(false);
            key = channel.register(selector, SelectionKey.OP_READ, this);
        }

        @Override
        public void run() {
            try {
                if (state == READING) {
                    read();
                } else if (state == SENDING) {
                    send();
                }
            } catch (IOException e) {
                closeChannel();
            }
        }

        private void read() throws IOException {
            readBuffer.clear();
            int n = channel.read(readBuffer);
            if (n == -1) {
                closeChannel();
                return;
            }
            readBuffer.flip();

            // decode
            byte[] data = new byte[readBuffer.remaining()];
            readBuffer.get(data);
            String request = new String(data).trim();
            System.out.println("[Handler] 收到: " + request);

            // compute (业务处理)
            String response = process(request);

            // encode
            writeBuffer.clear();
            writeBuffer.put(response.getBytes());
            writeBuffer.flip();

            // 切换到写状态
            state = SENDING;
            key.interestOps(SelectionKey.OP_WRITE);
        }

        private void send() throws IOException {
            channel.write(writeBuffer);
            if (!writeBuffer.hasRemaining()) {
                state = READING;
                key.interestOps(SelectionKey.OP_READ);
            }
        }

        /** 模拟业务处理 */
        private String process(String request) {
            return "ECHO: " + request + "\n";
        }

        private void closeChannel() {
            try {
                key.cancel();
                channel.close();
            } catch (IOException ignore) {}
        }
    }

    // ==================== 启动入口 ====================
    public static void main(String[] args) throws IOException {
        int port = 8080;
        SingleReactorSingleThread reactor = new SingleReactorSingleThread(port);
        new Thread(reactor, "Reactor").start();
    }
}
```
#### **单 Reactor 多线程：**

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.*;

/**
 * 模型二：单 Reactor 多线程
 *
 * 一个 Reactor 线程负责接收连接和 I/O 读写，
 * 业务逻辑（decode → compute → encode）交给线程池处理。
 * 优点：大部分场景够用，业务处理不阻塞 I/O。
 * 缺点：并发量大时，单个 Reactor 线程负责所有事件的接收和分发，容易成瓶颈。
 *
 * 使用方式：启动后用 telnet localhost 8080 测试
 */
public class SingleReactorMultiThread implements Runnable {

    private final Selector selector;
    private final ServerSocketChannel serverChannel;

    public SingleReactorMultiThread(int port) throws IOException {
        selector = Selector.open();
        serverChannel = ServerSocketChannel.open();
        serverChannel.socket().bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);
        serverChannel.register(selector, SelectionKey.OP_ACCEPT, new Acceptor());
        System.out.println("[单Reactor多线程] 启动，监听端口: " + port);
    }

    @Override
    public void run() {
        try {
            while (!Thread.interrupted()) {
                selector.select();
                Set<SelectionKey> keys = selector.selectedKeys();
                Iterator<SelectionKey> it = keys.iterator();
                while (it.hasNext()) {
                    dispatch(it.next());
                    it.remove();
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void dispatch(SelectionKey key) {
        Runnable handler = (Runnable) key.attachment();
        if (handler != null) {
            handler.run();
        }
    }

    // ==================== Acceptor ====================
    class Acceptor implements Runnable {
        @Override
        public void run() {
            try {
                SocketChannel channel = serverChannel.accept();
                if (channel != null) {
                    System.out.println("[Acceptor] 新连接: " + channel.getRemoteAddress());
                    new Handler(selector, channel);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // ==================== Handler ====================
    // read / send 在 Reactor 线程执行
    // decode → compute → encode 提交到线程池
    // ================================================
    static class Handler implements Runnable {

        /** 业务线程池：所有 Handler 共享 */
        private static final ExecutorService WORKER_POOL =
                Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

        private final SocketChannel channel;
        private final SelectionKey key;
        private final Selector selector;
        private final ByteBuffer readBuffer = ByteBuffer.allocate(1024);
        private final ByteBuffer writeBuffer = ByteBuffer.allocate(1024);

        private static final int READING = 0, PROCESSING = 1, SENDING = 2;
        private volatile int state = READING;

        public Handler(Selector selector, SocketChannel channel) throws IOException {
            this.selector = selector;
            this.channel = channel;
            channel.configureBlocking(false);
            key = channel.register(selector, SelectionKey.OP_READ, this);
        }

        @Override
        public void run() {
            try {
                if (state == READING) {
                    read();
                } else if (state == SENDING) {
                    send();
                }
            } catch (IOException e) {
                closeChannel();
            }
        }

        private void read() throws IOException {
            readBuffer.clear();
            int n = channel.read(readBuffer);
            if (n == -1) {
                closeChannel();
                return;
            }
            readBuffer.flip();
            byte[] data = new byte[readBuffer.remaining()];
            readBuffer.get(data);
            String request = new String(data).trim();
            System.out.println("[Handler] 收到: " + request);

            state = PROCESSING;

            // ★ 关键区别：业务逻辑提交到线程池执行
            WORKER_POOL.submit(() -> {
                // decode → compute → encode (在线程池线程中执行)
                String response = process(request);

                writeBuffer.clear();
                writeBuffer.put(response.getBytes());
                writeBuffer.flip();

                state = SENDING;
                key.interestOps(SelectionKey.OP_WRITE);
                selector.wakeup(); // 唤醒 Reactor 线程来处理写事件
            });
        }

        private void send() throws IOException {
            channel.write(writeBuffer);
            if (!writeBuffer.hasRemaining()) {
                state = READING;
                key.interestOps(SelectionKey.OP_READ);
            }
        }

        /** 模拟耗时业务处理 */
        private String process(String request) {
            try {
                Thread.sleep(10); // 模拟业务耗时
            } catch (InterruptedException ignore) {}
            return "ECHO: " + request + "\n";
        }

        private void closeChannel() {
            try {
                key.cancel();
                channel.close();
            } catch (IOException ignore) {}
        }
    }

    // ==================== 启动入口 ====================
    public static void main(String[] args) throws IOException {
        int port = 8080;
        SingleReactorMultiThread reactor = new SingleReactorMultiThread(port);
        new Thread(reactor, "Reactor").start();
    }
}
```

#### **多 Reactor 多线程：**

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.*;

/**
 * 模型三：主从 Reactor 多线程 (Netty 默认模型)
 *
 * mainReactor  → 专门负责 accept 连接 (对应 Netty 的 BossGroup)
 * subReactor[] → 负责 I/O 读写，每个有独立的 Selector 和线程 (对应 Netty 的 WorkerGroup)
 * ThreadPool   → 负责业务逻辑
 *
 * 优点：能扛住几十万连接的高并发。
 * 缺点：实现复杂度更高，资源管理要求也更高。
 *
 * 使用方式：启动后用 telnet localhost 8080 测试
 */
public class MainSubReactorMultiThread {

    private final ServerSocketChannel serverChannel;
    private final Selector mainSelector;          // 主 Reactor 的 Selector
    private final SubReactor[] subReactors;       // 从 Reactor 数组
    private final ExecutorService workerPool;     // 业务线程池
    private int nextSubReactor = 0;

    public MainSubReactorMultiThread(int port, int subReactorCount) throws IOException {
        serverChannel = ServerSocketChannel.open();
        serverChannel.socket().bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);

        mainSelector = Selector.open();
        serverChannel.register(mainSelector, SelectionKey.OP_ACCEPT);

        // 创建多个从 Reactor，每个拥有独立的 Selector
        subReactors = new SubReactor[subReactorCount];
        for (int i = 0; i < subReactorCount; i++) {
            subReactors[i] = new SubReactor(i);
        }

        workerPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        System.out.println("[主从Reactor] 启动，监听端口: " + port
                + "，从Reactor数量: " + subReactorCount);
    }

    /** 启动所有 Reactor */
    public void start() {
        // 启动所有从 Reactor 线程
        for (SubReactor sub : subReactors) {
            new Thread(sub, "SubReactor-" + sub.index).start();
        }
        // 启动主 Reactor 线程
        new Thread(this::runMainReactor, "MainReactor").start();
    }

    // ==================== 主 Reactor ====================
    // 职责：只负责 accept 新连接，然后分配给从 Reactor
    // ===================================================
    private void runMainReactor() {
        try {
            while (!Thread.interrupted()) {
                mainSelector.select();
                Set<SelectionKey> keys = mainSelector.selectedKeys();
                Iterator<SelectionKey> it = keys.iterator();
                while (it.hasNext()) {
                    SelectionKey key = it.next();
                    it.remove();
                    if (key.isAcceptable()) {
                        accept();
                    }
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /** accept 新连接，通过 Round-Robin 轮询分配给从 Reactor */
    private void accept() throws IOException {
        SocketChannel channel = serverChannel.accept();
        if (channel != null) {
            channel.configureBlocking(false);
            System.out.println("[MainReactor] 新连接: " + channel.getRemoteAddress()
                    + " → 分配给 SubReactor-" + nextSubReactor);

            SubReactor subReactor = subReactors[nextSubReactor];
            nextSubReactor = (nextSubReactor + 1) % subReactors.length;
            subReactor.registerChannel(channel);
        }
    }

    // ==================== 从 Reactor ====================
    // 职责：负责已连接 Channel 的 I/O 读写
    // ===================================================
    class SubReactor implements Runnable {

        final int index;
        final Selector selector;
        /** 待注册的新连接队列（线程安全，解决跨线程注册问题） */
        private final ConcurrentLinkedQueue<SocketChannel> pendingChannels = new ConcurrentLinkedQueue<>();

        SubReactor(int index) throws IOException {
            this.index = index;
            this.selector = Selector.open();
        }

        /** 由主 Reactor 调用，将新连接放入队列 */
        void registerChannel(SocketChannel channel) {
            pendingChannels.add(channel);
            selector.wakeup(); // 唤醒 select() 阻塞，让它去处理新注册
        }

        @Override
        public void run() {
            try {
                while (!Thread.interrupted()) {
                    selector.select(1000);

                    // 处理待注册的新连接
                    SocketChannel ch;
                    while ((ch = pendingChannels.poll()) != null) {
                        ch.register(selector, SelectionKey.OP_READ,
                                new SubReactorHandler(ch, selector, workerPool, index));
                    }

                    // 处理 I/O 事件
                    Set<SelectionKey> keys = selector.selectedKeys();
                    Iterator<SelectionKey> it = keys.iterator();
                    while (it.hasNext()) {
                        SelectionKey key = it.next();
                        it.remove();
                        Runnable handler = (Runnable) key.attachment();
                        if (handler != null) {
                            handler.run(); // 在从 Reactor 线程执行 I/O 读写
                        }
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // ==================== Handler ====================
    // I/O 读写在从 Reactor 线程执行
    // 业务逻辑（decode → compute → encode）在线程池执行
    // ================================================
    static class SubReactorHandler implements Runnable {

        private final SocketChannel channel;
        private final SelectionKey key;
        private final Selector selector;
        private final ExecutorService workerPool;
        private final int subReactorIndex;
        private final ByteBuffer readBuffer = ByteBuffer.allocate(1024);
        private final ByteBuffer writeBuffer = ByteBuffer.allocate(1024);

        private static final int READING = 0, PROCESSING = 1, SENDING = 2;
        private volatile int state = READING;

        SubReactorHandler(SocketChannel channel, Selector selector,
                          ExecutorService workerPool, int subReactorIndex) throws IOException {
            this.channel = channel;
            this.selector = selector;
            this.workerPool = workerPool;
            this.subReactorIndex = subReactorIndex;
            channel.configureBlocking(false);
            key = channel.register(selector, SelectionKey.OP_READ, this);
        }

        @Override
        public void run() {
            try {
                if (state == READING) {
                    read();
                } else if (state == SENDING) {
                    send();
                }
            } catch (IOException e) {
                closeChannel();
            }
        }

        private void read() throws IOException {
            readBuffer.clear();
            int n = channel.read(readBuffer);
            if (n == -1) {
                closeChannel();
                return;
            }
            readBuffer.flip();
            byte[] data = new byte[readBuffer.remaining()];
            readBuffer.get(data);
            String request = new String(data).trim();
            System.out.println("[SubReactor-" + subReactorIndex + "] 收到: " + request);

            state = PROCESSING;

            // ★ 业务逻辑丢给线程池
            workerPool.submit(() -> {
                // decode → compute → encode
                String response = process(request);

                writeBuffer.clear();
                writeBuffer.put(response.getBytes());
                writeBuffer.flip();

                state = SENDING;
                key.interestOps(SelectionKey.OP_WRITE);
                selector.wakeup(); // 唤醒从 Reactor 线程来处理写事件
            });
        }

        private void send() throws IOException {
            channel.write(writeBuffer);
            if (!writeBuffer.hasRemaining()) {
                state = READING;
                key.interestOps(SelectionKey.OP_READ);
            }
        }

        /** 模拟耗时业务处理 */
        private String process(String request) {
            try {
                Thread.sleep(10);
            } catch (InterruptedException ignore) {}
            return "ECHO: " + request + "\n";
        }

        private void closeChannel() {
            try {
                key.cancel();
                channel.close();
            } catch (IOException ignore) {}
        }
    }

    // ==================== 启动入口 ====================
    public static void main(String[] args) throws IOException {
        int port = 8080;
        int subReactorCount = Runtime.getRuntime().availableProcessors();
        MainSubReactorMultiThread reactor = new MainSubReactorMultiThread(port, subReactorCount);
        reactor.start();
    }
}
```



## Proactor



Reactor 走的是同步非阻塞的路子，应用程序收到“数据就绪”的通知后，得自己去读数据。Proactor 走的是异步非阻塞，操作系统帮你把数据读好了再通知你，应用程序直接处理就行。





![](https://pic.code-nav.cn/mianshiya/question_picture/1843904816956411905/5DFX38wk_ejTiZSOLrQ_mianshiya.webp)





# Netty 为什么不用JDK 原生的 NIO，要自己封装一层？

回答：JDK 的 NIO 有几个坑。==一是 Selector 的epoll 空轮询 bug,CPU 飙到100%，JDK 修了好几个版本都没彻底解决，Netty自己做了规避。==二是 ByteBuffer 不支持池化，每次分配回收开销大。三是 API设计反人类，读写要手动 flip，容易出错。Netty 封装了 EventLoop、ByteBuf、Pipeline 这些抽象，写起来简单多了。

## Netty 解决 Selector 空轮询的细节

JDK 的 Selector 空轮询是个老问题了，根因在 Linux 内核的 epoll实现上。

正常来说调 Selector.select（）应该阻塞到有事件就绪才返回，但在某些情况下，比如对端 RST、连接被中断，epoll 会触发一个 POLLHUP 或 POLLERR 事件，JDK 的 Selector 没正确处理这类事件，结果 select（）直接返回 O，外面的 while循环就疯狂空转。

Netty 的解决思路很实用：在 NioEventLoop 里加了一个计数器，记录 select（）连续返回0的次数。一旦发现短时间内连续空轮询超过 SELECTOR_AUTO_REBUILD_THRESHOLD，默认 512，就判定当前 Selector 已经废了，然后把所有 Channel 重新注册到一个全新的 Selector 上，老的直接关掉。

## selectedKeys 优化

JDK 的 Selector 内部用 HashSet 存放就绪的 SelectionKey， Netty 觉得不够快，直接用反射把它替换成了自己实现的SelectedSelectionKeySet，底层就是一个数组。好处很直接：数组顺序遍历对CPU 缓存友好，add 操作也只是keys［size++］一句赋值，不用像 HashSet 那样算 hash、处理冲突、扩容。在IO 密集型场景下，每次 select 可能返回上千个就绪key，这点优化积少成多效果显著。

## ByteBuf XJit ByteBuffer

JDK 原生的 ByteBuffer 有几个硬伤：读写共用一个指针，每次切换读写都得 flip（，忘了就出 Bug；容量固定，不能动态扩缩容；没有池化机制，高并发场景频繁创建回收 GC 压力大。

Netty的 ByteBuf 把这些痛点全解决了：读写分离用两个指针 readerlndex 和 writerIndex，不用 flip；支持动态扩容；内置PooledByteBufAllocator 做内存池化，类似jemalloc的思路，把内存分成 Chunk、Page、SubPage 多级管理，线程内还有 ThreadLocal 级别的缓存，高并发下分配释放几乎无锁竞争。





# Netty 核心组件

## **Channel**

对网络连接的抽象，代表一个到远端的 socket 连接。所有 I/O 操作（读、写、连接、绑定）都通过 Channel 进行。



一个 Channel 在注册之后就和一个特定的 NioEventLoop 绑定了，这个绑定关系在整个 Channel 的生命周期内不会变。这意味着一个 Channel 上的所有！/0 操作都在同一个线程里执行，天然线程安全，不需要加锁。

一个 NioEventLoop 可以同时管理成百上千个Channel。默认 workerGroup 的线程数是 CPU 核心数的2倍，所以一个 16核的机器，workerGroup 就是32个线程，每个线程管理一批 Channel。

```java
Channel channel = ctx.channel();
channel.writeAndFlush(Unpooled.copiedBuffer("Hello", CharsetUtil.UTF_8));
```

------

## EventLoop / EventLoopGroup

事件循环，负责处理 Channel 上的所有 I/O 事件。一个 EventLoop 绑定一个线程，一个 EventLoopGroup 包含多个 EventLoop。 相当于一个Reactor/Selector，说白了，EventLoop 的主要作用实际就是责监听网络事件并调用事件处理器进行相关I/O操作（读写）的处理。



每个 NioEventLoop 内部跑的是一个 for 死循环，每轮循环做三件事：

1. ﻿﻿﻿调用 Selector.select（） 拿到就绪的I/O事件
2. ﻿﻿﻿处理这些I/O 事件，比如 read、write、connect
3. ﻿﻿﻿执行任务队列里的任务，包括普通任务和定时任务



```java
EventLoopGroup bossGroup = new NioEventLoopGroup(1);    // 接受连接
EventLoopGroup workerGroup = new NioEventLoopGroup();     // 处理 I/O
```

------

## ChannelHandler（ChannelInboundHandler / ChannelOutboundHandler）

业务逻辑的核心。

当 Channel披创建时，它会被自动地分配到它专属的 ChannelPipeline. 一个 Channel包含一个ChanneiPipeline . ChannelPipeline 为 ChanneiHandler 的容器，一个 pipeline 上可以有多ChannelHandler.

我们可以在 ChannelPipeline 上通过 addLast（）方法添加一个或者多个ChannelHandler（一个数据或者事件可能会被多个Handler 处理）。当一个channelHandler 处理完之后就将数据交给下一个 ChannelHandler.

当 ChannelHandler被添加到的 ChanneiPipeline 它得到一个ChannelHandlerContext，它代表一个ChannelHandler 和 ChannelPipeline 之间的“绑定”.ChannelPipeline 通过 ChannelHandlerContext 来间接管理 ChannelHandler。

InboundHandler 处理入站事件（读数据），OutboundHandler 处理出站事件（写数据）。

```java
public class MyHandler extends ChannelInboundHandlerAdapter {
    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        ByteBuf buf = (ByteBuf) msg;
        System.out.println(buf.toString(CharsetUtil.UTF_8));
        ctx.writeAndFlush(Unpooled.copiedBuffer("OK", CharsetUtil.UTF_8));
    }
}
```

------

## **ChannelPipeline**

Handler 的有序链表，每个 Channel 都有一个 Pipeline。入站事件从头到尾流动，出站事件从尾到头流动。

```java
pipeline.addLast("decoder", new StringDecoder());
pipeline.addLast("encoder", new StringEncoder());
pipeline.addLast("handler", new MyHandler());
```

------

## **ChannelHandlerContext**

Handler 与 Pipeline 之间的桥梁，可以通过它触发事件传播、获取 Channel、读写数据。

它是每个 Handler 被添加到 Pipeline 时自动创建的上下文对象，**一个 Handler 对应一个 ctx**。它的作用有三个层面：

```java
ctx.fireChannelRead(msg);   // 传给下一个 InboundHandler

ctx.write(msg);             // 从当前 Handler 位置开始，往前找下一个 OutboundHandler
ctx.channel().write(msg);   // 从 Pipeline 的尾部开始，经过所有 OutboundHandler
```

------

## ChannelFuture（操作执行结果）

Netty 的 I/O 操作都是异步的，调用后立即返回一个 ChannelFuture，代表操作的未来结果。你可以通过它等待完成或注册回调。

```java
// 同步等待：阻塞直到操作完成
ChannelFuture f = b.bind(8080).sync();

// 异步回调：操作完成时触发
ChannelFuture f = channel.writeAndFlush(msg);
f.addListener((ChannelFutureListener) future -> {
    if (future.isSuccess()) {
        System.out.println("写入成功");
    } else {
        future.cause().printStackTrace();
    }
});

// 等待 Channel 关闭
f.channel().closeFuture().sync();
```



## **ByteBuf**

Netty 自己的字节缓冲区，替代 JDK 的 ByteBuffer。支持读写双指针、引用计数、零拷贝。

```java
ByteBuf buf = Unpooled.buffer(128);
buf.writeBytes("Hello".getBytes());
byte[] bytes = new byte[buf.readableBytes()];
buf.readBytes(bytes);
```

------

## **Bootstrap / ServerBootstrap**

启动引导类。Bootstrap 用于客户端，ServerBootstrap 用于服务端，负责组装上述所有组件。

```java
ServerBootstrap b = new ServerBootstrap();
b.group(bossGroup, workerGroup)
 .channel(NioServerSocketChannel.class)
 .childHandler(new ChannelInitializer<SocketChannel>() {
     @Override
     protected void initChannel(SocketChannel ch) {
         ch.pipeline().addLast(new MyHandler());
     }
 });
ChannelFuture f = b.bind(8080).sync();
```

------

**组件之间的关系简图：**

```
ServerBootstrap
  ├── EventLoopGroup (boss)  ──> 接受连接
  ├── EventLoopGroup (worker) ──> 处理 I/O
  └── Channel
        └── ChannelPipeline
              ├── Handler1 (decoder)
              ├── Handler2 (encoder)
              └── Handler3 (业务逻辑)
                    └── 通过 ChannelHandlerContext 交互
                          └── 读写 ByteBuf
```

这就是 Netty 的核心骨架：**Bootstrap 组装一切，EventLoop 驱动事件，Channel 承载连接，Pipeline 串联 Handler，Handler 处理业务，ByteBuf 承载数据**。

# Netty的零拷贝

传统方式把一个文件发送到网络，要经历 4 次数据拷贝和 4次用户态/内核态的上下文切换：

Netty 里体现在 4个方面：

﻿﻿﻿1. **FileRegion 接口：底层调用 sendfile 系统调用，把文件数据直接从磁盘送到网卡，不经过用户空间，典型的 OS级零拷贝。**

**传统文件传输过程（4 次拷贝）：**

```text
磁盘 → 内核缓冲区 → 用户空间缓冲区 → Socket 内核缓冲区 → 网卡
         拷贝1           拷贝2              拷贝3           拷贝4
```

数据要先从内核拷到用户空间，程序看一眼，再拷回内核发出去。中间两次完全是浪费。

**FileRegion（sendfile 系统调用）：**

```text
磁盘 →[DMA拷贝]→ 内核页缓存 →[CPU拷贝]→ Socket缓冲区 →[DMA拷贝]→ 网卡
共：2次DMA拷贝 + 1次CPU拷贝

中间那一步 CPU 要把数据从内核页缓存拷到 Socket 缓冲区，因为网卡的 DMA 只知道从 Socket 缓冲区取数据。 但如果网卡支持 scatter-gather DMA：

磁盘 →[DMA拷贝]→ 内核页缓存 →[DMA直接读]→ 网卡
共：2次DMA拷贝 + 0次CPU拷贝
```

数据根本不经过用户空间，内核直接把文件数据送到网卡。



﻿﻿﻿2. **CompositeByteBuf：把多个 ByteBuf 组合成一个逻辑上的缓冲区，拼接协议头和协议体的时候不需要真的拷贝数据，指针拼一拼就行了。**

**内存中的样子：**

```text
传统方式：
  header [AAAA]  body [BBBBBBBB]  →  new [AAAABBBBBBBB]  // 真拷贝

CompositeByteBuf：
  header [AAAA]  body [BBBBBBBB]
    ↑               ↑
    └── composite 持有两个指针，逻辑上当一个整体读 ──┘
```



3. ﻿**ByteBuf 的 Direct Buffer 和包装/切分操作：Direct Buffer 用堆外内存，省掉了堆内到对外那一次拷贝。wrappedBuffer 包装字节数组、slice 切分大 ByteBuf，都是共享底层内存，0次拷贝**

```text
HeapBuffer（堆内）发数据的过程：
  堆内存 → 堆外临时缓冲区 → 内核缓冲区 → 网卡
             多了这一步拷贝！

DirectBuffer（堆外）发数据的过程：
  堆外内存 → 内核缓冲区 → 网卡
  省掉了堆内到堆外那一次
```



﻿﻿﻿4.**内存映射文件：通过 MappedByteBuffer 把文件映射到内存，读写文件跟操作内存一样，不需要额外的数据复制，再封装成 Netty 的 ByteBuf 就能高效传输。**

mmap 的思路，它把文件映射到进程的虚拟地址空间，用户态和内核态共享同一块物理内存，读文件就跟读内存一样，不需要从内核拷到用户态。适合需要随机读取或者反复读取文件内容的场景，比如数据库的索引文件、消息队列的 commitlog。RocketMQ 的消息存储就大量使用 mmap。

```text
磁盘 →[DMA拷贝]→ 内核页缓存/用户空间（共享同一块物理内存）
                        ↓
                   [CPU拷贝] ← 这一步是要的
                        ↓
                  Socket缓冲区 →[DMA拷贝]→ 网卡
```

用户空间和内核空间通过页表映射**指向同一块物理内存**，用户态可以直接读写文件内容，不需要 read() 系统调用把数据拷过来。

核心区别

**sendfile：用户态碰不到数据。** 数据从文件直接到网络，程序没法看、没法改。就像快递从仓库直发客户，你经手都不经手。

**mmap：用户态能碰到数据，但不需要拷贝。** 内核和用户态看的是同一块物理内存，程序可以随便读、随便改、随机访问。就像仓库开了一扇窗，你站在窗口就能直接拿东西，不用搬到自己房间。


## 更详细描述
### 先看传统方式：read + write

```
应用程序要把一个文件发送到网络：

read(file_fd, buf, len);     // 从文件读到用户缓冲区
write(socket_fd, buf, len);  // 从用户缓冲区写到 Socket

实际发生了什么：

磁盘 → 内核页缓存(Page Cache) → 用户态缓冲区 → Socket缓冲区 → 网卡
         拷贝1(DMA)              拷贝2(CPU)      拷贝3(CPU)    拷贝4(DMA)

4次拷贝，2次用户态↔内核态切换
```

```
详细的切换过程：

用户态：调用 read()
  ────── 切换到内核态 ──────
内核态：DMA 把磁盘数据拷贝到 Page Cache（拷贝1）
        CPU 把 Page Cache 拷贝到用户缓冲区（拷贝2）
  ────── 切换回用户态 ──────
用户态：调用 write()
  ────── 切换到内核态 ──────
内核态：CPU 把用户缓冲区拷贝到 Socket 缓冲区（拷贝3）
        DMA 把 Socket 缓冲区发送到网卡（拷贝4）
  ────── 切换回用户态 ──────

中间那两次 CPU 拷贝（拷贝2和拷贝3）纯粹是浪费
数据经过用户态绕了一圈，用户程序根本没修改它
```

### sendfile：跳过用户态

```c
// 一个系统调用搞定
sendfile(socket_fd, file_fd, &offset, len);
```

```
sendfile 的数据流（Linux 2.4 之前）：

磁盘 → 内核页缓存(Page Cache) → Socket缓冲区 → 网卡
         拷贝1(DMA)              拷贝2(CPU)     拷贝3(DMA)

3次拷贝，数据全程不经过用户态
省了一次 CPU 拷贝和两次上下文切换
```

注意：**你的纠正是对的**。数据是从内核的 Page Cache 拷贝到 Socket 缓冲区，不是"文件描述符传到 Socket 描述符"——描述符只是个整数编号，数据是在它们背后的内核缓冲区之间流动的。

### Linux 2.4+ 的 sendfile：真正的零拷贝

```
Linux 2.4 之后，如果网卡支持 scatter-gather DMA：

磁盘 → 内核页缓存(Page Cache) ─ ─ ─ ─ ─ ─ → 网卡
         拷贝1(DMA)           不拷贝数据      拷贝2(DMA)
                              只传递内存地址
                              和长度信息给
                              Socket缓冲区
```

这里的关键优化：**Socket 缓冲区里不再存放实际数据，只存放一个指向 Page Cache 的指针（内存地址 + 数据长度）**。网卡的 DMA 引擎根据这个指针，直接从 Page Cache 读数据发出去。

```
Page Cache:  [实际数据在这里]
                  ↑
Socket缓冲区: [指针: 地址=0xABCD, 长度=4096]
                  ↑
网卡DMA:     根据指针直接去 Page Cache 读

全程只有 2 次 DMA 拷贝，0 次 CPU 拷贝
这才是真正意义上的"零拷贝"（零次 CPU 参与的拷贝）
```

### sendfile 和 mmap 不是一回事

```
mmap 的做法：

把内核 Page Cache 映射到用户态地址空间
用户态和内核态"看到"的是同一块物理内存

用户态地址空间
┌─────────────────┐
│  mmap映射区域     │──┐
└─────────────────┘  │  指向同一块物理内存
                     │
内核 Page Cache      │
┌─────────────────┐  │
│  文件数据         │←─┘
└─────────────────┘

使用方式：
  byte[] mapped = mmap(file_fd, ...);   // 映射
  write(socket_fd, mapped, len);        // 写到 Socket

数据流：
  磁盘 → Page Cache → Socket缓冲区 → 网卡
          (DMA)     (CPU拷贝,但没有    (DMA)
                     用户态↔内核态
                     之间的拷贝)
                     
                     
                     
第1次系统调用：mmap()
  用户态 → 内核态    ← 第1次切换
  内核：建立 Page Cache 到用户地址空间的映射
  内核态 → 用户态    ← 第2次切换

（用户态拿到了映射后的地址，可以像访问普通内存一样读写文件内容）

第2次系统调用：write(socket_fd, mapped_addr, len)
  用户态 → 内核态    ← 第3次切换
  内核：从 Page Cache 拷贝到 Socket 缓冲区（CPU拷贝1次）
       DMA 把 Socket 缓冲区发到网卡
  内核态 → 用户态    ← 第4次切换

总计：4 次上下文切换，1 次 CPU 拷贝                     
```

对比：

```
只有1个系统调用：sendfile(socket_fd, file_fd, ...)
  用户态 → 内核态    ← 第1次切换
  内核：全部搞定（Page Cache → Socket缓冲区 → 网卡）
  内核态 → 用户态    ← 第2次切换

总计：2 次上下文切换
```

```
                  CPU拷贝次数    上下文切换    用户态能否修改数据
传统 read+write      2次          4次            能
mmap + write         1次          4次            能（共享内存）
sendfile(2.4前)      1次          2次            不能
sendfile(2.4后)      0次          2次            不能
```

**sendfile 比 mmap 快的原因：更少的上下文切换，而且 2.4 之后可以做到零次 CPU 拷贝。但 sendfile 只能用于"文件直接发网络"这种场景，数据不经过用户态，你没法修改它。mmap 的优势是映射后用户态可以读写数据。**

## 回到 Netty

```java
// Netty 的 FileRegion，底层就是 sendfile
FileRegion region = new DefaultFileRegion(fileChannel, 0, fileChannel.size());
channel.writeAndFlush(region);

// 适用场景：文件直接传输，不需要修改内容
// 比如：静态文件服务器、文件下载
// 不适用：需要对文件内容编码、加密、压缩的场景
```

所以总结一下：sendfile 不是基于 mmap 实现的，它们是两种独立的零拷贝技术。sendfile 是内核内部直接搬数据（或者只传指针），全程不涉及用户态；mmap 是把内核内存映射到用户态，减少拷贝但不减少上下文切换。
# Netty的Reactor
如果是多线程的情况下。及在netty的场景，Reactor。每个从proactor注册的fd是不一样的，可是epoll不是返回所有就绪的fd吗？那这些所有就绪的fd是怎么分配给不同的Reactor的？
这个问题说明你对 epoll 的理解还差一个关键认知。

## 先纠正一点：不是共享一个 epoll

你的困惑来自一个隐含的错误假设：**你以为所有 EventLoop 共用一个 epoll 实例**，然后需要把就绪的 fd 分配给不同的 EventLoop。

实际上不是这样。**每个 EventLoop 有自己独立的 Selector，底层就是各自独立的 epoll 实例**。

```
WorkerGroup（假设 3 个 EventLoop）：

EventLoop-0:  自己的 epoll 实例 (epoll_fd = 5)
              监听: fd=101(连接A), fd=104(连接D), fd=107(连接G)

EventLoop-1:  自己的 epoll 实例 (epoll_fd = 6)
              监听: fd=102(连接B), fd=105(连接E), fd=108(连接H)

EventLoop-2:  自己的 epoll 实例 (epoll_fd = 7)
              监听: fd=103(连接C), fd=106(连接F), fd=109(连接I)
```

每个 epoll 实例只会返回**注册在自己身上的**就绪 fd。EventLoop-0 调用 `epoll_wait(5, ...)` 只可能拿到 101、104、107 中就绪的，绝对拿不到 102。

所以根本不存在"就绪 fd 怎么分配给不同 EventLoop"的问题——**它们从一开始就分开了**。

## 那 fd 是什么时候分开的？

在 BossGroup accept 新连接的那一刻：

```
客户端连接进来，内核分配 fd=101

BossGroup 的 EventLoop-0:
  → selector.select() 返回，发现 OP_ACCEPT
  → serverChannel.accept()，拿到新的 SocketChannel (fd=101)
  → 从 WorkerGroup 里用 round-robin 选一个 EventLoop
  → 比如选中了 EventLoop-1
  → 把 fd=101 注册到 EventLoop-1 的 Selector（epoll 实例）上
```

关键代码简化后是这样：

```java
// BossGroup 的处理逻辑（ServerBootstrapAcceptor）
public void channelRead(ChannelHandlerContext ctx, Object msg) {
    Channel child = (Channel) msg;  // 新连接

    // 从 WorkerGroup 里 round-robin 选一个 EventLoop
    // next() 内部就是个计数器取模：eventLoops[idx++ % length]
    EventLoop childEventLoop = workerGroup.next();

    // 把这个 Channel 注册到选中的 EventLoop 的 Selector 上
    childEventLoop.register(child);
}
```

`register` 内部做的事：

```java
// 简化后的注册逻辑
void register(Channel channel) {
    // 如果当前线程不是目标 EventLoop 的线程，
    // 就把注册操作封装成任务提交过去
    if (eventLoop.inEventLoop()) {
        doRegister(channel);
    } else {
        eventLoop.execute(() -> doRegister(channel));
    }
}

void doRegister(Channel channel) {
    // 底层就是：epoll_ctl(自己的epoll_fd, EPOLL_CTL_ADD, channel的fd, events)
    selectionKey = channel.javaChannel()
        .register(this.selector, 0, channel);  // 注册到"我的"Selector
}
```

## 所以完整的画面是这样的

```
                    BossGroup
                   ┌─────────────────────┐
                   │ EventLoop-0          │
                   │   epoll_fd = 3       │
                   │   监听: server_fd    │
                   │   只关注 OP_ACCEPT   │
                   └─────────┬───────────┘
                             │
                     新连接来了，accept 得到 fd
                     round-robin 选一个 Worker
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    WorkerGroup
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ EventLoop-0  │  │ EventLoop-1  │  │ EventLoop-2  │
  │ epoll_fd = 5 │  │ epoll_fd = 6 │  │ epoll_fd = 7 │
  │              │  │              │  │              │
  │ fd: 101,104  │  │ fd: 102,105  │  │ fd: 103,106  │
  │              │  │              │  │              │
  │ 各自独立地：  │  │ 各自独立地：  │  │ 各自独立地：  │
  │ epoll_wait() │  │ epoll_wait() │  │ epoll_wait() │
  │ 只返回自己   │  │ 只返回自己   │  │ 只返回自己   │
  │ 注册的fd     │  │ 注册的fd     │  │ 注册的fd     │
  └──────────────┘  └──────────────┘  └──────────────┘
     线程-0在跑        线程-1在跑        线程-2在跑
```

三个 EventLoop 是三个线程，各自跑自己的 `for(;;) { select(); processKeys(); }` 循环，互不干扰，也不需要任何同步。

## 另外，还是 Reactor 不是 Proactor

我注意到你一直在说"从 Proactor"。Netty 用的是 **Reactor** 模式。区别在于：

- **Reactor**：内核告诉你"数据准备好了"，你自己调 `read()` 去读。Netty 就是这样。
- **Proactor**：内核帮你把数据读完了，直接给你结果。Windows 的 IOCP 是这个模式。

你看 Netty 的代码里，`processSelectedKey` 之后还要自己调 `channel.read(byteBuf)` 去读数据，这就是 Reactor 的特征——内核只通知，不帮你干活。




# Netty的从Reactor是只负责从buffer里读写数据吗？那处理读到的数据，或者即将写入的数据呢？要怎么处理？

## Worker EventLoop 不只是读写，它默认把所有事都干了

从读数据到业务处理到写回去，默认都在同一个 EventLoop 线程里完成：

```
EventLoop 线程-2 的一次完整处理流程：

epoll_wait() 返回，fd=105 可读
  │
  ▼
从 Socket 读数据到 ByteBuf          ← I/O 操作
  │
  ▼
pipeline.fireChannelRead(byteBuf)    ← 触发 Pipeline
  │
  ▼
Handler1: 解码器，字节 → 对象        ← 还是 EventLoop 线程在干
  │
  ▼
Handler2: 业务逻辑处理              ← 还是 EventLoop 线程在干
  │
  ▼
Handler3: 编码器，对象 → 字节        ← 还是 EventLoop 线程在干
  │
  ▼
channel.writeAndFlush()             ← 写回 Socket，还是这个线程
  │
  ▼
回到 epoll_wait() 等下一个事件
```

**全程都是 EventLoop 线程-2 在执行，没有切换线程。**

## 这就带来一个问题

如果你的业务逻辑很慢——比如查数据库、调远程接口、做大量计算——会发生什么？

```
EventLoop-2 管着 500 个连接

处理连接B的请求：
  → 读数据          1ms
  → 解码            1ms
  → 业务逻辑：查数据库  200ms  ← 卡在这里！
  → 编码            1ms
  → 写回            1ms

这 200ms 里，EventLoop-2 管的另外 499 个连接全部得等着
因为这个线程被你的业务逻辑占住了，没法回去 epoll_wait()
```

这就是为什么 Netty 文档反复强调：**不要在 EventLoop 线程里做阻塞操作**。

## 解决办法：把耗时业务扔给业务线程池

有两种方式。

### 方式一：在 Pipeline 里指定独立的线程池

```java
// 创建一个专门跑业务逻辑的线程池
EventExecutorGroup businessGroup = new DefaultEventExecutorGroup(16);

ch.pipeline().addLast(new MyDecoder());
// 关键：第一个参数传 businessGroup
ch.pipeline().addLast(businessGroup, new MyBusinessHandler());
ch.pipeline().addLast(new MyEncoder());
```

这样处理流程就变了：

```
EventLoop 线程-2：
  → 读数据
  → 解码（MyDecoder）
  → 到 MyBusinessHandler 了，发现它绑定了 businessGroup
  → 把任务丢给 businessGroup 的某个线程
  → EventLoop 线程-2 解放了，立刻回去 epoll_wait()

businessGroup 线程-5：
  → 执行 MyBusinessHandler（查数据库，200ms）
  → 执行完了，调 ctx.writeAndFlush(response)
  → 编码、写出（可以在 business 线程里完成，也可以回到 EventLoop）
```

### 方式二：自己在 Handler 里提交到线程池

```java
public class MyBusinessHandler extends ChannelInboundHandlerAdapter {

    private static final ExecutorService pool = Executors.newFixedThreadPool(16);

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        // 当前在 EventLoop 线程，立刻把活甩出去
        pool.submit(() -> {
            // 这里是业务线程池的线程
            String result = queryDatabase(msg);  // 慢操作
            
            // 写回去，Netty 内部会确保写操作回到 EventLoop 线程
            ctx.writeAndFlush(result);
        });
        // EventLoop 线程立刻返回，继续处理其他连接
    }
}
```

## 完整的分工图

```
                EventLoop 线程（快，不能阻塞）
               ┌─────────────────────────────┐
               │                             │
网卡 → 内核 → epoll → read → 解码器 →  ─ ─ ─│─ → 业务线程池（可以慢）
                                             │     ┌──────────────┐
               │                             │     │ 查数据库      │
               │                             │     │ 调 RPC       │
               │                             │     │ 复杂计算      │
               │                             │     └──────┬───────┘
               │                             │            │
         write ← 编码器 ← ← ← ← ← ← ← ← ←│← ← ← ← ← ┘
               │                             │     ctx.writeAndFlush()
               └─────────────────────────────┘
```

## 总结

Worker EventLoop 默认负责**全链路**：读、解码、业务处理、编码、写，全在一个线程里串行执行。这对于轻量级业务（比如网关转发、协议代理）是最高效的，零线程切换。但如果业务逻辑耗时，你需要自己把耗时操作丢给业务线程池，让 EventLoop 线程赶紧回去服务其他连接。


# Netty的具体调用路径

## Netty Pipeline 调用链路

### 整体结构

Pipeline 是一个双向链表，头尾是 Netty 内置的：

```
HeadContext ↔ HandlerA ↔ HandlerB ↔ HandlerC ↔ TailContext
```

- `HeadContext`：既是 InboundHandler 也是 OutboundHandler，负责实际的 Socket I/O
- `TailContext`：是 InboundHandler，兜底处理未消费的入站消息

### 入站链路（数据进来）

```
Socket 收到字节
    ↓
NioEventLoop 检测到读事件
    ↓
调用 HeadContext.channelRead()
    ↓  ctx.fireChannelRead(msg)
ByteToMessageDecoder.channelRead()    // 把 ByteBuf 解码成 Java 对象
    ↓  ctx.fireChannelRead(msg)
你的业务 Handler.channelRead()        // 处理业务逻辑
    ↓  ctx.fireChannelRead(msg)（如果继续传递）
TailContext.channelRead()             // 兜底，释放未处理的消息
```

关键点：每个入站 Handler 通过 `ctx.fireChannelRead(msg)` 把消息传给链表中**下一个** InboundHandler。如果不调用，链路就断了。

### 出站链路（数据出去）

假设你在业务 Handler 中调用 `ctx.writeAndFlush(response)`：

```
你的业务 Handler 调用 ctx.writeAndFlush(response)
    ↓  从当前位置往 head 方向找 OutboundHandler
MessageToByteEncoder.write()          // 把 Java 对象编码成 ByteBuf
    ↓  ctx.write(msg, promise)
HeadContext.write()                   // 调用底层 Unsafe 写入 Socket 缓冲区
    ↓
HeadContext.flush()                   // 真正把数据刷到网络
    ↓
Socket 发出字节
```

关键点：每个出站 Handler 通过 `ctx.write(msg, promise)` 把消息传给链表中**上一个**（靠近 head 的）OutboundHandler。

### 一次完整的 RPC 调用示例

假设 Pipeline 这样配置：

```java
pipeline.addLast(new ProtocolDecoder());    // Inbound
pipeline.addLast(new ProtocolEncoder());    // Outbound
pipeline.addLast(new BusinessHandler());    // Inbound + Outbound
```

实际链表：

```
HeadContext ↔ ProtocolDecoder ↔ ProtocolEncoder ↔ BusinessHandler ↔ TailContext
```

**收到请求：**

```
Socket
  → HeadContext.channelRead()
    → ProtocolDecoder.channelRead()     // ByteBuf → ProtocolMessage
      → BusinessHandler.channelRead()   // 处理请求，生成响应
        ↑ ProtocolEncoder 是 Outbound，入站方向直接跳过它
```

**发送响应（BusinessHandler 中调用 `ctx.writeAndFlush(response)`）：**

```
BusinessHandler 调用 ctx.writeAndFlush(response)
  → ProtocolEncoder.write()             // ProtocolMessage → ByteBuf
    ↑ ProtocolDecoder 是 Inbound，出站方向直接跳过它
      → HeadContext.write()             // 写入 Socket
        → HeadContext.flush()           // 刷出去
          → Socket
```

### 核心规则

入站事件（`channelRead`、`channelActive` 等）只经过 `InboundHandler`，从 head 往 tail 走。

出站事件（`write`、`flush`、`connect` 等）只经过 `OutboundHandler`，从 tail 往 head 走。

Pipeline 中两种 Handler 交替排列没关系，Netty 内部会自动跳过不匹配的 Handler，只找对应方向的下一个。


## channelRead 和 fireChannelRead的区别是？

## 区别

`channelRead` 是你**重写的方法**，定义"收到数据时做什么"。

`fireChannelRead` 是你**调用的方法**，作用是"把数据传给下一个 InboundHandler 的 `channelRead`"。

## 例子

```java
public class HandlerA extends ChannelInboundHandlerAdapter {
    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        // 这里是 HandlerA 自己处理数据的逻辑
        System.out.println("HandlerA 收到: " + msg);

        // 把数据传给下一个 InboundHandler 的 channelRead
        ctx.fireChannelRead(msg);
    }
}
```

## 调用关系

```
HandlerA.channelRead()  ← Netty 调用
    ↓
ctx.fireChannelRead(msg)  ← 你主动调用
    ↓
HandlerB.channelRead()  ← Netty 调用
    ↓
ctx.fireChannelRead(msg)  ← 你主动调用
    ↓
HandlerC.channelRead()  ← Netty 调用
```

简单说，`fireChannelRead` 就是触发下一个 Handler 的 `channelRead`。如果你不调用 `fireChannelRead`，消息就停在当前 Handler，后面的 Handler 收不到。