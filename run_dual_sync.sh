#!/bin/bash
# Sport8 & Meituan 双地址同步定时脚本
# 每30分钟执行一次 (7:00-23:00)

set -euo pipefail

PROJECT_DIR="/Users/mxchip/Documents"
LOCK_FILE="/tmp/sync_dual_all.lock"
LOG_FILE="$PROJECT_DIR/logs/sync_dual_cron.log"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 防止重复执行
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') 另一个同步任务正在运行，跳过" >> "$LOG_FILE"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

{
echo "========================================"
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始双地址同步"
echo "========================================"

# ========== Sport8 同步 ==========
echo ""
echo "🏟️ Sport8 同步"
echo "----------------------------------------"

cd "$PROJECT_DIR/sport8-crawl"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv-311/bin/activate" ]; then
    source venv-311/bin/activate
fi

# 执行双地址同步
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始 Sport8 双地址同步..."
python3 sync_dual.py --config config/sport8_sync_dual.json 2>&1 || echo "⚠️ Sport8 同步部分失败"

# ========== Meituan 同步 ==========
echo ""
echo "🥡 Meituan 同步"
echo "----------------------------------------"

cd "$PROJECT_DIR/meituan-crawl"

# 激活虚拟环境
if [ -f "venv311/bin/activate" ]; then
    source venv311/bin/activate
fi

# 执行同步到 bakewell.cloud
echo "$(date '+%Y-%m-%d %H:%M:%S') Meituan -> bakewell.cloud..."
python3 -m sync.scheduler --config config.yaml --one-shot 2>&1 || echo "⚠️ Meituan(bakewell) 失败"

# 执行同步到 124.223.13.170
echo "$(date '+%Y-%m-%d %H:%M:%S') Meituan -> 124.223.13.170..."
python3 -m sync.scheduler --config config_backup.yaml --one-shot 2>&1 || echo "⚠️ Meituan(backup) 失败"

echo ""
echo "$(date '+%Y-%m-%d %H:%M:%S') 双地址同步完成"
echo "========================================"
echo ""

} >> "$LOG_FILE" 2>&1

# 清理旧日志（保留7天）
find "$PROJECT_DIR/logs" -name "sync_dual_cron.log*" -mtime +7 -delete 2>/dev/null || true
