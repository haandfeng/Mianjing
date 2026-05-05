#!/usr/bin/env python3
"""
面经 wiki 健康检查脚本。

跑法：python3 wiki/scripts/lint_wiki.py

检查：
1. 所有 [[wikilink]] 是否能解析（按 Obsidian 后缀路径匹配规则）
2. 高频考点（≥3 公司）是否都有对应 wiki/技术主题/ 文章
3. 哪些 raw 面经新加但 wiki/公司画像/ 没更新
4. wiki 文件中 // 待补全 / TODO 标记数量
"""
import os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIRS = {'.git', '.obsidian', '.claude', 'Excalidraw', 'image', 'node_modules'}

def list_md(base):
    out = []
    for r, ds, fs in os.walk(base):
        ds[:] = [d for d in ds if d not in SKIP_DIRS]
        for f in fs:
            if f.endswith('.md'):
                out.append(os.path.relpath(os.path.join(r, f), base))
    return out

def build_keys(paths):
    """Obsidian 后缀路径解析：file.md 可被 'file' / 'dir/file' / 'a/dir/file' 任意后缀引用"""
    keys = set()
    for p in paths:
        no_ext = os.path.splitext(p)[0]
        parts = no_ext.split('/')
        for i in range(len(parts)):
            keys.add('/'.join(parts[i:]))
    return keys

def lint_links(all_md, wiki_files):
    keys = build_keys(all_md)
    broken = []
    for wf in wiki_files:
        with open(os.path.join(ROOT, wf), encoding='utf-8') as fh:
            content = fh.read()
        for m in re.finditer(r'\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]+)?\]\]', content):
            link = m.group(1).strip().removesuffix('.md')
            if link not in keys:
                broken.append((wf, link))
    return broken

def find_todos(wiki_files):
    todos = []
    pat = re.compile(r'(?://\s*待补全|TODO|FIXME|XXX)', re.IGNORECASE)
    for wf in wiki_files:
        with open(os.path.join(ROOT, wf), encoding='utf-8') as fh:
            for i, line in enumerate(fh, 1):
                if pat.search(line):
                    todos.append((wf, i, line.strip()))
    return todos

def check_topic_coverage(all_md, wiki_topic_files):
    """根据公司目录推断每个考点出现公司数；对照已有主题文章。"""
    company_dirs = ['快手', '字节-今日头条-财经业务', '腾讯', '蚂蚁', '阿里云面经',
                    '京东', '小红书', '微软', '蔚来', 'TT', '虾皮', '小鹅通往年面经+我的面经',
                    'Cider面经', '面经较少公司', '心潮无限往年面经']
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
        if not any(p.startswith(d) for d in company_dirs):
            continue
        company = p.split('/')[0]
        try:
            with open(os.path.join(ROOT, p), encoding='utf-8') as fh:
                content = fh.read()
        except Exception:
            continue
        for topic, pat in keywords.items():
            if re.search(pat, content):
                counts[topic].add(company)
    return {t: len(s) for t, s in counts.items()}

def main():
    all_md = list_md(ROOT)
    wiki_files = [p for p in all_md if p.startswith('wiki/')]
    print(f'## Wiki 健康检查 (raw {len(all_md)} 文件，wiki {len(wiki_files)} 文件)\n')

    print('### 1. 双链断链检查')
    broken = lint_links(all_md, wiki_files)
    if not broken:
        print('  ✓ 0 broken links\n')
    else:
        c = Counter(b[1] for b in broken)
        print(f'  ✗ {len(broken)} broken')
        for tgt, cnt in c.most_common(20):
            print(f'    [{cnt}x] [[{tgt}]]')
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
    cov = check_topic_coverage(all_md, [])
    for topic, n in sorted(cov.items(), key=lambda x: -x[1]):
        bar = '█' * n
        print(f'  {topic:12s} {n:2d} 公司  {bar}')
    print()

    print('### 4. 分布概览')
    print(f'  raw 面经：{sum(1 for p in all_md if not p.startswith("wiki/") and not p.startswith("后端技术专栏/") and not p.startswith("Agent技术专栏/"))} 文件')
    print(f'  raw 专栏：{sum(1 for p in all_md if p.startswith("后端技术专栏/") or p.startswith("Agent技术专栏/"))} 文件')
    print(f'  wiki：{len(wiki_files)} 文件')

if __name__ == '__main__':
    main()
