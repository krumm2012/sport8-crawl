# 📚 文档索引

## 🚀 快速开始

| 你想要... | 查看文档 | 时间 |
|-----------|----------|------|
| **最快开始使用** | [QUICKSTART.md](QUICKSTART.md) | 5 分钟 |
| **Docker 部署** | [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | 5 分钟 |
| **了解完整功能** | [README.md](README.md) | 10 分钟 |
| **选择登录方案** | [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md) | 5 分钟 |

---

## 📖 文档列表

### 用户文档

#### 1. [QUICKSTART.md](QUICKSTART.md) ⭐ 最推荐
**5 分钟快速开始指南**
- 最快的使用方法
- 一步步的操作指南
- 适合所有用户

#### 2. [README.md](README.md)
**完整项目文档**
- 项目介绍和功能
- 安装和配置
- 详细使用说明
- 常见问题解答

#### 3. [SUMMARY.md](SUMMARY.md)
**项目总结**
- 项目目标和成果
- 数据示例
- 技术实现
- 遇到的挑战

---

### 技术文档

#### 4. [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md)
**自动登录方案对比指南**
- 5 种登录方案对比
- 每种方案的优缺点
- 使用场景和建议
- 快速决策树

#### 5. [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md)
**Token 提取方法完整指南**
- 8 种 token 提取方法
- 每种方法的成功率
- 问题根源分析
- 技术洞察和经验

#### 6. [FINAL_SUMMARY.md](FINAL_SUMMARY.md)
**最终总结**
- 项目完成情况
- 所有方案汇总
- 最终建议
- 使用指南

#### 7. [CAPTCHA_GUIDE.md](CAPTCHA_GUIDE.md) ✨ 新增
**验证码识别指南**
- 自动验证码识别（100% 识别率）
- 多种使用方法
- API 参考文档
- 集成到爬虫

#### 8. [LOCAL_SCHEDULE_GUIDE.md](LOCAL_SCHEDULE_GUIDE.md) 🕐 新增
**Mac 本地定时任务指南**
- launchd 定时任务设置
- 自动执行配置
- 日志查看和管理
- 常见问题解答

---

## 🛠️ 脚本文件

### 核心爬虫

#### 1. `auto_crawl.py` ⭐ 最推荐
**一键自动爬虫（手动验证码）**
- 自动登录（手动输入验证码）
- 自动提取 tokens
- 自动爬取数据

```bash
python3 auto_crawl.py
```

#### 2. `auto_crawl_with_ocr.py` ✨ 新增
**全自动爬虫（自动验证码识别）**
- 自动识别验证码（100% 识别率）
- 完全自动化
- 无需手动操作

```bash
python3 auto_crawl_with_ocr.py
```

#### 3. `crawl_final.py`
**主爬虫脚本（使用手动 tokens）**
- 最稳定（100% 成功率）
- 最快速（30 秒完成）
- 无需额外依赖

```bash
python3 crawl_final.py
```

#### 4. `captcha_recognizer.py` ✨ 新增
**验证码识别工具**
- 100% 识别率
- 命令行/Python API
- 批量测试

```bash
python3 captcha_recognizer.py
```

#### 5. `simple_auto_login.py`
**简化自动登录**
- 自动填写用户名密码
- 尝试自动提取 tokens
- 失败时提示手动输入

```bash
python3 simple_auto_login.py
```

#### 6. `auto_login_v2.py`
**多方法尝试版**
- 包含 7 种提取方法
- 详细的调试信息
- 适合研究和调试

```bash
python3 auto_login_v2.py
```

#### 7. `auto_login_v3_network.py`
**网络拦截版**
- 使用 Chrome DevTools Protocol
- 拦截网络请求
- 高级技术方案

```bash
python3 auto_login_v3_network.py
```

#### 8. `diagnose_token_issue.py`
**诊断工具**
- 10 个诊断步骤
- 详细的问题分析
- 帮助理解为什么失败

```bash
python3 diagnose_token_issue.py
```

#### 9. `integrations/sport8_sync.py` ✨ 新增
**Sport8 第三方同步**
- 自动把 CSV 预约/订单同步到 Sport8
- 先创建预约再记账支付
- 支持 dry-run 与 15 分钟轮询
- 配置：`config/sport8_sync.json`（CLI 参数可覆盖）

```bash
python3 integrations/sport8_sync.py --loop
```

#### 10. `run_scheduled.sh` 🕐 新增
**定时任务执行脚本（Mac 本地）**
- 自动执行数据爬取和同步
- 日志记录
- 虚拟环境自动激活

```bash
./run_scheduled.sh  # 手动执行一次
```

#### 11. `setup_schedule.sh` 🕐 新增
**定时任务设置脚本（Mac）**
- 自动创建 launchd 配置文件
- 支持多个时间点
- 一键安装定时任务

```bash
./setup_schedule.sh  # 设置定时任务
```

#### 12. `scheduler.py`
**Python 定时任务调度器（可选）**
- 可用于手动执行或测试
- 支持单次执行和循环模式

```bash
python3 scheduler.py        # 启动调度器（不推荐，使用 launchd 更好）
python3 scheduler.py crawl  # 执行一次爬取
python3 scheduler.py sync   # 执行一次同步
```

---

### 辅助工具

#### 11. `example_usage.py`
**使用示例**
- 5 个实用示例
- 过滤和处理数据
- 生成报告

```bash
python3 example_usage.py
```

#### 12. `test_all_methods.sh`
**测试脚本**
- 检查环境
- 推荐方案
- 快速测试

```bash
bash test_all_methods.sh
```

---

## 📁 配置文件

### 1. `login_tokens.json`
**登录凭据**
- 存储 tokens
- 用于爬虫认证
- ⚠️ 不要提交到 Git

### 2. `login_tokens.json.example`
**Tokens 模板**
- 示例格式
- 帮助创建配置

### 3. `requirements.txt`
**Python 依赖**
- 所需的包
- 版本要求

```bash
pip install -r requirements.txt
```

### 4. `.gitignore`
**Git 忽略文件**
- 保护敏感信息
- 忽略临时文件

### 5. `config/sport8_sync.json`
**Sport8 同步配置**
- 第三方系统账号信息
- 场地映射关系
- 时间窗口配置

### 6. `run_scheduled.sh` 🕐 新增
**定时任务执行脚本**
- 自动检测 Python 环境
- 自动激活虚拟环境
- 执行爬取和同步任务
- 日志记录

### 7. `setup_schedule.sh` 🕐 新增
**定时任务设置脚本**
- 创建 launchd 配置文件
- 自动安装定时任务
- 支持多个时间点

---

## 🎯 使用场景导航

### 场景 1：我是第一次使用

**推荐路径**：
1. 阅读 [QUICKSTART.md](QUICKSTART.md)（5 分钟）
2. 按照步骤提取 tokens
3. 运行 `python3 crawl_final.py`

**预计时间**：10 分钟

---

### 场景 2：我想了解所有功能

**推荐路径**：
1. 阅读 [README.md](README.md)（10 分钟）
2. 查看 [SUMMARY.md](SUMMARY.md)（5 分钟）
3. 运行 `python3 example_usage.py` 查看示例

**预计时间**：20 分钟

---

### 场景 3：我想尝试自动登录

**推荐路径**：
1. 阅读 [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md)（5 分钟）
2. 选择合适的方案
3. 运行对应的脚本

**推荐方案**：
- 新手：`simple_auto_login.py`
- 技术用户：`auto_login_v2.py`
- 研究者：`diagnose_token_issue.py`

**预计时间**：10-30 分钟

---

### 场景 4：遇到问题需要调试

**推荐路径**：
1. 运行 `python3 diagnose_token_issue.py`
2. 查看诊断结果
3. 阅读 [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md)
4. 如果仍有问题，回到手动方式（最可靠）

**预计时间**：15-30 分钟

---

### 场景 5：我想深入研究技术

**推荐路径**：
1. 阅读 [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md)（15 分钟）
2. 阅读 [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md)（10 分钟）
3. 阅读 [FINAL_SUMMARY.md](FINAL_SUMMARY.md)（10 分钟）
4. 查看所有脚本的源代码
5. 运行 `diagnose_token_issue.py` 观察详细过程

**预计时间**：1-2 小时

---

## 🔍 快速查找

### 我想知道...

| 问题 | 查看 |
|------|------|
| 如何快速开始？ | [QUICKSTART.md](QUICKSTART.md) |
| 如何设置定时任务？ | [LOCAL_SCHEDULE_GUIDE.md](LOCAL_SCHEDULE_GUIDE.md) |
| 有哪些功能？ | [README.md](README.md) |
| 如何选择登录方案？ | [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md) |
| 为什么无法获取 token？ | [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md) |
| 项目完成了什么？ | [FINAL_SUMMARY.md](FINAL_SUMMARY.md) |
| 如何使用高级功能？ | `example_usage.py` |
| 如何调试问题？ | `diagnose_token_issue.py` |

---

## 📊 文档阅读顺序建议

### 对于普通用户

```
QUICKSTART.md (5分钟)
    ↓
运行 crawl_final.py
    ↓
查看 example_usage.py（可选）
```

### 对于技术用户

```
README.md (10分钟)
    ↓
AUTO_LOGIN_GUIDE.md (5分钟)
    ↓
选择并运行自动登录脚本
    ↓
TOKEN_EXTRACTION_METHODS.md（如果遇到问题）
```

### 对于开发者/研究者

```
README.md (10分钟)
    ↓
SUMMARY.md (5分钟)
    ↓
TOKEN_EXTRACTION_METHODS.md (15分钟)
    ↓
AUTO_LOGIN_GUIDE.md (10分钟)
    ↓
FINAL_SUMMARY.md (10分钟)
    ↓
阅读所有脚本源代码
    ↓
运行 diagnose_token_issue.py
```

---

## 🆘 遇到问题？

### 第一步：查看文档
- [QUICKSTART.md](QUICKSTART.md) - 基本使用
- [README.md](README.md) - 常见问题

### 第二步：运行诊断
```bash
python3 diagnose_token_issue.py
```

### 第三步：查看详细分析
- [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md)
- [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md)

### 第四步：使用最可靠的方案
```bash
# 手动提取 tokens（100% 成功）
python3 crawl_final.py
```

---

## 💡 提示

- 📌 **最推荐**：手动提取 tokens（30 秒，100% 成功）
- 🔧 **半自动**：`simple_auto_login.py`（自动 + 手动兜底）
- 🔬 **研究**：`diagnose_token_issue.py`（了解技术细节）
- 📚 **学习**：阅读所有文档（深入理解）

---

## 🎉 开始使用

选择一个方案，开始你的爬虫之旅！

```bash
# 最快方式（推荐）
python3 crawl_final.py

# 或尝试自动化
python3 simple_auto_login.py

# 或深入研究
python3 diagnose_token_issue.py
```

---

*最后更新：2025-11-18*  
*版本：v2.2.0（移除 Docker，改用 Mac 本地定时任务）*

