---
title: TT / TikTok
type: company-profile
updated: 2026-05-04
---

# TT / TikTok

## 概览
- 方向：Ads SRE（北京/新加坡/美国多 office；广告投放稳定性、资源治理、ML 在线推理）；Search Ads（召回→粗排→精排漏斗，GPU 在线推理）
- 难度：SRE 一面就把 Linux 命令、文件系统、502 排查、零拷贝、CPU load vs 利用率全过一遍；Search Ads 偏八股 + 海量场景
- 一句话画像：SRE 是面经里 Linux/网络/系统八股密度最高的公司，二面专攻 502 排查 SOP；Search Ads 一道场景题（1 亿日志找 top-K IP）就能定差别

## 面经文件
- [[TT/SRE/TT SRE]] —— 西门子 ETL 深挖（XML→Markdown 改开源库表格嵌套、Milvus batch insert 25→10 分钟、GPU 没打满）+ Linux 常用命令 + ext4 + 滑动窗口最小覆盖子串（含保留 T 字符顺序的 follow-up）
- [[TT/SRE/TT SRE 二面]] —— 浏览器输 URL 全流程（DNS → TCP → TLS → 协议栈封装 → 网卡/交换机/路由器转发）+ DNS 递归 vs 迭代 + TCP 三/四次握手 + HTTPS 加密 + tiktok.com 1 分钟才显示的排查讨论
- [[TT/SRE/TT SRE 牛客]] —— K8s 搭建 + nginx 流量架构 + service 调度算法 + DNS 协议 + IO 吞吐 + free -h 字段 + 502 排查 6 步 SOP（错误日志归类 / 直连验证 / ss 看连接状态分布 / Recv-Q 看 accept 队列满 / 配置事故 / 队列调优）+ JWT 三段结构 + Redis 点赞缓存一致性（先更新 MySQL 后删 Redis）+ DNS / TCP / 双向队列 / 日志 awk 统计 / 站点慢排查 / top vs vmstat vs iostat / 零拷贝 mmap/sendfile/scatter-gather + 进程线程协程
- [[TT/Search-Ads/TT Search ADs 26 Summer Intern]] —— 西门子 RAG 深挖（面试官想看后端方向，反响一般）+ 1 小时 1 亿条 nginx access log 求 top-K IPv4 + ACID 实习实践 + 召回/粗排/精排漏斗

## 考察重点（按出现次数排序）
1. **502 排查 SOP（六步法）** —— 看 Nginx error.log upstream 错误 → 直连验证上游 → ss 看连接状态分布 → ss -lnt 看 Recv-Q 是不是 accept 队列满 → 修配置（超时不要离谱大、调 backlog/somaxconn、启用 keepalive）→ 资源治理
2. **浏览器输 URL 全流程** —— 解析协议域名 → DNS（缓存→hosts→根→TLD→权威）→ TCP 三次握手 → TLS（1.2 两 RTT / 1.3 一 RTT）→ HTTP 报文封装（TCP/IP/MAC 头）→ 网卡/交换机/路由器转发 → 服务器解封 → 浏览器渲染
3. **TCP/HTTPS 全套** —— 三次握手为什么不能两次（防历史连接 + 同步初始序列号 + 避免资源浪费）、四次挥手、滑动窗口、超时/快速/SACK 重传、慢启动/拥塞避免/快速恢复
4. **Linux 性能排查工具链** —— top（load avg / us / sy / wa / id）/ vmstat（r / b / wa / si/so / bi/bo）/ iostat（%util / await）/ free -h（available / swap）/ iotop / strace / netstat
5. **零拷贝** —— mmap（共享 buffer 节省一次 CPU 拷贝）/ sendfile（内核态搬运）/ sendfile + DMA scatter-gather（真正零拷贝，2 次上下文切换 + 2 次 DMA）
6. **CPU load vs 利用率** —— load 包括 R + D（不可中断睡眠 IO 等待）；利用率不高但慢 → 看 wa、b 队列、外部依赖
7. **海量数据 top-K** —— 1 亿条 IPv4 找出现最多 top-K（hash + 小顶堆 / 桶排 / 分治）
8. **K8s + nginx + Service** —— 流量调度算法、为什么用 K8s

## 真题摘录（值得背的）

> **外部访问 URL 出现 502 该怎么排查？** 出处 [[TT/SRE/TT SRE 牛客]]
> 六步法：①确认是谁返回的 502（curl -v 看 Nginx/Ingress）；②看 error.log upstream 报错归类（connect refused / timed out / prematurely closed / no live upstreams）；③直连验证（ss -tlnp 端口监听 / curl 健康检查 / journalctl 进程日志）；④ss -ant 看连接状态分布（SYN_SENT 卡住 / ESTABLISHED 堆积 / TIME_WAIT 爆炸）；⑤ss -lnt 看 Recv-Q 是不是 accept 队列满（Tomcat accept-count + somaxconn 默认偏小）；⑥修配置（超时不要离谱大触发雪崩、调 backlog、upstream keepalive 减少新建连接）。

> **CPU 利用率不高但系统就是慢，怎么排查？** 出处 [[TT/SRE/TT SRE 牛客]]
> 时间花在"等"上：top wa（iowait）高、进程 D 状态多 → 磁盘 IO；vmstat r/b 队列、si/so 换页、bi/bo 块设备读写；iostat %util > 80% / await > 50ms 看磁盘；iotop 看谁在大量读写；free -h 看 swap；strace -p 跟踪系统调用；netstat 看 TCP 是否大量 SYN-SENT/TIME-WAIT/CLOSE-WAIT 等外部依赖慢。

> **redis 做点赞缓存如何避免数据不一致？** 出处 [[TT/SRE/TT SRE 牛客]]
> 先更新 MySQL 后删除 Redis：MySQL 写入 >> Redis 删除耗时，正常并发下读请求很难在写完前后那段间隙旧值写回。如果先删后更新反而更容易不一致——MySQL 写入慢，期间读请求会把旧值写回。删除失败兜底：依赖 TTL 过期 / 消息队列重试 / 订阅 binlog + MQ 重试。

## 复习清单（双链）
- [[TCP与HTTPS]]
- [[Linux与IO模型]]
- [[缓存一致性]]
- [[Redis数据结构与大Key]]
- [[Redis缓存三大问题]]
- [[消息队列不丢不重]]
- [[限流熔断容错]]
- [[MySQL索引与执行计划]]
- _算法/README_（已移除）
- [[西门子RAG]]
- [[ARM-Profiling]]
