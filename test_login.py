import requests
import time
import json
from pathlib import Path
import os
import re

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": BASE_URL,
})

# 1. 访问登录页获取会话
print("📍 步骤 1: 初始化会话...")
login_page = f"{BASE_URL}/StadiumHelper/login/login.jsp"
resp = session.get(login_page, timeout=20, verify=False)
print(f"   状态: {resp.status_code}")

# 2. 获取验证码
print("\n📍 步骤 2: 获取验证码...")
captcha_url = f"{BASE_URL}/StadiumHelper/common/checkCodeServlet"
params = {"width": 578, "height": 136, "ts": str(int(time.time() * 1000))}
resp = session.get(captcha_url, params=params, timeout=20, verify=False)
print(f"   状态: {resp.status_code}")

# 保存验证码
captcha_path = Path("data/captcha/captcha_test.png")
captcha_path.parent.mkdir(parents=True, exist_ok=True)
captcha_path.write_bytes(resp.content)
print(f"   验证码已保存: {captcha_path}")

# 打开验证码图片
os.system(f"open '{captcha_path}'")

# 3. 等待用户输入验证码
print("\n🔢 请输入验证码图片中的字符:")
captcha_code = input("   验证码: ").strip()

# 4. 提交登录
print("\n📍 步骤 3: 提交登录...")
login_endpoint = f"{BASE_URL}/StadiumHelper/login/loginServlet"
payload = {
    "loginname": USERNAME,
    "password": PASSWORD,
    "checkcode": captcha_code,
}
resp = session.post(login_endpoint, data=payload, timeout=20, verify=False, allow_redirects=False)
print(f"   状态: {resp.status_code}")
print(f"   URL: {resp.url}")

if resp.status_code in (301, 302):
    location = resp.headers.get("Location", "")
    print(f"   重定向到: {location}")
    
    # 跟随重定向
    resp = session.get(f"{BASE_URL}{location}" if location.startswith("/") else location, 
                       timeout=20, verify=False)
    print(f"   最终页面: {resp.url}")
    
    # 5. 尝试提取 token
    print("\n📍 步骤 4: 提取 tokens...")
    
    tokens = {}
    
    # 尝试从页面找到 localStorage 设置
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 'setCustId', 'setLoginname', 'setMobile']:
        pattern = key + r"['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern, resp.text)
        if match:
            tokens[key] = match.group(1)
    
    if tokens:
        print(f"✅ 找到 {len(tokens)} 个 tokens")
        
        # 保存
        with open("login_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2)
        print(f"✅ 已保存到 login_tokens.json")
        
        print("\n📋 Token 列表:")
        for k, v in tokens.items():
            print(f"   {k}: {v[:20]}...")
    else:
        print("⚠️  未找到 tokens，尝试从 cookies 获取...")
        cookies = session.cookies.get_dict()
        print(f"   Cookies: {list(cookies.keys())}")
        
else:
    print(f"   响应: {resp.text[:500]}")

print("\n✅ 登录流程完成")
