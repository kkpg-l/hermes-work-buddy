#!/usr/bin/env bash
# Hermes Work Buddy 专家团一键安装脚本
set -euo pipefail

HERMES_SKILLS_DIR="${HOME}/.hermes/skills"
PANEL_DIR="${HERMES_SKILLS_DIR}/expert-panel"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Hermes Work Buddy 专家团安装 ==="
echo ""

# 1. 检查 Hermes
echo -n "检查 Hermes... "
if command -v hermes &>/dev/null; then
    echo "OK ($(hermes --version 2>/dev/null || echo 'version unknown'))"
else
    echo "未找到"
    echo "请先安装 Hermes Agent: https://github.com/nicepkg/hermes"
    exit 1
fi

# 2. 创建技能目录
echo -n "创建技能目录... "
mkdir -p "${PANEL_DIR}/tests"
echo "OK (${PANEL_DIR})"

# 3. 复制技能文件
echo -n "复制 SKILL.md... "
cp -f "${SCRIPT_DIR}/skills/expert-panel/SKILL.md" "${PANEL_DIR}/"
echo "OK"

echo -n "复制 run.py... "
cp -f "${SCRIPT_DIR}/skills/expert-panel/run.py" "${PANEL_DIR}/"
chmod +x "${PANEL_DIR}/run.py"
echo "OK"

echo -n "复制 smoke.sh... "
cp -f "${SCRIPT_DIR}/skills/expert-panel/tests/smoke.sh" "${PANEL_DIR}/tests/"
chmod +x "${PANEL_DIR}/tests/smoke.sh"
echo "OK"

# 4. 配置示例提示
echo ""
echo "配置提示："
echo "  - API Key: export DEEPSEEK_API_KEY=sk-xxx (加入 ~/.bashrc)"
echo "  - 本地模型: 参考 config/config.example.yaml"
echo ""

# 5. 验证
echo -n "运行冒烟测试... "
if bash "${PANEL_DIR}/tests/smoke.sh"; then
    echo ""
    echo "=== 安装完成 ==="
else
    echo ""
    echo "冒烟测试未通过，请检查网络/API Key/Hermes 版本"
    echo "调试：HERMES_EXPERT_PANEL_DEBUG=1 hermes run \"expert-panel --query=自检\""
fi
