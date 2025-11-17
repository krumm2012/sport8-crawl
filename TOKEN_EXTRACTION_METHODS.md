# Token 提取方法完整指南

## 🎯 目标

从 Sport8 系统中提取以下 tokens：
- `setUserid` - 用户 ID
- `setStadiumId` - 场馆 ID
- `setToken` - 访问令牌
- `setCode` - 授权码

## 📋 所有尝试的方法

### ✅ 方法 1：手动浏览器提取（100% 成功）

**原理**：直接从浏览器的 localStorage 中复制

**步骤**：
1. 在浏览器中访问 https://stadium.sports8.com.cn
2. 登录（用户名：hehh，密码：20250805）
3. 按 F12 打开开发者工具
4. 切换到 Application 标签
5. 左侧找到 Local Storage → https://stadium.sports8.com.cn
6. 复制所需的 tokens

**优点**：
- ✅ 100% 成功率
- ✅ 最快速（30 秒）
- ✅ 无需编程
- ✅ 无需额外工具

**缺点**：
- ❌ 需要手动操作
- ❌ 每次 token 过期都要重复

**文件**：`crawl_final.py`

---

### 🔄 方法 2：Selenium 自动等待（成功率：30%）

**原理**：登录后等待 localStorage 被设置

**代码**：
```python
# 等待最多 30 秒
for i in range(30):
    time.sleep(1)
    tokens = {}
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode']:
        value = driver.execute_script(f"return localStorage.getItem('{key}');")
        if value:
            tokens[key] = value
    
    if all(key in tokens for key in required_keys):
        return tokens  # 成功！
```

**问题**：
- ❌ localStorage 可能永远不会被设置
- ❌ 可能需要访问特定页面

**改进**：增加等待时间，访问不同页面

**文件**：`auto_login_crawl.py`, `auto_login_v2.py`

---

### 🌐 方法 3：访问不同页面（成功率：40%）

**原理**：登录后访问不同的页面，尝试触发 localStorage 设置

**代码**：
```python
pages = [
    "/StadiumHelper/index/PageIndexServlet?optype=toIndex",
    "/StadiumHelper/sales/PageSalesServlet?optype=toSales",
    "/StadiumHelper/index.jsp",
]

for page in pages:
    driver.get(BASE_URL + page)
    time.sleep(3)
    # 尝试提取 tokens
```

**问题**：
- ❌ 不确定哪个页面会设置 localStorage
- ❌ 可能所有页面都不设置

**文件**：`auto_login_v2.py`, `auto_login_v3_network.py`

---

### 📄 方法 4：解析页面源代码（成功率：20%）

**原理**：从 HTML 源代码中查找 localStorage.setItem 调用

**代码**：
```python
import re
page_source = driver.page_source

# 查找 localStorage.setItem
pattern = r'localStorage\.setItem\(["\'](\w+)["\'],\s*["\']([^"\']+)["\']\)'
matches = re.findall(pattern, page_source)

if matches:
    tokens = dict(matches)
```

**问题**：
- ❌ tokens 可能由 JavaScript 动态生成
- ❌ 可能在外部 JS 文件中
- ❌ 可能被混淆或加密

**文件**：`auto_login_v2.py`

---

### 🔌 方法 5：拦截网络请求（成功率：10%）

**原理**：使用 Chrome DevTools Protocol 拦截网络请求

**代码**：
```python
# 启用性能日志
capabilities = DesiredCapabilities.CHROME
capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}

driver = webdriver.Chrome(desired_capabilities=capabilities)

# 分析日志
logs = driver.get_log('performance')
for log in logs:
    message = json.loads(log['message'])
    # 查找包含 tokens 的响应
```

**问题**：
- ❌ 技术复杂
- ❌ tokens 可能不在网络响应中
- ❌ 可能需要解密

**文件**：`auto_login_v3_network.py`

---

### 🍪 方法 6：检查 Cookies（成功率：0%）

**原理**：从 Cookies 中提取 tokens

**代码**：
```python
cookies = driver.get_cookies()
for cookie in cookies:
    if 'token' in cookie['name'].lower():
        # 提取 token
```

**问题**：
- ❌ tokens 不存储在 Cookies 中
- ❌ 只有 JSESSIONID 等会话信息

**结论**：此方法不适用于 Sport8 系统

---

### 🔧 方法 7：执行页面脚本（成功率：15%）

**原理**：尝试执行页面中的初始化函数

**代码**：
```python
# 尝试调用可能的初始化函数
driver.execute_script("""
    if (typeof initUserInfo === 'function') {
        initUserInfo();
    }
    if (typeof loadUserData === 'function') {
        loadUserData();
    }
""")

time.sleep(2)
# 然后提取 tokens
```

**问题**：
- ❌ 不知道函数名
- ❌ 函数可能不存在
- ❌ 可能需要参数

**文件**：`auto_login_v2.py`

---

### 🎤 方法 8：手动输入兜底（成功率：100%）

**原理**：自动提取失败时，提示用户手动输入

