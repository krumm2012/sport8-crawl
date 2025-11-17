# 目录清理报告

**清理日期**: 2025-11-15  
**清理目的**: 整理项目目录，将临时、测试和过时文件移至归档目录

---

## 📊 清理统计

### 归档文件总数: **55 个文件**

| 分类 | 数量 | 目录 |
|------|------|------|
| 旧版本脚本 | 10 | `archive/old_versions/` |
| 测试脚本 | 11 | `archive/test_scripts/` |
| 调试文件 | 9 | `archive/debug_files/` |
| 临时文件 | 13 | `archive/temp_files/` |
| 过时文档 | 12 | `archive/docs_archive/` |

### 清理效果

- ✅ **根目录文件**: 从 70+ 个减少到 24 个（包含目录）
- ✅ **核心文件**: 18 个（4 个程序 + 9 个文档 + 4 个配置 + 1 个脚本）
- ✅ **目录结构**: 更清晰、更易于导航

---

## 📁 归档目录结构

```
archive/
├── README.md              ← 归档说明文档
├── old_versions/          ← 旧版本脚本（10个）
│   ├── auto_login_v2.py
│   ├── auto_login_v3_network.py
│   ├── auto_login_v4_smart.py
│   ├── auto_login_v5_aggressive.py
│   ├── simple_auto_login.py
│   ├── auto_login_crawl.py
│   ├── selenium_login.py
│   ├── browser_like_login.py
│   ├── exact_browser_login.py
│   └── crawl_with_manual_tokens.py
│
├── test_scripts/          ← 测试脚本（11个）
│   ├── test_all_methods.sh
│   ├── test_api_with_cookies.py
│   ├── test_login_interactive.py
│   ├── test_login_page.py
│   ├── test_new_login.py
│   ├── simple_login_test.py
│   ├── manual_captcha_test.py
│   ├── example_usage.py
│   ├── diagnose_login.py
│   ├── diagnose_token_issue.py
│   └── inspect_order_api.py
│
├── debug_files/           ← 调试文件（9个）
│   ├── login_page_screenshot.png
│   ├── login_page_source.html
│   ├── order_page_screenshot.png
│   ├── order_page_source.html
│   ├── captcha-current.png
│   ├── captcha.jpg
│   ├── login-response.bin
│   ├── api.txt
│   └── orders-20251115.csv  ← 旧格式订单数据
│
├── temp_files/            ← 临时文件（13个）
│   ├── tmp-common.js
│   ├── tmp-index.js
│   ├── tmp-sales.js
│   ├── app.js
│   ├── chunk-common.js
│   ├── chunk-vendors.js
│   ├── index.js
│   ├── validate.js
│   ├── login.jsp
│   ├── extract_browser_tokens.html
│   ├── extract_tokens_from_browser.js
│   ├── get_tokens.html
│   └── copy_browser_request.py
│
└── docs_archive/          ← 过时文档（12个）
    ├── AUTO_FILL_ANALYSIS.md
    ├── BROWSER_KEEP_OPEN.md
    ├── COMPARISON.md
    ├── OPTIMIZATION_SUMMARY.md
    ├── ORDER_API_DEBUG.md
    ├── ORDER_API_FIXED.md
    ├── SPEED_OPTIMIZATION.md
    ├── SUMMARY.md
    ├── TOKEN_FIX.md
    ├── TROUBLESHOOTING.md
    ├── UPDATE_LOGIN_URL.md
    └── VERSION_COMPARISON.md
```

---

## 🎯 当前根目录（核心文件）

### 🚀 主程序（4个）

| 文件 | 用途 |
|------|------|
| `auto_crawl.py` | ⭐ 一键运行（推荐） |
| `crawl_final.py` | 手动 token 方式 |
| `crawl_orders.py` | 单独爬取订单 |
| `diagnose_tokens.py` | Token 诊断工具 |

### 📚 核心文档（9个）

| 文件 | 用途 |
|------|------|
| `readme.md` | 项目总览 |
| `QUICKSTART.md` | 快速开始 |
| `INDEX.md` | 文档索引 |
| `ONE_CLICK_GUIDE.md` | 一键运行指南 |
| `ORDER_CRAWL_GUIDE.md` | 订单爬取指南 |
| `ORDER_DATE_UPDATE.md` | 日期更新说明 |
| `AUTO_LOGIN_GUIDE.md` | 自动登录指南 |
| `TOKEN_EXTRACTION_METHODS.md` | Token 提取方法 |
| `TIMING_IMPROVEMENTS.md` | 时序优化说明 |
| `FINAL_SUMMARY.md` | 最终总结 |

