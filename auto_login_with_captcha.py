#!/usr/bin/env python3
"""
Sport8 自动登录脚本 - 使用验证码识别
自动识别验证码并完成登录
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
try:
    from captcha_recognizer import CaptchaRecognizer
    HAS_RECOGNIZER = True
    print("✅ 验证码识别器已加载")
except ImportError as e:
    print(f"⚠️  验证码识别器未加载: {e}")
    print("   请运行: pip install ddddocr pillow")
    HAS_RECOGNIZER = False

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"


def auto_login_with_recognition():
    """自动识别验证码并登录"""
    
    print("=" * 70)
    print("🔐 Sport8 自动登录（带验证码识别）")
    print("=" * 70)
    print(f"用户名: {USERNAME}")
    
    # 创建 session
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Origin": BASE_URL,
    })
    
    # 初始化验证码识别器
    recognizer = CaptchaRecognizer() if HAS_RECOGNIZER else None
    
    # 尝试多次登录
    for attempt in range(5):
        print(f"\n🔄 尝试 {attempt + 1}/5")
        print("-" * 70)
        
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
            continue
        
        # 保存验证码
        captcha_path = Path(f"data/captcha/auto_{int(time.time())}.png")
        captcha_path.parent.mkdir(parents=True, exist_ok=True)
        captcha_path.write_bytes(resp.content)
        print(f"   ✅ 验证码已保存: {captcha_path}")
        
        # 2. 识别验证码
        if recognizer:
            print("🔍 自动识别验证码...")
            captcha_code = recognizer.recognize_from_bytes(resp.content)
            
            if captcha_code:
                print(f"   ✅ 识别结果: {captcha_code}")
            else:
                print(f"   ⚠️  识别失败，使用手动输入")
                captcha_code = input("   请输入验证码: ").strip()
        else:
            # 打开图片让用户输入
            os.system(f"open '{captcha_path}'")
            captcha_code = input("   请输入验证码: ").strip()
        
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
            continue
        
        print(f"   状态码: {resp.status_code}")
        
        # 4. 检查登录结果
        if resp.status_code in (301, 302):
            location = resp.headers.get("Location", "")
            print(f"   ✅ 登录成功，重定向到: {location}")
            
            # 跟随重定向获取 cookies
            try:
                resp = session.get(
                    f"{BASE_URL}{location}" if location.startswith("/") else location,
                    timeout=20,
                    verify=False
                )
                print(f"   最终页面: {resp.url}")
            except Exception as e:
                print(f"   ⚠️  重定向失败: {e}")
            
            # 5. 保存 session 信息
            cookies = session.cookies.get_dict()
            print(f"\n🍪 获取到 {len(cookies)} 个 cookies")
            
            # 尝试从响应中提取 tokens
            print("🔑 提取 tokens...")
            import re
            tokens = {}
            
            for key in ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                       'setCustId', 'setLoginname', 'setMobile']:
                pattern = key + r"['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
                match = re.search(pattern, resp.text)
                if match:
                    tokens[key] = match.group(1)
            
            # 如果没有从页面提取到，使用 cookies
            if not tokens and cookies:
                tokens = {
                    "cookies": cookies,
                    "extracted_from": "cookies"
                }
            
            if tokens:
                # 保存到文件
                tokens_path = Path("login_tokens.json")
                with open(tokens_path, "w") as f:
                    json.dump(tokens, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Tokens 已保存: {tokens_path}")
                
                # 显示 tokens
                print("\n📋 Token 信息:")
                for k, v in tokens.items():
                    if isinstance(v, str) and len(v) > 20:
                        print(f"   {k}: {v[:20]}...")
                    else:
                        print(f"   {k}: {v}")
                
                return True, session, tokens
            else:
                print("   ⚠️  未找到 tokens，但 cookies 已保存到 session")
                return True, session, {"cookies": cookies}
        
        else:
            # 登录失败
            print(f"   ❌ 登录失败")
            if resp.text:
                # 尝试提取错误信息
                import re
                error_match = re.search(r'id="myAlertMsg"[^\u003e]*\u003e([^\u003c]+)', resp.text)
                if error_match:
                    print(f"   错误信息: {error_match.group(1).strip()}")
            
            # 询问是否继续
            if attempt < 4:
                retry = input("   是否继续尝试? (y/n): ").strip().lower()
                if retry != 'y':
                    break
    
    print("\n" + "=" * 70)
    print("❌ 登录失败，已达到最大尝试次数")
    print("=" * 70)
    return False, None, None


def test_with_new_session():
    """使用新登录的 session 测试 API"""
    success, session, tokens = auto_login_with_recognition()
    
    if not success:
        print("\n登录失败，无法继续测试")
        return
    
    print("\n" + "=" * 70)
    print("🧪 测试 API 访问")
    print("=" * 70)
    
    # 测试场地查询 API
    print("\n📍 测试场地查询 API...")
    api_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet"
    
    if isinstance(tokens, dict) and "setToken" in tokens:
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
                else:
                    result = data.get("data", {}).get("result", [])
                    print(f"   ✅ 成功获取 {len(result)} 条记录")
                    if result:
                        print(f"   示例: {result[0]}")
            except:
                print(f"   响应: {resp.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
    else:
        print("   ⚠️  未找到有效 token，跳过 API 测试")
    
    print("\n✅ 测试完成")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🏟️ Sport8 自动登录工具")
    print("=" * 70)
    
    if not HAS_RECOGNIZER:
        print("\n⚠️  验证码识别器未安装")
        print("   将使用手动输入模式")
        print("\n安装命令:")
        print("   pip install ddddocr pillow")
    
    print("\n功能:")
    print("  1. 自动获取验证码")
    print("  2. 自动识别验证码 (如果安装了 ddddocr)")
    print("  3. 自动登录并保存 token")
    print("  4. 测试 API 访问")
    
    print("\n选项:")
    print("  1. 仅登录")
    print("  2. 登录并测试 API")
    print("  0. 退出")
    
    choice = input("\n请选择 (0-2): ").strip()
    
    if choice == "1":
        auto_login_with_recognition()
    elif choice == "2":
        test_with_new_session()
    else:
        print("再见！")


if __name__ == "__main__":
    main()
