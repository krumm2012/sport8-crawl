# 双向预约同步架构设计

## 1. 系统架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           同步协调层 (Sync Orchestrator)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   状态管理    │  │   冲突解决    │  │   操作队列    │  │   审计日志    │ │
│  │  State Mgr   │  │   Resolver   │  │    Queue     │  │    Audit     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐      ┌───────────────────────┐
        │   基准数据源 (Master)  │      │   操作执行层 (Executor) │
        │  bakewell.cloud       │      │  ┌─────────────────┐  │
        │  124.223.13.170       │      │  │  Sport8 Operator │  │
        └───────────────────────┘      │  │  (Selenium/API)  │  │
                    │                  │  └─────────────────┘  │
                    │                  │  ┌─────────────────┐  │
                    ▼                  │  │ Meituan Operator│  │
        ┌───────────────────────┐      │  │  (Selenium/API)  │  │
        │   事件监听器          │      │  └─────────────────┘  │
        │  Webhook/Polling      │      └───────────────────────┘
        └───────────────────────┘
```

### 1.2 数据流向

```
正向同步 (当前已实现):
Sport8/Meituan ──抓取──▶ bakewell.cloud ──写入──▶ 124.223.13.170

反向同步 (新需求):
bakewell.cloud ──检测变化──▶ 操作转换 ──执行──▶ Sport8/Meituan
```

## 2. 核心组件设计

### 2.1 状态管理器 (State Manager)

```python
@dataclass
class BookingState:
    """预订状态数据模型"""
    id: str                    # bakewell  booking_id
    external_ids: Dict[str, str]  # {sport8: "xxx", meituan: "yyy"}
    court_id: int
    court_name: str
    date: str                  # YYYY-MM-DD
    time_slot: str             # HH:00-HH:00
    status: BookingStatus      # pending/confirmed/cancelled/completed
    source: str                # sport8/meituan/manual
    sync_status: SyncStatus    # synced/syncing/failed/conflict
    version: int               # 乐观锁版本
    updated_at: datetime
    
class StateManager:
    """状态管理器 - 维护单一事实来源"""
    
    def __init__(self, db_path: str):
        self.db = SQLiteStateDB(db_path)
    
    def get_state(self, booking_id: str) -> Optional[BookingState]:
        """获取预订状态"""
        pass
    
    def update_state(self, state: BookingState, source: str) -> bool:
        """更新状态（带版本控制）"""
        pass
    
    def find_conflicts(self) -> List[ConflictRecord]:
        """发现状态冲突"""
        pass
    
    def get_pending_operations(self) -> List[Operation]:
        """获取待执行操作"""
        pass
```

### 2.2 冲突解决器 (Conflict Resolver)

```python
@dataclass
class ConflictRecord:
    """冲突记录"""
    booking_id: str
    bakewell_state: BookingState
    sport8_state: Optional[BookingState]
    meituan_state: Optional[BookingState]
    conflict_type: ConflictType
    detected_at: datetime

class ConflictType(Enum):
    STATUS_MISMATCH = "status_mismatch"      # 状态不一致
    DOUBLE_BOOKING = "double_booking"        # 重复预订
    TIME_OVERLAP = "time_overlap"            # 时间重叠
    SOURCE_CONFLICT = "source_conflict"      # 来源冲突

class ConflictResolver:
    """冲突解决策略"""
    
    def __init__(self, strategy: ResolutionStrategy):
        self.strategy = strategy
    
    def resolve(self, conflict: ConflictRecord) -> Resolution:
        """根据策略解决冲突"""
        if conflict.conflict_type == ConflictType.STATUS_MISMATCH:
            return self._resolve_status_mismatch(conflict)
        elif conflict.conflict_type == ConflictType.DOUBLE_BOOKING:
            return self._resolve_double_booking(conflict)
        # ...
    
    def _resolve_status_mismatch(self, conflict: ConflictRecord) -> Resolution:
        """状态不一致解决策略:
        1. 以 bakewell 为准
        2. 如果 bakewell 是 manual 创建，优先级最高
        3. 如果都是系统创建，以更新时间最新为准
        """
        pass
```

### 2.3 操作执行器 (Operator)

```python
class BookingOperation(Enum):
    """预订操作类型"""
    CREATE = "create"           # 创建预订
    CANCEL = "cancel"           # 取消预订
    MODIFY_TIME = "modify_time" # 修改时间
    MODIFY_COURT = "modify_court" # 修改场地
    LOCK = "lock"               # 锁定场地
    UNLOCK = "unlock"           # 解锁场地

