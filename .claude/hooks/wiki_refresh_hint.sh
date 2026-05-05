#!/bin/bash
# 当 Claude 在 raw 层（公司面经 / 技术专栏）写文件时，
# 输出一条提醒，让 Claude 记得增量刷新对应 wiki 页。
# stdin 是 PostToolUse hook 的 JSON payload。

set -e

PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0

# 仅对 raw 层（仓库根目录下，非 wiki/ 非 .claude/ 非 .obsidian/）的 .md 文件触发
RAW_DIRS="快手 字节-今日头条-财经业务 腾讯 蚂蚁 阿里云面经 京东 小红书 微软 蔚来 TT 虾皮 小鹅通往年面经+我的面经 Cider面经 面经较少公司 心潮无限往年面经 后端技术专栏 Agent技术专栏 项目"

for dir in $RAW_DIRS; do
    if [[ "$FILE_PATH" == *"/$dir/"* ]] || [[ "$FILE_PATH" == *"$dir/"* ]]; then
        REL=$(echo "$FILE_PATH" | sed -E 's|.*strange-mayer-9d2094/||')
        cat <<EOF
{"systemMessage": "📌 raw 层文件被修改：\`$REL\`。请增量刷新 wiki：\n  1) 对应 wiki/公司画像/*.md（如适用）\n  2) wiki/索引/高频考点榜.md（如有新考点）\n  3) wiki/索引/公司索引.md（如新增公司目录）\n  4) 跑 \`python3 wiki/scripts/lint_wiki.py\` 验证双链。\n详见 wiki/README.md 维护规范第 3 条。"}
EOF
        exit 0
    fi
done

exit 0
