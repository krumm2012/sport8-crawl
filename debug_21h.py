#!/usr/bin/env python3
"""调试脚本 - 验证 21:00 数据"""
import os
import sys
import time
import json
from datetime import date

# 先执行自动登录
sys.path.insert(0, '/Users/mxchip/Documents/sport8-crawl')
os.chdir('/Users/mxchip/Documents/sport8-crawl')

from auto_crawl_with_ocr import auto_login_with_ocr

print("🚀 开始调试验证...")

# 自动登录
tokens, driver = auto_login_with_ocr()
if not tokens:
    print("❌ 登录失败")
    sys.exit(1)

print(f"✅ 登录成功，用户ID: {tokens.get('setUserid')}")

# 调用 API 获取今日数据
import requests
import urllib3
urllib3.disable_warnings()

session = requests.Session()
API_URL = "https://stadium.sports8.com.cn/StadiumHelper/sales/StadiumSalesServlet"

payload = {
    "method": "getStadiumSalesDetail",
    "date": "2026-03-12",
    "userId": tokens.get("setUserid", ""),
    "stadiumId": tokens.get("setStadiumId", ""),
    "token": tokens.get("setToken", ""),
    "nonce": int(time.time()),
}

print("\n🚀 调用 API 获取今日数据...")
resp = session.post(API_URL, json=payload, verify=False, timeout=30)
data = resp.json()

print(f"\nAPI 返回码: {data.get('result_code')}")
print(f"API 返回消息: {data.get('result_msg')}")

if data.get("result_code") == "0":
    status_list = data.get("result_data", {}).get("statusList", [])
    print(f"\n✅ 获取成功，{len(status_list)} 个场地")
    print("\n" + "="*70)
    print("🔍 今日 21:00 时段详细数据：")
    print("="*70)
    
    for court in status_list:
        court_name = court.get("name", "")
        for slot in court.get("siteStatus", []):
            hour = int(slot.get("time", 0))
            if hour == 21:
                flag = str(slot.get("flag", "0"))
                price = slot.get("relprice", 0)
                bookinfo = slot.get("bookinfo", {})
                
                status_map = {
                    "0": "available（空闲）❌",
                    "1": "online_reserved（线上预订）✅",
                    "2": "offline_reserved（线下预订）✅", 
                    "3": "free（免费预订）✅",
                    "4": "locked（锁定）✅",
                    "5": "long_term（长订）✅",
                }
                status = status_map.get(flag, f"unknown({flag})")
                
                print(f"\n{court_name}:")
                print(f"  时间: {hour}:00")
                print(f"  flag值: {flag}")
                print(f"  解析状态: {status}")
                print(f"  价格: ¥{price}")
                if bookinfo:
                    print(f"  预订信息: {json.dumps(bookinfo, ensure_ascii=False, indent=2)}")
                
    print("\n" + "="*70)
    print("📊 与截图对比：")
    print("  学练馆-01 21:00 应该是: 线上预订 (红色)")
    print("  学练馆-02 21:00 应该是: 线下预订 (绿色)")
    print("  学练馆小-03 21:00 应该是: 免费预订 (绿色)")
    print("="*70)
else:
    print(f"❌ API 错误: {data.get('result_msg')}")

# 保持浏览器打开
print("\n✅ 调试完成，浏览器保持打开")
