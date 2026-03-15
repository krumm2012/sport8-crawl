#!/usr/bin/env python3
"""
Sport8 完整登录流程 - 获取验证码并登录
"""

import sys
import json
import os

sys.path.insert(0, '.')
from src.login import Sport8Client
from src.config import Settings

print("=" * 70)
print("🔐 Sport8 登录")
print("=" * 70)

# 创建客户端
settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)

# 步骤 1: 初始化会话
print("\n📍 步骤 1: 初始化会话...")
client._initialise_session()
print(f"✅ 会话初始化完成")
print(f"   Cookies: {list(client.session.cookies.get_dict().keys())}")

# 步骤 2: 获取验证码
print("\n📍 步骤 2: 获取验证码...")
captcha_path = client.fetch_captcha()
print(f"✅ 验证码已保存: {captcha_path}")

# 打开验证码图片
os.system(f"open '{captcha_path}'")
print("   图片已打开，请查看...")

# 步骤 3: 等待用户输入验证码
print("\n📍 步骤 3: 输入验证码")
captcha_code = input("请输入验证码图片中的字符: ").strip().upper()
print(f"   输入的验证码: {captcha_code}")

# 步骤 4: 提交登录
print("\n📍 步骤 4: 提交登录...")
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

print(f"   状态码: {resp.status_code}")

if resp.status_code in (301, 302) and "Location" in resp.headers:
    print("✅ 登录成功！")
    location = resp.headers["Location"]
    print(f"   重定向到: {location}")
    
    # 获取 tokens
    try:
        client._populate_tokens_from_location(location)
    except Exception as e:
        print(f"   ⚠️ 从 location 获取 token 失败: {e}")
        try:
            client._populate_tokens_from_page()
        except Exception as e2:
            print(f"   ⚠️ 从页面获取 token 失败: {e2}")
    
    if client.tokens:
        print(f"\n✅ 获取到 {len(client.tokens)} 个 tokens")
        
        # 保存
        with open("login_tokens.json", "w") as f:
            json.dump(client.tokens, f, indent=2, ensure_ascii=False)
        print("✅ 已保存到 login_tokens.json")
        
        print("\n📋 Token 信息:")
        for k, v in client.tokens.items():
            print(f"   {k}: {v[:30]}..." if len(str(v)) > 30 else f"   {k}: {v}")
        
        print("\n" + "=" * 70)
        print("🎉 登录完成！")
        print("=" * 70)
        
    else:
        print("\n⚠️  未获取到 tokens")
        
elif resp.status_code == 200:
    # 检查是否是登录失败返回的登录页
    if "login.jsp" in resp.url:
        error_msg = client._extract_alert(resp.text)
        if error_msg:
            print(f"❌ 登录失败: {error_msg}")
        else:
            print(f"❌ 登录失败（验证码错误或账号密码错误）")
    else:
        # 可能是其他情况
        print(f"⚠️  未预期的响应")
        print(f"   URL: {resp.url}")
        # 尝试解析 JSON
        try:
            data = resp.json()
            print(f"   JSON: {data}")
        except:
            pass
else:
    print(f"❌ 登录失败，状态码: {resp.status_code}")
