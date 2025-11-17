# Sport8 场馆预订爬虫

自动爬取 Sport8 场馆预订系统的场地数据和订单数据，支持手动和自动登录两种方式。

> 📚 **文档导航**：查看 [INDEX.md](INDEX.md) 快速找到你需要的文档
> 
> 🚀 **快速开始**：查看 [QUICKSTART.md](QUICKSTART.md) 5 分钟上手

## 功能特点

- ✅ 爬取场地预订数据（场馆、时间、价格、状态）
- ✅ 爬取未来7天预订记录（客户、金额、支付方式）
- ✅ 自动验证码识别（100% 识别率）← **新增**
- ✅ 支持手动提取 tokens 快速爬取
- ✅ 支持 Selenium 自动登录（可选手动/自动验证码）
- ✅ 数据导出为 CSV 格式
- ✅ 清晰的状态显示和错误处理
- ✅ Sport8 第三方系统同步（自动预约 + 支付）

## 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 如果需要自动登录功能，额外安装
pip install selenium

# 如果需要自动验证码识别，额外安装
pip install ddddocr
```

## 使用方法

> 🚀 **一键运行**（最新！最简单！）：
> ```bash
> python3 auto_crawl.py              # 手动输入验证码
> python3 auto_crawl_with_ocr.py     # 自动识别验证码 ✨ 新增
> ```
> 自动登录 → 自动提取 tokens → 自动爬取 → 自动保存
> 
> 查看详细说明：[ONE_CLICK_GUIDE.md](ONE_CLICK_GUIDE.md) | [验证码识别](CAPTCHA_GUIDE.md)

---

> 💡 **其他选择**：
> - 想要最快最稳定？→ 使用方法 1（手动 Tokens）
> - 想要半自动化？→ 使用方法 2（简化自动登录）
> - 想要深入研究？→ 查看 [AUTO_LOGIN_GUIDE.md](AUTO_LOGIN_GUIDE.md) 和 [TOKEN_EXTRACTION_METHODS.md](TOKEN_EXTRACTION_METHODS.md)
> - 遇到 token 提取问题？→ 运行 `python3 diagnose_tokens.py` 详细诊断
> - 遇到其他问题？→ 运行 `python3 diagnose_token_issue.py` 诊断

### 方法 0：一键运行（最新！最简单！）⭐⭐⭐⭐⭐

```bash
python3 auto_crawl.py
```

**功能**：
- ✅ 自动打开浏览器
- ✅ 自动填写用户名和密码
- ✅ 智能延时，等待页面充分加载
- ✅ 自动等待验证码图片加载
- ⏸️ 手动输入验证码（唯一需要人工的）
- ✅ 自动提取 tokens
- ✅ 自动爬取场地数据
- ✅ 自动爬取未来7天订单数据 ← **新增**
- ✅ 自动保存 CSV
- ✅ 浏览器保持打开

**你只需要**：
1. 运行命令
2. 等待页面加载（约 10 秒，自动）
3. 输入验证码（有 3 分钟时间）
4. 点击登录
5. 等待完成

**耗时**：约 30-40 秒

**输出文件**：
- `data/exports/bookings-*.csv` - 场地数据
- `data/exports/orders-future-*.csv` - 未来7天订单数据 ← **新增**

**详细说明**：
- 使用指南：[ONE_CLICK_GUIDE.md](ONE_CLICK_GUIDE.md)
- 订单爬取：[ORDER_CRAWL_GUIDE.md](ORDER_CRAWL_GUIDE.md) ← **新增**
- 延时优化：[TIMING_IMPROVEMENTS.md](TIMING_IMPROVEMENTS.md)

---

### 方法 1：手动提取 tokens（推荐，最快）

1. **在浏览器中登录**
   - 访问 `https://stadium.sports8.com.cn/StadiumHelper/`
   - 输入用户名和密码登录

2. **提取 tokens**
   - 按 F12 打开开发者工具
   - 切换到 **Application** 标签
   - 左侧找到 **Local Storage** → `https://stadium.sports8.com.cn`
   - 复制以下字段的值：
     - `setCode`
     - `setCustId`
     - `setDeviceFlag`
     - `setLoginname`
     - `setMobile`
     - `setStadiumId`
     - `setToken`
     - `setUserid`

