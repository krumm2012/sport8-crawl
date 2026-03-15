#!/usr/bin/env python3
"""
Sport8 完整流程：使用指定验证码登录 + 爬取 2026-03-15 数据
"""

import sys
import json

sys.path.insert(0, '.')
from src.login import Sport8Client
from src.config import Settings

# 用户提供的验证码
CAPTCHA_CODE = "P3XD"

print("=" * 70)
print("🏟️ Sport8 完整流程 - 登录 + 爬取")
print("=" * 70)
print(f"验证码: {CAPTCHA_CODE}")

# ========== 步骤 1: 登录 ==========
print("\n🔐 步骤 1: 登录 Sport8")
print("=" * 70)

settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)

# 初始化会话
print("初始化会话...")
client._initialise_session()
print("✅ 会话初始化完成")

# 获取验证码（为了更新 session）
print("获取验证码...")
captcha_path = client.fetch_captcha()
print(f"验证码已保存: {captcha_path}")

# 使用提供的验证码登录
print(f"\n使用验证码 '{CAPTCHA_CODE}' 登录...")

import requests
login_endpoint = f"{client.base_url}/StadiumHelper/login/loginServlet"
payload = {
    "loginname": settings.username,
    "password": settings.password,
    "checkcode": CAPTCHA_CODE,
}

resp = client.session.post(
    login_endpoint,
    data=payload,
    timeout=20,
    verify=False,
    allow_redirects=False,
)

print(f"状态码: {resp.status_code}")

if resp.status_code in (301, 302):
    location = resp.headers.get("Location", "")
    print(f"✅ 登录成功！重定向到: {location}")
    
    # 跟随重定向
    resp2 = client.session.get(
        location if location.startswith("http") else f"{client.base_url}{location}",
        timeout=20,
        verify=False
    )
    
    # 提取 tokens
    import re
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                'setCustId', 'setLoginname', 'setMobile']:
        pattern = rf"localStorage\.setItem\(['\"]{key}['\"],\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, resp2.text)
        if match:
            client.tokens[key] = match.group(1)
    
    if client.tokens:
        print(f"✅ 获取到 {len(client.tokens)} 个 tokens")
        with open("login_tokens.json", "w") as f:
            json.dump(client.tokens, f, indent=2, ensure_ascii=False)
        print("✅ Tokens 已保存")
    else:
        print("⚠️  未找到 tokens")
        sys.exit(1)
else:
    print(f"❌ 登录失败")
    import re
    error_match = re.search(r'id="myAlertMsg"[^\u003e]*\u003e([^\u003c]+)', resp.text)
    if error_match:
        print(f"错误: {error_match.group(1).strip()}")
    sys.exit(1)

# ========== 步骤 2: 爬取数据 ==========
print("\n" + "=" * 70)
print("🕷️ 步骤 2: 爬取 2026-03-15 场地数据")
print("=" * 70)

import asyncio
import aiohttp
from datetime import date

stadium_id = client.tokens.get("setStadiumId", "966")
target_date = date(2026, 3, 15)

courts = [
    {"court_id": "1", "court_name": "学练馆-01"},
    {"court_id": "2", "court_name": "学练馆-02"},
    {"court_id": "3", "court_name": "学练馆小-03"},
]

async def fetch_court_data(court_id, court_name):
    """获取单个场地数据"""
    
    url = f"https://stadium.sports8.com.cn/StadiumHelper/venue/PageStadiumServlet"
    
    payload = {
        "optype": "getCourtTimeListByCourtId",
        "court_id": court_id,
        "stadium_id": stadium_id,
        "search_date": target_date.strftime("%Y-%m-%d"),
        "setToken": client.tokens.get("setToken", ""),
        "setStadiumId": stadium_id,
        "setUserid": client.tokens.get("setUserid", ""),
        "setCode": client.tokens.get("setCode", ""),
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://stadium.sports8.com.cn",
        "Referer": "https://stadium.sports8.com.cn/StadiumHelper/venue/PageStadiumServlet?optype=toStadium",
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload, headers=headers, ssl=False) as resp:
                data = await resp.json()
                
                if data.get("error"):
                    return []
                
                result = data.get("data", {}).get("result", [])
                return result
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return []

async def crawl_all():
    """爬取所有场地"""
    all_results = []
    
    for court in courts:
        print(f"\n爬取 {court['court_name']}...")
        
        result = await fetch_court_data(court['court_id'], court['court_name'])
        
        if result:
            print(f"  ✅ 获取 {len(result)} 条记录")
            
            # 统计 locked
            locked = [r for r in result if r.get("status") == "locked"]
            if locked:
                print(f"  🔒 Locked: {[r.get('hour') for r in locked]}")
            
            all_results.extend(result)
        else:
            print(f"  ⚠️  无数据")
    
    return all_results

# 运行爬取
results = asyncio.run(crawl_all())

print("\n" + "=" * 70)
print("📊 爬取结果")
print("=" * 70)
print(f"总计: {len(results)} 条记录")

# 统计
status_counts = {}
for r in results:
    status = r.get("status", "unknown")
    status_counts[status] = status_counts.get(status, 0) + 1

print("\n状态统计:")
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

# 显示 locked
locked_records = [r for r in results if r.get("status") == "locked"]
if locked_records:
    print("\n🔒 Locked 记录:")
    for r in locked_records:
        print(f"  {r.get('venue_name', 'N/A')} {r.get('date')} {r.get('hour')}:00 - ¥{r.get('money', 0)}")

print("\n" + "=" * 70)
print("✅ 完成！")
print("=" * 70)
