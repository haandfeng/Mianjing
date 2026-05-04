---
title: MySQL日志与两阶段提交
type: topic
updated: 2026-05-04
---

# MySQL日志与两阶段提交

> Undo（回滚 + MVCC）/ Redo（崩溃恢复）/ Binlog（主从复制 + 时点恢复）三日志各司其职；commit 时 redo 与 binlog 用 2PC 协调写入。

## 高频问法
- "MySQL 除了 binlog 还有什么日志？三种 log 写入顺序" — [[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]
- "redo / binlog 分别在哪一层（server / 引擎）？" — [[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]
- "binlog 提交失败了怎么办？两阶段提交怎么保证一致" — [[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]
- "为什么 InnoDB 是先写日志再写数据（WAL）" — [[蔚来/xhs]]、[[快手/支付方向/快手日常实习面经]]

## 答题骨架

### 1. 三种 log 各自的角色
| 日志 | 所属层 | 作用 | 关键属性 |
|---|---|---|---|
| Undo log | InnoDB（引擎层） | 事务回滚 + MVCC 版本链 | 逻辑日志，记录"反向操作" |
| Redo log | InnoDB（引擎层） | Crash recovery（保证已提交事务的修改不丢） | 物理日志，记录页的物理修改 |
| Binlog | Server 层 | 主从复制、时点恢复（PITR） | 逻辑日志（statement/row/mixed） |

### 2. 一条 INSERT 的完整流程
1. **Server 层** 解析 SQL，进入 InnoDB
2. InnoDB 先生成 **undo log**（用于回滚）
3. 修改 **Buffer Pool** 中的数据页（内存，未落盘）
4. 写 **redo log buffer**（内存，记录页的物理修改）—— WAL：先日志后数据
5. **COMMIT** 阶段触发 2PC：
   - **Prepare**：redo log fsync 到磁盘，打 prepare 标记
   - **Commit**：写 binlog 并 fsync，再给 redo log 写 commit 标记

### 3. 两阶段提交（2PC）解决什么
- 没有 2PC 的话：先 redo 后 binlog，binlog 写之前崩了 → 主库恢复有这条，从库没有
- 反过来先 binlog 后 redo，redo 写之前崩了 → 从库有，主库恢复后没有
- **2PC 解法**：crash 恢复时若 redo 是 prepare 状态，去看 binlog 有没有这条
  - binlog 完整 → 提交（写 commit 标记）
  - binlog 不完整 → 回滚

### 4. WAL（Write-Ahead Logging）核心思想
- 数据页改完不一定立刻刷盘（脏页），但 redo log 一定先落盘
- 崩溃后 InnoDB 拿 redo log 重做，把丢失的脏页改动补回内存→刷盘
- 顺序写日志比随机写数据页快得多

### 5. binlog 三种格式
- **statement**：记录原 SQL，binlog 小但有不确定函数（NOW()、UUID）问题
- **row**：记录行变化，最准确，AUTO-INC 锁场景下要用 row
- **mixed**：默认 statement，遇到不确定函数自动切换 row

## 易错点 & 追问
- "redo 是循环写、固定大小；binlog 是追加写、不删旧文件（按时间/大小切分）"
- redo 是物理日志（"某页 offset 写入某字节"），binlog 是逻辑日志（"某行被改成什么"）
- crash recovery 只看 redo log；做主从复制和回滚到时点用 binlog
- 2PC 的失败兜底：恢复时未提交的事务 redo + undo 一起回滚

## 深入阅读
- 原始专栏 [[后端技术专栏/Mysql日志]]
- 真题来源 [[快手/支付方向/快手日常实习面经]]、[[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]、[[蔚来/xhs]]
