#!/usr/bin/env python3
"""
Sport8 场地操作测试 - 简化版
先手动登录，然后分析场地管理页面
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://stadium.sports8.com.cn"


def main():
    print("=" * 70)
    print("🏟️ Sport8 场地操作测试 - 简化版")
    print("=" * 70)
    
    # 启动浏览器
    print("\n🌐 启动 Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 访问登录页
        print("📍 访问登录页...")
        driver.get(f"{BASE_URL}/StadiumHelper/login/login.jsp")
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("🔐 请手动完成以下操作:")
        print("=" * 70)
        print("1. 填写用户名: hehh")
        print("2. 填写密码: 20250805")
        print("3. 查看验证码图片并输入")
        print("4. 点击登录按钮")
        print("5. 等待页面跳转到首页")
        print()
        print("完成后按 Enter 继续...")
        input()
        
        # 检查登录状态
        current_url = driver.current_url
        print(f"\n当前 URL: {current_url}")
        
        if "login.jsp" in current_url:
            print("⚠️  似乎还在登录页，请完成登录后按 Enter")
            input()
        
        # 访问场地管理页面
        print("\n📍 访问场地管理页面...")
        venue_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium"
        driver.get(venue_url)
        time.sleep(3)
        
        print(f"✅ 页面标题: {driver.title}")
        
        # 保存页面信息
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存 HTML
        html_file = debug_dir / f"court_page_{timestamp}.html"
        html_file.write_text(driver.page_source, encoding='utf-8')
        print(f"\n📝 页面 HTML 已保存: {html_file}")
        
        # 截图
        screenshot_file = debug_dir / f"court_screenshot_{timestamp}.png"
        driver.save_screenshot(str(screenshot_file))
        print(f"📝 页面截图已保存: {screenshot_file}")
        
        print("\n" + "=" * 70)
        print("🔍 现在请手动操作:")
        print("=" * 70)
        print("\n测试锁定:")
        print("  1. 找到 21:00 的 available 时段")
        print("  2. 点击该时段")
        print("  3. 查看是否有'锁定'按钮")
        print()
        print("测试解锁:")
        print("  1. 找到 16:00 的 locked 时段")
        print("  2. 点击该时段")
        print("  3. 查看是否有'解锁'按钮")
        print()
        print("观察页面元素，记录:")
        print("  - 时段单元格的 class 或 id")
        print("  - 锁定/解锁按钮的选择器")
        print("  - 任何相关的 data-* 属性")
        
        print("\n完成后按 Enter 关闭浏览器...")
        input()
        
        print("\n✅ 测试完成!")
        print(f"请查看保存的文件:")
        print(f"  - {html_file}")
        print(f"  - {screenshot_file}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()
        print("\n✅ 浏览器已关闭")


if __name__ == "__main__":
    main()
