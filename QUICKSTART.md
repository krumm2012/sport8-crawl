# 快速开始指南

## 🚀 5 分钟快速上手

### 步骤 1：提取登录 Tokens

1. 在浏览器中访问并登录：`https://stadium.sports8.com.cn/StadiumHelper/`

2. 按 **F12** 打开开发者工具 → **Application** 标签

3. 左侧找到 **Local Storage** → `https://stadium.sports8.com.cn`

4. 你会看到类似这样的数据：

   | Key | Value |
   |-----|-------|
   | setCode | 0d7d4b6c-6e0a-41f1-bcdc-ce4f3778cd50-966-13524696546-198818 |
   | setCustId | 199137 |
   | setDeviceFlag | 1 |
   | setLoginname | hehh |
   | setMobile | 13524696546 |
   | setStadiumId | 966 |
   | setToken | 544ebfd4aca9036daf1d6b85e73d8a28 |
   | setUserid | 198818 |

5. 复制这些值

### 步骤 2：创建 login_tokens.json

在项目根目录创建 `login_tokens.json` 文件：

```json
{
  "setCode": "粘贴你的 setCode",
  "setCustId": "粘贴你的 setCustId",
  "setDeviceFlag": "1",
  "setLoginname": "粘贴你的 setLoginname",
  "setMobile": "粘贴你的 setMobile",
  "setStadiumId": "粘贴你的 setStadiumId",
  "setToken": "粘贴你的 setToken",
  "setUserid": "粘贴你的 setUserid"
}
```

### 步骤 3：运行爬虫

```bash
python3 crawl_final.py
```

### 步骤 4：查看结果

数据会保存到：`data/exports/bookings-YYYYMMDD.csv`

用 Excel 或任何文本编辑器打开即可！

---

## 🔄 使用自动登录（可选）

如果你不想每次都手动提取 tokens，可以使用自动登录：

### 前置条件

1. 安装 Selenium：
   ```bash
   pip install selenium
   ```

2. 安装 ChromeDriver：
   ```bash
   # Mac
   brew install chromedriver
   
   # 或从官网下载
   # https://chromedriver.chromium.org/
   ```

### 运行

```bash
python3 auto_login_crawl.py
```

脚本会：
1. 自动打开 Chrome 浏览器
2. 填写用户名和密码
3. 等待你输入验证码并点击登录
4. 自动提取 tokens
5. 开始爬取数据

---

## 📊 数据格式

CSV 文件包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| venue_name | 场馆名称 | 学练馆 |
| court_name | 场地名称 | 学练馆-01 |
| date | 日期 | 2025-11-14 |
| hour | 小时 | 7 |
| status | 状态 | available |
| price | 价格（元） | 70.4 |

### 状态说明

- `available`: 空闲，可预订
- `online_reserved`: 已被线上预订
- `offline_reserved`: 已被线下预订
- `locked`: 锁定或会员专享
- `free`: 免费时段
- `long_term`: 长期预订

---

## ⚠️ 常见问题

### Q: 提示 "签名失效"

**A:** Tokens 已过期（通常几小时后），重新提取最新的 tokens 即可。

### Q: 如何修改爬取天数？

**A:** 编辑脚本中的这一行：
```python
days = 7  # 改成你需要的天数
```

### Q: CSV 文件中文乱码？

**A:** 用 Excel 打开时选择 "UTF-8" 编码，或者用 Numbers/Google Sheets 打开。

---

## 💡 小贴士

1. **Tokens 有效期**：通常几小时，建议每次爬取前检查
2. **请求频率**：脚本已内置 0.5 秒延迟，避免过快
3. **数据备份**：建议定期备份 CSV 文件
4. **自动化**：可以配合 cron/Task Scheduler 实现定时爬取

---

## 🆘 需要帮助？

查看完整文档：`README.md`

或检查以下文件：
- `crawl_final.py` - 主爬虫脚本
- `auto_login_crawl.py` - 自动登录版本
- `login_tokens.json.example` - Tokens 示例文件


