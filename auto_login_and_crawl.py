#!/usr/bin/env python3
"""
Sport8 自动登录 + 异步爬取组合脚本
使用 ddddocr 自动识别验证码，然后运行 async_crawler
"""

import sys
import json
import os
import re

sys.path.insert(0, '.')

print("=" * 70)
print("🏟️ Sport8 全自动登录 + 爬取")
print("=" * 70)

# ========== 步骤 1: 自动登录 ==========
print("\n🔐 步骤 1: 自动登录")
print("=" * 70)

from src.login import Sport8Client
from src.config import Settings
from captcha_recognizer import CaptchaRecognizer

settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)
recognizer = CaptchaRecognizer()

# 初始化会话
client._initialise_session()
print("✅ 会话初始化完成")

# 尝试自动登录
login_success = False
for attempt in range(5):
    print(f"\n🔄 登录尝试 {attempt + 1}/5")
    
    # 获取验证码
    captcha_path = client.fetch_captcha()
    
    # 读取并识别验证码
    with open(captcha_path, 'rb') as f:
        captcha_bytes = f.read()
    
    captcha_code = recognizer.recognize_from_bytes(captcha_bytes)
    
    if not captcha_code:
        print("  ⚠️ 识别失败，重试...")
        continue
    
    print(f"  ✅ 识别结果: {captcha_code}")
    
    # 提交登录
    import requests
    login_endpoint = f"{client.base_url}/StadiumHelper/login/loginServlet"
    payload = {
        "loginname": settings.username,
        "password": settings.password,
        "checkcode": captcha_code,
    }
    
    resp = client.session.post(
        login_endpoint,
        data=payload,
        timeout=20,
        verify=False,
        allow_redirects=False,
    )
    
    if resp.status_code in (301, 302):
        print("  ✅ 登录成功!")
        location = resp.headers.get("Location", "")
        
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
            with open("login_tokens.json", "w") as f:
                json.dump(client.tokens, f, indent=2, ensure_ascii=False)
            print(f"  ✅ Tokens 已保存 ({len(client.tokens)} 个)")
            login_success = True
            break
    else:
        # 检查错误
        error_match = re.search(r'id="myAlertMsg"[^\u003e]*\u003e([^\u003c]+)', resp.text)
        if error_match:
            print(f"  ❌ 错误: {error_match.group(1).strip()}")
        else:
            print(f"  ❌ 登录失败 (状态码: {resp.status_code})")

if not login_success:
    print("\n❌ 自动登录失败，请使用手动方式:")
    print("   python3 -c \"from src.login import Sport8Client; ...\"")
    sys.exit(1)

# ========== 步骤 2: 运行 async_crawler ==========
print("\n" + "=" * 70)
print("🕷️ 步骤 2: 运行异步爬虫")
print("=" * 70)

import asyncio
from async_crawler import AsyncSport8Crawler, load_tokens

# 重新加载 tokens
tokens = load_tokens()

# 创建爬虫
crawler = AsyncSport8Crawler(
    tokens=tokens,
    max_concurrent=3,
    timeout=30
)

# 定义场地 (使用正确的 court_id)
courts = [
    {"court_id": "1", "court_name": "学练馆-01"},
    {"court_id": "2", "court_name": "学练馆-02"},
    {"court_id": "3", "court_name": "学练馆小-03"},
]

# 运行爬取
result = asyncio.run(crawler.crawl(courts, days=7))

# 打印统计
crawler.print_stats()

print("\n" + "=" * 70)
print("✅ 全部完成!")
print("=" * 70)
print(f"总预订数据: {result['total_bookings']} 条")
print(f"CSV 文件: data/exports/")
print(f"Token 文件: login_tokens.json")
