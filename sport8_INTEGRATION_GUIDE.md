## 第三方（韵动吧等）预约与支付对接指南

- **脚本入口**：`python3 integrations/sport8_sync.py`
- **数据来源**：`data/exports/orders-*.csv`（已支付）与 `data/exports/bookings-*.csv`（locked）
- **同步策略**：
  - orders：先 `/bookings/with-datetime` 创建预约，再 `/payments` 记账（`order_no` 幂等）。
  - bookings：仅创建预约，幂等键 `date + court_id + hour`。
- **去重存档**：`data/state/sport8_synced.json`
- **运行窗口**：07:00-23:00（`--loop` 模式下每 15 分钟一次）
- **配置位置**：`config/sport8_sync.json`（可设置账号、场地映射、时间窗、是否循环）

- **核心参数**：
  - `--username / --password`（默认 `superadmin/admin123`）
  - `--venue-id`（默认 `12`）
  - `--orders-glob` / `--bookings-glob`（默认 `orders-*.csv` / `bookings-*.csv`）
  - `--since` / `--until`（YYYY-MM-DD；默认全量）
  - `--dry-run`（仅打印 payload 不请求接口）
  - `--config`（默认 `config/sport8_sync.json`，CLI 参数优先级最高）

- **场地映射**（可在脚本顶部修改）：
  - `[学练馆][01]` / `学练馆-01` → `court_id=24`
  - `[学练馆][02]` / `学练馆-02` → `court_id=25`
  - `[学练馆小][03]` / `学练馆小-03` → `court_id=26`

- 基础地址（Base URL）: `https://51alljoin.cn:8000/api/v1`
- 统一返回格式：`{ code: 0, message: "success", data|items|total... }`（`code != 0` 为失败）
- 建议超时：请求 10s；重试：幂等操作可安全重试
- 编码：UTF-8，JSON 请求时使用 `Content-Type: application/json`

### 一、典型业务流程（第三方不走微信支付）
1) 登录获取访问令牌（Token）
2) 创建预约（或按幂等规则“查→有则更新，无则创建”）
3) 记账一笔“外部支付”（支付方式为 offline/sport8/meituan 等），金额=第三方实付
4) 可按业务将预约状态置为 confirmed/completed
5) 对账：依赖第三方订单号（建议写入 note/description 或扩展字段）

> 说明：我们前台/管理后台展示金额优先使用 `payment_amount`（来自支付记录），无则回退 `price`（预约定价）。

---

### 二、认证

- 登录
```
POST /auth/login   (form)
username=superadmin&password=admin123

响应:
{ "code": 0, "data": { "access_token": "Bearer xxx" } }
```
- 后续所有接口在 Header 携带：`Authorization: Bearer <token>`

---

### 三、预约（Bookings）

- 列表（带支付摘要：payment_amount/payment_status/payment_method/out_trade_no/payment_id）
```
GET /bookings?skip=0&limit=20&status=&start_date=&end_date=&venue_id=
```

- 详情
```
GET /bookings/{booking_id}
```

- 便捷创建（推荐，日期+时间字符串）
```
POST /bookings/with-datetime
{
  "venue_id": 1,
  "court_id": 2,
  "booking_date": "2025-11-16",
  "start_time": "20:00",
  "end_time": "21:00",
  "user_name": "张三",
  "phone": "13800138000",
  "note": "yund:order_no=yund202511160001"
}

响应: { "code":0, "data": { "id": 123, ... } }
```

- 确认预约（需管理员权限）
```
POST /bookings/{booking_id}/confirm
```

- 取消预约
```
POST /bookings/{booking_id}/cancel
{ "reason": "韵动吧取消" }
```

- 设置状态（管理员）
```
PUT /bookings/{booking_id}/status
{ "status": "completed" }  // 支持: pending/confirmed/completed/cancelled/no_show
```

---

### 四、支付记账（第三方渠道）

> 不使用微信时，直接在我们系统里“记账一笔外部支付”。金额将体现在 `payment_amount`，前端页面以该值为准。

