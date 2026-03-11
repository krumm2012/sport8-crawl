#!/bin/bash
# 启动同步任务循环模式（07:00-23:00 每 15 分钟）
# 这个脚本会在后台运行，持续执行同步任务

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/sync_loop_$(date +%Y%m%d).log"
PID_FILE="$SCRIPT_DIR/sync_loop.pid"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  同步循环任务已在运行 (PID: $OLD_PID)"
        echo "   如需重启，请先运行: ./stop_sync_loop.sh"
        exit 1
    else
        # PID 文件存在但进程不存在，删除旧文件
        rm -f "$PID_FILE"
    fi
fi

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

PYTHON_CMD=$(which python3)

# 检查虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "venv-311" ]; then
    source venv-311/bin/activate
fi

# 检查同步脚本是否存在
if [ ! -f "integrations/sport8_sync.py" ]; then
    echo "❌ 错误: 未找到 integrations/sport8_sync.py"
    exit 1
fi

echo "=========================================="
echo "启动同步任务循环模式"
echo "=========================================="
echo "执行时间: 07:00 - 23:00"
echo "执行间隔: 每 15 分钟"
echo "日志文件: $LOG_FILE"
echo ""

# 在后台启动同步循环任务
nohup "$PYTHON_CMD" integrations/sport8_sync.py --loop > "$LOG_FILE" 2>&1 &
SYNC_PID=$!

# 保存 PID
echo $SYNC_PID > "$PID_FILE"

echo "✓ 同步循环任务已启动"
echo "  PID: $SYNC_PID"
echo "  日志: tail -f $LOG_FILE"
echo ""
echo "停止命令: ./stop_sync_loop.sh"
echo "或: kill $SYNC_PID"
echo ""