### ⚙️ 配置文件（4个）

| 文件 | 用途 |
|------|------|
| `requirements.txt` | Python 依赖 |
| `run.sh` | 快速运行脚本 |
| `login_tokens.json` | Token 文件（gitignore） |
| `login_tokens.json.example` | Token 示例 |

### 📂 目录（6个）

| 目录 | 用途 |
|------|------|
| `src/` | 源代码模块 |
| `scripts/` | 辅助脚本 |
| `data/` | 数据文件（captcha, debug, exports） |
| `debug_logs/` | 调试日志 |
| `archive/` | ✨ 归档文件（新增） |
| `venv/` | Python 虚拟环境 |

---

## 🔄 清理详情

### 1. 旧版本脚本 → `archive/old_versions/`

**原因**: 项目已稳定，`auto_crawl.py` 已整合所有功能

**归档文件**:
- 各版本自动登录脚本（v2-v5）
- 早期测试版本
- 手动 token 早期版本

### 2. 测试脚本 → `archive/test_scripts/`

**原因**: 开发调试完成，保留 `diagnose_tokens.py` 作为主要诊断工具

**归档文件**:
- 各种测试脚本
- 旧版诊断工具
- API 检查工具

### 3. 调试文件 → `archive/debug_files/`

**原因**: 调试完成，不再需要这些临时文件

**归档文件**:
- 页面截图和源码
- 验证码测试图片
- API 响应数据
- 旧格式订单数据

### 4. 临时文件 → `archive/temp_files/`

**原因**: 开发过程中的临时文件，已不再使用

**归档文件**:
- JavaScript 文件副本
- HTML 辅助页面
- 网站资源副本

### 5. 过时文档 → `archive/docs_archive/`

**原因**: 文档已整合到主文档中，或已过时

**归档文件**:
- 各种开发过程文档
- 问题修复记录
- 版本对比文档

---

## 📝 .gitignore 更新

添加了归档目录的可选忽略规则：

```gitignore
# 归档文件（可选：如果不想提交归档文件，取消注释下一行）
# archive/
```

**建议**:
- 如果你想保留开发历史，可以提交 `archive/` 目录
- 如果只想保留核心代码，可以取消注释以忽略归档目录

---

## 💡 使用建议

### 日常使用

```bash
# 一键运行
python3 auto_crawl.py

# 查看文档
cat readme.md
cat QUICKSTART.md
```

### 查看归档

```bash
# 查看归档说明
cat archive/README.md

# 查看旧版本脚本
ls archive/old_versions/

# 查看过时文档
ls archive/docs_archive/
```

### 恢复文件

如果需要恢复某个归档文件：

```bash
# 复制到根目录
cp archive/old_versions/auto_login_v4_smart.py .

# 或移动回根目录
mv archive/old_versions/auto_login_v4_smart.py .
```

### 删除归档

如果确认不再需要归档文件：

```bash
# 删除整个归档目录
rm -rf archive/

# 或只删除某个子目录
rm -rf archive/temp_files/
```

---

## ✅ 清理验证

### 根目录文件数量

- **清理前**: 70+ 个文件
- **清理后**: 24 个（包含目录）
- **核心文件**: 18 个

### 目录结构

```
sport8-crawl/
├── 主程序 (4)
├── 核心文档 (9)
├── 配置文件 (4)
├── 脚本 (1)
├── src/
├── scripts/
├── data/
├── debug_logs/
├── archive/  ← 新增
└── venv/
```

### 归档目录

```
archive/
├── README.md
├── old_versions/ (10)
├── test_scripts/ (11)
├── debug_files/ (9)
├── temp_files/ (13)
└── docs_archive/ (12)
```

---

## 🎉 清理完成

✅ 目录结构更清晰  
✅ 核心文件易于识别  
✅ 归档文件分类存放  
✅ 保留完整开发历史  
✅ 便于后续维护

---

## 📚 相关文档

- [项目总览](readme.md)
- [快速开始](QUICKSTART.md)
- [文档索引](INDEX.md)
- [归档说明](archive/README.md)


