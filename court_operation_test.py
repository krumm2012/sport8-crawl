#!/usr/bin/env python3
"""
Sport8 场地操作测试脚本
测试锁定/解锁功能
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
from selenium.webdriver.common.action_chains import ActionChains

# 配置
BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

# 测试数据
TEST_DATE = "2026-03-15"
TEST_COURTS = [
    {"name": "学练馆-01", "id": "1"},
    {"name": "学练馆-02", "id": "2"},
    {"name": "学练馆小-03", "id": "3"},
]


class CourtOperator:
    """场地操作类"""
    
    def __init__(self):
        self.driver = None
        self.tokens = {}
        
    def setup_driver(self):
        """初始化浏览器"""
        print("🌐 启动 Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        # options.add_argument('--headless')  # 非 headless 以便观察
        
        self.driver = webdriver.Chrome(options=options)
        print("✅ Chrome 已启动")
        
    def login(self):
        """登录 Sport8"""
        print("\n🔐 登录 Sport8")
        print("=" * 60)
        
        self.driver.get(f"{BASE_URL}/StadiumHelper/login/login.jsp")
        time.sleep(2)
        
        # 填写用户名密码
        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "loginname"))
        )
        password_field = self.driver.find_element(By.NAME, "loginpass")
        
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        print(f"✅ 已填写用户名: {USERNAME}")
        
        # 等待用户输入验证码
        print("\n⏳ 请查看弹出的验证码图片...")
        print("在终端输入验证码后按回车")
        
        # 这里会暂停等待用户输入
        captcha_code = input("\n请输入验证码: ").strip()
        
        if captcha_code.lower() == 'q':
            print("用户取消")
            return False
        
        # 填写验证码
        code_field = self.driver.find_element(By.NAME, "checkcode")
        code_field.send_keys(captcha_code)
        print(f"✅ 已填写验证码: {captcha_code}")
        
        # 点击登录
        login_btn = self.driver.find_element(By.ID, "loginbtn")
        login_btn.click()
        time.sleep(3)
        
        # 检查登录结果
        current_url = self.driver.current_url
        if "index/PageIndexServlet" in current_url or "toIndex" in current_url:
            print("✅ 登录成功!")
            
            # 提取 tokens
            self.tokens = self.driver.execute_script("""
                const tokens = {};
                const keys = ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                              'setCustId', 'setLoginname', 'setMobile'];
                keys.forEach(key => {
                    const value = localStorage.getItem(key);
                    if (value) tokens[key] = value;
                });
                return tokens;
            """)
            
            if self.tokens:
                print(f"✅ 获取到 {len(self.tokens)} 个 tokens")
                # 保存
                with open("login_tokens.json", "w") as f:
                    json.dump(self.tokens, f, indent=2, ensure_ascii=False)
            
            return True
        else:
            print(f"❌ 登录失败")
            print(f"当前URL: {current_url}")
            return False
            
    def navigate_to_venue(self):
        """导航到场地管理页面"""
        print("\n📍 导航到场地管理页面")
        print("=" * 60)
        
        # 访问场地管理页面
        venue_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium"
        self.driver.get(venue_url)
        time.sleep(3)
        
        print(f"✅ 页面标题: {self.driver.title}")
        print(f"✅ 当前URL: {self.driver.current_url}")
        
        # 检查是否在正确的页面
        if "login.jsp" in self.driver.current_url:
            print("⚠️  被重定向到登录页，可能需要重新登录")
            return False
            
        return True
        
    def analyze_page(self):
        """分析页面结构"""
        print("\n🔍 分析页面结构")
        print("=" * 60)
        
        # 保存页面源码
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        html_file = debug_dir / f"venue_page_{timestamp}.html"
        html_file.write_text(self.driver.page_source, encoding='utf-8')
        print(f"✅ 页面 HTML 已保存: {html_file}")
        
        # 截图
        screenshot_file = debug_dir / f"venue_screenshot_{timestamp}.png"
        self.driver.save_screenshot(str(screenshot_file))
        print(f"✅ 页面截图已保存: {screenshot_file}")
        
        # 分析元素
        print("\n📊 页面元素分析:")
        
        # 查找 iframe
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   iframe 数量: {len(iframes)}")
        
        if iframes:
            # 切换到第一个 iframe
            self.driver.switch_to.frame(iframes[0])
            print("   ✅ 已切换到 iframe 1")
        
        # 查找表格
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        print(f"   table 数量: {len(tables)}")
        
        # 查找按钮
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"   button 数量: {len(buttons)}")
        
        # 查找包含特定文本的元素
        for text in ["锁定", "解锁", "预约", "16:00", "21:00"]:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
            if elements:
                print(f"   包含 '{text}' 的元素: {len(elements)} 个")
        
        return True
        
    def find_time_slot(self, court_name, hour):
        """查找指定时段"""
        print(f"\n🔍 查找时段: {court_name} {hour}:00")
        
        try:
            # 尝试多种方式查找
            
            # 方法 1: 通过文本查找
            xpath = f"//*[contains(text(), '{hour}:00')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            
            if elements:
                print(f"   ✅ 找到 {len(elements)} 个包含 '{hour}:00' 的元素")
                return elements
            else:
                print(f"   ⚠️  未找到 '{hour}:00'")
                return None
                
        except Exception as e:
            print(f"   ❌ 查找失败: {e}")
            return None
            
    def test_lock_operation(self):
        """测试锁定操作"""
        print("\n🔒 测试锁定操作")
        print("=" * 60)
        
        # 查找一个 available 的时段进行锁定测试
        print(f"尝试查找 21:00 的 available 时段...")
        
        # 这里需要根据实际页面结构调整
        # 这是一个示例实现
        
        print("⚠️  需要手动操作:")
        print("   1. 在浏览器中找到要锁定的时段")
        print("   2. 点击该时段")
        print("   3. 查看是否有锁定按钮")
        
        input("\n按 Enter 继续...")
        
    def test_unlock_operation(self):
        """测试解锁操作"""
        print("\n🔓 测试解锁操作")
        print("=" * 60)
        
        print("尝试查找 16:00 的 locked 时段...")
        print("根据数据，2026-03-15 16:00 三个场地都是 locked 状态")
        
        print("\n⚠️  需要手动操作:")
        print("   1. 在浏览器中找到 16:00 的 locked 时段")
        print("   2. 点击该时段")
        print("   3. 查看是否有解锁按钮")
        
        input("\n按 Enter 继续...")
        
    def run_test(self):
        """运行完整测试"""
        print("\n" + "=" * 70)
        print("🏟️ Sport8 场地操作测试")
        print("=" * 70)
        print(f"测试日期: {TEST_DATE}")
        print(f"测试场地: {[c['name'] for c in TEST_COURTS]}")
        
        try:
            # 1. 启动浏览器
            self.setup_driver()
            
            # 2. 登录
            if not self.login():
                print("\n❌ 登录失败，测试终止")
                return
                
            # 3. 导航到场地管理
            if not self.navigate_to_venue():
                print("\n❌ 导航失败")
                return
                
            # 4. 分析页面
            self.analyze_page()
            
            # 5. 测试锁定
            self.test_lock_operation()
            
            # 6. 测试解锁
            self.test_unlock_operation()
            
            print("\n" + "=" * 70)
            print("✅ 测试完成!")
            print("=" * 70)
            print("\n请查看:")
            print(f"  - 截图: debug_logs/venue_screenshot_*.png")
            print(f"  - HTML: debug_logs/venue_page_*.html")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                print("\n⏳ 浏览器保持打开，请手动检查页面")
                print("完成后按 Enter 关闭浏览器...")
                input()
                self.driver.quit()
                print("✅ 浏览器已关闭")


def main():
    operator = CourtOperator()
    operator.run_test()


if __name__ == "__main__":
    main()