- 创建支付记录
```
POST /payments
{
  "booking_id": 123,
  "amount": 100.0,
  "payment_method": "offline",   // 也可 "alipay" / "voucher" / "balance" 等
  "description": "yund:order_no=yund202511160001,pay_channel=meituan"
}

响应: { "code":0, "data": { "payment_id":456, "amount":100.0, "status":"pending|success", "out_trade_no": "" } }
```

- 查询支付详情
```
GET /payments/{payment_id}

响应: { "code":0, "data": { "id", "booking_id", "amount", "status", "payment_method", "out_trade_no", ... } }
```

> 备注：若需要，我们可扩展接口支持 `external_order_no` 并直接置为已支付（success）以简化同步步骤。

---

### 五、幂等与对账建议

- 幂等键：第三方订单号（如韵动吧订单号）。写入 `note/description`，统一前缀如 `yund:order_no=...`
- 幂等策略：同步前先列表查询你关注日期范围内的预约并在本地匹配 `note` 含该订单号；存在→更新状态/金额，不存在→创建后记账
- 状态映射参考：
  - 韵动吧“待到店/待核销” → 我方 pending/confirmed（按你业务选择）
  - 韵动吧“已完成” → 我方 completed
  - 韵动吧“已取消/超时” → 我方 cancelled（reason 写详细原因）

---

### 六、端到端 cURL 示例（可直接运行，替换变量）

```bash
# 1) 获取 TOKEN
TOKEN=$(curl -s -X POST 'https://51alljoin.cn:8000/api/v1/auth/login' \
  -d 'username=superadmin' -d 'password=admin123' | jq -r '.data.access_token')

# 2) 创建预约（便捷接口）
BOOKING=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"venue_id":1,"court_id":2,"booking_date":"2025-11-16","start_time":"20:00","end_time":"21:00","user_name":"张三","phone":"13800138000","note":"yund:order_no=yund202511160001"}' \
  'https://51alljoin.cn:8000/api/v1/bookings/with-datetime')
BOOKING_ID=$(echo "$BOOKING" | jq -r '.data.id // .data.data.id // .data')

# 3) 记账一笔外部支付（100.00）
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"booking_id\":$BOOKING_ID,\"amount\":100.0,\"payment_method\":\"offline\",\"description\":\"yund:order_no=yund202511160001\"}" \
  'https://51alljoin.cn:8000/api/v1/payments'

# 4) （可选）将预约置为已完成
curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"completed"}' \
  "https://51alljoin.cn:8000/api/v1/bookings/$BOOKING_ID/status"

# 5) 验证（列表含支付摘要与金额）
curl -s -H "Authorization: Bearer $TOKEN" \
  'https://51alljoin.cn:8000/api/v1/bookings?skip=0&limit=10'
```

---

### 七、字段说明（关键）
- `booking.price`：预约定价（可能为 0）；展示金额优先取 `payment_amount`
- `booking.payment_amount`：来自支付记录的金额（我们列表已返回）
- `booking.payment_status`：支付状态（pending/success/failed/refunded/partially_refunded/cancelled）
- `booking.payment_method`：支付方式（wechat/alipay/offline/balance/voucher/...）
- `booking.out_trade_no`：商户订单号（微信等渠道有；线下可为空）
- `payments.description`：建议写第三方订单号与渠道，便于对账（如 `yund:order_no=...`）

---

### 八、扩展与支持
- 如需更强幂等/单接口 upsert 能力，或要增加 `external_order_no` 字段（服务端唯一约束），我们可快速扩展端点：
  - `POST /payments/external`（例）：接收 `booking_id/external_order_no/amount/payment_method/status`，按外部单号幂等写入
  - `POST /bookings/external-upsert`（例）：按外部单号创建或更新预约

请对接人告知是否需要上述扩展，我们即可在后端加上并部署。

---

### 九、联系方式
- 技术支持窗口：请通过你方对接群或工单联系；如需紧急通道请备注“第三方同步”

（完）


