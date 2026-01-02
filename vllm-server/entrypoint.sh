#!/bin/bash
set -e

echo "🔧 Preparing WSL2 GPU environment..."

# 1. 建立存放修補庫的目錄
mkdir -p /tmp/gpu_libs

# 2. 建立 libcuda.so 符號連結 (解決 WSL2 下 triton 編譯找不到庫的問題)
if [ -f "/usr/lib/wsl/lib/libcuda.so.1" ]; then
    echo "🔗 Symlinking libcuda.so.1 to libcuda.so..."
    ln -sf /usr/lib/wsl/lib/libcuda.so.1 /tmp/gpu_libs/libcuda.so
else
    echo "⚠️  WARNING: /usr/lib/wsl/lib/libcuda.so.1 not found. CUDA Graph compilation might fail."
fi

# 3. 設定 LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/tmp/gpu_libs:/usr/lib/wsl/lib:$LD_LIBRARY_PATH
echo "📂 LD_LIBRARY_PATH set to: $LD_LIBRARY_PATH"

echo "🚀 Starting vLLM server..."
# 執行傳入的指令 (vllm serve ...)
exec "$@"
