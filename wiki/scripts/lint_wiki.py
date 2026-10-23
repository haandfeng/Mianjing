#!/usr/bin/env python3
"""
面经 wiki 健康检查脚本。

跑法：python3 wiki/scripts/lint_wiki.py

检查：
1. wiki 双链是否能解析，资料中的历史断链单列提示
2. wiki 文件中 // 待补全 / TODO 标记数量
3. 高频考点出现的公司数（关键词扫描估算）
4. 资料与 wiki 的文件分布
"""
import os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIRS = {'.git', '.obsidian', '.claude', '.agents', '.codex',
             'Excalidraw', 'node_modules', '__pycache__'}

def list_files(base):
    out = []
    for r, ds, fs in os.walk(base):
        ds[:] = [d for d in ds if d not in SKIP_DIRS]
        for f in fs:
            out.append(os.path.relpath(os.path.join(r, f), base))
    return out

def build_keys(paths):
    """Obsidian 后缀路径解析：file.md 可被 'file' / 'dir/file' / 'a/dir/file' 任意后缀引用"""
    keys = set()
    for p in paths:
        no_ext = p.removesuffix('.md')
        parts = no_ext.split('/')
        for i in range(len(parts)):
            keys.add('/'.join(parts[i:]))
    return keys

def lint_links(all_files, md_files):
    keys = build_keys(all_files)
    broken = []
    for wf in md_files:
        with open(os.path.join(ROOT, wf), encoding='utf-8') as fh:
            content = fh.read()
        for m in re.finditer(r'\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]+)?\]\]', content):
            link = m.group(1).strip().removesuffix('.md')
            if link not in keys:
                broken.append((wf, link))
    return broken

def find_todos(wiki_files):
    todos = []
    # 严格匹配：// 待补全 / 大写 TODO/FIXME 单词 / "⚠️ TODO"
    # 不匹配 xxx (小写, 常见于占位符如 'xxx%' 'setXxx')
    pat = re.compile(r'//\s*待补全|⚠️\s*TODO|\bTODO\b|\bFIXME\b')
    for wf in wiki_files:
        if wf == 'wiki/log.md':
            continue  # 操作日志会引用检查结果中的 TODO 字样，不是内容待办。
        with open(os.path.join(ROOT, wf), encoding='utf-8') as fh:
            for i, line in enumerate(fh, 1):
                if pat.search(line):
                    todos.append((wf, i, line.strip()))
    return todos

def check_topic_coverage(all_md):
    """从面经档案的公司目录统计考点出现公司数。"""
    keywords = {
        'MySQL索引': r'索引|B\+树|EXPLAIN',
        'MVCC': r'MVCC|隔离级别|可重复读|幻读',
        'Redis缓存': r'缓存击穿|缓存穿透|缓存雪崩|布隆过滤',
        'JVM-GC': r'JVM|GC|垃圾回收|Eden|Survivor',
        'CHM': r'ConcurrentHashMap|CAS|AQS',
        'TCP': r'三次握手|四次挥手|TCP|滑动窗口',
        'MQ': r'RabbitMQ|Kafka|RocketMQ|消息队列|死信',
        'RPC': r'RPC|Netty|Dubbo',
        'RAG': r'RAG|混合检索|Reranker|向量',
        '限流': r'限流|熔断|令牌桶|漏桶|Sentinel',
    }
    counts = defaultdict(set)
    for p in all_md:
        parts = p.split('/')
        if parts[:2] != ['资料', '面经'] or len(parts) < 4:
            continue
        company = parts[3] if parts[2] == '其他' and len(parts) > 4 else parts[2]
        with open(os.path.join(ROOT, p), encoding='utf-8') as fh:
            content = fh.read()
        for topic, pat in keywords.items():
            if re.search(pat, content):
                counts[topic].add(company)
    return {t: len(s) for t, s in counts.items()}

def main():
    all_files = list_files(ROOT)
    all_md = [p for p in all_files if p.endswith('.md')]
    wiki_files = [p for p in all_md if p.startswith('wiki/')]
    source_files = [p for p in all_md if p.startswith('资料/')]
    print(f'## Wiki 健康检查 (全库 {len(all_md)} 篇 Markdown，wiki {len(wiki_files)} 篇)\n')

    print('### 1. 双链断链检查（wiki 断链阻断检查）')
    broken = lint_links(all_files, wiki_files)
    if not broken:
        print('  ✓ 0 broken links\n')
    else:
        c = Counter(b[1] for b in broken)
        print(f'  ✗ {len(broken)} broken')
        for tgt, cnt in c.most_common(20):
            print(f'    [{cnt}x] [[{tgt}]]')
        print()

    source_broken = lint_links(all_files, source_files)
    print(f'  资料历史断链：{len(source_broken)} 条（仅提示，不阻断）')
    for path, target in source_broken[:20]:
        print(f'    {path} → [[{target}]]')
    if len(source_broken) > 20:
        print(f'    其余 {len(source_broken) - 20} 条省略')
    print()

    print('### 2. 待补全 / TODO 标记')
    todos = find_todos(wiki_files)
    if not todos:
        print('  ✓ 0 TODO\n')
    else:
        print(f'  {len(todos)} TODO 标记：')
        by_file = defaultdict(int)
        for f, _, _ in todos:
            by_file[f] += 1
        for f, n in sorted(by_file.items(), key=lambda x: -x[1]):
            print(f'    [{n}] {f}')
        print()

    print('### 3. 高频考点公司覆盖度（关键词扫描估算）')
    cov = check_topic_coverage(all_md)
    for topic, n in sorted(cov.items(), key=lambda x: -x[1]):
        bar = '█' * n
        print(f'  {topic:12s} {n:2d} 公司  {bar}')
    print()

    print('### 4. 分布概览')
    for label, prefix in [('面经档案', '资料/面经/'),
                          ('学习材料', '资料/学习材料/'),
                          ('项目参考', '资料/项目参考/')]:
        print(f'  {label}：{sum(p.startswith(prefix) for p in all_md)} 篇')
    print(f'  wiki：{len(wiki_files)} 篇')
    print(f'  其他 Markdown：{len(all_md) - len(source_files) - len(wiki_files)} 篇')
    return 1 if broken else 0

if __name__ == '__main__':
    sys.exit(main())
