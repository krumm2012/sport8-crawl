#!/usr/bin/env python3
"""
Sport8 完整流程：登录 + 爬取 2026-03-15 数据
使用 async_crawler 的方式
"""

import sys
import json
import os

sys.path.insert(0, '.')
from src.login import Sport8Client
from src.config import Settings

print("=" * 70)
print("🏟️ Sport8 完整流程 - 登录 + 爬取")
print("=" * 70)

# ========== 步骤 1: 登录 ==========
print("\n🔐 步骤 1: 登录 Sport8")
print("=" * 70)

settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)

# 使用交互式登录
print("开始交互式登录...")
print("验证码图片将自动打开，请在终端输入")
print()

try:
    client.interactive_login()
    print("\n✅ 登录成功！")
    print(f"获取到 {len(client.tokens)} 个 tokens")
    
    # 保存 tokens
    with open("login_tokens.json", "w") as f:
        json.dump(client.tokens, f, indent=2, ensure_ascii=False)
    print("✅ Tokens 已保存到 login_tokens.json")
    
except Exception as e:
    print(f"\n❌ 登录失败: {e}")
    sys.exit(1)

# ========== 步骤 2: 爬取数据 ==========
print("\n" + "=" * 70)
print("🕷️ 步骤 2: 爬取 2026-03-15 场地数据")
print("=" * 70)

# 使用 async_crawler 爬取
import asyncio
from async_crawler import AsyncSport8Crawler, load_tokens

tokens = load_tokens()

# 定义场地列表
from async_crawler import CrawlTask
from datetime import date

# 创建爬虫
crawler = AsyncSport8Crawler(
    tokens=tokens,
    max_concurrent=3,
    timeout=30
)

# 爬取 2026-03-15 的数据
async def crawl_0315():
    """爬取 2026-03-15 的数据"""
    
    # 创建 session
    import aiohttp
    session = await crawler._create_session()
    
    target_date = date(2026, 3, 15)
    stadium_id = tokens.get("setStadiumId", "966")
    
    courts = [
        {"court_id": "1", "court_name": "学练馆-01"},
        {"court_id": "2", "court_name": "学练馆-02"},
        {"court_id": "3", "court_name": "学练馆小-03"},
    ]
    
    results = []
    
    for court in courts:
        print(f"\n爬取 {court['court_name']} {target_date}...")
        
        task = CrawlTask(
            stadium_id=stadium_id,
            court_id=court["court_id"],
            court_name=court["court_name"],
            target_date=target_date,
            token=tokens.get("setToken", "")
        )
        
        try:
            bookings = await crawler._fetch_bookings(session, task)
            
            if bookings:
                print(f"  ✅ 获取 {len(bookings)} 条记录")
                
                # 只打印 locked 的记录
                locked = [b for b in bookings if b.status == "locked"]
                if locked:
                    print(f"  🔒 Locked 时段: {[f'{b.hour}:00' for b in locked]}")
                
                results.extend(bookings)
            else:
                print(f"  ⚠️  无数据")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    await session.close()
    
    return results

# 运行爬取
results = asyncio.run(crawl_0315())

print("\n" + "=" * 70)
print("📊 爬取结果")
print("=" * 70)
print(f"总计: {len(results)} 条记录")

# 统计状态
status_counts = {}
for r in results:
    status = r.status
    status_counts[status] = status_counts.get(status, 0) + 1

print("\n状态统计:")
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

# 显示 locked 记录
locked_records = [r for r in results if r.status == "locked"]
if locked_records:
    print("\n🔒 Locked 记录:")
    for r in locked_records:
        print(f"  {r.court_name} {r.date} {r.hour}:00 - ¥{r.price}")

print("\n" + "=" * 70)
print("✅ 完成！")
print("=" * 70)
print("\n数据已保存到 data/exports/")
print("Tokens 已保存到 login_tokens.json")
