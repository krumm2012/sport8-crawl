#!/usr/bin/env python3
"""
场地操作自动测试脚本 - 使用已保存的 token
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

# 配置
BASE_URL = "https://stadium.sports8.com.cn"
TEST_DATE = "2026-03-15"

# 加载已保存的 token
TOKENS_FILE = Path("login_tokens.json")
if TOKENS_FILE.exists():
    TOKENS = json.loads(TOKENS_FILE.read_text())
    print(f"✅ 已加载 token: {TOKENS.get('setLoginname', 'unknown')}")
else:
    print("❌ 未找到 token 文件")
    sys.exit(1)


class CourtOperatorAutoTest:
    """场地操作自动测试类"""
    
    def __init__(self):
        self.driver = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_date": TEST_DATE,
            "steps": []
        }
        
    def setup_driver(self):
        """初始化浏览器"""
        print("\n🌐 启动 Chrome 浏览器...")
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        
        # 设置 localStorage token
        print("🔧 注入登录 token...")
        self.driver.get(f"{BASE_URL}/StadiumHelper/login/login.jsp")
        time.sleep(1)
        
        for key, value in TOKENS.items():
            self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
            
        print(f"✅ 已注入 {len(TOKENS)} 个 token")
        
    def navigate_to_venue(self):
        """导航到场地管理页面"""
        print("\n📍 导航到场地管理页面...")
        
        venue_url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium"
        self.driver.get(venue_url)
        time.sleep(5)  # 等待页面加载
        
        print(f"✅ 页面标题: {self.driver.title}")
        print(f"✅ 当前URL: {self.driver.current_url}")
        
        # 检查是否被重定向到登录页
        if "login.jsp" in self.driver.current_url:
            print("⚠️ token 已过期，被重定向到登录页")
            return False
            
        return True
        
    def analyze_page(self):
        """分析页面结构"""
        print("\n🔍 分析页面结构...")
        print("=" * 60)
        
        analysis = {}
        
        # 1. 检查 iframe
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        analysis["iframes_count"] = len(iframes)
        print(f"📊 发现 {len(iframes)} 个 iframe")
        
        if iframes:
            # 切换到第一个 iframe
            self.driver.switch_to.frame(iframes[0])
            print("✅ 已切换到 iframe 1")
            analysis["in_iframe"] = True
        else:
            analysis["in_iframe"] = False
            
        # 2. 查找表格
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        analysis["tables_count"] = len(tables)
        print(f"📊 发现 {len(tables)} 个 table")
        
        # 3. 查找行
        rows = self.driver.find_elements(By.TAG_NAME, "tr")
        analysis["rows_count"] = len(rows)
        print(f"📊 发现 {len(rows)} 个 tr")
        
        # 4. 查找按钮
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        analysis["buttons_count"] = len(buttons)
        print(f"📊 发现 {len(buttons)} 个 button")
        
        # 5. 查找包含"锁定"的元素
        lock_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '锁定')]")
        analysis["lock_elements_count"] = len(lock_elements)
        print(f"📊 发现 {len(lock_elements)} 个包含'锁定'的元素")
        
        # 6. 查找包含"解锁"的元素
        unlock_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '解锁')]")
        analysis["unlock_elements_count"] = len(unlock_elements)
        print(f"📊 发现 {len(unlock_elements)} 个包含'解锁'的元素")
        
        # 7. 查找包含"预约"的元素
        book_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '预约')]")
        analysis["book_elements_count"] = len(book_elements)
        print(f"📊 发现 {len(book_elements)} 个包含'预约'的元素")
        
        # 8. 查找时间相关元素
        time_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '16:00') or contains(text(), '16')]")
        analysis["time_16_count"] = len(time_elements)
        print(f"📊 发现 {len(time_elements)} 个包含'16:00'或'16'的元素")
        
        # 9. 保存页面源码
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        html_file = debug_dir / f"venue_page_{timestamp}.html"
        html_file.write_text(self.driver.page_source, encoding='utf-8')
        print(f"\n📝 页面 HTML 已保存: {html_file}")
        
        # 10. 截图
        screenshot_file = debug_dir / f"venue_screenshot_{timestamp}.png"
        self.driver.save_screenshot(str(screenshot_file))
        print(f"📝 页面截图已保存: {screenshot_file}")
        
        self.results["page_analysis"] = analysis
        return analysis
        
    def test_search_date(self):
        """测试搜索指定日期"""
        print(f"\n🔍 测试搜索日期: {TEST_DATE}")
        print("=" * 60)
        
        try:
            # 查找日期输入框
            date_inputs = self.driver.find_elements(By.XPATH, "//input[@type='date']")
            print(f"📊 发现 {len(date_inputs)} 个 date input")
            
            # 查找文本输入框（可能用于日期）
            text_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text']")
            print(f"📊 发现 {len(text_inputs)} 个 text input")
            
            # 尝试查找搜索按钮
            search_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), '查询') or contains(text(), '搜索')]")
            print(f"📊 发现 {len(search_buttons)} 个查询/搜索按钮")
            
            # 检查当前显示的日期
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if TEST_DATE in page_text:
                print(f"✅ 页面已包含目标日期: {TEST_DATE}")
            else:
                print(f"⚠️ 页面未显示目标日期，可能默认显示今天")
                
            self.results["date_search"] = {
                "date_inputs": len(date_inputs),
                "text_inputs": len(text_inputs),
                "search_buttons": len(search_buttons),
                "date_found": TEST_DATE in page_text
            }
            
        except Exception as e:
            print(f"❌ 日期搜索测试失败: {e}")
            
    def analyze_court_structure(self):
        """分析场地结构"""
        print("\n🏟️ 分析场地结构...")
        print("=" * 60)
        
        try:
            # 查找包含场地名称的元素
            court_names = ["学练馆-01", "学练馆-02", "学练馆小-03"]
            
            for court in court_names:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{court}')]")
                print(f"📍 {court}: 找到 {len(elements)} 个元素")
                
        except Exception as e:
            print(f"❌ 场地结构分析失败: {e}")
            
    def run_test(self):
        """运行完整测试"""
        print("\n" + "=" * 70)
        print("🧪 Sport8 场地操作自动测试")
        print("=" * 70)
        print(f"📅 测试日期: {TEST_DATE}")
        print(f"👤 用户: {TOKENS.get('setLoginname')}")
        
        try:
            # 1. 启动浏览器并注入 token
            self.setup_driver()
            
            # 2. 导航到场地管理
            if not self.navigate_to_venue():
                print("\n❌ 导航失败，token 可能已过期")
                self.results["success"] = False
                return
                
            # 3. 分析页面
            analysis = self.analyze_page()
            
            # 4. 测试日期搜索
            self.test_search_date()
            
            # 5. 分析场地结构
            self.analyze_court_structure()
            
            self.results["success"] = True
            
            # 保存结果
            result_file = Path("debug_logs/court_operator_auto_test.json")
            result_file.write_text(json.dumps(self.results, indent=2, ensure_ascii=False), encoding='utf-8')
            
            print("\n" + "=" * 70)
            print("✅ 测试完成!")
            print("=" * 70)
            print(f"\n📁 测试结果: {result_file}")
            print(f"📝 页面 HTML: debug_logs/venue_page_*.html")
            print(f"📸 页面截图: debug_logs/venue_screenshot_*.png")
            
            print("\n📋 关键发现:")
            print(f"   - iframe 数量: {analysis.get('iframes_count', 0)}")
            print(f"   - 表格数量: {analysis.get('tables_count', 0)}")
            print(f"   - 锁定按钮: {analysis.get('lock_elements_count', 0)} 个")
            print(f"   - 解锁按钮: {analysis.get('unlock_elements_count', 0)} 个")
            
            print("\n🔧 下一步:")
            print("   1. 查看截图和 HTML 文件分析页面结构")
            print("   2. 找到锁定/解锁按钮的具体选择器")
            print("   3. 开发操作功能")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.results["success"] = False
            self.results["error"] = str(e)
            
        finally:
            if self.driver:
                time.sleep(2)
                self.driver.quit()
                print("\n✅ 浏览器已关闭")


def main():
    tester = CourtOperatorAutoTest()
    tester.run_test()


if __name__ == "__main__":
    main()
