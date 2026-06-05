#!/usr/bin/env bash
# Llama.cpp 本地推理服务启动脚本
set -euo pipefail

LLAMA_DIR="${HOME}/llama.cpp"
MODEL="${LLAMA_DIR}/models/Qwen3-4B-Instruct-Q4_K_M.gguf"
PORT=8080
HOST=127.0.0.1
GPU_LAYERS=25
CTX=4096
THREADS=8
BATCH=512

# 检查模型文件
if [ ! -f "${MODEL}" ]; then
    echo "模型文件不存在: ${MODEL}"
    echo "请从 https://huggingface.co/Qwen/Qwen3-4B-Instruct-GGUF 下载 Q4_K_M 量化版"
    exit 1
fi

# 检查编译产物
if [ ! -x "${LLAMA_DIR}/build/bin/llama-server" ]; then
    echo "llama-server 未找到，请先编译: cd ${LLAMA_DIR} && make -j\$(nproc)"
    exit 1
fi

echo "启动 Llama.cpp 服务..."
echo "  模型: ${MODEL}"
echo "  监听: ${HOST}:${PORT}"
echo "  GPU 层: ${GPU_LAYERS}"
echo "  上下文: ${CTX}"
echo ""

exec "${LLAMA_DIR}/build/bin/llama-server" \
    --model "${MODEL}" \
    --n-gpu-layers "${GPU_LAYERS}" \
    --n-ctx "${CTX}" \
    --threads "${THREADS}" \
    --batch-size "${BATCH}" \
    --port "${PORT}" \
    --host "${HOST}" \
    --mlock