@dataclass
class Operation:
    """操作指令"""
    id: str
    type: BookingOperation
    target: str                 # sport8/meituan
    booking_id: str
    params: Dict[str, Any]
    priority: int               # 优先级
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime

class Sport8Operator:
    """Sport8 操作执行器"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.base_url = "https://stadium.sports8.com.cn"
    
    def execute(self, operation: Operation) -> OperationResult:
        """执行操作"""
        if operation.type == BookingOperation.LOCK:
            return self._lock_court(operation)
        elif operation.type == BookingOperation.UNLOCK:
            return self._unlock_court(operation)
        elif operation.type == BookingOperation.CANCEL:
            return self._cancel_booking(operation)
        # ...
    
    def _lock_court(self, op: Operation) -> OperationResult:
        """锁定场地操作:
        1. 导航到 场馆销售 -> 场馆预订
        2. 设置日期
        3. 找到目标时段
        4. 点击锁定按钮
        5. 确认弹窗
        6. 验证结果
        """
        steps = [
            lambda: self._navigate_to_booking_page(),
            lambda: self._select_date(op.params['date']),
            lambda: self._find_and_click_time_slot(
                court_id=op.params['court_id'],
                hour=op.params['hour']
            ),
            lambda: self._click_lock_button(),
            lambda: self._confirm_dialog(),
            lambda: self._verify_lock_success()
        ]
        
        for i, step in enumerate(steps):
            try:
                step()
            except Exception as e:
                return OperationResult(
                    success=False,
                    failed_step=i,
                    error=str(e),
                    screenshot=self._take_screenshot()
                )
        
        return OperationResult(success=True)
    
    def _unlock_court(self, op: Operation) -> OperationResult:
        """解锁场地操作"""
        pass
    
    def _cancel_booking(self, op: Operation) -> OperationResult:
        """取消预订操作"""
        pass

class MeituanOperator:
    """Meituan 操作执行器"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.base_url = "https://e.dianping.com"
    
    def execute(self, operation: Operation) -> OperationResult:
        """执行操作"""
        # Meituan 可能有不同的操作流程
        pass
```

## 3. 同步策略设计

### 3.1 监听机制

```python
class ChangeDetector:
    """变化检测器"""
    
    def __init__(self, sources: List[DataSource]):
        self.sources = sources
        self.poll_interval = 30  # 30秒轮询
    
    async def start_monitoring(self):
        """启动监控"""
        while True:
            for source in self.sources:
                changes = await source.detect_changes()
                for change in changes:
                    await self._handle_change(change)
            await asyncio.sleep(self.poll_interval)
    
    async def _handle_change(self, change: ChangeEvent):
        """处理变更事件"""
        # 1. 记录变更
        await self._log_change(change)
        
        # 2. 生成操作指令
        operations = self._convert_to_operations(change)
        
        # 3. 加入操作队列
        for op in operations:
            await self.operation_queue.put(op)

class BakewellChangeDetector(ChangeDetector):
    """bakewell.cloud 变更检测"""
    
    def __init__(self, api_base: str, token: str):
        self.api = BakewellAPI(api_base, token)
        self.last_check = datetime.now()
    
    async def detect_changes(self) -> List[ChangeEvent]:
        """检测 bakewell 变更:
        方法1: 轮询 /bookings API (当前)
        方法2: Webhook (如果支持)
        方法3: 数据库 binlog (如果有权限)
        """
        # 轮询方式
        current_bookings = await self.api.list_bookings(
            since=self.last_check
        )
        
        changes = []
        for booking in current_bookings:
            previous = await self._get_previous_state(booking.id)
            if previous != booking:
                changes.append(ChangeEvent(
                    source="bakewell",
                    booking_id=booking.id,
                    previous=previous,
                    current=booking,
                    change_type=self._determine_change_type(previous, booking)
                ))
        
        self.last_check = datetime.now()
        return changes
```

### 3.2 操作转换映射

```python
class OperationConverter:
    """操作转换器 - 将 bakewell 操作转换为各平台操作"""
    
    CONVERSION_MAP = {
        # bakewell 状态 -> Sport8 操作
        "sport8": {
            ("available", "locked"): BookingOperation.LOCK,
            ("locked", "available"): BookingOperation.UNLOCK,
            ("confirmed", "cancelled"): BookingOperation.CANCEL,
        },
        # bakewell 状态 -> Meituan 操作
        "meituan": {
            ("available", "booked"): BookingOperation.CREATE,
            ("booked", "cancelled"): BookingOperation.CANCEL,
        }
    }
    
    def convert(self, change: ChangeEvent, target: str) -> List[Operation]:
        """转换变更事件为操作指令"""
        operations = []
        
        prev_status = change.previous.status if change.previous else "none"
        curr_status = change.current.status
        
        # 查找转换映射
        mapping = self.CONVERSION_MAP.get(target, {})
        op_type = mapping.get((prev_status, curr_status))
        
        if op_type:
            operations.append(Operation(
                id=generate_uuid(),
                type=op_type,
                target=target,
                booking_id=change.current.id,
                params=self._extract_params(change.current),
                priority=self._calculate_priority(change)
            ))
        
        return operations
