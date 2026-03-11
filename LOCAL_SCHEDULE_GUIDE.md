# Mac 本地定时任务指南

本指南将帮助你在 Mac 上设置本地定时任务，自动执行数据爬取和同步。

## 📋 前置要求

1. **Python 3.9+** 已安装
2. **项目依赖** 已安装（`pip install -r requirements.txt`）
3. **Chrome 和 ChromeDriver**（如果使用自动登录）

## 🚀 快速开始

### 方式 1：使用自动设置脚本（推荐）

```bash
# 1. 运行设置脚本
./setup_schedule.sh

# 2. 按提示操作（选择是否创建多个时间点）
```

### 方式 2：手动设置

#### 步骤 1：测试执行脚本

```bash
# 确保脚本有执行权限
chmod +x run_scheduled.sh

# 手动执行一次，测试是否正常
./run_scheduled.sh
```

#### 步骤 2：创建 launchd 配置文件

创建文件：`~/Library/LaunchAgents/com.sport8.crawler.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sport8.crawler</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/你的用户名/Documents/sport8-crawl/run_scheduled.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/你的用户名/Documents/sport8-crawl</string>
    
    <key>StandardOutPath</key>
    <string>/Users/你的用户名/Documents/sport8-crawl/logs/launchd_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/你的用户名/Documents/sport8-crawl/logs/launchd_stderr.log</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**注意**：将路径中的 `你的用户名` 替换为你的实际用户名。

#### 步骤 3：加载任务

```bash
# 加载任务
launchctl load ~/Library/LaunchAgents/com.sport8.crawler.plist

# 查看任务状态
launchctl list | grep com.sport8.crawler
```

## ⏰ 默认执行时间

- **数据爬取**：每天 08:00、12:00、18:00（如果创建了多个任务）
- **数据同步**：每次爬取后自动执行一次

## 🔧 自定义执行时间

### 修改单个任务时间

编辑 plist 文件中的 `StartCalendarInterval`：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>    <!-- 修改小时 -->
    <key>Minute</key>
    <integer>30</integer>    <!-- 修改分钟 -->
</dict>
```

然后重新加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.sport8.crawler.plist
launchctl load ~/Library/LaunchAgents/com.sport8.crawler.plist
```

### 创建多个时间点

可以创建多个 plist 文件，每个文件对应一个执行时间：

- `com.sport8.crawler_08.plist` - 08:00
- `com.sport8.crawler_12.plist` - 12:00
- `com.sport8.crawler_18.plist` - 18:00

## 📊 查看日志

```bash
# 查看今天的执行日志
tail -f logs/scheduled_$(date +%Y%m%d).log

# 查看 launchd 标准输出
tail -f logs/launchd_stdout.log

# 查看 launchd 错误日志
tail -f logs/launchd_stderr.log
```

## 🛠️ 常用命令

### 查看任务状态

```bash
# 查看所有相关任务
launchctl list | grep com.sport8.crawler

# 查看任务详情
launchctl list com.sport8.crawler
```

### 手动执行任务

```bash
# 直接执行脚本
./run_scheduled.sh

# 或使用 Python 直接执行
python3 scheduler.py crawl  # 只执行爬取
python3 scheduler.py sync    # 只执行同步
```

### 卸载任务

```bash
# 卸载单个任务
launchctl unload ~/Library/LaunchAgents/com.sport8.crawler.plist

# 卸载所有相关任务
launchctl unload ~/Library/LaunchAgents/com.sport8.crawler*.plist
```

### 重新加载任务

```bash
# 修改配置后重新加载
launchctl unload ~/Library/LaunchAgents/com.sport8.crawler.plist
launchctl load ~/Library/LaunchAgents/com.sport8.crawler.plist
```

## 🔄 同步任务循环模式

如果你想让同步任务在 07:00-23:00 每 15 分钟执行一次，可以使用提供的脚本：

### 启动循环模式

```bash
# 启动同步循环任务（07:00-23:00 每 15 分钟）
./start_sync_loop.sh

# 查看日志
tail -f logs/sync_loop_$(date +%Y%m%d).log
```

### 停止循环模式

```bash
# 停止同步循环任务
./stop_sync_loop.sh
```

### 配置说明

确保 `config/sport8_sync.json` 中的配置正确：

```json
{
  "loop_enabled": true,
  "loop_interval": 900,
  "window_start": 7,
  "window_end": 23
}
```

- `loop_enabled: true` - 启用循环模式
- `loop_interval: 900` - 间隔 900 秒（15 分钟）
- `window_start: 7` - 开始时间 07:00
- `window_end: 23` - 结束时间 23:00

### 手动启动（备选）

如果脚本不可用，也可以手动运行：

```bash
# 在后台运行同步循环
nohup python3 integrations/sport8_sync.py --loop > logs/sync_loop.log 2>&1 &

# 查看进程
ps aux | grep sport8_sync

# 停止进程
pkill -f "sport8_sync.py --loop"
```

## ❓ 常见问题

### Q: 任务没有执行？

A: 检查以下几点：
1. 任务是否已加载：`launchctl list | grep com.sport8.crawler`
2. 查看错误日志：`cat logs/launchd_stderr.log`
3. 检查脚本权限：`ls -l run_scheduled.sh`
4. 手动执行测试：`./run_scheduled.sh`

### Q: 如何修改执行时间？

A: 编辑 plist 文件中的 `StartCalendarInterval`，然后重新加载任务。

### Q: 如何立即执行一次？

A: 直接运行：`./run_scheduled.sh`

### Q: 任务会在 Mac 休眠时执行吗？

A: 不会。launchd 任务只在 Mac 唤醒时检查是否错过了执行时间。如果需要唤醒时执行，可以添加 `Wake` 键。

### Q: 如何让任务在 Mac 启动时也执行？

A: 在 plist 文件中设置：
```xml
<key>RunAtLoad</key>
<true/>
```

## 📝 配置文件位置

- **任务脚本**：`run_scheduled.sh`
- **设置脚本**：`setup_schedule.sh`
- **launchd 配置**：`~/Library/LaunchAgents/com.sport8.crawler.plist`
- **日志目录**：`logs/`

## 🎯 推荐配置

1. **每天 3 次爬取**：08:00、12:00、18:00
2. **同步任务**：每次爬取后自动执行一次
3. **日志保留**：建议定期清理旧日志（保留最近 7 天）

## 📚 相关文档

- [README.md](README.md) - 项目总体说明
- [sport8_INTEGRATION_GUIDE.md](sport8_INTEGRATION_GUIDE.md) - 同步功能说明

