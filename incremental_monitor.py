#!/usr/bin/env python3
"""
增量监控服务 - 事件驱动雏形
持续监控场地状态变化，检测到变化时触发回调

用法:
    python3 incremental_monitor.py --interval 60  # 每60秒检查一次
    python3 incremental_monitor.py --webhook http://localhost:3000/webhook
"""

import asyncio
import aiohttp
import json
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Callable, Optional
import logging

# 从主爬虫导入
from async_crawler import AsyncSport8Crawler, CrawlTask, Booking, load_tokens

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IncrementalMonitor:
    """增量监控器 - 检测变化并触发事件"""
    
    def __init__(
        self,
        tokens: Dict[str, str],
        courts: List[Dict[str, str]],
        check_interval: int = 60,
        webhook_url: Optional[str] = None,
        on_change: Optional[Callable] = None
    ):
        self.tokens = tokens
        self.courts = courts
        self.check_interval = check_interval
        self.webhook_url = webhook_url
        self.on_change = on_change
        
        self.crawler = AsyncSport8Crawler(tokens, max_concurrent=5)
        self.last_bookings: Dict[str, Dict] = {}
        self.running = False
        
        # 加载历史状态
        self._load_history()
    
    def _load_history(self):
        """加载历史预订状态"""
        state_file = Path("data/async_crawler_state.json")
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                self.last_bookings = state.get("last_bookings", {})
                logger.info(f"加载历史状态: {len(self.last_bookings)} 条记录")
    
    def _get_key(self, booking: Booking) -> str:
        """生成唯一键"""
        return f"{booking.court_name}_{booking.date}_{booking.hour}"
    
    def _detect_changes(
        self,
        new_bookings: List[Booking]
    ) -> List[Dict]:
        """检测变化并返回事件列表"""
        changes = []
        
        for booking in new_bookings:
            key = self._get_key(booking)
            last = self.last_bookings.get(key)
            
            if not last:
                # 新预订
                changes.append({
                    "type": "new",
                    "timestamp": datetime.now().isoformat(),
                    "booking": booking.to_dict()
                })
            elif last.get("status") != booking.status:
                # 状态变化
                changes.append({
                    "type": "status_change",
                    "timestamp": datetime.now().isoformat(),
                    "court": booking.court_name,
                    "date": booking.date,
                    "hour": booking.hour,
                    "from_status": last.get("status"),
                    "to_status": booking.status,
                    "price": booking.price
                })
        
        return changes
    
    async def _send_webhook(self, changes: List[Dict]):
        """发送 Webhook 通知"""
        if not self.webhook_url:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "event": "bookings_changed",
                    "timestamp": datetime.now().isoformat(),
                    "changes": changes
                }
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Webhook 发送成功: {len(changes)} 个变化")
                    else:
                        logger.warning(f"Webhook 失败: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"Webhook 错误: {e}")
    
    def _update_history(self, bookings: List[Booking]):
        """更新历史状态"""
        for booking in bookings:
            key = self._get_key(booking)
            self.last_bookings[key] = booking.to_dict()
        
        # 保存到文件
        state_file = Path("data/async_crawler_state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({"last_bookings": self.last_bookings}, f, indent=2)
    
    async def check_once(self) -> List[Dict]:
        """执行一次检查"""
        logger.info("🔍 开始增量检查...")
        
        # 只检查今天和明天的数据（高频变化）
        result = await self.crawler.crawl(
            self.courts,
            days=2,  # 只检查近期
            incremental=False  # 我们自己处理增量逻辑
        )
        
        # 获取本次爬取的所有预订
        # 注意：这里需要修改 async_crawler 来返回 bookings
        # 简化版本：从状态文件读取
        changes = self._detect_changes_from_crawl()
        
        if changes:
            logger.info(f"🚨 检测到 {len(changes)} 个变化")
            await self._send_webhook(changes)
            
            if self.on_change:
                self.on_change(changes)
        else:
            logger.info("✅ 无变化")
        
        return changes
    
    def _detect_changes_from_crawl(self) -> List[Dict]:
        """从爬取结果检测变化"""
        # 简化实现：检查 state 文件
        state_file = Path("data/async_crawler_state.json")
        if not state_file.exists():
            return []
        
        with open(state_file) as f:
            state = json.load(f)
        
        current_bookings = state.get("last_bookings", {})
        changes = []
        
        # 检测新增和变化
        for key, booking in current_bookings.items():
            last = self.last_bookings.get(key)
            if not last:
                changes.append({"type": "new", "booking": booking})
            elif last.get("status") != booking.get("status"):
                changes.append({
                    "type": "status_change",
                    "from": last.get("status"),
                    "to": booking.get("status"),
                    "booking": booking
                })
        
        # 更新历史
        self.last_bookings = current_bookings.copy()
        
        return changes
    
    async def run(self):
        """持续运行监控"""
        self.running = True
        logger.info(f"🚀 增量监控服务启动，检查间隔: {self.check_interval}秒")
        
        while self.running:
            try:
                await self.check_once()
            except Exception as e:
                logger.error(f"检查失败: {e}")
            
            logger.info(f"⏱️  等待 {self.check_interval} 秒...")
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """停止监控"""
        self.running = False
        logger.info("🛑 监控服务停止")


def main():
    parser = argparse.ArgumentParser(description='增量监控服务')
    parser.add_argument('--interval', type=int, default=60, help='检查间隔(秒)')
    parser.add_argument('--webhook', type=str, help='Webhook URL')
    parser.add_argument('--tokens', type=str, default='login_tokens.json')
    
    args = parser.parse_args()
    
    # 加载 tokens
    tokens = load_tokens(args.tokens)
    
    # 场地列表
    courts = [
        {"court_id": "24", "court_name": "学练馆-01"},
        {"court_id": "25", "court_name": "学练馆-02"},
        {"court_id": "26", "court_name": "学练馆小-03"},
    ]
    
    # 创建监控器
    monitor = IncrementalMonitor(
        tokens=tokens,
        courts=courts,
        check_interval=args.interval,
        webhook_url=args.webhook
    )
    
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()
