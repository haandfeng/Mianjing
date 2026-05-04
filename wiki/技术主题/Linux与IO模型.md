---
title: Linux与IO模型
type: topic
updated: 2026-05-04
---

# Linux与IO模型

> select / poll / epoll 是 IO 多路复用三代演进；零拷贝靠 sendfile / mmap / splice 跳过用户态拷贝；SRE 排查靠 top / vmstat / iostat / ss / netstat 一套组合拳。

## 高频问法
- "select / poll / epoll 区别；epoll 数据结构（红黑树 + 就绪链表）" — [[TT/TT SRE]]、[[京东/京东零售一面]]
- "BIO / NIO / AIO；Reactor / Proactor" — [[TT/TT SRE]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]
- "零拷贝（read+write / sendfile / mmap / splice）" — [[TT/TT SRE 牛客]]
- "Linux 排查命令：top / vmstat / iostat / ss / strace / netstat" — [[TT/TT SRE]]、[[TT/TT SRE 牛客]]
- "进程 vs 线程 vs 协程" — [[TT/TT SRE 牛客]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/字节跳动中国商业化一面面经]]
- "网站访问慢怎么排查；502 怎么排查" — [[TT/TT SRE 牛客]]
- "CPU 占用不高但系统慢怎么排查" — [[TT/TT SRE 牛客]]
- "Redis 用什么 IO 模型" — [[京东/京东零售一面]]

## 答题骨架

### 1. 5 种 IO 模型
| 模型 | 阻塞 | 同步 | 场景 |
|---|---|---|---|
| 阻塞 IO | 阻塞 | 同步 | 最基础 socket |
| 非阻塞 IO | 不阻塞 | 同步 | 轮询 |
| IO 多路复用 | 阻塞在 select/epoll | 同步 | 高并发服务器 |
| 信号驱动 IO | 不阻塞 | 同步 | 较少使用 |
| 异步 IO（AIO） | 不阻塞 | 异步 | Windows IOCP |

### 2. select / poll / epoll
| | select | poll | epoll |
|---|---|---|---|
| fd 上限 | 1024（fd_set） | 系统限制 | 系统限制 |
| 存储 | bitmap | 链表 | 红黑树 + 就绪链表 |
| 就绪发现 | 遍历全部 | 遍历全部 | O(1) 内核回调 |
| 用户/内核拷贝 | 每次全量拷贝 fd_set | 每次全量拷贝 | 只在 epoll_ctl 时 |
| 复杂度 | O(N) | O(N) | O(1) 通知，O(logN) 注册 |

- epoll **红黑树**：高效注册 / 删除监听的 fd
- epoll **就绪链表**：内核回调时把就绪 fd 放进链表，用户 epoll_wait 直接拿
- LT（水平触发）vs ET（边缘触发）：ET 只在状态变化时通知一次，必须一次读完所有数据；性能高但写法严格

### 3. BIO / NIO / AIO 对比
- BIO：1 连接 1 线程，read/write 阻塞
- NIO：Selector 多路复用，1 线程管 N 连接
- AIO：内核完成 IO 后回调（Linux 实现弱，多用 epoll 模拟）

### 4. Reactor 模式
- 单 Reactor 单线程：Redis 6 之前
- 单 Reactor 多线程：accept 单线程，业务线程池
- 主从 Reactor 多线程：BossGroup（accept）+ WorkerGroup（IO），Netty 主推
- Reactor = 内核就绪通知，应用自己去读
- Proactor = 内核读完通知应用（Windows IOCP 真正实现）

### 5. Redis 的 IO 模型
- IO 多路复用 + **单线程事件循环**
- Linux 上底层 epoll
- 6.0+ 引入多线程网络读写，命令执行仍单线程
- 单线程为何快：纯内存 + 无锁 + epoll；100K+ QPS 不在话下

### 6. 零拷贝（Zero-Copy）
**传统 read + write**：
1. 磁盘 → 内核页缓存（DMA）
2. 内核页缓存 → 用户态 buffer（CPU 拷贝）
3. 用户态 buffer → 内核 socket buffer（CPU 拷贝）
4. socket buffer → 网卡（DMA）
- 4 次切换 + 2 次 CPU 拷贝

