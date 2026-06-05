#!/usr/bin/env bash
# Hermes Work Buddy 健康检查脚本
set -euo pipefail

PASS=0
FAIL=0
SKIP=0

check() {
    local name="$1"
    local cmd="$2"
    echo -n "  ${name}... "
    if eval "$cmd" &>/dev/null; then
        echo "OK"
        ((PASS++))
    else
        echo "FAIL"
        ((FAIL++))
    fi
}

echo "=== Hermes Work Buddy 健康检查 ==="
echo ""

echo "[1] 基础环境"
check "Hermes CLI"     "command -v hermes"
check "Python 3.11+"   "python3 -c 'import sys; assert sys.version_info >= (3, 11)'"
check "venv 存在"      "test -f ~/.hermes/hermes-agent/venv/bin/python"

echo ""
echo "[2] 网络"
check "DeepSeek API"   "curl -sSf https://api.deepseek.com"
check "DNS 解析"       "nslookup api.deepseek.com"

echo ""
echo "[3] API Key"
echo -n "  DEEPSEEK_API_KEY... "
if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    echo "已设置 (${#DEEPSEEK_API_KEY} 字符)"
    ((PASS++))
else
    echo "未设置"
    ((FAIL++))
fi

echo ""
echo "[4] 本地推理（可选）"
echo -n "  Llama.cpp 服务... "
if curl -s http://127.0.0.1:8080/health &>/dev/null; then
    echo "运行中"
    ((PASS++))
else
    echo "未运行 (不影响核心功能)"
    ((SKIP++))
fi

echo -n "  GPU 可用... "
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "是"
    ((PASS++))
else
    echo "否 (本地推理将走 CPU)"
    ((SKIP++))
fi

echo ""
echo "[5] 专家团技能"
check "SKILL.md 存在"  "test -f ~/.hermes/skills/expert-panel/SKILL.md"
check "run.py 存在"    "test -f ~/.hermes/skills/expert-panel/run.py"
check "smoke.sh 存在"  "test -f ~/.hermes/skills/expert-panel/tests/smoke.sh"

echo ""
echo "[6] 代理环境"
proxy_vars=$(env | grep -ciE 'proxy' || true)
if [ "$proxy_vars" -gt 0 ]; then
    echo "  ⚠ 检测到代理环境变量 (${proxy_vars} 个)，可能导致 API 调用失败"
    echo "  修复：unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY"
    ((FAIL++))
else
    echo "  无代理干扰"
    ((PASS++))
fi

echo ""
echo "=== 结果: ${PASS} 通过 / ${FAIL} 失败 / ${SKIP} 跳过 ==="
if [ "$FAIL" -gt 0 ]; then
    echo "请修复失败项后重新运行"
    exit 1
fi
