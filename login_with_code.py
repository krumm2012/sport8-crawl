#!/usr/bin/env python3
"""
使用指定验证码完成登录 - 直接使用现有 session
"""

import sys
import json
import re

# 导入项目模块
sys.path.insert(0, '.')
from src.login import Sport8Client
from src.config import Settings

# 验证码 - 用户提供的验证码对应的是当前已保存的图片
CAPTCHA_CODE = "VUBW"

print("=" * 70)
print("🔐 Sport8 登录")
print("=" * 70)
print(f"验证码: {CAPTCHA_CODE}")
print()

# 创建客户端
settings = Settings(
    base_url='https://stadium.sports8.com.cn',
    username='hehh',
    password='20250805'
)

client = Sport8Client(settings)

# 关键：初始化会话 - 这会设置必要的 cookies
print("📍 初始化会话...")
client._initialise_session()
print("✅ 会话初始化完成")
print(f"   Cookies: {list(client.session.cookies.get_dict().keys())}")

# 注意：我们需要使用与用户看到验证码时相同的 session
# 所以不能重新获取验证码，而是使用当前 session 直接登录
print(f"🚀 使用验证码 '{CAPTCHA_CODE}' 登录...")

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

print(f"📊 状态码: {resp.status_code}")
print(f"📊 Headers: {dict(resp.headers)}")

if resp.status_code in (301, 302):
    location = resp.headers.get("Location", "")
    print(f"✅ 登录成功！重定向到: {location}")
    
    # 跟随重定向
    resp2 = client.session.get(
        f"{client.base_url}{location}" if location.startswith("/") else location,
        timeout=20,
        verify=False
    )
    print(f"📍 最终页面: {resp2.url}")
    
    # 提取 tokens from page
    print("\n🔑 提取 tokens...")
    import re
    tokens = {}
    
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                'setCustId', 'setLoginname', 'setMobile']:
        pattern = rf"localStorage\.setItem\(['\"]{key}['\"],\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, resp2.text)
        if match:
            tokens[key] = match.group(1)
    
    if tokens:
        print(f"✅ 找到 {len(tokens)} 个 tokens")
        
        # 保存
        with open("login_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        print("✅ 已保存到 login_tokens.json")
        
        print("\n📋 Token 信息:")
        for k, v in tokens.items():
            print(f"   {k}: {v[:30]}..." if len(str(v)) > 30 else f"   {k}: {v}")
        
        print("\n" + "=" * 70)
        print("🎉 登录完成！")
        print("=" * 70)
        
    else:
        print("⚠️  未找到 tokens，检查页面内容...")
        # 保存页面用于调试
        debug_file = "debug_logs/login_success_page.html"
        import os
        os.makedirs("debug_logs", exist_ok=True)
        with open(debug_file, "w") as f:
            f.write(resp2.text[:10000])
        print(f"📝 页面已保存: {debug_file}")
        
else:
    print(f"\n❌ 登录失败")
    
    # 提取错误信息
    error_match = re.search(r'id="myAlertMsg"[^>]*>([^\u003c]+)', resp.text)
    if error_match:
        print(f"   错误: {error_match.group(1).strip()}")
    
    # 保存调试信息
    debug_file = "debug_logs/login_failed_response.html"
    import os
    os.makedirs("debug_logs", exist_ok=True)
    with open(debug_file, "w") as f:
        f.write(resp.text)
    print(f"📝 调试信息已保存: {debug_file}")
