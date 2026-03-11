#!/bin/bash
# 停止同步任务循环模式

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/sync_loop.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到 PID 文件，可能任务未运行"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 不存在，可能已经停止"
    rm -f "$PID_FILE"
    exit 1
fi

echo "正在停止同步循环任务 (PID: $PID)..."
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 如果还在运行，强制终止
if ps -p "$PID" > /dev/null 2>&1; then
    echo "强制终止进程..."
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
echo "✓ 同步循环任务已停止"





