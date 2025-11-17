#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 提取诊断工具
帮助诊断为什么登录后无法提取 tokens
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

def diagnose():
    """诊断 token 提取问题"""
    print("="*70)
    print("Token 提取诊断工具")
    print("="*70)
    
    # 启动浏览器
    print("\n[1] 启动浏览器...")
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    
    try:
        # 访问登录页
        login_url = f"{BASE_URL}/StadiumHelper/"
        print(f"\n[2] 访问登录页: {login_url}")
        driver.get(login_url)
        time.sleep(5)
        
        # 填写用户名密码
        print("\n[3] 填写登录信息...")
        wait = WebDriverWait(driver, 15)
        
        # 用户名
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        username_input.clear()
        time.sleep(0.5)
        username_input.send_keys(USERNAME)
        print(f"  ✓ 用户名: {USERNAME}")
        
        # 密码
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        time.sleep(0.5)
        password_input.send_keys(PASSWORD)
        print(f"  ✓ 密码: ********")
        
        # 等待验证码
        print("\n" + "="*70)
        print("⚠️  请在浏览器中输入验证码并点击登录")
        print("="*70)
        time.sleep(3)
        
        # 等待登录成功
        print("\n[4] 等待登录成功...")
        start_time = time.time()
        login_success = False
        
        for i in range(180):  # 3 分钟
            time.sleep(1)
            current_url = driver.current_url
            
            # 检查是否登录成功（URL 变化）
            if current_url != login_url and "login" not in current_url.lower():
                login_success = True
                print(f"  ✓ 登录成功！耗时 {int(time.time() - start_time)} 秒")
                print(f"  当前 URL: {current_url}")
                break
            
            if i % 10 == 0 and i > 0:
                print(f"  等待中... ({i}s)")
        
        if not login_success:
            print("  ✗ 登录超时")
            return
        
        # 开始诊断
        print("\n" + "="*70)
        print("开始诊断 Token 提取")
        print("="*70)
        
        # 诊断 1: 检查当前页面的 localStorage
        print("\n[诊断 1] 当前页面 localStorage")
        print(f"  URL: {driver.current_url}")
        check_storage(driver)
        
        # 诊断 2: 检查 sessionStorage
        print("\n[诊断 2] 当前页面 sessionStorage")
        check_session_storage(driver)
        
        # 诊断 3: 检查 cookies
        print("\n[诊断 3] 当前页面 Cookies")
        check_cookies(driver)
        
        # 诊断 4: 检查页面 JavaScript 变量
        print("\n[诊断 4] 检查全局 JavaScript 变量")
        check_js_variables(driver)
        
        # 诊断 5: 访问销售页面
        print("\n[诊断 5] 访问销售页面")
        sales_url = f"{BASE_URL}/StadiumHelper/sales/PageSalesServlet?optype=toSales"
        print(f"  URL: {sales_url}")
        driver.get(sales_url)
        time.sleep(5)
        check_storage(driver)
        
        # 诊断 6: 访问主页
        print("\n[诊断 6] 访问主页")
        index_url = f"{BASE_URL}/StadiumHelper/index/PageIndexServlet?optype=toIndex"
        print(f"  URL: {index_url}")
        driver.get(index_url)
        time.sleep(5)
        check_storage(driver)
        
        # 诊断 7: 检查页面源码
        print("\n[诊断 7] 检查页面源码中的 token")
        page_source = driver.page_source
        if "setToken" in page_source:
            print("  ✓ 页面源码中找到 'setToken'")
            # 尝试提取
            import re
            tokens = re.findall(r'setToken["\']?\s*[:=]\s*["\']([^"\']+)["\']', page_source)
            if tokens:
                print(f"  可能的 token 值: {tokens}")
        else:
            print("  ✗ 页面源码中未找到 'setToken'")
        
        # 诊断 8: 等待一段时间后再检查
        print("\n[诊断 8] 等待 10 秒后再次检查")
        time.sleep(10)
        check_storage(driver)
        
        print("\n" + "="*70)
        print("诊断完成！浏览器将保持打开")
        print("你可以手动在浏览器控制台中检查 localStorage")
        print("按 F12 打开控制台，输入: localStorage")
        print("="*70)
        
        input("\n按 Enter 键关闭浏览器...")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

def check_storage(driver):
    """检查 localStorage"""
    try:
        # 获取所有 localStorage
        all_storage = driver.execute_script("""
            const storage = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                storage[key] = localStorage.getItem(key);
            }
            return storage;
        """)
        
        if all_storage:
            print(f"  ✓ 找到 {len(all_storage)} 个 localStorage 项:")
            for key, value in all_storage.items():
                # 截断长值
                display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"    {key}: {display_value}")
            
            # 检查必需的 tokens
            required_keys = ['setUserid', 'setStadiumId', 'setToken', 'setCode']
            found_keys = [k for k in required_keys if k in all_storage]
            if found_keys:
                print(f"  ✓ 找到必需的 keys: {found_keys}")
            else:
                print(f"  ✗ 未找到必需的 keys: {required_keys}")
        else:
            print("  ✗ localStorage 为空")
    except Exception as e:
        print(f"  ✗ 检查 localStorage 失败: {e}")

def check_session_storage(driver):
    """检查 sessionStorage"""
    try:
        all_storage = driver.execute_script("""
            const storage = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                storage[key] = sessionStorage.getItem(key);
            }
            return storage;
        """)
        
        if all_storage:
            print(f"  ✓ 找到 {len(all_storage)} 个 sessionStorage 项:")
            for key, value in all_storage.items():
                display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"    {key}: {display_value}")
        else:
            print("  ✗ sessionStorage 为空")
    except Exception as e:
        print(f"  ✗ 检查 sessionStorage 失败: {e}")

def check_cookies(driver):
    """检查 cookies"""
    try:
        cookies = driver.get_cookies()
        if cookies:
            print(f"  ✓ 找到 {len(cookies)} 个 cookies:")
            for cookie in cookies:
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"    {name}: {display_value}")
        else:
            print("  ✗ 未找到 cookies")
    except Exception as e:
        print(f"  ✗ 检查 cookies 失败: {e}")

def check_js_variables(driver):
    """检查 JavaScript 全局变量"""
    try:
        # 检查常见的全局变量
        result = driver.execute_script("""
            const vars = {};
            // 检查 window 对象上的 token 相关属性
            const keys = ['token', 'userId', 'stadiumId', 'userInfo', 'loginInfo'];
            keys.forEach(key => {
                if (window[key] !== undefined) {
                    vars[key] = window[key];
                }
            });
            return vars;
        """)
        
        if result:
            print(f"  ✓ 找到全局变量:")
            for key, value in result.items():
                print(f"    window.{key}: {value}")
        else:
            print("  ✗ 未找到相关全局变量")
    except Exception as e:
        print(f"  ✗ 检查全局变量失败: {e}")

if __name__ == "__main__":
    diagnose()


