#!/bin/bash
# 创建一份新的面试复盘文件，从 wiki/复盘/模板.md 拷贝并填好元信息。
#
# 用法：
#   bash wiki/scripts/new_review.sh <公司> [<轮次>]
# 示例：
#   bash wiki/scripts/new_review.sh 字节 一面
#   bash wiki/scripts/new_review.sh 快手        # 默认 一面
#
# 输出：wiki/复盘/<YYYY-MM-DD>-<公司>-<轮次>.md

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TEMPLATE="$REPO_ROOT/wiki/复盘/模板.md"
TARGET_DIR="$REPO_ROOT/wiki/复盘"

if [ -z "$1" ]; then
    echo "用法: $0 <公司> [<轮次>]" >&2
    echo "例: $0 字节 一面" >&2
    exit 1
fi

COMPANY="$1"
ROUND="${2:-一面}"
DATE=$(date +%Y-%m-%d)
FILE="$TARGET_DIR/${DATE}-${COMPANY}-${ROUND}.md"

if [ -e "$FILE" ]; then
    echo "✗ 文件已存在: $FILE" >&2
    echo "   今天可能已经填过这场了。要追加用编辑器打开它。" >&2
    exit 1
fi

if [ ! -f "$TEMPLATE" ]; then
    echo "✗ 模板找不到: $TEMPLATE" >&2
    exit 1
fi

# 拷贝模板，并把头部元信息填好
{
    echo "---"
    echo "title: ${COMPANY} ${ROUND} 复盘"
    echo "type: review"
    echo "company: ${COMPANY}"
    echo "round: ${ROUND}"
    echo "date: ${DATE}"
    echo "updated: ${DATE}"
    echo "---"
    echo ""
    echo "# ${COMPANY} ${ROUND} 复盘 (${DATE})"
    echo ""
    # 跳过模板原始 frontmatter，从第一个 ## 开始
    awk '/^## /,EOF' "$TEMPLATE"
} > "$FILE"

echo "✓ 已创建: $FILE"
echo ""
echo "下一步："
echo "  1. 30 分钟内填完（趁记忆新鲜）"
echo "  2. 答崩的考点 → 在 wiki/索引/高频考点榜.md 把对应自评 -1"
echo "  3. 新出现的真题 → 加进 wiki/算法/README.md（如算法）或对应 wiki/公司/${COMPANY}.md"
echo "  4. 更新 wiki/offer.md（如有进展）"
