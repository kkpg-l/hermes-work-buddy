#!/usr/bin/env bash
# Expert Panel 冒烟测试 v4.0
set -e

echo "=== Expert Panel Smoke Test ==="
echo ""

# T1: 最小调用
echo -n "T1: 最小调用 (1+1)... "
result=$(hermes run "expert-panel --query=1+1=几" 2>/dev/null)
if echo "$result" | grep -q "2"; then
    echo "PASS"
else
    echo "FAIL"
    echo "$result" | head -5
fi

# T2: 单一专家
echo -n "T2: 单一专家 (tech)... "
result=$(hermes run "expert-panel --query=hello --experts=tech" 2>/dev/null)
if echo "$result" | grep -q "."; then
    echo "PASS"
else
    echo "FAIL"
fi

# T3: 中文长问
echo -n "T3: 中文长问... "
result=$(hermes run "expert-panel --query=分析 WSL2 与 VirtualBox 的优劣" 2>/dev/null)
if echo "$result" | grep -q "分析"; then
    echo "PASS"
else
    echo "FAIL"
fi

# T4: 串行模式
echo -n "T4: 串行模式... "
result=$(hermes run "expert-panel --query=test --mode=serial" 2>/dev/null)
if echo "$result" | grep -q "."; then
    echo "PASS"
else
    echo "FAIL"
fi

# T5: 本地模型（若启用）
echo -n "T5: 本地模型... "
if curl -s http://127.0.0.1:8080/health >/dev/null 2>&1; then
    result=$(hermes run "expert-panel --query=写一个 python 排序函数" 2>/dev/null)
    if echo "$result" | grep -q "."; then
        echo "PASS"
    else
        echo "FAIL"
    fi
else
    echo "SKIP (本地未启)"
fi

echo ""
echo "=== Done ==="
