#!/usr/bin/env python3
"""
Sport8 重新登录脚本 - 使用 unified_crawler 的登录方法
"""

import os
import sys
import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置
BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"


def login_sport8():
    """使用 Selenium 登录 Sport8 并保存 token"""
    
    print("=" * 70)
    print("🔐 Sport8 登录")
    print("=" * 70)
    print(f"\n用户名: {USERNAME}")
    print(f"密码: {'*' * len(PASSWORD)}")
    
    # 启动浏览器
    print("\n🌐 启动 Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 访问登录页
        print("📍 访问登录页面...")
        driver.get(f"{BASE_URL}/StadiumHelper/login/login.jsp")
        time.sleep(2)
        
        # 填写用户名密码
        print("📝 填写登录信息...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "loginname"))
        )
        password_field = driver.find_element(By.NAME, "loginpass")
        
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        
        # 处理验证码
        print("\n🔢 验证码处理")
        print("-" * 70)
        
        for attempt in range(5):
            print(f"\n尝试 {attempt + 1}/5:")
            
            # 获取验证码
            captcha_img = driver.find_element(By.ID, "codeImg")
            captcha_src = captcha_img.get_attribute("src")
            print(f"  验证码图片: {captcha_src[:50]}...")
            
            # 提示用户输入
            captcha_code = input("  请输入验证码 (或输入 'q' 退出): ").strip()
            
            if captcha_code.lower() == 'q':
                print("  用户取消")
                return False
            
            # 填写验证码
            code_field = driver.find_element(By.NAME, "checkcode")
            code_field.clear()
            code_field.send_keys(captcha_code)
            
            # 点击登录
            login_btn = driver.find_element(By.ID, "loginbtn")
            login_btn.click()
            time.sleep(3)
            
            # 检查登录结果
            current_url = driver.current_url
            if "index/PageIndexServlet" in current_url or "toIndex" in current_url:
                print(f"\n✅✅✅ 登录成功!")
                print(f"   当前页面: {current_url}")
                break
            else:
                # 检查错误信息
                try:
                    error_msg = driver.find_element(By.ID, "errorMsg").text
                    if error_msg:
                        print(f"  ❌ 登录失败: {error_msg}")
                        # 刷新验证码
                        driver.find_element(By.ID, "codeImg").click()
                        time.sleep(1)
                except:
                    print(f"  ⚠️  登录状态未知，继续...")
        else:
            print("\n❌ 登录失败，达到最大尝试次数")
            return False
        
        # 提取 tokens
        print("\n🔑 提取登录 tokens...")
        tokens = driver.execute_script("""
            const tokens = {};
            const keys = ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                          'setCustId', 'setLoginname', 'setMobile', 'setDeviceFlag'];
            keys.forEach(key => {
                const value = localStorage.getItem(key);
                if (value) tokens[key] = value;
            });
            return tokens;
        """)
        
        if len(tokens) >= 4:
            print(f"✅ 成功提取 {len(tokens)} 个 tokens")
            
            # 保存 tokens
            with open("login_tokens.json", "w", encoding="utf-8") as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
            print(f"✅ 已保存到: login_tokens.json")
            
            # 显示 token 信息
            print("\n📋 Token 信息:")
            for key, value in tokens.items():
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"   {key}: {masked}")
            
            return True
        else:
            print(f"⚠️  只找到 {len(tokens)} 个 tokens，可能不完整")
            return False
            
    except Exception as e:
        print(f"\n❌ 登录出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        input("\n按 Enter 关闭浏览器...")
        driver.quit()
        print("✅ 浏览器已关闭")


def main():
    print("\n" + "=" * 70)
    print("🏟️ Sport8 重新登录工具")
    print("=" * 70)
    print("\n这个脚本将:")
    print("  1. 打开 Chrome 浏览器")
    print("  2. 访问 Sport8 登录页面")
    print("  3. 自动填写用户名密码")
    print("  4. 等待你输入验证码")
    print("  5. 登录成功后保存 token")
    
    success = login_sport8()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ 登录完成!")
        print("=" * 70)
        print("\n现在可以运行其他脚本使用新的 token:")
        print("  python3 async_crawler.py")
        print("  python3 test_court_api.py")
    else:
        print("\n" + "=" * 70)
        print("❌ 登录失败")
        print("=" * 70)


if __name__ == "__main__":
    main()
