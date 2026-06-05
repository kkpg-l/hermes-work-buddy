#!/usr/bin/env bash
# Hermes Work Buddy 专家团卸载脚本
set -euo pipefail

PANEL_DIR="${HOME}/.hermes/skills/expert-panel"

echo "=== Hermes Work Buddy 专家团卸载 ==="
echo ""
echo "将删除: ${PANEL_DIR}"
read -rp "确认? (y/N) " confirm

if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
    echo "取消"
    exit 0
fi

if [ -d "${PANEL_DIR}" ]; then
    mv "${PANEL_DIR}" "${PANEL_DIR}.bak.$(date +%Y%m%d%H%M%S)"
    echo "已备份并移除"
else
    echo "目录不存在，无需操作"
fi

echo ""
echo "如需恢复："
echo "  mv ${PANEL_DIR}.bak.* ${PANEL_DIR}"
