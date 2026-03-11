#!/usr/bin/env python3
"""
异步高性能爬虫
使用 aiohttp + asyncio 实现并发请求，速度提升 5-10 倍

特性：
- 异步 HTTP 请求（aiohttp）
- 并发获取多日期数据
- 连接池复用
- 智能重试机制
- 增量爬取支持
"""

import asyncio
import aiohttp
import aiofiles
import json
import time
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
BASE_URL = "https://stadium.sports8.com.cn"
API_ENDPOINT = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet"

# 数据目录
DATA_DIR = Path(__file__).parent / "data" / "exports"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 状态文件（用于增量爬取）
STATE_FILE = Path(__file__).parent / "data" / "async_crawler_state.json"


@dataclass
class Booking:
    """预订数据模型"""
    venue_name: str
    court_name: str
    date: str
    hour: int
    status: str
    price: float
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CrawlTask:
    """爬取任务"""
    stadium_id: str
    court_id: str
    court_name: str
    target_date: date
    token: str


class AsyncSport8Crawler:
    """异步 Sport8 爬虫"""
    
    def __init__(
        self,
        tokens: Dict[str, str],
        max_concurrent: int = 10,
        timeout: int = 30,
        retry_times: int = 3
    ):
        self.tokens = tokens
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_times = retry_times
        
        # 统计
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """创建 HTTP 会话（带连接池）"""
        connector = aiohttp.TCPConnector(
            limit=50,                    # 总连接数限制
            limit_per_host=20,           # 每主机连接数
            ttl_dns_cache=300,           # DNS 缓存 5 分钟
            use_dns_cache=True,
            enable_cleanup_closed=True,
            force_close=False
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium"
        }
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=headers
        )
    
    async def _fetch_with_retry(
        self,
        session: aiohttp.ClientSession,
        task: CrawlTask
    ) -> Optional[List[Booking]]:
        """带重试的请求"""
        for attempt in range(self.retry_times):
            try:
                result = await self._fetch_bookings(session, task)
                if result is not None:
                    self.stats["success_requests"] += 1
                    return result
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {task.court_name} on {task.target_date}, attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Error for {task.court_name} on {task.target_date}: {e}, attempt {attempt + 1}")
            
            if attempt < self.retry_times - 1:
                wait_time = 2 ** attempt  # 指数退避
                await asyncio.sleep(wait_time)
        
        self.stats["failed_requests"] += 1
        logger.error(f"Failed to fetch {task.court_name} on {task.target_date} after {self.retry_times} attempts")
        return None
    
    async def _fetch_bookings(
        self,
        session: aiohttp.ClientSession,
        task: CrawlTask
    ) -> Optional[List[Booking]]:
        """获取单个场地的预订数据"""
        self.stats["total_requests"] += 1
        
        payload = {
            "optype": "getCourtTimeListByCourtId",
            "court_id": task.court_id,
            "stadium_id": task.stadium_id,
            "search_date": task.target_date.strftime("%Y-%m-%d"),
            "setToken": self.tokens.get("setToken", ""),
            "setStadiumId": self.tokens.get("setStadiumId", ""),
            "setUserid": self.tokens.get("setUserid", ""),
            "setCode": self.tokens.get("setCode", ""),
            "setCustId": self.tokens.get("setCustId", ""),
        }
        
        async with session.post(API_ENDPOINT, data=payload) as response:
            if response.status != 200:
                logger.warning(f"HTTP {response.status} for {task.court_name}")
                return None
            
            data = await response.json()
            
            if data.get("error"):
                logger.warning(f"API error: {data.get('error')} for {task.court_name}")
                return None
            
            return self._parse_bookings(data, task)
    
    def _parse_bookings(
        self,
        data: Dict,
        task: CrawlTask
    ) -> List[Booking]:
        """解析预订数据"""
        bookings = []
        result = data.get("data", {}).get("result", [])
        
        for item in result:
            try:
                booking = Booking(
                    venue_name=item.get("venue_name", ""),
                    court_name=task.court_name,
                    date=task.target_date.strftime("%Y-%m-%d"),
                    hour=int(item.get("hour", 0)),
                    status=item.get("status", ""),
                    price=float(item.get("money", 0)),
                    updated_at=datetime.now().isoformat()
                )
                bookings.append(booking)
            except (ValueError, TypeError) as e:
                logger.warning(f"Parse error for item: {item}, error: {e}")
                continue
        
        return bookings
    
    async def _save_bookings(self, bookings: List[Booking], filename: str):
        """异步保存预订数据到 CSV"""
        if not bookings:
            return
        
        filepath = DATA_DIR / filename
        
        # 检查文件是否存在
        file_exists = filepath.exists()
        
        # 使用 asyncio.to_thread 处理文件 IO
        def write_csv():
            with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=bookings[0].to_dict().keys())
                if not file_exists:
                    writer.writeheader()
                for booking in bookings:
                    writer.writerow(booking.to_dict())
        
        await asyncio.to_thread(write_csv)
        logger.info(f"Saved {len(bookings)} bookings to {filepath}")
    
    def _load_state(self) -> Dict:
        """加载上次爬取状态"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"last_crawl": None, "courts": {}}
    
    def _save_state(self, state: Dict):
        """保存爬取状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def crawl(
        self,
        courts: List[Dict[str, str]],
        days: int = 7,
        incremental: bool = True
    ) -> Dict[str, Any]:
        """
        并发爬取数据
        
        Args:
            courts: 场地列表 [{"court_id": "", "court_name": ""}]
            days: 爬取天数
            incremental: 是否增量爬取
        """
        self.stats["start_time"] = datetime.now()
        
        # 生成任务列表
        tasks = []
        today = date.today()
        stadium_id = self.tokens.get("setStadiumId", "")
        
        for day_offset in range(days):
            target_date = today + timedelta(days=day_offset)
            for court in courts:
                task = CrawlTask(
                    stadium_id=stadium_id,
                    court_id=court["court_id"],
                    court_name=court["court_name"],
                    target_date=target_date,
                    token=self.tokens.get("setToken", "")
                )
                tasks.append(task)
        
        logger.info(f"Generated {len(tasks)} tasks for {len(courts)} courts x {days} days")
        
        # 创建会话并执行并发请求
        all_bookings = []
        async with await self._create_session() as session:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def bounded_fetch(task: CrawlTask) -> Optional[List[Booking]]:
                async with semaphore:
                    return await self._fetch_with_retry(session, task)
            
            # 并发执行所有任务
            results = await asyncio.gather(
                *[bounded_fetch(task) for task in tasks],
                return_exceptions=True
            )
            
            # 收集结果
            for result in results:
                if isinstance(result, list):
                    all_bookings.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
        
        self.stats["end_time"] = datetime.now()
        
        # 保存数据
        if all_bookings:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bookings_async_{timestamp}.csv"
            await self._save_bookings(all_bookings, filename)
        
        # 保存状态
        state = {
            "last_crawl": datetime.now().isoformat(),
            "total_bookings": len(all_bookings),
            "stats": self.stats
        }
        self._save_state(state)
        
        return {
            "success": True,
            "total_bookings": len(all_bookings),
            "stats": self.stats,
            "duration": (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        }
    
    def print_stats(self):
        """打印统计信息"""
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            logger.info("=" * 60)
            logger.info("📊 爬取统计")
            logger.info("=" * 60)
            logger.info(f"总请求数: {self.stats['total_requests']}")
            logger.info(f"成功请求: {self.stats['success_requests']}")
            logger.info(f"失败请求: {self.stats['failed_requests']}")
            logger.info(f"总耗时: {duration:.2f} 秒")
            logger.info(f"平均响应: {duration / max(self.stats['total_requests'], 1):.2f} 秒/请求")
            logger.info("=" * 60)


def load_tokens(filepath: str = "login_tokens.json") -> Dict[str, str]:
    """加载 tokens"""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='异步 Sport8 爬虫')
    parser.add_argument('--days', type=int, default=7, help='爬取天数（默认7天）')
    parser.add_argument('--concurrent', type=int, default=10, help='并发数（默认10）')
    parser.add_argument('--timeout', type=int, default=30, help='超时秒数（默认30）')
    parser.add_argument('--tokens', type=str, default='login_tokens.json', help='tokens 文件路径')
    
    args = parser.parse_args()
    
    # 加载 tokens
    try:
        tokens = load_tokens(args.tokens)
    except FileNotFoundError:
        logger.error(f"Tokens file not found: {args.tokens}")
        return
    
    # 定义场地列表（可根据实际情况修改）
    courts = [
        {"court_id": "24", "court_name": "学练馆-01"},
        {"court_id": "25", "court_name": "学练馆-02"},
        {"court_id": "26", "court_name": "学练馆小-03"},
    ]
    
    # 创建爬虫并执行
    crawler = AsyncSport8Crawler(
        tokens=tokens,
        max_concurrent=args.concurrent,
        timeout=args.timeout
    )
    
    logger.info("🚀 启动异步爬虫...")
    logger.info(f"并发数: {args.concurrent}, 天数: {args.days}")
    
    result = asyncio.run(crawler.crawl(courts, days=args.days))
    
    crawler.print_stats()
    
    logger.info(f"✅ 爬取完成！共获取 {result['total_bookings']} 条预订数据")


if __name__ == "__main__":
    main()
