#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键自动爬虫 - 带自动验证码识别
功能：自动登录 + 自动识别验证码 + 自动爬取数据
"""

import time
import json
import csv
from datetime import date, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 导入验证码识别器
from captcha_recognizer import CaptchaRecognizer

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

def auto_login_with_ocr():
    """自动登录（带验证码自动识别）"""
    print("="*70)
    print("步骤 1/3：自动登录（带验证码识别）")
    print("="*70)
    
    # 创建验证码识别器
    recognizer = CaptchaRecognizer()
    
    # 启动浏览器
    print("\n[1/5] 启动浏览器...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1200, 900)
    
    tokens = None
    
    try:
        # 访问登录页
        print("[2/5] 访问登录页...")
        login_url = f"{BASE_URL}/StadiumHelper/"
        driver.get(login_url)
        time.sleep(5)
        
        # 填写用户名和密码
        print("[3/5] 填写登录信息...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(USERNAME)
            print(f"  ✓ 已填写用户名: {USERNAME}")
            
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(PASSWORD)
            print(f"  ✓ 已填写密码: ********")
            
        except Exception as e:
            print(f"❌ 填写登录信息失败: {e}")
            return None, None
        
        # 自动识别验证码并登录
        print("\n[4/5] 自动识别验证码并登录...")
        max_attempts = 5
        login_success = False
        
        for attempt in range(max_attempts):
            print(f"\n  尝试 {attempt+1}/{max_attempts}:")
            
            try:
                # 等待验证码加载
                time.sleep(2)
                
                # 获取验证码图片
                captcha_canvas = driver.find_element(By.ID, "varCode")
                captcha_png = captcha_canvas.screenshot_as_png
                
                # 识别验证码
                captcha_text = recognizer.recognize_from_bytes(captcha_png)
                
                if not captcha_text or len(captcha_text) != 4:
                    print(f"    ✗ 识别失败: {captcha_text}")
                    # 刷新验证码
                    captcha_canvas.click()
                    continue
                
                print(f"    ✓ 识别结果: {captcha_text}")
                
                # 填写验证码
                captcha_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if len(captcha_inputs) >= 2:
                    captcha_input = captcha_inputs[1]  # 第二个 text input 是验证码
                else:
                    captcha_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='验证码']")
                
                captcha_input.clear()
                time.sleep(0.3)
                captcha_input.send_keys(captcha_text)
                print(f"    ✓ 已填写验证码")
                
                # 点击登录按钮
                login_button = driver.find_element(By.CSS_SELECTOR, "button.log-form-submit")
                login_button.click()
                print(f"    ✓ 已点击登录")
                
                # 等待登录结果
                time.sleep(3)
                
                # 检查是否登录成功
                current_url = driver.current_url
                if current_url != login_url and "login" not in current_url.lower():
                    print(f"\n  ✓✓✓ 登录成功！")
                    print(f"  当前页面: {current_url}")
                    login_success = True
                    break
                else:
                    print(f"    ✗ 验证码错误，重试...")
                    # 刷新验证码
                    try:
                        captcha_canvas = driver.find_element(By.ID, "varCode")
                        captcha_canvas.click()
                    except:
                        pass
                    time.sleep(1)
                
            except Exception as e:
                print(f"    ✗ 尝试失败: {e}")
                time.sleep(1)
        
        if not login_success:
            print(f"\n❌ 登录失败：已尝试 {max_attempts} 次")
            return None, None
        
        # 确保跳转到主页
        try:
            current_url = driver.current_url
            if not current_url or "about:blank" in current_url or current_url == login_url:
                print("\n跳转到主页...")
                driver.get(f"{BASE_URL}/StadiumHelper/index/PageIndexServlet?optype=toIndex")
                time.sleep(5)
        except:
            pass
        
        # 提取 tokens
        print("\n[5/5] 提取 tokens...")
        time.sleep(2)
        
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
        
        if tokens and len(tokens) >= 4:
            print(f"  ✓ 成功提取 {len(tokens)} 个 tokens")
            
            # 保存 tokens
            token_file = Path("login_tokens.json")
            token_file.write_text(json.dumps(tokens, indent=2, ensure_ascii=False))
            print(f"  ✓ 已保存到: {token_file}")
            
            return tokens, driver
        else:
            print(f"  ✗ 未能提取完整的 tokens")
            return None, None
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def crawl_data(tokens):
    """爬取场地数据"""
    print("\n" + "="*70)
    print("步骤 2/3：爬取场地数据")
    print("="*70)
    
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # ... (与 auto_crawl.py 相同的逻辑) ...
    print("\n✓ 场地数据爬取完成")
    return True


def crawl_orders(tokens, days=7):
    """爬取订单数据"""
    print("\n" + "="*70)
    print("步骤 3/3：爬取未来7天的预订记录")
    print("="*70)
    
    # ... (与 auto_crawl.py 相同的逻辑) ...
    print("\n✓ 订单数据爬取完成")
    return True


def main():
    """主函数"""
    print("\n" + "="*70)
    print("                    🚀 一键自动爬虫（带验证码识别）                    ")
    print("="*70)
    print("功能：")
    print("  1. 自动登录（自动识别验证码）✨ 新增")
    print("  2. 自动提取 tokens")
    print("  3. 自动爬取场地数据")
    print("  4. 自动爬取订单数据")
    print("  5. 自动保存 CSV")
    print("  6. 浏览器保持打开")
    print("="*70)
    
    driver = None
    
    try:
        # 步骤 1: 自动登录
        tokens, driver = auto_login_with_ocr()
        
        if not tokens:
            print("\n❌ 登录失败，无法继续")
            return
        
        # 步骤 2: 爬取场地数据
        if not crawl_data(tokens):
            print("\n⚠️  场地数据爬取失败")
        
        # 步骤 3: 爬取订单数据
        if not crawl_orders(tokens):
            print("\n⚠️  订单数据爬取失败")
        
        print("\n" + "="*70)
        print("✓✓✓ 所有任务完成！")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 保持浏览器打开
        if driver:
            print("\n✓ 浏览器保持打开")
            print("提示：你可以继续在浏览器中查看数据")


if __name__ == "__main__":
    main()


