#!/usr/bin/env python3
"""
Sport8 登录 - 使用用户提供的验证码
"""

import sys
import json

sys.path.insert(0, '.')
from src.login import Sport8Client
from src.config import Settings

# 用户提供的验证码
CAPTCHA_CODE = "CETA"

print("=" * 70)
print("🔐 Sport8 登录")
print("=" * 70)
print(f"验证码: {CAPTCHA_CODE}")

# 创建客户端
settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)

# 初始化会话
print("\n📍 初始化会话...")
client._initialise_session()
print(f"✅ 会话初始化完成")

# 不获取新验证码，直接使用用户提供的验证码
print(f"\n🚀 使用验证码 '{CAPTCHA_CODE}' 登录...")

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

print(f"   状态码: {resp.status_code}")

if resp.status_code in (301, 302):
    location = resp.headers.get("Location", "")
    print(f"✅ 登录成功！重定向到: {location}")
    
    # 跟随重定向获取页面
    resp2 = client.session.get(
        location if location.startswith("http") else f"{client.base_url}{location}",
        timeout=20,
        verify=False
    )
    
    # 提取 tokens
    import re
    tokens = {}
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                'setCustId', 'setLoginname', 'setMobile']:
        pattern = rf"localStorage\.setItem\(['\"]{key}['\"],\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, resp2.text)
        if match:
            tokens[key] = match.group(1)
    
    if tokens:
        print(f"\n✅ 获取到 {len(tokens)} 个 tokens")
        with open("login_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        print("✅ 已保存到 login_tokens.json")
        
        print("\n📋 Tokens:")
        for k, v in tokens.items():
            print(f"   {k}: {v[:30]}..." if len(v) > 30 else f"   {k}: {v}")
        
        print("\n" + "=" * 70)
        print("🎉 登录成功！")
        print("=" * 70)
    else:
        print("⚠️  未找到 tokens")
        
else:
    print(f"❌ 登录失败")
    # 尝试提取错误
    import re
    error_match = re.search(r'id="myAlertMsg"[^>]*>([^\u003c]+)', resp.text)
    if error_match:
        print(f"   错误: {error_match.group(1).strip()}")
    
    # 保存调试
    with open("debug_logs/login_failed.html", "w") as f:
        f.write(resp.text)
    print("   调试信息已保存到 debug_logs/login_failed.html")
