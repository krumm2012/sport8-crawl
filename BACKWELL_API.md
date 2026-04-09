# Backwell (hehaa135booking) API 地址列表

> 配置名称: **hehaa135booking**
> 基础地址: `https://backwell.cloud/api/v1`
> 更新时间: 2026-03-12

---

## 🔐 认证接口

### 1. 登录
```
POST https://backwell.cloud/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=superadmin&password=superadmin123
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "access_token": "Bearer xxx"
  }
}
```

---

## 📋 预约接口 (Bookings)

### 2. 查询预约列表
```
GET https://backwell.cloud/api/v1/bookings?skip=0&limit=20&status=&start_date=&end_date=&venue_id=11
Authorization: Bearer {token}
```

### 3. 查询预约详情
```
GET https://backwell.cloud/api/v1/bookings/{booking_id}
Authorization: Bearer {token}
```

### 4. 创建预约（推荐）
```
POST https://backwell.cloud/api/v1/bookings/with-datetime
Authorization: Bearer {token}
Content-Type: application/json

{
  "venue_id": 11,
  "court_id": 21,
  "booking_date": "2026-03-12",
  "start_time": "21:00",
  "end_time": "22:00",
  "user_name": "Yiqi",
  "phone": "19901638069",
  "note": "hehaa135booking:order_no=T2603122031344482805"
}
```

### 5. 确认预约
```
POST https://backwell.cloud/api/v1/bookings/{booking_id}/confirm
Authorization: Bearer {token}
```

### 6. 取消预约
```
POST https://backwell.cloud/api/v1/bookings/{booking_id}/cancel
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "hehaa135booking: 取消原因"
}
```

### 7. 更新预约状态
```
PUT https://backwell.cloud/api/v1/bookings/{booking_id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "completed"
}
```

**状态枚举:**
- `pending` - 待确认
- `confirmed` - 已确认
- `completed` - 已完成
- `cancelled` - 已取消
- `no_show` - 未到

---

## 💰 支付接口 (Payments)

### 8. 创建支付记录
```
POST https://backwell.cloud/api/v1/payments
Authorization: Bearer {token}
Content-Type: application/json

{
  "booking_id": 365,
  "amount": 102.4,
  "payment_method": "sport8",
  "description": "hehaa135booking:order_no=T2603122031344482805"
}
```

**支付方式枚举:**
- `wechat` - 微信支付
- `alipay` - 支付宝
- `offline` - 线下支付
- `sport8` - Sport8 来源
- `balance` - 余额
- `voucher` - 代金券

### 9. 查询支付详情
```
GET https://backwell.cloud/api/v1/payments/{payment_id}
Authorization: Bearer {token}
```

---

## 🏟️ 场馆接口 (Venues)

### 10. 查询场馆列表
```
GET https://backwell.cloud/api/v1/venues
Authorization: Bearer {token}
```

### 11. 查询场地列表
```
GET https://backwell.cloud/api/v1/venues/{venue_id}/courts
Authorization: Bearer {token}
```

---

## 📊 当前配置

**文件:** `config/sport8_sync.json`

```json
{
  "name": "hehaa135booking",
  "base_url": "https://backwell.cloud/api/v1",
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

**场地ID映射:**
| 场地名称 | court_id |
|---------|---------|
| 学练馆-01 | 21 |
| 学练馆-02 | 22 |
| 学练馆小-03 | 23 |

---

## 📝 常用 cURL 示例

### 登录并获取 Token
```bash
curl -s -X POST \
  -d "username=superadmin&password=superadmin123" \
  https://backwell.cloud/api/v1/auth/login
```

### 查询今日预订
```bash
TOKEN="your_token_here"
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://backwell.cloud/api/v1/bookings?skip=0&limit=50&start_date=2026-03-12&end_date=2026-03-12&venue_id=11"
```

### 创建新预订
```bash
TOKEN="your_token_here"
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "venue_id": 11,
    "court_id": 21,
    "booking_date": "2026-03-12",
    "start_time": "21:00",
    "end_time": "22:00",
    "user_name": "测试用户",
    "phone": "13800138000",
    "note": "hehaa135booking:test"
  }' \
  https://backwell.cloud/api/v1/bookings/with-datetime
```

---

**最后更新:** 2026-03-12 23:42
**配置名称:** hehaa135booking
**API 地址:** https://backwell.cloud/api/v1
