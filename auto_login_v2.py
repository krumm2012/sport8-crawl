#!/usr/bin/env python3
"""
Sport8 全自动登录脚本 - 修复版
使用 ddddocr 自动识别验证码并完成登录
"""

import os
import sys
import time
import json
import re
import requests
from pathlib import Path

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入验证码识别器
from captcha_recognizer import CaptchaRecognizer

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"


def auto_login_v2():
    """全自动登录 V2 - 修复版"""
    
    print("=" * 70)
    print("🔐 Sport8 全自动登录 V2")
    print("=" * 70)
    
    # 创建 session
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": BASE_URL,
    })
    
    # 初始化验证码识别器
    print("\n🚀 初始化验证码识别器...")
    try:
        recognizer = CaptchaRecognizer()
        print("✅ 识别器已加载")
    except Exception as e:
        print(f"❌ 识别器加载失败: {e}")
        return False, None, None
    
    # 关键：先访问登录页，设置必要的 cookies 和 session
    print("\n📍 步骤 0: 初始化会话...")
    login_page = f"{BASE_URL}/StadiumHelper/login/login.jsp"
    resp = session.get(login_page, timeout=20, verify=False)
    print(f"   状态码: {resp.status_code}")
    print(f"   Cookies: {list(session.cookies.get_dict().keys())}")
    
    # 设置 Referer
    session.headers["Referer"] = login_page
    
    # 尝试多次登录
    for attempt in range(10):
        print(f"\n{'='*70}")
        print(f"🔄 尝试 {attempt + 1}/10")
        print(f"{'='*70}")
        
        # 1. 获取验证码
        print("📥 获取验证码...")
        captcha_url = f"{BASE_URL}/StadiumHelper/common/checkCodeServlet"
        params = {
            "width": 578,
            "height": 136,
            "ts": str(int(time.time() * 1000))
        }
        
        try:
            resp = session.get(captcha_url, params=params, timeout=20, verify=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"   ❌ 获取验证码失败: {e}")
            time.sleep(2)
            continue
        
        print(f"   ✅ 验证码获取成功 ({len(resp.content)} bytes)")
        
        # 2. 自动识别验证码
        print("🔍 自动识别验证码...")
        captcha_code = recognizer.recognize_from_bytes(resp.content)
        
        if not captcha_code:
            print("   ⚠️  识别失败，等待后重试...")
            time.sleep(2)
            continue
            
        print(f"   ✅ 识别结果: '{captcha_code}' (长度: {len(captcha_code)})")
        
        # 3. 提交登录
        print("🚀 提交登录...")
        login_endpoint = f"{BASE_URL}/StadiumHelper/login/loginServlet"
        payload = {
            "loginname": USERNAME,
            "password": PASSWORD,
            "checkcode": captcha_code,
        }
        
        try:
            resp = session.post(
                login_endpoint, 
                data=payload, 
                timeout=20, 
                verify=False, 
                allow_redirects=True  # 允许重定向以跟踪完整流程
            )
        except Exception as e:
            print(f"   ❌ 登录请求失败: {e}")
            time.sleep(2)
            continue
        
        print(f"   状态码: {resp.status_code}")
        print(f"   最终URL: {resp.url}")
        
        # 4. 分析登录结果
        # 情况 1: 重定向到首页
        if "index/PageIndexServlet" in resp.url or "toIndex" in resp.url:
            print(f"   ✅ 登录成功（重定向到首页）")
            
            # 提取 tokens
            tokens = extract_tokens_from_page(resp.text)
            
            if tokens:
                save_tokens(tokens)
                return True, session, tokens
            else:
                # 尝试从页面获取
                tokens = extract_tokens_from_localstorage(resp.text)
                if tokens:
                    save_tokens(tokens)
                    return True, session, tokens
        
        # 情况 2: 还在登录页，说明验证码错误或登录失败
        elif "login.jsp" in resp.url:
            # 提取错误信息
            error_msg = extract_error_message(resp.text)
            if error_msg:
                print(f"   ❌ 登录失败: {error_msg}")
            else:
                print(f"   ❌ 登录失败（仍在登录页）")
                # 保存调试信息
                debug_file = Path(f"debug_logs/login_response_{attempt}.html")
                debug_file.parent.mkdir(exist_ok=True)
                debug_file.write_text(resp.text[:5000], encoding='utf-8')
                print(f"   📝 调试信息已保存: {debug_file}")
        
        # 情况 3: 其他情况，检查响应内容
        else:
            print(f"   ⚠️  未预期的URL，检查响应...")
            
            # 尝试解析 JSON 响应
            try:
                data = resp.json()
                print(f"   JSON响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                
                # 检查是否包含 token
                if "result_data" in data or "token" in str(data):
                    print("   ✅ 可能是登录成功响应")
                    # 从 JSON 提取 token
                    tokens = extract_tokens_from_json(data)
                    if tokens:
                        save_tokens(tokens)
                        return True, session, tokens
            except:
                # 不是 JSON，检查是否是 HTML
                if "<html" in resp.text:
                    print("   响应是 HTML，可能是登录页或错误页")
                    # 检查是否包含错误信息
                    error_msg = extract_error_message(resp.text)
                    if error_msg:
                        print(f"   错误: {error_msg}")
        
        print(f"   等待 2 秒后重试...")
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print("❌ 登录失败，已达到最大尝试次数")
    print("=" * 70)
    return False, None, None


def extract_tokens_from_page(html):
    """从页面 HTML 提取 tokens"""
    tokens = {}
    
    # 从 localStorage 设置中提取
    for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                'setCustId', 'setLoginname', 'setMobile', 'setDeviceFlag']:
        # 模式 1: localStorage.setItem('key', 'value')
        pattern1 = rf"localStorage\.setItem\(['\"]{key}['\"],\s*['\"]([^'\"]+)['\"]"
        match = re.search(pattern1, html)
        
        # 模式 2: key = 'value'
        if not match:
            pattern2 = rf"{re.escape(key)}\s*=\s*['\"]([^'\"]+)['\"]"
            match = re.search(pattern2, html)
        
        if match:
            tokens[key] = match.group(1)
    
    return tokens if len(tokens) >= 4 else {}


