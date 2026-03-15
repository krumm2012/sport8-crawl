#!/usr/bin/env python3
"""
Sport8 全自动登录脚本 - 无需交互
使用 ddddocr 自动识别验证码并完成登录
"""

import os
import sys
import time
import json
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


def auto_login_fully_automatic():
    """全自动登录 - 无需人工干预"""
    
    print("=" * 70)
    print("🔐 Sport8 全自动登录")
    print("=" * 70)
    print(f"用户名: {USERNAME}")
    print("验证码识别: ddddocr (自动)")
    
    # 创建 session
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
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
    
    # 尝试多次登录
    for attempt in range(5):
        print(f"\n{'='*70}")
        print(f"🔄 尝试 {attempt + 1}/5")
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
            
        print(f"   ✅ 识别结果: {captcha_code}")
        
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
                allow_redirects=False
            )
        except Exception as e:
            print(f"   ❌ 登录请求失败: {e}")
            time.sleep(2)
            continue
        
        print(f"   状态码: {resp.status_code}")
        
        # 4. 检查登录结果
        if resp.status_code in (301, 302):
            location = resp.headers.get("Location", "")
            print(f"   ✅ 登录成功！重定向到: {location}")
            
            # 跟随重定向
            try:
                resp = session.get(
                    f"{BASE_URL}{location}" if location.startswith("/") else location,
                    timeout=20,
                    verify=False
                )
            except Exception as e:
                print(f"   ⚠️  重定向失败: {e}")
            
            # 5. 提取和保存 tokens
            print("\n🔑 提取 tokens...")
            import re
            tokens = {}
            
            for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                       'setCustId', 'setLoginname', 'setMobile']:
                pattern = key + r"['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
                match = re.search(pattern, resp.text)
                if match:
                    tokens[key] = match.group(1)
            
            if tokens:
                # 保存到文件
                tokens_path = Path("login_tokens.json")
                with open(tokens_path, "w") as f:
                    json.dump(tokens, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Tokens 已保存: {tokens_path}")
                
                # 显示 tokens
                print("\n📋 Token 信息:")
                for k, v in tokens.items():
                    print(f"   {k}: {v[:25]}..." if len(v) > 25 else f"   {k}: {v}")
                
                print("\n" + "=" * 70)
                print("✅ 登录完成！")
                print("=" * 70)
                
                return True, session, tokens
            else:
                print("   ⚠️  未找到 tokens")
                return False, None, None
        
        else:
            # 登录失败，提取错误信息
            print(f"   ❌ 登录失败")
            import re
            error_match = re.search(r'id="myAlertMsg"[^>]*>([^<]+)', resp.text)
            if error_match:
                print(f"   错误: {error_match.group(1).strip()}")
            
            print(f"   等待 2 秒后重试...")
            time.sleep(2)
    
    print("\n" + "=" * 70)
    print("❌ 登录失败，已达到最大尝试次数")
    print("=" * 70)
    return False, None, None


def test_api_access(session, tokens):
    """测试 API 访问"""
    print("\n" + "=" * 70)
    print("🧪 测试 API 访问")
    print("=" * 70)
    
    # 测试场地查询 API
    print("\n📍 测试场地查询 API...")
    api_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet"
    
    payload = {
        "optype": "getCourtTimeListByCourtId",
        "court_id": "1",
        "stadium_id": tokens.get("setStadiumId", ""),
        "search_date": "2026-03-15",
        "setToken": tokens.get("setToken", ""),
        "setStadiumId": tokens.get("setStadiumId", ""),
        "setUserid": tokens.get("setUserid", ""),
        "setCode": tokens.get("setCode", ""),
    }
    
    try:
        resp = session.post(api_url, data=payload, timeout=30, verify=False)
        print(f"   状态码: {resp.status_code}")
        
        try:
            data = resp.json()
            if data.get("error"):
                print(f"   ⚠️  API 错误: {data.get('error')}")
                return False
            else:
                result = data.get("data", {}).get("result", [])
                print(f"   ✅ 成功！获取 {len(result)} 条场地记录")
                if result:
                    print(f"\n   示例数据:")
                    print(f"      场地: {result[0].get('venue_name', 'N/A')}")
                    print(f"      时间: {result[0].get('hour', 'N/A')}:00")
                    print(f"      状态: {result[0].get('status', 'N/A')}")
                return True
        except:
            print(f"   响应: {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False


def main():
    """主函数 - 全自动运行"""
    print("\n" + "=" * 70)
    print("🏟️ Sport8 全自动登录系统")
    print("=" * 70)
    print("\n功能:")
    print("  ✓ 自动获取验证码")
    print("  ✓ 自动识别验证码 (ddddocr)")
    print("  ✓ 自动登录")
    print("  ✓ 自动保存 token")
    print("  ✓ 自动测试 API")
    
    # 执行登录
    success, session, tokens = auto_login_fully_automatic()
    
    if success:
        # 测试 API
        api_ok = test_api_access(session, tokens)
        
        print("\n" + "=" * 70)
        print("📊 最终结果")
        print("=" * 70)
        print(f"✅ 登录: 成功")
        print(f"{'✅' if api_ok else '❌'} API 测试: {'成功' if api_ok else '失败'}")
        print(f"\n💾 Token 文件: login_tokens.json")
        print("=" * 70)
        
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ 登录失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
