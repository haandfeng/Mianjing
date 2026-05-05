# MySQL 调优与八股总览

> 本文是 MySQL 这块面试入口，按「索引 → EXPLAIN → Join → 范式 → MVCC / 事务 → 锁 → 三大日志 → 两阶段提交 → 调优实战」一条主线写成，新人系统学习 + 面试速查都用它。
>
> 主题文章：[[MySQL索引与执行计划]]、[[MySQL-MVCC与隔离级别]]、[[MySQL日志与两阶段提交]]、[[InnoDB事务与锁]]
>
> 真题来源：[[快手/支付方向/我的快手支付二面]]、[[快手/支付方向/快手日常实习面经]]、[[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]、[[字节/国际广告/字节跳动中国商业化一面面经]]、[[字节/国际广告/面经记录_国际商业化创业_3.9]]、[[字节/字节财经一面]]、[[蔚来/xhs]]、[[Cider面经/1]]、[[心潮无限往年面经/1]]、[[其他/昆仑数智/3]]、[[其他/银河智学]]

---

## 一、索引

### 1.1 为什么 InnoDB 用 B+ 树而不用 B 树 / Hash

- **B+ 树**非叶子节点只存 key + 指针，不存数据 → 单页能装更多 key → 树更矮 → 磁盘 IO 次数更少（典型 3~4 层就能容纳上千万行）。
- **B+ 树**叶子节点之间有双向链表 → 范围查询、`ORDER BY`、`LIMIT N, M` 可以顺序扫描，不需要回到根重新走。
- B 树非叶子节点也存数据，每页能装的 key 更少，IO 多。
- Hash 索引只支持等值，不支持范围、不支持前缀匹配、不支持排序。

### 1.2 聚簇索引 vs 二级索引 vs 回表

- **聚簇索引**（主键索引）：叶子节点存**完整行数据**。一张表只有一个聚簇索引。
- **二级索引**（非聚簇索引）：叶子节点存「索引列 + 主键值」；查到主键后再回到聚簇索引取整行 = **回表**。
- 没主键时 InnoDB 选第一个 NOT NULL UNIQUE 列；都没有就用 6 字节隐藏 row_id。

```
        聚簇索引（主键 = 1)               二级索引（name = 'tom')
        ┌───────────────┐                   ┌─────────────────┐
        │ id=1, name=…, │                   │ name='tom', id=1│
        │ age=…         │ ◄────回表 (id=1)──┤                 │
        └───────────────┘                   └─────────────────┘
```

### 1.3 联合索引最左匹配

- 索引 `(A, B, C)`：能走 `A`、`A,B`、`A,B,C`；**不能直接走** `B` 或 `B,C`。
- 等值条件优化器会自动调整顺序：`WHERE B=x AND A=y AND C=z` 实际能完全命中 `(A,B,C)`。
- **范围查询后续列失效**：`WHERE A>1 AND B=2`，B 在 `A` 范围扫描中是无序的，B 列走不了索引（仍可在过滤阶段用）。

### 1.4 覆盖索引（Using index）

- `SELECT` 的字段都在索引里 → 不用回表，`Extra` 显示 `Using index`。
- 经典优化：把高频查询的字段加进联合索引。
- 警惕 `SELECT *`，会破坏覆盖索引。

### 1.5 索引下推（ICP）

- MySQL 5.6+，针对联合索引的非最左字段，把过滤动作**下推到存储引擎层**，少回表。
- `(name, age)` 上 `WHERE name LIKE 'L%' AND age > 30`：5.5 时代会先按 `name LIKE 'L%'` 扫一批，逐行回表再判断 age；5.6+ 直接在二级索引里就过滤了 age，再回表只取通过的行。

### 1.6 索引失效场景

| 场景 | 例子 | 解释 |
|---|---|---|
| 跳过最左列 | `(A,B,C)` 上只查 `WHERE B=x` | 违反最左前缀 |
| 范围后列失效 | `WHERE A>1 AND B=2` | 范围后 B 无序 |
| 函数包裹列 | `WHERE YEAR(create_time)=2024` | 索引存原值，函数计算后失配 |
| 隐式类型转换 | `phone` 是 varchar 但写 `WHERE phone=138...`（漏引号） | MySQL 转换会忽略索引 |
| 左模糊 | `LIKE '%abc'` | B+ 树有序前缀匹配，左模糊扫不出 |
| OR 连非索引列 | `WHERE A=1 OR D=2`（D 没索引） | 必然全表扫，除非两侧都有索引（index merge） |
| `!=` / `<>` / `NOT IN` | 选择性差时优化器直接全表扫 | — |
| `IS NULL` / `IS NOT NULL` | 老版本 NULL 不走索引（5.7+ 已优化） | — |

### 1.7 哪些字段适合建索引

- **高区分度**：user_id、order_id、phone（区分度 > 90%）。
- **频繁出现在 WHERE / JOIN / ORDER BY** 里的列。
- **不适合**：性别、状态枚举（区分度低，加了反而拖慢写入和占空间）、超长字符串（要建前缀索引）。
- 写多读少的表慎加索引；每个索引都会让 INSERT / UPDATE / DELETE 多写一棵 B+ 树。

---

## 二、EXPLAIN 执行计划解读

| 列 | 关注点 |
|---|---|
| `id` | 子查询编号，相同 id 看 type，不同 id 看顺序 |
| `select_type` | SIMPLE / PRIMARY / SUBQUERY / DERIVED / UNION |
| `table` | 当前查询的表 |
| `partitions` | 命中的分区 |
| `type` | **命中级别**，从好到差：`system > const > eq_ref > ref > range > index > ALL`，看到 `ALL` 就是全表扫 |
| `possible_keys` | 候选索引 |
| `key` | 实际用到的索引 |
| `key_len` | 索引长度，能判断联合索引用了几列 |
| `ref` | 跟索引比较的列或常量 |
| `rows` | 优化器估算扫描行数（不是精确值） |
| `filtered` | 服务层再过滤后剩余比例 |
| `Extra` | **关键诊断信息**，下表 |

### Extra 常见取值

- `Using index`：覆盖索引，**不回表**，最优。
- `Using where`：过滤发生在 server 层。
- `Using index condition`：索引下推（ICP）生效。
- `Using filesort`：额外排序（**优化目标：用索引顺序代替**）。
- `Using temporary`：用了临时表（GROUP BY、UNION 常见，性能差）。
- `Using join buffer (Block Nested Loop)`：被驱动表没索引在 BNL。

---

## 三、Join 优化

### 3.1 三种 Join 算法

- **Index Nested-Loop Join (NLJ)**：被驱动表的 join 列**有索引** → 走 B+ 树，复杂度 `O(N · logM)`。
- **Block Nested-Loop Join (BNL)**：被驱动表**无索引** → 驱动表批量加载到 join_buffer，扫被驱动表整表与 buffer 比对。
  - 扫描行数 ≈ N + M
  - **比对次数** ≈ N × M（这部分在内存中，单次比对很快）
  - 真正可怕的是 join_buffer **装不下**驱动表时，会**多次扫描**被驱动表。
- **Hash Join**（MySQL 8.0.18+）：build 表先建 hash table，probe 表查找，等值 join 利器。

### 3.2 优化方向

- 给被驱动表的 join 列加索引 → 自动从 BNL 升级到 NLJ。
- 让**小表（过滤后行数少）**做驱动表，MySQL 优化器一般会自动选，但复杂查询可以用 `STRAIGHT_JOIN` 强指定。
- 调大 `join_buffer_size`，减少 BNL 多次扫描。
- 避免在 join 列上有函数 / 类型不一致。

---

## 四、范式（来自 [[字节/字节财经一面]]）

| 范式 | 要求 | 例子 |
|---|---|---|
| 1NF | 列必须**原子**，不可再分 | 不能把电话写成 "138xxx;010-xxx" |
| 2NF | 在 1NF 基础上，消除**部分依赖**（针对组合主键） | 订单表中 order_id + product_id 联合主键，product_name 只依赖 product_id → 拆出商品表 |
| 3NF | 消除**传递依赖** | 员工表里 dept_id, dept_name；dept_name 通过 dept_id 才能确定 → 拆出部门表 |
| BCNF | 所有决定因子必须是**候选键** | 工程上很少要求到这一层 |

工程上一般做到 3NF，再按读写性能**反范式**（冗余字段）：例如订单冗余商品快照、用户冗余昵称头像，避免每次 join。

---

## 五、MVCC 与隔离级别

### 5.1 三种读异常 + 四种隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | InnoDB 实现 |
|---|---|---|---|---|
| READ UNCOMMITTED | ✗ | ✗ | ✗ | 不加锁直接读 |
| READ COMMITTED | ✓ | ✗ | ✗ | MVCC，每次 SELECT 重生成 Read View |
| **REPEATABLE READ**（默认） | ✓ | ✓ | 大部分场景已解决 | MVCC（首次 SELECT 生成 RV） + Next-Key Lock |
| SERIALIZABLE | ✓ | ✓ | ✓ | 所有 SELECT 都加共享锁 |

- **脏读**：读到其他事务**未提交**的修改。
- **不可重复读**：同一事务两次读同一行结果不同（其他事务 update 已提交）。
- **幻读**：同一事务两次范围查询行数不同（其他事务 insert 已提交）。

### 5.2 MVCC 三件套

每行隐藏列：
- `trx_id`：最后修改它的事务 ID。
- `roll_pointer`：指向 undo log 中的旧版本。

每次 update 不覆盖原数据，旧版本写入 undo log，roll_pointer 串成**版本链**。

**Read View** 字段：
- `m_ids`：创建 RV 时**活跃**（已启动未提交）的事务 ID 列表。
- `min_trx_id`：m_ids 最小值。
- `max_trx_id`：**下一个**将分配的 trx_id（不是 m_ids 最大值，常考点）。
- `creator_trx_id`：自己。

### 5.3 可见性判断

```
拿到行后看 trx_id：
  trx_id < min_trx_id           → 已提交 → 可见
  trx_id ≥ max_trx_id           → RV 之后才启动 → 不可见
  min_trx_id ≤ trx_id < max_trx_id：
      在 m_ids 中（活跃中）       → 不可见
      不在 m_ids（已提交）        → 可见

不可见 → 沿 roll_pointer 找上一版本，重复判断。
```

### 5.4 RC vs RR 的关键区别 = Read View 创建时机

- **RC**：每个 SELECT 语句都重新生成 RV → 看到最新已提交，所以会出现**不可重复读**。
- **RR**：事务**第一次** SELECT 时生成 RV，后续整个事务复用 → 视图固定，重复读结果一致。

### 5.5 RR 下幻读怎么处理

- **快照读**（普通 `SELECT`）：MVCC 看的是事务启动时的快照，期间别人 insert 也读不到 → 解决幻读。
- **当前读**（`SELECT ... FOR UPDATE` / `UPDATE` / `DELETE`）：用 **Next-Key Lock = 记录锁 + 间隙锁**，锁住范围内不允许 insert → 解决幻读。
- **边角无法解决**：先快照读 → 别的事务 insert 并提交 → 自己再 `UPDATE` 那条新插入行 → 该行 trx_id 变成自己 → 下次快照读就能看到 → "诱发的幻读"。

### 5.6 START TRANSACTION 不等于 RV 已生成

- `BEGIN` / `START TRANSACTION` 后，**第一条 SELECT** 才真正启动事务、生成 RV。
- 想立即生成：`START TRANSACTION WITH CONSISTENT SNAPSHOT`。

---

## 六、锁体系

### 6.1 全局锁
- `FLUSH TABLES WITH READ LOCK`：用于全库备份；其间不允许 DML（可重复读 + MVCC 备份不需要这个锁）。

### 6.2 表级锁
- **表锁**：`LOCK TABLES t1 READ, t2 WRITE`，粗粒度，影响范围大。
- **元数据锁（MDL）**：CRUD 加 MDL 读锁；DDL 加 MDL 写锁。读写互斥，写写互斥。
- **意向锁（IS / IX）**：表级，标记表里有行级共享锁 / 独占锁。**目的：快速判断表里是否有记录被加锁**，加表锁时不用遍历全表。
- **AUTO-INC 锁**：插入自增列时持有；5.1.22 起改为更轻的「自增锁模式」。

### 6.3 行级锁（InnoDB）

- **记录锁（Record Lock）**：锁某一行。
- **间隙锁（Gap Lock）**：锁某段开区间，**禁止 insert**，用于解决幻读。
- **临键锁（Next-Key Lock）= 记录锁 + 间隙锁**：左开右闭，是 RR 的默认行锁。
- **插入意向锁（Insert Intention Lock）**：插入时获取，间隙锁存在则等待。

### 6.4 共享锁 vs 独占锁
- `SELECT ... LOCK IN SHARE MODE` → 共享锁（S）。
- `SELECT ... FOR UPDATE` → 独占锁（X）。
- DML（UPDATE / DELETE / INSERT）自动加 X 锁。

---

## 七、三大日志

| 日志 | 所属层 | 作用 | 关键属性 |
|---|---|---|---|
| **Undo log** | InnoDB（引擎层） | 事务**回滚** + MVCC 版本链 | 逻辑日志，记录"反向操作" |
| **Redo log** | InnoDB（引擎层） | **崩溃恢复**（保证已提交事务的修改不丢） | 物理日志，记录页的物理修改 |
| **Binlog** | Server 层 | 主从复制、时点恢复（PITR） | 逻辑日志（statement / row / mixed） |

### 7.1 一条 INSERT 的完整流程

1. **Server 层**解析 SQL，进入 InnoDB。
2. InnoDB 先生成 **undo log**（用于回滚）。
3. 修改 **Buffer Pool** 中的数据页（内存，未落盘）。
4. 写 **redo log buffer**（内存，记录页的物理修改）—— **WAL：先日志后数据**。
5. **COMMIT** 阶段触发 2PC：
   - **Prepare**：redo log fsync 到磁盘，打 prepare 标记。
   - **Commit**：写 binlog 并 fsync，再给 redo log 写 commit 标记。

### 7.2 两阶段提交（2PC）解决什么

> 来自 [[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]。

如果没有 2PC：
- 先 redo 后 binlog，binlog 写之前崩了 → 主库恢复有这条，从库没有 → 主从不一致。
- 先 binlog 后 redo，redo 写之前崩了 → 从库有，主库恢复后没有 → 主从不一致。

**2PC 解法**：crash 恢复时若 redo 是 prepare 状态，去看 binlog：
- binlog 完整 → 提交（写 commit 标记）。
- binlog 不完整 → 回滚。

### 7.3 WAL（Write-Ahead Logging）

- 数据页改完不一定立刻刷盘（脏页），但 redo log 一定先落盘。
- 崩溃后 InnoDB 拿 redo log 重做，把丢失的脏页改动补回内存→刷盘。
- 顺序写日志比随机写数据页快得多。

### 7.4 binlog 三种格式

- **statement**：记录原 SQL，binlog 小，但有不确定函数（NOW()、UUID）问题。
- **row**：记录行变化，最准确；AUTO-INC 锁场景下要用 row。
- **mixed**：默认 statement，遇到不确定函数自动切换 row。

### 7.5 redo vs binlog 关键差异

| 维度 | Redo log | Binlog |
|---|---|---|
| 所属 | InnoDB 引擎层 | Server 层 |
| 文件结构 | **循环写**、固定大小 | **追加写**、按时间或大小切分 |
| 内容 | 物理日志（某页 offset 写入某字节） | 逻辑日志（某行被改成什么） |
| 用途 | 崩溃恢复 | 主从复制、时点恢复 |

---

## 八、调优实战

### 8.1 慢查询定位

```sql
-- 开启慢查询日志（生产环境一般默认开）
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;          -- 超过 1 秒记录
SET GLOBAL log_queries_not_using_indexes = ON;
```

工具：
- `mysqldumpslow` / `pt-query-digest`：聚合慢日志，按总耗时排序。
- `EXPLAIN` + `SHOW WARNINGS`：看优化器实际选择。
- `EXPLAIN ANALYZE`（8.0.18+）：实际执行 + 计时。
- `SHOW PROFILE`（要开 profiling）：看 SQL 各阶段耗时。

### 8.2 SQL 改写常用套路

- 用 `EXISTS` 替代 `IN`（小表驱动大表）。
- 用 `JOIN` 替代相关子查询。
- `LIMIT N, M` 大偏移时改成「主键定位 + LIMIT」：`WHERE id > last_id ORDER BY id LIMIT 20`。
- `COUNT(*)` 优于 `COUNT(列)`（不需判 NULL）。
- 避免 `SELECT *`，按需取列以保留覆盖索引可能。

### 8.3 库表设计建议

- 主键用自增 BIGINT，避免随机插入导致 B+ 树页分裂。
- 长字符串（varchar > 255）建前缀索引或单独建索引表。
- 大字段（TEXT / BLOB）拆出附属表。
- 时间字段用 `DATETIME` 或 `BIGINT`（Unix ms），不要用字符串。
- 字符集用 `utf8mb4`，避免 emoji 入库报错。

### 8.4 InnoDB 关键参数

```
innodb_buffer_pool_size = 物理内存 60%~70%   # 缓存数据页 + 索引页，最重要
innodb_log_file_size = 1G                    # redo log 文件大小，足够大避免频繁切换
innodb_flush_log_at_trx_commit = 1           # 1 = 每次 commit fsync（最安全）
                                             # 2 = 每秒 fsync（性能好但崩溃丢 1s）
sync_binlog = 1                              # 每次 commit fsync binlog
innodb_io_capacity = 2000                    # SSD 可调高，加速脏页刷新
```

### 8.5 主从复制

- binlog（master 端）→ relay log（slave 端）→ 重放。
- **半同步复制**（semi-sync）：至少一个从库 ACK 才返回成功，损失一些性能换数据安全。
- **GTID 模式**：每个事务有全局唯一 ID，故障切换更友好。
- 主从延迟监控：`SHOW SLAVE STATUS\G` 看 `Seconds_Behind_Master`。

---

## 九、面试速记口诀

> **索引**：B+ 树高 3-4 层 → 几百万行 IO 仅 3-4 次；最左前缀，范围阻断；覆盖索引免回表；ICP 索引下推。
>
> **EXPLAIN**：看 type 分级、看 key 是否命中、看 Extra 是否有 filesort / temporary。
>
> **Join**：能走索引就走 NLJ；BNL 时让小表驱动并调大 join_buffer。
>
> **MVCC**：隐藏 trx_id + roll_pointer + Read View；RR 首次 SELECT 生成 RV，之后复用 → 重复读一致；幻读 = MVCC + Next-Key Lock。
>
> **三大日志**：undo 回滚、redo 崩溃恢复（物理）、binlog 复制（逻辑）；2PC 让 redo 和 binlog 在 commit 阶段对齐。
>
> **OOM 排查**：慢日志 + EXPLAIN + 看 Buffer Pool 命中率（Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests）。

---

## 十、深入阅读 / 双链

- 主题文章：[[MySQL索引与执行计划]]、[[MySQL-MVCC与隔离级别]]、[[MySQL日志与两阶段提交]]、[[InnoDB事务与锁]]
- 同专栏：[[InnoDB事务]]、[[Mysql日志]]、[[Mysql锁]]、[[PgSql]]
- 项目联动：[[黑马点评秒杀]]（一人一单 + 乐观锁）、[[用友数据迁移]]（迁移一致性）
- 真题来源：[[快手/支付方向/我的快手支付二面]]、[[快手/支付方向/快手日常实习面经]]、[[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]、[[字节/国际广告/字节跳动中国商业化一面面经]]、[[字节/字节财经一面]]、[[蔚来/xhs]]、[[Cider面经/1]]、[[心潮无限往年面经/1]]、[[其他/昆仑数智/3]]
