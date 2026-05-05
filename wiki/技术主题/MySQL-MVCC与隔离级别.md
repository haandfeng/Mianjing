---
title: MySQL-MVCC与隔离级别
type: topic
updated: 2026-05-04
---

# MySQL-MVCC与隔离级别

> 四个隔离级别每升一级多解决一种问题（脏读 → 不可重复读 → 幻读）；InnoDB 用 MVCC + Next-Key Lock 在 RR 下基本解决幻读，默认 RR。

## 高频问法
- "InnoDB 默认隔离级别？怎么实现？" — [[快手/支付方向/快手日常实习面经]]、[[Cider面经/1]]
- "MVCC 实现原理？" — [[字节/中国商业化/字节跳动中国商业化一面面经]]、[[Cider面经/1]]、[[蔚来/蔚来一面RAG深挖]]
- "幻读是什么？RR 下还会幻读吗？" — [[快手/支付方向/快手Java开发日常实习生（支付方向）一面（挂）]]、[[快手/支付方向/我的快手支付二面]]
- "RC 和 RR 的核心区别在哪一步？" — [[心潮无限往年面经/1]]、[[其他/昆仑数智/3]]

## 答题骨架

### 1. 三种读异常 + 四种隔离级别
| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---|---|---|---|
| READ UNCOMMITTED | ✗ | ✗ | ✗ |
| READ COMMITTED | ✓ | ✗ | ✗ |
| REPEATABLE READ（默认） | ✓ | ✓ | 大部分场景已解决 |
| SERIALIZABLE | ✓ | ✓ | ✓ |

- **脏读**：读到其他事务未提交的修改
- **不可重复读**：同一事务两次读同一行结果不同（其他事务 update 已提交）
- **幻读**：同一事务两次范围查询结果行数不同（其他事务 insert 已提交）

### 2. MVCC 三件套：隐藏字段 + Undo Log + Read View
- 每行隐藏列：`trx_id`（最后修改的事务 ID）、`roll_pointer`（指向 undo log 中的旧版本）
- 每次 update 不覆盖原数据，旧版本写入 undo log，roll_pointer 串成版本链
- **Read View** 字段：
  - `m_ids`：创建 RV 时活跃（已启动未提交）的事务 ID 列表
  - `min_trx_id`：m_ids 最小值
  - `max_trx_id`：下一个将分配的 trx_id（不是 m_ids 最大值）
  - `creator_trx_id`：自己

### 3. 可见性判断（拿到行后看 trx_id）
- `trx_id < min_trx_id` → RV 创建前已提交 → 可见
- `trx_id >= max_trx_id` → RV 创建后才启动 → 不可见
- `min_trx_id <= trx_id < max_trx_id`：在 m_ids 列表中 → 不可见（活跃中），否则 → 可见
- 不可见就沿 roll_pointer 找上一版本，重复判断

### 4. RC vs RR 关键区别 = Read View 创建时机
- **RC**：每个 SELECT 语句都重新生成 RV → 看到最新已提交，所以会出现不可重复读
- **RR**：事务**第一次** SELECT 时生成 RV，后续整个事务复用 → 视图固定，重复读一致

### 5. RR 下幻读怎么处理
- **快照读**（普通 `SELECT`）：靠 MVCC，看到的就是事务启动时的快照，期间别人 insert 也读不到 → 解决幻读
- **当前读**（`SELECT ... FOR UPDATE` / `UPDATE` / `DELETE`）：靠 **Next-Key Lock = 记录锁 + 间隙锁**，锁住范围内不允许 insert → 解决幻读
- **不能完全解决的边角**：事务先快照读，中途别的事务 insert 并提交，自己再 `UPDATE` 那条新插入的行 → 自己 update 后这行 trx_id 变成自己的，下次快照读就能看到了 → 视为"诱发的幻读"

### 6. 启动事务 ≠ 已生成快照
- `BEGIN` / `START TRANSACTION` 后，**第一条 SELECT** 才真正启动事务、生成 RV
- `START TRANSACTION WITH CONSISTENT SNAPSHOT` 命令立即启动

## 易错点 & 追问
- "max_trx_id 是 m_ids 最大值吗？" → 不是，是下一个将分配的 ID
- 串行化通过加读写锁（`SELECT` 也加共享锁）实现，性能差
- RC 在每条 SELECT 都建 RV，开销略高于 RR
- 提到"间隙锁解决幻读"时要补：只在 RR 下生效，RC 不开间隙锁

## 深入阅读
- 原始专栏 [[专栏/后端/InnoDB事务]]
- 真题来源 [[快手/支付方向/快手日常实习面经]]、[[字节/中国商业化/字节跳动中国商业化一面面经]]、[[蔚来/蔚来一面RAG深挖]]、[[心潮无限往年面经/1]]、[[其他/昆仑数智/3]]、[[Cider面经/1]]