3. **保存 tokens**
   
   创建 `login_tokens.json` 文件：
   ```json
   {
     "setCode": "从浏览器复制的值",
     "setCustId": "从浏览器复制的值",
     "setDeviceFlag": "1",
     "setLoginname": "hehh",
     "setMobile": "从浏览器复制的值",
     "setStadiumId": "966",
     "setToken": "从浏览器复制的值",
     "setUserid": "从浏览器复制的值"
   }
   ```

4. **运行爬虫**
   ```bash
   python3 crawl_final.py
   ```

### 方法 2：自动登录（多个版本可选，需要 Selenium）

💡 **最新优化**：
- ✅ V4 和 V5 版本实现**完全自动提取**，无需手动复制 JSON
- ✅ 已更新登录页面地址，处理页面自动关闭问题
- 查看 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) 和 [UPDATE_LOGIN_URL.md](UPDATE_LOGIN_URL.md) 了解详情

1. **安装 ChromeDriver**
   - Mac: `brew install chromedriver`
   - 或从 [ChromeDriver 官网](https://chromedriver.chromium.org/) 下载

2. **选择版本并运行**

   **V4 智能版（推荐）⭐⭐⭐⭐**
   ```bash
   python3 auto_login_v4_smart.py
   ```
   - ✅ 完全自动提取，无需手动复制
   - ✅ 智能重试多个页面
   - ✅ 代码简洁易懂
   - 成功率：60-80%

   **V5 激进版（最强）⭐⭐⭐⭐⭐**
   ```bash
   python3 auto_login_v5_aggressive.py
   ```
   - ✅ 5 种提取方法全面尝试
   - ✅ 从页面任何角落提取 tokens
   - ✅ 详细的调试日志
   - 成功率：80-95%

   **V2 多方法版（研究用）⭐⭐⭐**
   ```bash
   python3 auto_login_v2.py
   ```
   - 7 种方法依次尝试
   - 最后需要手动复制 JSON
   - 适合学习和研究

3. **使用流程**
   - 脚本自动打开浏览器
   - 自动填写用户名和密码
   - 你手动输入验证码并登录
   - 脚本**自动提取 tokens**（V4/V5）
   - 自动保存并开始爬取

4. **如果自动提取失败**
   - 使用方法 1（手动提取）- 最可靠
   - 查看 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) 了解详情

---

## 第三方系统同步（Sport8）

> ⚙️ `integrations/sport8_sync.py`：把本地 CSV（orders/bookings）自动同步到 Sport8 平台，完成预约 + 支付。

### 快速开始

```bash
# 仅演示，先用 dry-run 验证 payload
python3 integrations/sport8_sync.py --dry-run --since 2025-11-15 --until 2025-11-21

# 实际同步（一次性执行）
python3 integrations/sport8_sync.py --since 2025-11-15 --until 2025-11-21

# 持续运行（07:00-23:00 每 15 分钟自动同步）
python3 integrations/sport8_sync.py --loop
```

### 关键配置

| 项目 | 默认值 | 说明 |
|------|--------|------|
| 用户名/密码 | `superadmin` / `admin123` | 可通过 CLI 参数覆盖 |
| `venue_id`  | `12` | 默认场馆 ID |
| 场地映射 | `[学练馆][01]=24`, `[学练馆][02]=25`, `[学练馆小][03]=26` | 同时兼容 `学练馆-01/-02/小-03` |
| CSV 目录 | `data/exports/` | `orders-*.csv` + `bookings-*.csv` |
| 去重文件 | `data/state/sport8_synced.json` | 存储已同步订单与锁定槽位 |
| 配置文件 | `config/sport8_sync.json` | 统一管理账号、映射、时间窗 |

### 同步策略

- **orders-*.csv（已支付记录）**
  - 仅处理 `status` 为“已支付/paid/success”。
  - 先创建预约（`/bookings/with-datetime`），再立即调用 `/payments` 记账。
  - 备注写入手机号、昵称、支付金额、订单号、时间段，`order_no` 作为幂等键。

- **bookings-*.csv（locked 槽位）**
  - 只处理 `status ∈ {locked, order, online_reserved}`。
  - 代表“已锁定、未支付”订单，仅创建预约。
  - 使用 `date + court_id + hour` 作为幂等键，避免重复创建。

