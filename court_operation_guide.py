#!/usr/bin/env python3
"""
Sport8 场地操作测试 - 基于实际操作路径
页面路径: 场馆销售 -> 场馆预订
Chrome 缩放: 50%
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

BASE_URL = "https://stadium.sports8.com.cn"


def main():
    print("=" * 70)
    print("🏟️ Sport8 场地操作测试")
    print("=" * 70)
    print("\n操作路径: 场馆销售 -> 场馆预订")
    print("Chrome 缩放: 50%")
    print("\n测试数据: 2026-03-15")
    print("  - 16:00 locked (3个场地)")
    print("  - 21:00 available (可锁定测试)")
    
    # 启动浏览器
    print("\n🌐 启动 Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    # 设置 50% 缩放
    print("📏 设置页面缩放 50%...")
    driver.get("chrome://settings/")
    driver.execute_script("chrome.settingsPrivate.setDefaultZoom(0.5);")
    time.sleep(1)
    
    try:
        # 访问登录页
        print("\n📍 访问登录页...")
        driver.get(f"{BASE_URL}/StadiumHelper/login/login.jsp")
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("🔐 步骤 1: 手动登录")
        print("=" * 70)
        print("用户名: hehh")
        print("密码: 20250805")
        print("验证码: (查看图片)")
        print("\n登录完成后按 Enter 继续...")
        input()
        
        # 检查登录状态
        if "login.jsp" in driver.current_url:
            print("⚠️  还在登录页，请完成登录后按 Enter")
            input()
        
        print(f"✅ 当前页面: {driver.current_url}")
        
        # 导航到 场馆销售 -> 场馆预订
        print("\n" + "=" * 70)
        print("📍 步骤 2: 导航到 场馆销售 -> 场馆预订")
        print("=" * 70)
        
        # 保存当前 cookies 和 localStorage
        tokens = driver.execute_script("""
            const tokens = {};
            const keys = ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                          'setCustId', 'setLoginname', 'setMobile'];
            keys.forEach(key => {
                const value = localStorage.getItem(key);
                if (value) tokens[key] = value;
            });
            return tokens;
        """)
        
        if tokens:
            print(f"✅ 获取到 {len(tokens)} 个 tokens")
            with open("login_tokens.json", "w") as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        # 访问场馆预订页面
        # 根据用户提供的路径，可能需要通过菜单导航
        print("\n请手动操作:")
        print("1. 点击左侧菜单 '场馆销售'")
        print("2. 点击子菜单 '场馆预订'")
        print("3. 等待页面加载")
        print("\n完成后按 Enter 继续...")
        input()
        
        # 保存页面信息
        debug_dir = Path("debug_logs/court_operation")
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n📍 当前 URL: {driver.current_url}")
        print(f"📍 页面标题: {driver.title}")
        
        # 保存 HTML
        html_file = debug_dir / f"venue_booking_{timestamp}.html"
        html_file.write_text(driver.page_source, encoding='utf-8')
        print(f"\n📝 页面 HTML 已保存: {html_file}")
        
        # 截图
        screenshot_file = debug_dir / f"venue_booking_{timestamp}.png"
        driver.save_screenshot(str(screenshot_file))
        print(f"📝 页面截图已保存: {screenshot_file}")
        
        # 分析页面
        print("\n" + "=" * 70)
        print("🔍 步骤 3: 页面结构分析")
        print("=" * 70)
        
        # 查找关键元素
        print("\n查找关键元素:")
        
        # 时间显示
        time_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '16:00') or contains(text(), '21:00')]")
        print(f"  时间元素 (16:00/21:00): {len(time_elements)}")
        
        # 场地名称
        for court in ["学练馆-01", "学练馆-02", "学练馆小-03"]:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{court}')]")
            if elements:
                print(f"  场地 '{court}': 找到 {len(elements)} 个元素")
        
        # 按钮
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"  按钮总数: {len(buttons)}")
        
        # 可点击元素
        clickable = driver.find_elements(By.CSS_SELECTOR, "[onclick], [data-action], [role='button']")
        print(f"  可点击元素: {len(clickable)}")
        
        print("\n" + "=" * 70)
        print("🔒 步骤 4: 测试锁定操作")
        print("=" * 70)
        print("\n请手动操作并记录:")
        print("1. 找到 21:00 时段 (available 状态)")
        print("2. 点击该时段")
        print("3. 记录弹出的元素:")
        print("   - 是否有'锁定'按钮?")
        print("   - 按钮的 HTML 结构?")
        print("   - 是否有确认弹窗?")
        print("\n完成后按 Enter 继续...")
        input()
        
        # 保存操作后的页面
        timestamp2 = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file2 = debug_dir / f"lock_dialog_{timestamp2}.html"
        html_file2.write_text(driver.page_source, encoding='utf-8')
        screenshot_file2 = debug_dir / f"lock_dialog_{timestamp2}.png"
        driver.save_screenshot(str(screenshot_file2))
        print(f"\n📝 锁定对话框页面已保存")
        
        print("\n" + "=" * 70)
        print("🔓 步骤 5: 测试解锁操作")
        print("=" * 70)
        print("\n请手动操作并记录:")
        print("1. 找到 16:00 时段 (locked 状态)")
        print("2. 点击该时段")
        print("3. 记录弹出的元素:")
        print("   - 是否有'解锁'按钮?")
        print("   - 按钮的 HTML 结构?")
        print("   - 是否有确认弹窗?")
        print("\n完成后按 Enter 继续...")
        input()
        
        # 保存操作后的页面
        timestamp3 = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file3 = debug_dir / f"unlock_dialog_{timestamp3}.html"
        html_file3.write_text(driver.page_source, encoding='utf-8')
        screenshot_file3 = debug_dir / f"unlock_dialog_{timestamp3}.png"
        driver.save_screenshot(str(screenshot_file3))
        print(f"\n📝 解锁对话框页面已保存")
        
        print("\n" + "=" * 70)
        print("📝 步骤 6: 记录关键信息")
        print("=" * 70)
        print("\n请提供以下信息:")
        print("1. 时段单元格的选择器 (如: class='time-cell')")
        print("2. 锁定按钮的选择器 (如: button[data-action='lock'])")
        print("3. 解锁按钮的选择器 (如: button[data-action='unlock'])")
        print("4. 确认弹窗的选择器 (如: div.modal-confirm)")
        print("5. 日期选择器的选择器 (如果需要切换日期)")
        
        print("\n你可以:")
        print("- 在 Chrome 中按 F12 打开开发者工具")
        print("- 右键点击元素 -> '检查' 查看 HTML 结构")
        print("- 记录 class, id, data-* 属性")
        
        print("\n按 Enter 结束测试...")
        input()
        
        print("\n" + "=" * 70)
        print("✅ 测试完成!")
        print("=" * 70)
        print(f"\n所有文件保存在: {debug_dir}/")
        print("\n请查看保存的 HTML 和截图文件，")
        print("并提供关键元素的选择器信息，")
        print("以便开发全自动操作脚本。")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n按 Enter 关闭浏览器...")
        input()
        driver.quit()
        print("✅ 浏览器已关闭")


if __name__ == "__main__":
    main()
