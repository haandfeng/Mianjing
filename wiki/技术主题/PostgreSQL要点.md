---
title: PostgreSQL要点
type: topic
updated: 2026-05-04
---

# PostgreSQL要点

> PG 与 MySQL 是两种不同思路的关系库。索引种类丰富、并行查询、强大的优化器使它在分析与复杂查询场景占优；调优靠 `pg_stat_statements` + `EXPLAIN ANALYZE`。

## 高频问法
- "PG 和 MySQL 区别？为什么 PG 复杂查询更强？" — [[字节-今日头条-财经业务/我的字节一面]]
- "PG 慢查询怎么排查、优化" — [[蔚来/蔚来一面RAG深挖]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
- "PG 索引种类（B-Tree / Hash / GIN / GiST / BRIN / SP-GiST / Bloom）" — [[蔚来/蔚来一面RAG深挖]]
- "PG 没 binlog 怎么做 CDC / 主从？" — [[阿里云面经/阿里云消息团队一面面经]]

## 答题骨架

### 1. PG vs MySQL 核心差异
- **优化器**：PG 模块化优化器，对子查询、Join 多策略选择更细致；MySQL 偏单机 OLTP
- **并行查询**：PG 支持 Parallel Seq Scan / Parallel Hash Join；MySQL 直到 8.0 才在部分场景并行
- **索引种类**：PG 多达 7 种（B-Tree / Hash / GIN / GiST / BRIN / SP-GiST / Bloom）；MySQL 主要 B+ 树
- **数据类型**：PG 原生 JSONB、ARRAY、HSTORE、UUID，可自定义类型与操作符
- **MVCC 实现**：PG 用元组版本（事务 ID 标记 + VACUUM 清理）；InnoDB 用 undo log + roll_pointer
- **复制日志**：PG 用 WAL（逻辑解码可做 CDC）；MySQL 有 binlog

### 2. PG 索引选用速记
| 索引 | 使用场景 |
|---|---|
| B-Tree | 默认；等值 + 范围 |
| Hash | 仅等值，更新代价高，少用 |
| GIN | 倒排，多值字段（数组）、全文（tsvector）、JSONB 内部检索 |
| GiST | 范围模糊匹配、地理空间（PostGIS） |
| BRIN | 块范围，超大表上顺序字段（时间戳）；索引超小 |
| SP-GiST | 非平衡树（前缀树、四叉树），IP 段、字符串前缀 |
| Bloom | 多列等值近似匹配（布隆过滤器） |
| 部分索引 | `... WHERE status='active'`，过滤后才进索引 |
| 表达式索引 | 对 `lower(name)`、`(a+b)` 这类函数结果建索引 |
| INCLUDE 覆盖 | 减少回表 |

### 3. 慢查询排查链路
1. **打开慢日志**：`SET log_min_duration_statement = 200;`
2. **热点统计**：`pg_stat_statements` 扩展 → `ORDER BY total_time DESC`
3. **现场看**：`pg_stat_activity`（当前活跃 + 等待事件）、`pg_locks WHERE NOT granted`（锁等待）
4. **执行计划**：`EXPLAIN (ANALYZE, BUFFERS) <SQL>`
   - `Seq Scan` = 全表；`Index Scan` / `Bitmap Heap Scan` 走索引
   - `rows` 估计 vs `actual rows`：差距大 → `ANALYZE` 表更新统计信息
   - `Sort Method: external merge Disk` / `temp read/write`：内存不够 → 调 `work_mem`
   - `Buffers: shared read` 高 = 读盘多

### 4. 常用优化动作
- 复合索引匹配 WHERE + ORDER BY（如 `(user_id, created_at DESC)`）
- `INCLUDE(...)` 让索引变覆盖索引，减少回表
- 大 OFFSET 改键集分页：`WHERE id > ? ORDER BY id LIMIT N`
- 部分索引：`CREATE INDEX ... WHERE status='active'`
- 模糊查询：前缀 `abc%` 走 B-Tree；含 `%abc%` 用 `pg_trgm` + GIN
- `VACUUM ANALYZE` 控膨胀，大量删除后偶尔 `VACUUM (FULL)` 或分区

### 5. PG 的 CDC 思路（没有 binlog）
- 用 **WAL 逻辑解码（logical decoding）**：Debezium 监听，输出每条 INSERT / UPDATE / DELETE
- 发到 Kafka 等消息队列，下游消费
- 同用户操作有序：用 user_id 做 partition key

## 易错点 & 追问
- PG 的 MVCC 会留下死元组，长事务阻塞 VACUUM 是经典坑
- `Sort` 落盘出现 `external merge Disk` 时只调 `work_mem` 仍可能不够，最好加合适索引让排序消失
- B-Tree 索引在 `LIKE 'abc%'` 时能用，`'%abc%'` 用不了 → pg_trgm
- `CREATE INDEX CONCURRENTLY` 在线建索引不锁表

## 深入阅读
- 原始专栏 [[后端技术专栏/PgSql]]
- 真题来源 [[字节-今日头条-财经业务/我的字节一面]]、[[蔚来/蔚来一面RAG深挖]]、[[阿里云面经/阿里云消息团队一面面经]]、[[字节-今日头条-财经业务/字节-国际广告and中国广告/面经记录_国际商业化创业_3.9]]
