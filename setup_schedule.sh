#!/bin/bash
# Mac 定时任务设置脚本
# 使用 launchd 创建定时任务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Mac 定时任务设置"
echo "=========================================="
echo ""

# 检查必要文件
if [ ! -f "run_scheduled.sh" ]; then
    echo "❌ 错误: 未找到 run_scheduled.sh"
    exit 1
fi

# 确保脚本有执行权限
chmod +x run_scheduled.sh
echo "✓ 已设置执行权限"
echo ""

# 创建 launchd plist 文件
PLIST_NAME="com.sport8.crawler"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# 获取脚本的绝对路径
RUN_SCRIPT="$SCRIPT_DIR/run_scheduled.sh"

echo "创建 launchd 配置文件..."
cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${RUN_SCRIPT}</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
    
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/logs/launchd_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/logs/launchd_stderr.log</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

echo "✓ 配置文件已创建: $PLIST_FILE"
echo ""

# 创建多个时间点的任务（可选）
echo "是否创建多个时间点的任务？(08:00, 12:00, 18:00)"
read -p "输入 y 创建，其他键跳过: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 创建 12:00 的任务
    PLIST_FILE_12="$HOME/Library/LaunchAgents/${PLIST_NAME}_12.plist"
    cp "$PLIST_FILE" "$PLIST_FILE_12"
    sed -i '' "s/<integer>8<\/integer>/<integer>12<\/integer>/" "$PLIST_FILE_12"
    sed -i '' "s/${PLIST_NAME}/${PLIST_NAME}_12/g" "$PLIST_FILE_12"
    echo "✓ 已创建 12:00 任务"
    
    # 创建 18:00 的任务
    PLIST_FILE_18="$HOME/Library/LaunchAgents/${PLIST_NAME}_18.plist"
    cp "$PLIST_FILE" "$PLIST_FILE_18"
    sed -i '' "s/<integer>8<\/integer>/<integer>18<\/integer>/" "$PLIST_FILE_18"
    sed -i '' "s/${PLIST_NAME}/${PLIST_NAME}_18/g" "$PLIST_FILE_18"
    echo "✓ 已创建 18:00 任务"
fi

echo ""
echo "=========================================="
echo "安装定时任务"
echo "=========================================="
echo ""

# 卸载旧任务（如果存在）
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "卸载旧任务..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# 加载新任务
echo "加载定时任务..."
launchctl load "$PLIST_FILE"

if [ -f "$PLIST_FILE_12" ]; then
    launchctl load "$PLIST_FILE_12" 2>/dev/null || true
fi

if [ -f "$PLIST_FILE_18" ]; then
    launchctl load "$PLIST_FILE_18" 2>/dev/null || true
fi

echo "✓ 定时任务已安装"
echo ""

# 显示任务状态
echo "=========================================="
echo "任务状态"
echo "=========================================="
launchctl list | grep "$PLIST_NAME" || echo "未找到运行中的任务（这是正常的，任务会在指定时间执行）"
echo ""

echo "=========================================="
echo "完成！"
echo "=========================================="
echo ""
echo "常用命令："
echo "  查看任务列表: launchctl list | grep $PLIST_NAME"
echo "  卸载任务:     launchctl unload $PLIST_FILE"
echo "  重新加载:     launchctl load $PLIST_FILE"
echo "  立即测试:     ./run_scheduled.sh"
echo "  查看日志:     tail -f logs/scheduled_\$(date +%Y%m%d).log"
echo ""
echo "配置文件位置:"
echo "  $PLIST_FILE"
echo ""