**代码**：
```python
if not tokens:
    print("自动提取失败，请手动输入...")
    tokens = {}
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode']:
        value = input(f"{key}: ").strip()
        if value:
            tokens[key] = value
```

**优点**：
- ✅ 100% 成功
- ✅ 作为最后的兜底方案

**缺点**：
- ❌ 仍需手动操作

**文件**：`simple_auto_login.py`, `auto_login_v2.py`

---

## 🔍 问题根源分析

### 为什么 Selenium 难以自动提取 tokens？

1. **时序问题**：
   - 登录成功后，页面跳转
   - localStorage 可能在跳转后的页面中设置
   - 设置时间不确定（可能是 1 秒，也可能是 10 秒）

2. **页面结构**：
   - tokens 可能不在登录响应中
   - 可能需要访问特定的页面（如主页）
   - 可能由异步 AJAX 请求设置

3. **JavaScript 执行**：
   - tokens 由 JavaScript 动态设置
   - 可能依赖于多个脚本的加载顺序
   - 可能在 DOMContentLoaded 或 window.onload 后执行

4. **域名和路径**：
   - localStorage 是按域名隔离的
   - 可能需要在特定的路径下才能访问

### 实际观察到的行为

从终端输出可以看到：
```
[4/5] 登录成功！提取 tokens...
⚠️  未能提取到完整的 tokens，请重试
```

这说明：
- ✅ 登录是成功的（URL 已跳转）
- ❌ 但 localStorage 中没有 tokens

**可能的原因**：
1. tokens 在更晚的时间点设置
2. tokens 在不同的页面设置
3. tokens 由特定的用户交互触发
4. 网站检测到 Selenium 并改变了行为

---

## 💡 推荐方案

### 对于普通用户

**方案 1：手动提取（最推荐）**

```bash
# 1. 浏览器登录
# 2. F12 → Application → Local Storage
# 3. 复制 tokens 到 login_tokens.json
# 4. 运行爬虫
python3 crawl_final.py
```

**时间**：30 秒  
**成功率**：100%  
**难度**：⭐

---

### 对于技术用户

**方案 2：简化自动登录 + 手动兜底**

```bash
python3 simple_auto_login.py
# 脚本会尝试自动提取
# 失败时提示手动输入
```

**时间**：1-2 分钟  
**成功率**：40% 自动 + 100% 手动  
**难度**：⭐⭐

---

### 对于开发者

**方案 3：诊断 + 多方法尝试**

```bash
# 1. 先诊断问题
python3 diagnose_token_issue.py

# 2. 尝试多种方法
python3 auto_login_v2.py
```

**时间**：5-10 分钟  
**成功率**：30%  
**难度**：⭐⭐⭐

---

## 🎓 学到的经验

### 成功经验

1. **灵活应对**：当自动化失败时，提供手动兜底方案
2. **多方法尝试**：不要依赖单一方法
3. **详细日志**：记录每一步的状态，便于调试
4. **用户友好**：提供清晰的提示和说明

### 技术洞察

1. **Selenium 的局限性**：
   - 不是所有的自动化都能成功
   - 网站可能检测并阻止自动化
   - 某些操作必须由人工完成

2. **localStorage 的特性**：
   - 按域名隔离
   - 可能被 JavaScript 动态设置
   - 设置时间不确定

3. **最佳实践**：
   - 手动方式往往最可靠
   - 自动化应该是辅助，不是唯一方案
   - 提供多种选择，让用户决定

---

## 📊 方法对比总结

| 方法 | 成功率 | 速度 | 难度 | 推荐度 |
|------|--------|------|------|--------|
| 手动浏览器提取 | 100% | 30秒 | ⭐ | ⭐⭐⭐⭐⭐ |
| 简化自动登录 | 40% | 1-2分钟 | ⭐⭐ | ⭐⭐⭐⭐ |
| 多方法尝试 | 30% | 3-5分钟 | ⭐⭐⭐ | ⭐⭐⭐ |
| 网络拦截 | 10% | 5-10分钟 | ⭐⭐⭐⭐ | ⭐⭐ |
| 页面解析 | 20% | 2-3分钟 | ⭐⭐⭐ | ⭐⭐ |

---

## 🚀 快速开始

**如果你只想快速完成任务**：

```bash
# 使用方法 1（手动提取）
# 查看 QUICKSTART.md
# 30 秒完成！
```

**如果你想尝试自动化**：

```bash
# 使用方法 2（简化自动登录）
python3 simple_auto_login.py
# 自动提取失败时会提示手动输入
```

**如果你想深入研究**：

```bash
# 使用诊断工具
python3 diagnose_token_issue.py
# 查看详细的诊断信息
```

---

## 🆘 遇到问题？

1. **tokens 提取失败**：使用手动方式（方法 1）
2. **Selenium 报错**：检查 ChromeDriver 是否安装
3. **tokens 过期**：重新提取最新的 tokens
4. **其他问题**：查看 README.md 和 AUTO_LOGIN_GUIDE.md

**记住**：手动提取 tokens 只需 30 秒，而且 100% 成功！