**sendfile**：
- 内核态直接 内核页缓存 → socket buffer，跳过用户态
- 仍需 CPU 拷贝从页缓存到 socket buffer

**sendfile + DMA scatter/gather**（Linux 2.4+）：
- 真零拷贝：把页缓存的"文件描述符 + 偏移"发给 socket buffer，DMA 直接把数据从页缓存搬到网卡
- 全程无 CPU 拷贝，2 次切换

**mmap**：
- 内核页缓存映射到用户态虚拟内存，避免一次拷贝
- 适合频繁小读写场景

**Netty 的零拷贝**还包括应用层：
- CompositeByteBuf 多个 buffer 逻辑合并
- slice / duplicate 共享底层数组
- DirectByteBuf 堆外内存

### 7. 进程 / 线程 / 协程
| | 进程 | 线程 | 协程 |
|---|---|---|---|
| 调度 | 内核 | 内核 | 用户态 |
| 切换开销 | 高 | 中（陷内核） | 极低（函数调用级） |
| 栈大小 | 1-8 MB | 1-8 MB | KB 级 |
| 资源 | 独立内存空间 | 共享进程堆 | 共享线程栈外的所有 |
| 数量 | 千级 | 千级 | 百万级 |

- Go goroutine M:N 模型；Java 21 虚拟线程

### 8. SRE 常用命令
- `top` / `htop`：实时 CPU / 内存 / load / 任务数
- `vmstat`：r（运行队列）b（D 状态）wa（IO wait）si/so（swap）
- `iostat -x 1`：%util、await、r/s w/s
- `iotop`：哪个进程在大量 IO
- `free -h`：内存可用 + swap 使用
- `ss -tlnp` / `netstat -anp`：端口监听 / 连接状态
- `ss -lnt | grep 8080`：看 Recv-Q（accept 队列堆积）
- `dig` / `nslookup`：DNS
- `ping` / `traceroute`：网络连通
- `strace -p <pid>`：跟踪系统调用
- `perf top` / `perf record`：热点函数
- `jstack` / `jmap` / `jstat`：JVM 进程

### 9. CPU 不高但系统慢的排查
- top 看 wa（iowait）高吗？b 列（D 状态）多吗？→ IO 等待
- vmstat 看 r、b、wa、si/so → 区分 IO / swap
- iostat 看 %util、await → 磁盘瓶颈
- ss / netstat → 网络连接堆积
- strace / 火焰图 → 锁等待、外部依赖

### 10. 502 排查 SOP
1. `tail -n 50 /var/log/nginx/error.log | grep upstream` 找类型：connect refused / timed out / prematurely closed / no live upstreams
2. 直连上游：`ss -tlnp | grep 8080`，`curl -v http://127.0.0.1:8080/health`
3. 看连接状态分布：`ss -ant | grep 8080 | awk '{print $1}' | sort | uniq -c` → SYN_SENT 多 / ESTABLISHED 堆积 / TIME_WAIT 爆
4. 看 accept 队列：`ss -lnt | grep 8080`，Recv-Q 接近 Send-Q（默认 net.core.somaxconn=128）说明队列满
5. 修复：合理超时（不要把 proxy_connect_timeout 调到 500s）+ 调大 backlog + Tomcat accept-count + Nginx upstream keepalive

## 易错点 & 追问
- "select 用 bitmap，poll 用链表，epoll 用红黑树 + 就绪链表"
- ET 模式必须循环读到 EAGAIN，否则下一个事件不来
- 真零拷贝必须是 sendfile + DMA scatter/gather
- Java NIO 在 Linux 上 Selector 底层是 epoll
- TIME_WAIT 大量积累会耗尽端口，调 `net.ipv4.tcp_tw_reuse=1`

## 深入阅读
- 原始专栏 [[后端技术专栏/Netty]]（select/poll/epoll、零拷贝、Reactor 章节）
- 真题来源 [[TT/TT SRE]]、[[TT/TT SRE 二面]]、[[TT/TT SRE 牛客]]
