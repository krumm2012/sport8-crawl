#!/usr/bin/env python3
"""
统一数据爬取工具 - 同时爬取场地状态和订单数据
验证两者一致性，生成对比报告
"""

import os
import sys
import time
import json
import csv
import requests
import urllib3
from datetime import date, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 导入验证码识别器
try:
    from captcha_recognizer import CaptchaRecognizer
except ImportError:
    print("⚠️  未安装验证码识别器，将使用手动输入模式")
    CaptchaRecognizer = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

# 数据目录
DATA_DIR = Path(__file__).parent / "data" / "exports"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class UnifiedCrawler:
    """统一爬虫 - 同时获取场地状态和订单数据"""
    
    def __init__(self):
        self.tokens = None
        self.driver = None
        self.session = requests.Session()
        self.court_status_data = []
        self.order_data = []
        self.comparison_report = []
        
    def auto_login(self):
        """自动登录（带验证码自动识别）"""
        print("="*70)
        print("🔐 步骤 1/4：自动登录")
        print("="*70)
        
        # 创建验证码识别器
        recognizer = CaptchaRecognizer() if CaptchaRecognizer else None
        
        # 启动浏览器
        print("\n[1/5] 启动浏览器...")
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 检查是否需要 headless 模式
        headless_mode = os.getenv("HEADLESS", "false").lower() == "true"
        if headless_mode:
            print("  使用 headless 模式...")
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        
        try:
            # 访问登录页面
            print("[2/5] 访问登录页...")
            self.driver.get(f"{BASE_URL}/StadiumHelper/index/login.jsp")
            time.sleep(2)
            
            # 填写用户名和密码
            print("[3/5] 填写登录信息...")
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "loginname"))
            )
            password_field = self.driver.find_element(By.NAME, "loginpass")
            
            username_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)
            print(f"  ✓ 已填写用户名: {USERNAME}")
            print(f"  ✓ 已填写密码: {'*' * len(PASSWORD)}")
            
            # 处理验证码
            print("\n[4/5] 自动识别验证码并登录...")
            
            for attempt in range(5):
                print(f"\n  尝试 {attempt + 1}/5:")
                
                # 获取验证码图片
                captcha_img = self.driver.find_element(By.ID, "codeImg")
                captcha_src = captcha_img.get_attribute("src")
                
                if recognizer and "data:image" in captcha_src:
                    # 自动识别验证码
                    captcha_code = recognizer.recognize_from_base64(captcha_src.split(",")[1])
                    print(f"    ✓ 识别结果: {captcha_code}")
                else:
                    # 手动输入
                    captcha_code = input("    请输入验证码: ")
                
                # 填写验证码
                code_field = self.driver.find_element(By.NAME, "checkcode")
                code_field.clear()
                code_field.send_keys(captcha_code)
                print(f"    ✓ 已填写验证码")
                
                # 点击登录
                login_btn = self.driver.find_element(By.ID, "loginbtn")
                login_btn.click()
                time.sleep(3)
                
                # 检查是否登录成功
                current_url = self.driver.current_url
                if "index/PageIndexServlet" in current_url or "toIndex" in current_url:
                    print(f"\n  ✓✓✓ 登录成功！")
                    print(f"  当前页面: {current_url}")
                    break
                else:
                    # 检查是否有错误提示
                    try:
                        error_msg = self.driver.find_element(By.ID, "errorMsg").text
                        if error_msg:
                            print(f"    ✗ 登录失败: {error_msg}")
                            # 刷新验证码
                            self.driver.find_element(By.ID, "codeImg").click()
                            time.sleep(1)
                    except:
                        pass
            else:
                print("\n  ❌ 登录失败，已达到最大尝试次数")
                return False
            
            # 提取 tokens
            print("\n[5/5] 提取 tokens...")
            self.tokens = self.driver.execute_script("""
                const tokens = {};
                const keys = ['setUserid', 'setStadiumId', 'setToken', 'setCode', 
                              'setCustId', 'setLoginname', 'setMobile', 'setDeviceFlag'];
                keys.forEach(key => {
                    const value = localStorage.getItem(key);
                    if (value) tokens[key] = value;
                });
                return tokens;
            """)
            
            if len(self.tokens) >= 4:
                print(f"  ✓ 成功提取 {len(self.tokens)} 个 tokens")
                
                # 保存 tokens
                with open("login_tokens.json", "w", encoding="utf-8") as f:
                    json.dump(self.tokens, f, indent=2, ensure_ascii=False)
                print(f"  ✓ 已保存到: login_tokens.json")
                return True
            else:
                print(f"  ⚠️  只找到 {len(self.tokens)} 个 tokens，可能不完整")
                return False
                
        except Exception as e:
            print(f"\n  ❌ 登录过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def crawl_court_status(self, target_date=None):
        """爬取场地状态数据"""
        print("\n" + "="*70)
        print("🏟️  步骤 2/4：爬取场地状态")
        print("="*70)
        
        if not target_date:
            target_date = date.today()
        
        print(f"\n目标日期: {target_date}")
        
        # 设置请求头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.tokens.get('setCode', '')}",
        })
        
        API_URL = f"{BASE_URL}/StadiumHelper/sales/StadiumSalesServlet"
        
        payload = {
            "method": "getStadiumSalesDetail",
            "date": target_date.strftime("%Y-%m-%d"),
            "userId": self.tokens.get("setUserid", ""),
            "stadiumId": self.tokens.get("setStadiumId", ""),
            "token": self.tokens.get("setToken", ""),
            "nonce": int(time.time()),
        }
        
        try:
            print("🚀 调用场地状态 API...")
            resp = self.session.post(API_URL, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("result_code") != "0":
                print(f"❌ API 错误: {data.get('result_msg')}")
                return False
            
            status_list = data.get("result_data", {}).get("statusList", [])
            print(f"✓ 获取成功，{len(status_list)} 个场地")
            
            # 解析场地状态
            self.court_status_data = []
            for court in status_list:
                court_name = court.get("name", "")
                area_name = court.get("areaname", "")
                
                for slot in court.get("siteStatus", []):
                    hour = int(slot.get("time", 0))
                    flag = str(slot.get("flag", "0"))
                    price = float(slot.get("relprice", 0.0))
                    
                    # 状态映射
                    status_map = {
                        "0": "available",
                        "1": "online_reserved",
                        "2": "offline_reserved",
                        "3": "free",
                        "4": "locked",
                        "5": "long_term",
                    }
                    status = status_map.get(flag, f"unknown({flag})")
                    
                    # 如果有预订信息，增强状态
                    bookinfo = slot.get("bookinfo", {})
                    book_content = bookinfo.get("content", "") if bookinfo else ""
                    
                    self.court_status_data.append({
                        "venue_name": area_name,
                        "court_name": court_name,
                        "date": target_date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "status": status,
                        "flag": flag,
                        "price": price,
                        "book_content": book_content,
                    })
            
            print(f"✓ 共解析 {len(self.court_status_data)} 个时段")
            
            # 保存 CSV
            csv_path = DATA_DIR / f"court_status_{target_date.strftime('%Y%m%d')}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                fieldnames = ["venue_name", "court_name", "date", "hour", "status", "flag", "price", "book_content"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.court_status_data)
            
            print(f"✓ 已保存到: {csv_path}")
            
            # 显示 21:00 数据
            print("\n📊 今日 21:00 场地状态:")
            print("-" * 60)
            for item in self.court_status_data:
                if item["hour"] == 21:
                    print(f"  {item['court_name']:12s} {item['status']:20s} ¥{item['price']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def crawl_orders(self, target_date=None):
        """爬取订单数据"""
        print("\n" + "="*70)
        print("📋 步骤 3/4：爬取订单数据")
        print("="*70)
        
        if not target_date:
            target_date = date.today()
        
        print(f"\n目标日期: {target_date}")
        
        API_URL = f"{BASE_URL}/StadiumHelper/service/fieldOrderAPI/getFieldOrderList"
        
        payload = {
            "method": "getOrderList",
            "mobile": "",
            "pageNum": 1,
            "maxPage": 100,
            "orderType": "",
            "payType": "",
            "dateType": "",
            "areaType": "",
            "startDate": target_date.strftime("%Y%m%d"),
            "endDate": target_date.strftime("%Y%m%d"),
            "userId": self.tokens.get("setUserid", ""),
            "stadiumId": self.tokens.get("setStadiumId", ""),
            "token": self.tokens.get("setToken", ""),
        }
        
        try:
            print("🚀 调用订单 API...")
            resp = self.session.post(API_URL, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("result_code") != "0":
                print(f"❌ API 错误: {data.get('result_msg')}")
                return False
            
            result_data = data.get("result_data", {})
            order_list = result_data.get("fieldOrderList", [])
            print(f"✓ 获取成功，{len(order_list)} 条订单")
            
            # 解析订单数据
            self.order_data = []
            for order in order_list:
                status_map = {"0": "待支付", "1": "已支付", "2": "已完成", "3": "已取消"}
                status = status_map.get(order.get("status", ""), "未知")
                
                # 解析时间和场地
                time_detail = order.get("timeDetail", "")
                field_name = order.get("fieldName", "")
                
                self.order_data.append({
                    "order_id": order.get("orderId", ""),
                    "order_no": order.get("orderUID", ""),
                    "date": order.get("bookDate", ""),
                    "time": time_detail,
                    "field_name": field_name,
                    "customer_name": order.get("userName", ""),
                    "customer_phone": order.get("mobile", ""),
                    "price": float(order.get("expense", 0.0)),
                    "status": status,
                    "confirmation_code": order.get("confirmationcode", ""),
                })
            
            # 保存 CSV
            csv_path = DATA_DIR / f"orders_{target_date.strftime('%Y%m%d')}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                fieldnames = ["order_id", "order_no", "date", "time", "field_name", 
                             "customer_name", "customer_phone", "price", "status", "confirmation_code"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.order_data)
            
            print(f"✓ 已保存到: {csv_path}")
            
            # 显示订单摘要
            if self.order_data:
                print("\n📋 今日订单摘要:")
                print("-" * 60)
                for order in self.order_data[:5]:
                    print(f"  订单: {order['order_no']}")
                    print(f"  时间: {order['date']} {order['time']}")
                    print(f"  场地: {order['field_name']}")
                    print(f"  客户: {order['customer_name']} | 状态: {order['status']}")
                    print("-" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_comparison_report(self, target_date=None):
        """生成对比报告 - 对比场地状态和订单数据"""
        print("\n" + "="*70)
        print("📊 步骤 4/4：生成对比报告")
        print("="*70)
        
        if not target_date:
            target_date = date.today()
        
        print(f"\n对比日期: {target_date}")
        
        # 构建订单时间映射
        order_map = {}
        for order in self.order_data:
            # 解析场地和时间
            field_name = order.get("field_name", "")
            time_str = order.get("time", "")
            
            # 尝试匹配场地
            court_name = None
            if "学练馆-01" in field_name or "[01]" in field_name:
                court_name = "学练馆-01"
            elif "学练馆-02" in field_name or "[02]" in field_name:
                court_name = "学练馆-02"
            elif "学练馆小-03" in field_name or "[03]" in field_name:
                court_name = "学练馆小-03"
            
            # 解析时间
            if time_str:
                try:
                    hour = int(time_str.split(":")[0])
                    if court_name:
                        key = f"{court_name}_{hour}"
                        order_map[key] = order
                except:
                    pass
        
        print(f"\n✓ 订单数据映射: {len(order_map)} 条")
        
        # 对比分析
        self.comparison_report = []
        inconsistencies = []
        
        print("\n" + "-" * 70)
        print("🔍 对比分析 (21:00 时段):")
        print("-" * 70)
        
        for item in self.court_status_data:
            if item["hour"] != 21:  # 只对比 21:00
                continue
            
            court_name = item["court_name"]
            status = item["status"]
            flag = item["flag"]
            
            key = f"{court_name}_21"
            order = order_map.get(key)
            
            # 判断一致性
            has_order = order is not None
            is_reserved = status in ["online_reserved", "offline_reserved", "locked"]
            
            if has_order and is_reserved:
                consistency = "✅ 一致"
                note = f"场地状态: {status}, 订单存在"
            elif not has_order and status == "available":
                consistency = "✅ 一致"
                note = "场地空闲，无订单"
            elif has_order and status == "available":
                consistency = "❌ 不一致"
                note = f"⚠️  有订单但场地显示 available！订单: {order.get('customer_name', '')}"
                inconsistencies.append({
                    "court": court_name,
                    "hour": 21,
                    "issue": "有订单但场地空闲",
                    "order": order,
                    "status": status
                })
            elif not has_order and is_reserved:
                consistency = "⚠️  需确认"
                note = f"场地显示 {status} 但无订单，可能是锁定或长订"
            else:
                consistency = "❓ 未知"
                note = f"状态: {status}, 有订单: {has_order}"
            
            report_item = {
                "court": court_name,
                "hour": 21,
                "status": status,
                "flag": flag,
                "has_order": has_order,
                "consistency": consistency,
                "note": note,
            }
            self.comparison_report.append(report_item)
            
            print(f"\n  {court_name} 21:00:")
            print(f"    场地状态: {status} (flag={flag})")
            print(f"    订单状态: {'✓ 有订单' if has_order else '✗ 无订单'}")
            print(f"    一致性: {consistency}")
            print(f"    备注: {note}")
        
        # 保存对比报告
        report_path = DATA_DIR / f"comparison_report_{target_date.strftime('%Y%m%d')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "date": target_date.strftime("%Y-%m-%d"),
                "comparison": self.comparison_report,
                "inconsistencies": inconsistencies,
                "summary": {
                    "total_checked": len(self.comparison_report),
                    "consistent": sum(1 for r in self.comparison_report if "✅" in r["consistency"]),
                    "inconsistent": len(inconsistencies),
                    "needs_check": sum(1 for r in self.comparison_report if "⚠️" in r["consistency"]),
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 对比报告已保存: {report_path}")
        
        # 显示总结
        print("\n" + "="*70)
        print("📋 对比总结:")
        print("="*70)
        print(f"  总检查数: {len(self.comparison_report)}")
        print(f"  ✅ 一致: {sum(1 for r in self.comparison_report if '✅' in r['consistency'])}")
        print(f"  ❌ 不一致: {len(inconsistencies)}")
        print(f"  ⚠️  需确认: {sum(1 for r in self.comparison_report if '⚠️' in r['consistency'])}")
        
        if inconsistencies:
            print("\n" + "⚠️  发现数据不一致:" + "\n" + "-" * 70)
            for inc in inconsistencies:
                print(f"  • {inc['court']} {inc['hour']}:00 - {inc['issue']}")
                if inc.get('order'):
                    print(f"    订单: {inc['order'].get('customer_name', '')} {inc['order'].get('customer_phone', '')}")
        
        return len(inconsistencies) == 0
    
    def run(self, target_date=None):
        """运行完整流程"""
        print("\n" + "="*70)
        print("🚀 统一数据爬取工具 - 场地状态 + 订单数据")
        print("="*70)
        
        start_time = time.time()
        
        try:
            # 1. 登录
            if not self.auto_login():
                return False
            
            # 2. 爬取场地状态
            if not self.crawl_court_status(target_date):
                print("⚠️  场地状态爬取失败，继续尝试订单数据...")
            
            # 3. 爬取订单数据
            if not self.crawl_orders(target_date):
                print("⚠️  订单数据爬取失败...")
            
            # 4. 生成对比报告
            if self.court_status_data and self.order_data:
                self.generate_comparison_report(target_date)
            
            elapsed = time.time() - start_time
            print("\n" + "="*70)
            print(f"✅ 所有任务完成！耗时: {elapsed:.1f} 秒")
            print("="*70)
            print(f"\n📁 输出文件:")
            print(f"  • 场地状态: data/exports/court_status_YYYYMMDD.csv")
            print(f"  • 订单数据: data/exports/orders_YYYYMMDD.csv")
            print(f"  • 对比报告: data/exports/comparison_report_YYYYMMDD.json")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
            return False
        except Exception as e:
            print(f"\n❌ 运行出错: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 保持浏览器打开
            if self.driver:
                print("\n💡 浏览器保持打开，您可以继续查看")
                # self.driver.quit()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一数据爬取工具')
    parser.add_argument('--date', type=str, help='目标日期 (YYYY-MM-DD)，默认今天')
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        from datetime import datetime
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    
    crawler = UnifiedCrawler()
    success = crawler.run(target_date)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
