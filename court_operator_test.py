#!/usr/bin/env python3
"""
场地操作测试脚本 - 测试 Sport8 场地锁定/解锁功能
使用 2026-03-15 数据进行测试
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

# 测试数据 - 2026-03-15
TEST_DATE = "2026-03-15"
LOCKED_SLOTS = [
    {"court": "学练馆-01", "hour": 16, "court_id": "1"},
    {"court": "学练馆-02", "hour": 16, "court_id": "2"},
    {"court": "学练馆小-03", "hour": 16, "court_id": "3"},
]
AVAILABLE_SLOTS = [
    {"court": "学练馆-01", "hour": 21, "court_id": "1"},
    {"court": "学练馆-02", "hour": 21, "court_id": "2"},
    {"court": "学练馆小-03", "hour": 21, "court_id": "3"},
]


class CourtOperatorTest:
    """场地操作测试类"""
    
    def __init__(self):
        self.driver = None
        self.tokens = {}
        self.test_results = []
        
    def setup_driver(self):
        """初始化浏览器"""
        print("🌐 启动 Chrome 浏览器...")
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        # 非 headless 模式以便观察操作
        # options.add_argument('--headless')
        
        self.driver = webdriver.Chrome(options=options)
        print("✅ 浏览器启动成功")
        
    def login(self):
        """登录 Sport8"""
        print("\n🔐 步骤 1: 登录 Sport8")
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
        
        # 处理验证码
        print("\n⏳ 请手动输入验证码...")
        code_field = self.driver.find_element(By.NAME, "checkcode")
        
        # 等待用户输入验证码
        captcha_code = input("请输入验证码图片中的字符 (或输入 'skip' 跳过登录测试): ").strip()
        
        if captcha_code.lower() == 'skip':
            print("⚠️ 跳过登录测试")
            return False
            
        code_field.send_keys(captcha_code)
        
        # 点击登录
        login_btn = self.driver.find_element(By.ID, "loginbtn")
        login_btn.click()
        time.sleep(3)
        
        # 检查登录结果
        current_url = self.driver.current_url
        if "index/PageIndexServlet" in current_url or "toIndex" in current_url:
            print("✅ 登录成功!")
            self._extract_tokens()
            return True
        else:
            print(f"❌ 登录失败，当前URL: {current_url}")
            return False
            
    def _extract_tokens(self):
        """提取登录 tokens"""
        try:
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
            print(f"✅ 提取到 {len(self.tokens)} 个 token")
        except Exception as e:
            print(f"⚠️ 提取 token 失败: {e}")
            
    def navigate_to_venue_management(self):
        """导航到场地管理页面"""
        print("\n📍 步骤 2: 导航到场地管理页面")
        print("=" * 60)
        
        # 场地管理页面 URL
        venue_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium"
        self.driver.get(venue_url)
        time.sleep(3)
        
        print(f"✅ 当前页面: {self.driver.title}")
        print(f"✅ URL: {self.driver.current_url}")
        
        # 检查是否有 iframe
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        print(f"📊 发现 {len(iframes)} 个 iframe")
        
        return len(iframes) > 0
        
    def analyze_page_structure(self):
        """分析页面结构"""
        print("\n🔍 步骤 3: 分析页面结构")
        print("=" * 60)
        
        # 查找场地时间表格
        try:
            # 尝试查找表格
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"📊 发现 {len(tables)} 个 table 元素")
            
            # 查找所有按钮
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"📊 发现 {len(buttons)} 个 button 元素")
            
            # 查找包含"锁定"文本的元素
            lock_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '锁定')]")
            print(f"📊 发现 {len(lock_elements)} 个包含'锁定'文本的元素")
            
            # 查找包含"解锁"文本的元素
            unlock_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '解锁')]")
            print(f"📊 发现 {len(unlock_elements)} 个包含'解锁'文本的元素")
            
            # 保存页面源码用于分析
            debug_dir = Path("debug_logs")
            debug_dir.mkdir(exist_ok=True)
            page_source = self.driver.page_source
            debug_file = debug_dir / f"venue_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            debug_file.write_text(page_source, encoding='utf-8')
            print(f"\n📝 页面源码已保存到: {debug_file}")
            
            return {
                "tables": len(tables),
                "buttons": len(buttons),
                "lock_elements": len(lock_elements),
                "unlock_elements": len(unlock_elements),
            }
            
        except Exception as e:
            print(f"❌ 分析页面结构失败: {e}")
            return None
            
    def test_find_time_slot(self, court_name, hour):
        """测试查找指定时段"""
        print(f"\n🔍 查找场地: {court_name}, 时段: {hour}:00")
        
        try:
            # 尝试多种方式查找元素
            
            # 方法 1: 通过文本查找
            xpath_patterns = [
                f"//*[contains(text(), '{hour}:00')]/following::*[contains(text(), '{court_name}')]",
                f"//*[contains(text(), '{court_name}')]/following::*[contains(text(), '{hour}:00')]",
                f"//td[contains(text(), '{hour}')]",
            ]
            
            for i, xpath in enumerate(xpath_patterns, 1):
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        print(f"  ✅ 方法 {i} 找到 {len(elements)} 个元素: {xpath[:50]}...")
                        return elements
                except:
                    continue
                    
            print(f"  ⚠️ 未找到 {court_name} {hour}:00 的时段元素")
            return None
            
        except Exception as e:
            print(f"  ❌ 查找失败: {e}")
            return None
            
    def run_diagnostic(self):
        """运行诊断测试"""
        print("\n" + "=" * 70)
        print("🧪 Sport8 场地操作测试 - 诊断模式")
        print("=" * 70)
        print(f"📅 测试日期: {TEST_DATE}")
        print(f"🔒 测试锁定场地: {len(LOCKED_SLOTS)} 个")
        print(f"🔓 测试解锁场地: {len(AVAILABLE_SLOTS)} 个")
        
        try:
            # 1. 启动浏览器
            self.setup_driver()
            
            # 2. 登录
            if not self.login():
                print("\n⚠️ 登录失败或跳过，尝试分析页面结构...")
                # 即使没有登录，也可以尝试访问场地页面看是否需要登录
                
            # 3. 导航到场地管理
            has_iframe = self.navigate_to_venue_management()
            
            # 4. 分析页面结构
            structure = self.analyze_page_structure()
            
            # 5. 测试查找时段
            print("\n🔍 步骤 4: 测试查找时段元素")
            print("=" * 60)
            for slot in LOCKED_SLOTS[:1]:  # 只测试第一个
                self.test_find_time_slot(slot["court"], slot["hour"])
                
            # 保存测试结果
            result = {
                "test_date": TEST_DATE,
                "timestamp": datetime.now().isoformat(),
                "login_success": len(self.tokens) > 0,
                "page_structure": structure,
                "current_url": self.driver.current_url,
                "page_title": self.driver.title,
            }
            
            result_file = Path("debug_logs/court_operator_test_result.json")
            result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"\n📝 测试结果已保存到: {result_file}")
            
            print("\n" + "=" * 70)
            print("✅ 诊断测试完成!")
            print("=" * 70)
            print("\n📋 下一步建议:")
            print("   1. 检查保存的 HTML 文件，分析场地表格结构")
            print("   2. 找到锁定/解锁按钮的准确选择器")
            print("   3. 开发完整的锁定/解锁功能")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                print("\n⏳ 按 Enter 关闭浏览器...")
                input()
                self.driver.quit()
                print("✅ 浏览器已关闭")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🏟️ Sport8 场地操作测试工具")
    print("=" * 70)
    print("\n这个脚本将:")
    print("  1. 登录 Sport8 系统")
    print("  2. 导航到场地管理页面")
    print("  3. 分析页面结构")
    print("  4. 尝试查找场地时段元素")
    print("\n测试数据 (2026-03-15):")
    print(f"  - 锁定场地: {len(LOCKED_SLOTS)} 个")
    print(f"  - 可用场地: {len(AVAILABLE_SLOTS)} 个")
    
    operator = CourtOperatorTest()
    operator.run_diagnostic()


if __name__ == "__main__":
    main()
