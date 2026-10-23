#!/bin/bash
# 资料文件变动后提醒同步当前知识、索引与日志。
set -e

FILE_PATH=$(jq -r '.tool_input.file_path // empty')
case "$FILE_PATH" in
    */资料/*.md|资料/*.md)
        jq -n --arg file "$FILE_PATH" '{systemMessage: ("资料文件已更新：" + $file + "。请按 wiki/使用指南.md 检查相关公司画像、主专题或项目追问，同步 wiki/index.md 与操作日志，然后运行 python3 wiki/scripts/lint_wiki.py。保留历史原话，完整解释只在主专题或项目追问维护。")}'
        ;;
esac