```

## 4. 容错与一致性

### 4.1 操作重试机制

```python
class OperationQueue:
    """操作队列 - 带重试和死信队列"""
    
    def __init__(self):
        self.pending = asyncio.Queue()
        self.retry_queue = asyncio.Queue()
        self.dead_letter = []
    
    async def process(self):
        """处理队列"""
        while True:
            operation = await self.pending.get()
            
            try:
                result = await self._execute(operation)
                
                if result.success:
                    await self._mark_completed(operation)
                else:
                    await self._handle_failure(operation, result)
                    
            except Exception as e:
                await self._handle_error(operation, e)
    
    async def _handle_failure(self, op: Operation, result: OperationResult):
        """处理执行失败"""
        op.retry_count += 1
        
        if op.retry_count < op.max_retries:
            # 延迟重试（指数退避）
            delay = 2 ** op.retry_count
            await asyncio.sleep(delay)
            await self.pending.put(op)
        else:
            # 移入死信队列
            self.dead_letter.append({
                "operation": op,
                "last_error": result.error,
                "failed_at": datetime.now()
            })
            await self._alert_admin(op, result)
```

### 4.2 一致性检查

```python
class ConsistencyChecker:
    """一致性检查器"""
    
    async def run_check(self):
        """运行一致性检查"""
        discrepancies = []
        
        # 获取所有预订
        bakewell_bookings = await self.bakewell_api.list_all_bookings()
        
        for booking in bakewell_bookings:
            # 检查 Sport8
            if booking.source == "sport8":
                sport8_state = await self.sport8_api.query_booking(
                    booking.external_ids.get("sport8")
                )
                if not self._states_match(booking, sport8_state):
                    discrepancies.append(Discrepancy(
                        booking_id=booking.id,
                        platform="sport8",
                        bakewell_state=booking,
                        platform_state=sport8_state
                    ))
            
            # 检查 Meituan
            elif booking.source == "meituan":
                meituan_state = await self.meituan_api.query_booking(
                    booking.external_ids.get("meituan")
                )
                if not self._states_match(booking, meituan_state):
                    discrepancies.append(Discrepancy(
                        booking_id=booking.id,
                        platform="meituan",
                        bakewell_state=booking,
                        platform_state=meituan_state
                    ))
        
        if discrepancies:
            await self._reconcile(discrepancies)
```

## 5. 状态流转图

```
┌──────────────┐     创建      ┌──────────────┐
│   Available  │──────────────▶│   Locked     │
└──────────────┘               └──────────────┘
       ▲                              │
       │                              │ 解锁
       │                              ▼
       │                       ┌──────────────┐
       │                       │  Confirmed   │
       │                       └──────────────┘
       │                              │
       │                              │ 取消
       │                              ▼
       │                       ┌──────────────┐
       └───────────────────────│  Cancelled   │
                               └──────────────┘

状态流转规则:
1. Available + 锁定操作 → Locked
2. Locked + 确认/支付 → Confirmed
3. Confirmed + 取消 → Cancelled → Available
4. Locked + 解锁 → Available
```

## 6. 技术实现要点

### 6.1 幂等性保证
- 每个操作带唯一 ID
- 目标平台记录操作 ID
- 重复操作检测并跳过

### 6.2 并发控制
- 同一时间同一时段只允许一个操作
- 使用分布式锁（Redis/SQLite）
- 操作队列串行处理

### 6.3 监控告警
- 成功率监控
- 延迟监控
- 死信队列告警
- 一致性差异告警

## 7. 实施建议

### Phase 1: 基础架构
- 实现 StateManager
- 实现基础操作映射
- 实现 Sport8 操作器

### Phase 2: 单向同步
- 先实现 bakewell → Sport8 取消/解锁
- 验证稳定性

### Phase 3: 完整双向
- 添加创建/锁定操作
- 添加 Meituan 支持
- 添加冲突解决

### Phase 4: 优化
- 性能优化
- 监控完善
- 自动化运维

---

*设计完成 - 待评审后实施*