def extract_tokens_from_localstorage(html):
    """从 localStorage 脚本提取 tokens"""
    # 查找 localStorage 相关脚本
    pattern = r"localStorage\.setItem\(['\"](\w+)['\"],\s*['\"]([^'\"]+)['\"]\)"
    matches = re.findall(pattern, html)
    
    tokens = {}
    for key, value in matches:
        tokens[key] = value
    
    return tokens if len(tokens) >= 4 else {}


def extract_tokens_from_json(data):
    """从 JSON 响应提取 tokens"""
    tokens = {}
    
    result = data.get("result_data", {})
    if not result and "data" in data:
        result = data.get("data", {})
    
    mapping = {
        "setUserid": ["userId", "user_id", "userid"],
        "setStadiumId": ["stadiumId", "stadium_id", "stadiumid"],
        "setToken": ["token", "access_token"],
        "setCode": ["code", "auth_code"],
        "setCustId": ["custId", "cust_id", "custid", "customer_id"],
        "setLoginname": ["loginname", "login_name", "username"],
        "setMobile": ["mobile", "phone"],
    }
    
    for target_key, possible_keys in mapping.items():
        for key in possible_keys:
            if key in result:
                tokens[target_key] = result[key]
                break
    
    return tokens if len(tokens) >= 4 else {}


def extract_error_message(html):
    """从 HTML 提取错误信息"""
    patterns = [
        r'id="myAlertMsg"[^>]*>([^<]+)',
        r'class="[^"]*error[^"]*"[^>]*>([^<]+)',
        r'alert\([\'"]([^\'"]+)[\'"]\)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def save_tokens(tokens):
    """保存 tokens 到文件"""
    tokens_path = Path("login_tokens.json")
    with open(tokens_path, "w") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Tokens 已保存: {tokens_path}")
    print("\n📋 Token 信息:")
    for k, v in tokens.items():
        if len(str(v)) > 25:
            print(f"   {k}: {str(v)[:25]}...")
        else:
            print(f"   {k}: {v}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🏟️ Sport8 全自动登录系统 V2")
    print("=" * 70)
    
    success, session, tokens = auto_login_v2()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ 登录成功！")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ 登录失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
