---
title: Redis数据结构与大Key
type: topic
updated: 2026-05-04
---

# Redis数据结构与大Key

> 5 大数据结构 + 编码自动切换；ZSet = 跳表 + 哈希；大 key 是阻塞主线程的元凶，删除用 UNLINK。

## 高频问法
- "Redis 5 种数据结构，分别什么场景；ZSet 怎么实现" — [[腾讯/数据平台/我的腾讯一面]]、[[字节/财经/字节财经一面]]
- "ZSet 大 Key 会带来什么问题，怎么优化" — [[字节/财经/字节财经一面]]、[[腾讯/数据平台/我的腾讯一面]]
- "Redis 单线程为什么这么快" — [[字节/中国商业化/字节跳动中国商业化一面面经]]
- "DEL 一个 key 时间复杂度" — [[字节/国际商业化/面经记录_国际商业化创业_3.9]]
- "Redis 内存清理方式（过期键 + 淘汰策略）" — [[字节/国际商业化/面经记录_国际商业化创业_3.9]]

## 答题骨架

### 1. 5 大类型 + 编码切换
| 类型 | 底层编码 | 切换条件 | 典型场景 |
|---|---|---|---|
| String | SDS | — | 缓存对象、计数器、分布式锁 |
| List | quicklist（listpack 节点 + 双向链表） | 老版本 ziplist + linkedlist | 队列、栈、最近浏览 |
| Hash | listpack / hashtable | <128 entry 且每值 <64B 用 listpack | 存对象字段 |
| Set | intset / hashtable | 全是整数且 <512 用 intset | 标签、好友集合、UV |
| ZSet | listpack / skiplist + dict | <128 entry 且每值 <64B 用 listpack | 排行榜、延时任务、范围查询 |

### 2. ZSet = 跳表 + 哈希双结构
- **跳表**按 score 排序，O(logN) 插入 / 删除 / 范围查询
- **哈希表**存 member → score，支持 O(1) `ZSCORE`
- 同时维护两个结构：插入 / 删除整体 O(logN)
- 跳表节点的 `span` 字段记录跨度，`ZRANK` 累加 span 算排名 → O(logN)
- 选跳表不选红黑树：实现简单、范围查询天然友好（叶子链表）、插入删除局部修改不旋转

### 3. 大 Key 问题与优化
- **危害**：DEL 阻塞主线程；网络传输延迟；持久化 / 主从同步压力大
- **判断**：`redis-cli --bigkeys`、`MEMORY USAGE key`
- **优化方向**：
  - **拆分**：ZSet 1000w → 按业务维度拆成多个 ZSet
  - **改结构**：超大 Hash 拆 1000 个小 Hash（用 hashKey + suffix）
  - **删除用 UNLINK**（4.0+）：异步释放内存，不阻塞主线程
  - **渐进式删除**：按段 `ZREMRANGEBYRANK` / `HSCAN + HDEL`
- 业界经验：单 key 大小不超过 10KB；元素数控制在万级以内

### 4. DEL 时间复杂度
| 类型 | DEL 复杂度 |
|---|---|
| String | O(1) |
| List | O(N) |
| Hash | O(N) field 数 |
| Set | O(N) |
| ZSet | O(N·logN) |

- 大 key 必须用 `UNLINK` 把释放丢到后台线程

### 5. Redis 单线程为何快
1. **纯内存操作**（纳秒级）
2. **I/O 多路复用**（epoll）+ 单线程事件循环 → 没有锁竞争和上下文切换
3. **优化的内部数据结构**（listpack / intset 等紧凑编码）
4. **RESP 协议简单**，序列化/反序列化开销低
- 6.0+ 引入多线程 I/O：网络读写多线程，命令执行仍单线程

### 6. 内存清理：过期键 + 淘汰策略
- **过期键删除**：惰性删除（访问时才清）+ 定期删除（每 100ms 抽样删过期，超过 25% 再抽一批）
- **maxmemory 满**：8 种淘汰策略
  - `noeviction`（默认报错）
  - `allkeys-lru / lfu / random`
  - `volatile-lru / lfu / random / ttl`
- 最常用 `allkeys-lru`

## 易错点 & 追问
- "ziplist" 在新版本（7.0+）已被 listpack 替代
- ZSet 不直接用红黑树是历史原因 + 范围查询便利
- `UNLINK` 不是异步删除整张表，单 key 大也是异步释放该 key 的内存
- LRU 是近似 LRU（采样实现），不是严格 LRU；LFU 4.0 引入

## 深入阅读
- 原始专栏 [[专栏/后端/Redis]]
- 真题来源 [[腾讯/数据平台/我的腾讯一面]]、[[字节/财经/字节财经一面]]、[[快手/支付方向/快手日常实习面经]]、[[字节/国际商业化/面经记录_国际商业化创业_3.9]]
