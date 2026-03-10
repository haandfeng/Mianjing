

主要日志： undolog    redolog   binlog 




**步骤 1：执行语句（进入 InnoDB）**
• MySQL Server 层解析语句、生成执行计划，进入 InnoDB。
• InnoDB 准备插入数据，**先生成一份 undo log**。

---
**步骤 2：修改内存中的数据页（Buffer Pool）**
• 插入数据被写入到 Buffer Pool（内存中的页结构）中，**尚未写入磁盘**

----
**步骤 3：生成 redo log（WAL）**
• **写 redo log buffer（内存）**
• 内容是对数据页的物理修改，比如：某页第 20 字节插入了某个值。
• **时机：修改数据页之后立即生成**

---
**步骤 4：执行 COMMIT 提交事务**
这是关键环节，涉及到 redo log 和 binlog 的真正写入。
**4.1 写 binlog**
• MySQL Server 层记录一条逻辑日志：insert into users ...
• Binlog 是逻辑日志：不关心页结构，只记录 SQL 或变更后的行内容（根据格式）。
**4.2 触发两阶段提交机制（2PC）**
为了确保 **binlog 和 redo log 的一致性**，MySQL 使用“两阶段提交”：
**阶段一：准备阶段**
• redo log 持久化到磁盘（写入并 fsync()），并打上 prepare 标记
**阶段二：提交阶段**
• binlog 持久化到磁盘
• redo log 写入 commit 标记，表示事务提交完成

![](https://cdn.xiaolincoding.com//picgo/image-20240725231904598.png)


| **阶段**      | **undo log** | **redo log**    | **binlog** |
| ----------- | ------------ | --------------- | ---------- |
| 执行语句时       | 写入（用于回滚）     | 写入 buffer       | 无          |
| 修改内存页       | -            | 写入 buffer       | 无          |
| 执行 COMMIT 前 | 无            | flush + prepare | 写入（磁盘）     |
| COMMIT 时    | 无            | commit 标记写入     | 已写入        |
| 事务提交后       | undo 等待清理    | 已完成             | 已完成        |