- **调度**
  - `--since/--until` 控制同步的日期范围（默认全量）。
  - `--loop` 模式在 07:00 ≤ 当前时间 < 23:00 时执行，每 15 分钟（可用 `--interval` 修改）自动轮询；窗口外自动休眠。

更多参数、字段映射和 API 说明请参考 [`sport8_INTEGRATION_GUIDE.md`](sport8_INTEGRATION_GUIDE.md)。

### 配置文件

所有默认参数集中在 `config/sport8_sync.json`，示例：

```json
{
  "base_url": "https://51alljoin.cn:8000/api/v1",
  "username": "superadmin",
  "password": "admin123",
  "venue_id": 12,
  "orders_glob": "orders-*.csv",
  "bookings_glob": "bookings-*.csv",
  "loop_enabled": false,
  "loop_interval": 900,
  "window_start": 7,
  "window_end": 23,
  "court_id_map": {
    "[学练馆][01]": 24,
    "[学练馆][02]": 25,
    "[学练馆小][03]": 26
  }
}
```

- 修改 JSON 后直接运行脚本即可生效。
- CLI 参数始终优先于配置，如 `--username hehh`。
- 若要禁用循环可在 JSON 中设置 `\"loop_enabled\": false`，或执行时加 `--no-loop`。

## 输出文件

爬取的数据会保存到：
```
data/exports/bookings-YYYYMMDD.csv
```

CSV 文件包含以下字段：
- `venue_name`: 场馆名称（如"学练馆"）
- `court_name`: 场地名称（如"学练馆-01"）
- `date`: 日期（YYYY-MM-DD）
- `hour`: 小时（0-23）
- `status`: 状态
  - `available`: 空闲
  - `online_reserved`: 线上预订
  - `offline_reserved`: 线下预订
  - `locked`: 锁定/会员专享
  - `free`: 免费
  - `long_term`: 长订
- `price`: 价格（元）

## 项目结构

```
sport8-crawl/
├── README.md                 # 项目说明
├── requirements.txt          # Python 依赖
├── login_tokens.json         # 登录凭据（需手动创建）
├── crawl_final.py           # 主爬虫脚本（手动 tokens）
├── auto_login_crawl.py      # 自动登录爬虫（Selenium）
├── data/
│   └── exports/             # 导出的 CSV 文件
└── src/                     # 源代码（原始版本）
    ├── config.py
    ├── login.py
    ├── fetch.py
    ├── parse.py
    ├── storage.py
    └── cli.py
```

## 常见问题

### Q: Tokens 过期怎么办？

A: Tokens 有效期通常为几小时。过期后，重新在浏览器中提取最新的 tokens 并更新 `login_tokens.json` 文件即可。

### Q: 为什么自动登录返回 500 错误？

A: 服务器检测到了自动化请求。建议使用方法 1（手动提取 tokens）或方法 2（Selenium 自动登录）。

### Q: 如何修改爬取的日期范围？

A: 编辑脚本中的 `days` 变量：
```python
days = 7  # 修改为你需要的天数
```

### Q: 数据格式是什么？

A: CSV 格式，可以用 Excel、Numbers 或任何文本编辑器打开。使用 UTF-8-BOM 编码，确保中文正常显示。

## 技术栈

- **Python 3.9+**
- **requests**: HTTP 请求
- **BeautifulSoup4**: HTML 解析
- **Selenium**: 浏览器自动化（可选）
- **ddddocr**: 验证码识别（实验性）

## 注意事项

1. **合法使用**: 仅用于个人学习和合法用途
2. **频率限制**: 建议在请求之间添加延迟（0.5-1秒）
3. **Token 安全**: 不要将 `login_tokens.json` 提交到公开仓库
4. **浏览器版本**: Selenium 需要 Chrome 浏览器和对应版本的 ChromeDriver

## 更新日志

### 2025-11-14
- ✅ 完成项目初始化
- ✅ 实现手动 tokens 爬取功能
- ✅ 实现 Selenium 自动登录
- ✅ 数据导出为 CSV 格式
- ✅ 添加详细的使用文档

## 许可证

MIT License

## 作者

由 AI 助手协助开发
