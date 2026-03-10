## PostgreSQL 慢查询：新人友好版

用最少概念，告诉你：怎么发现慢 SQL，怎么看计划，怎么改快。

### A. 先把“发现慢 SQL”的开关打开（按重要度）
1) 慢日志：  
   - 会话级临时开启，安全：`SET log_min_duration_statement = 200;`（记录 >200ms 的 SQL）  
2) 热点统计：  
   - 安装扩展：`CREATE EXTENSION IF NOT EXISTS pg_stat_statements;`  
   - 查看最慢/最频繁：`SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;`  
3) 自动计划：  
   - 会话级：  
     ```sql
     LOAD 'auto_explain';
     SET auto_explain.log_min_duration = '200ms';
     SET auto_explain.log_analyze = on;
     SET auto_explain.log_buffers = on;
     SET auto_explain.log_timing = off;  -- 降开销
     ```  
4) 看现场：  
   - 正在跑：`SELECT pid, now()-query_start AS run, wait_event, query FROM pg_stat_activity WHERE state='active' ORDER BY run DESC;`  
   - 是否锁住：`SELECT * FROM pg_locks WHERE NOT granted;`

### B. 用 EXPLAIN 看懂慢在哪里（只记这些）
执行：`EXPLAIN (ANALYZE, BUFFERS) 你的SQL;`
- 扫描方式：  
  - `Seq Scan` = 全表扫描，像把整本书翻完；  
  - `Index Scan` / `Bitmap Heap Scan` = 走索引，像按目录直跳页码。  
- 行数：`rows`（估计） vs `actual rows`（实际）  
  - 两者差很大 → 统计信息不准，先 `ANALYZE 表;`。  
- 排序/哈希是否落盘：  
  - `Sort Method: external merge Disk`，或 `Hash Batches` 很多 → 内存不够或缺索引导致落盘。  
  - 处理：会话级 `SET work_mem = '64MB';`，或加复合索引让它少排序。  
- 连接方式：  
  - `Nested Loop` 大表套大表多半慢；希望用 `Hash Join`/`Merge Join` 或让小表驱动大表。  
  - 处理：给 join 键建索引，必要时改写 SQL。  
- I/O：  
  - `Buffers: shared read` 高 = 在读盘；  
  - `temp read/write` 有 = 排序/哈希溢出用临时文件。  
  - 处理：索引/过滤减少数据量，或会话级调 `work_mem`。  
- 时间：  
  - `Execution Time` = 执行耗时；  
  - `Planning Time` = 生成计划耗时。哪块高就优化哪块。

### C. 立刻可用的优化动作（按优先顺序）
1) 补索引，让过滤+排序都能用上  
   - 例：`WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC LIMIT 50`  
   - 建：`CREATE INDEX CONCURRENTLY idx_orders_user_created ON orders (user_id, created_at DESC);`  
   - 若还要字段：`INCLUDE(total_amount)` 减少回表。  
2) 避免大 OFFSET，改键集分页  
   - `WHERE id > ? ORDER BY id LIMIT 50` 替代 `OFFSET 100000`。  
3) IN/子查询过慢 → 改 JOIN，确保 join 键有索引  
4) 高频条件建部分索引  
   - 例：`CREATE INDEX CONCURRENTLY idx_reports_active ON reports (created_at DESC) WHERE status='active';`  
5) 防排序/哈希落盘  
   - 会话级调内存：`SET work_mem = '64MB';`（只对当前连接，避免全局风险）  
   - 或加复合索引避免排序。  
6) 统计信息与膨胀  
   - `ANALYZE 表;` 若估计偏差大可适当提高 `default_statistics_target`。  
   - 定期 `VACUUM ANALYZE`；大量删除后再看是否需要 `VACUUM (FULL)`/分区。  
7) 模糊匹配  
   - 前缀匹配 `abc%` 用 B-Tree；包含匹配 `%abc%` 装 `pg_trgm`：  
     `CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE INDEX CONCURRENTLY idx_title_trgm ON docs USING gin (title gin_trgm_ops);`

### D. 两个最常见的慢 SQL 案例
1) 订单列表慢（过滤+排序）  
   - SQL：  
   ```sql
   SELECT id, user_id, created_at, total_amount
   FROM orders
   WHERE user_id = 123 AND created_at >= now() - interval '30 days'
   ORDER BY created_at DESC
   LIMIT 50;
   ```  
   - 看计划：若是 `Seq Scan` 或 `Sort Method: external merge Disk` → 缺索引/排序落盘。  
   - 方案：建 `(user_id, created_at DESC)`，必要时 INCLUDE 字段；如仍排序落盘，会话级 `SET work_mem='64MB';`

2) JOIN + 聚合慢  
   ```sql
   SELECT d.department_id, count(*) AS cnt
   FROM employees e
   JOIN departments d ON e.department_id = d.id
   WHERE d.status = 'active'
   GROUP BY d.department_id;
   ```  
   - 方案：  
     - 部分索引：`CREATE INDEX CONCURRENTLY idx_dept_active ON departments(id) WHERE status='active';`  
     - 确保 `employees.department_id`、`departments.id` 有索引，促使 Hash/Merge Join。  
     - 大表聚合可用分区或物化视图定期刷新。

### E. 一张“我该先做什么”速查
- 先抓：`log_min_duration_statement` + `pg_stat_statements`，定位最耗时 SQL。  
- 再看：对目标 SQL 跑 `EXPLAIN (ANALYZE, BUFFERS)`，关注扫描方式、行数偏差、排序/哈希是否落盘。  
- 决策：  
  1) 加/改索引（匹配过滤+排序）；  
  2) 改写 SQL（少 select *，少大 OFFSET，多用 JOIN+索引）；  
  3) 会话级调 `work_mem` 避免落盘；  
  4) `ANALYZE` + 需要时 `VACUUM` 控制膨胀；  
  5) 模糊匹配用 `pg_trgm`。  

就按 A→B→C 的顺序操作，先能看见慢 SQL，再用 EXPLAIN 定位瓶颈，再用对应的优化动作。  
