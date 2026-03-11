#!/bin/bash
# 定时任务执行脚本（Mac 本地版本）
# 用于定时执行数据爬取和同步任务

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/scheduled_$(date +%Y%m%d).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "开始执行定时任务"
log "=========================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    log "❌ 错误: 未找到 python3"
    exit 1
fi

PYTHON_CMD=$(which python3)
log "使用 Python: $PYTHON_CMD"

# 检查虚拟环境（如果存在）
if [ -d "venv" ]; then
    log "激活虚拟环境: venv"
    source venv/bin/activate
elif [ -d "venv-311" ]; then
    log "激活虚拟环境: venv-311"
    source venv-311/bin/activate
fi

# 执行爬取任务
log "开始执行数据爬取任务..."
if [ -f "auto_crawl_with_ocr.py" ]; then
    log "使用: auto_crawl_with_ocr.py"
    "$PYTHON_CMD" auto_crawl_with_ocr.py >> "$LOG_FILE" 2>&1
    CRAWL_EXIT=$?
    if [ $CRAWL_EXIT -eq 0 ]; then
        log "✓ 数据爬取成功"
    else
        log "✗ 数据爬取失败 (退出码: $CRAWL_EXIT)"
    fi
elif [ -f "auto_crawl.py" ]; then
    log "使用: auto_crawl.py"
    "$PYTHON_CMD" auto_crawl.py >> "$LOG_FILE" 2>&1
    CRAWL_EXIT=$?
    if [ $CRAWL_EXIT -eq 0 ]; then
        log "✓ 数据爬取成功"
    else
        log "✗ 数据爬取失败 (退出码: $CRAWL_EXIT)"
    fi
else
    log "⚠️  警告: 未找到爬取脚本"
fi

# 执行同步任务（单次执行，不循环）
log "开始执行数据同步任务..."
if [ -f "integrations/sport8_sync.py" ]; then
    log "使用: integrations/sport8_sync.py (单次执行)"
    "$PYTHON_CMD" integrations/sport8_sync.py >> "$LOG_FILE" 2>&1
    SYNC_EXIT=$?
    if [ $SYNC_EXIT -eq 0 ]; then
        log "✓ 数据同步成功"
    else
        log "✗ 数据同步失败 (退出码: $SYNC_EXIT)"
    fi
else
    log "⚠️  警告: 未找到同步脚本"
fi

# 注意：如果需要同步任务循环模式（07:00-23:00 每15分钟），
# 请单独运行: nohup python3 integrations/sport8_sync.py --loop > logs/sync_loop.log 2>&1 &

log "=========================================="
log "定时任务执行完成"
log "=========================================="

