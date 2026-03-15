# 预订 API 同步策略文档

> 配置名称: **hehaa135booking**
> 最后更新: 2026-03-14

---

## 📊 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Sport8 源站   │────>│   同步脚本       │────>│  bakewell.cloud │
│  (场馆预订系统) │     │  sport8_sync.py  │     │  (目标 API)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        │                        │                        │
   ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
   │ CSV文件 │             │  state  │             │ 数据库  │
   │ 导出    │             │  状态   │             │ 存储    │
   └─────────┘             └─────────┘             └─────────┘
```

---

## 🔧 当前配置

**文件:** `config/sport8_sync.json`

```json
{
  "name": "hehaa135booking",
  "base_url": "https://bakewell.cloud/api/v1",
  "username": "superadmin",
  "password": "superadmin123",
  "venue_id": 11,
  "court_id_map": {
    "学练馆-01": 21,
    "学练馆-02": 22,
    "学练馆小-03": 23
  }
}
```

---

## 🔄 同步策略详解

### 1️⃣ 数据源 (Sport8)

| 数据类型 | 文件模式 | 状态标识 |
|---------|---------|---------|
| **订单数据** | `orders-*.csv` | 已支付 (paid/success) |
| **场地状态** | `bookings-*.csv` | locked/online_reserved |

### 2️⃣ 同步类型

#### A. 订单同步 (Orders)
**触发条件:** CSV 中 status = "已支付" | "paid" | "success"

**同步流程:**
```
1. 读取 orders-*.csv
2. 提取订单信息 (订单号、客户、时间、场地)
3. 调用 API 创建预订
4. 调用 API 创建支付记录
5. 保存同步状态
```

**API 调用:**
```python
# 1. 创建预订
POST /bookings/with-datetime
{
  "venue_id": 11,
  "court_id": 21,
  "booking_date": "2026-03-12",
  "start_time": "21:00",
  "end_time": "22:00",
  "user_name": "Yiqi",
  "phone": "19901638069",
  "note": "sport8:orders;order_no=T260312..."
}

# 2. 创建支付记录
POST /payments
{
  "booking_id": 123,
  "amount": 102.4,
  "payment_method": "sport8",
  "description": "sport8:payment;order_no=T260312..."
}
```

#### B. 锁定预订同步 (Locked Bookings)
**触发条件:** CSV 中 status = "locked" | "online_reserved" | "order"

**同步流程:**
```
1. 读取 bookings-*.csv
2. 提取 locked 时段
3. 调用 API 仅创建预订（不创建支付）
4. 保存同步状态
```

**API 调用:**
```python
POST /bookings/with-datetime
{
  "venue_id": 11,
  "court_id": 21,
  "booking_date": "2026-03-12",
  "start_time": "20:00",
  "end_time": "21:00",
  "user_name": "Locked-21",
  "phone": "00000000000",
  "note": "sport8:locked;venue=学练馆;court=01"
}
```

### 3️⃣ 幂等性策略

**订单幂等键:** `order_no`
```python
if order_no in state["orders"]:
    skip()  # 已同步，跳过
```

**锁定预订幂等键:** `date::court_id::hour`
```python
key = f"{date}::{court_id}::{hour}"
if key in state["bookings"]:
    skip()  # 已同步，跳过
```

### 4️⃣ 冲突处理

**冲突场景:** 目标系统已存在相同时段预订

**处理策略:**
```python
try:
    create_booking()
except ConflictError:
    # 错误码 3001 或 "已被预约"
    mark_as_conflict()
    skip()
```

**状态记录:**
```json
{
  "booking_id": null,
  "synced_at": "2026-03-12T14:19:58",
  "reason": "conflict"
}
```

---

## 📁 状态管理

**状态文件:** `data/state/sport8_synced.json`

```json
{
  "orders": {
    "T2603122031344482805": {
      "booking_id": 365,
      "payment_id": 456,
      "synced_at": "2026-03-12T14:19:58"
    }
  },
  "bookings": {
    "2026-03-12::21::20": {
      "booking_id": 366,
      "synced_at": "2026-03-12T14:20:15"
    }
  },
  "last_run": "2026-03-12T14:20:15"
}
```

---

## ⏰ 调度策略

**循环模式:**
```
时间窗口: 07:00 - 23:00
执行间隔: 900 秒 (15 分钟)
```

**伪代码:**
```python
while True:
    if 07:00 <= current_time < 23:00:
        run_sync()
    else:
        sleep()
    sleep(900)
```

---

## 🔌 API 端点清单

| 功能 | 方法 | 端点 | 状态 |
|------|------|------|------|
| **认证** | POST | `/auth/login` | ✅ 已验证 |
| **创建预订** | POST | `/bookings/with-datetime` | ✅ 实现 |
| **创建支付** | POST | `/payments` | ✅ 实现 |
| **取消预订** | POST | `/bookings/{id}/cancel` | ❌ 未实现 |
| **更新状态** | PUT | `/bookings/{id}/status` | ❌ 未实现 |
| **查询预订** | GET | `/bookings` | ❌ 未实现 |

---

## 🚀 使用方式

### 手动执行
```bash
cd /Users/mxchip/Documents/sport8-crawl
python3 integrations/sport8_sync.py --no-loop
```

### 定时循环
```bash
python3 integrations/sport8_sync.py --loop
```

### 干运行测试
```bash
python3 integrations/sport8_sync.py --dry-run
```

---

## 📊 场地 ID 映射

| Sport8 场地 | bakewell court_id |
|------------|------------------|
| 学练馆-01 | 21 |
| 学练馆-02 | 22 |
| 学练馆小-03 | 23 |

---

## ⚠️ 已知限制

1. **单向同步** - 只能从 Sport8 → bakewell，不能反向
2. **无删除同步** - 如果 Sport8 取消预订，不会自动同步取消到 bakewell
3. **无更新同步** - 修改预订信息不会自动更新
4. **时间窗口** - 只在 07:00-23:00 执行同步

---

## 🔧 待优化项

- [ ] 实现取消预订同步
- [ ] 实现更新预订同步
- [ ] 添加实时 Webhook 支持
- [ ] 添加同步失败重试机制
- [ ] 添加数据一致性校验

---

**最后更新:** 2026-03-14 09:52
**维护者:** 德鲁伊
