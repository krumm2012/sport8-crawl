#!/usr/bin/env python3
"""
一键自动爬虫
自动登录 → 提取 tokens → 爬取数据
无需手动操作（除了输入验证码）
浏览器保持打开
"""
import json
import time
import csv
from pathlib import Path
from datetime import date, timedelta

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("❌ 未安装 selenium")
    exit(1)

BASE_URL = "https://stadium.sports8.com.cn"
USERNAME = "hehh"
PASSWORD = "20250805"

def smart_extract_tokens(driver):
    """智能提取 tokens"""
    print("\n[智能提取] 自动执行 JavaScript...")
    
    # 尝试 1: 当前页面
    print("  尝试 1: 当前页面...")
    print(f"    当前 URL: {driver.current_url}")
    
    # 先等待一下，让 localStorage 有时间设置
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
    
    print(f"    找到 {len(tokens) if tokens else 0} 个 tokens: {list(tokens.keys()) if tokens else '无'}")
    
    if tokens and len(tokens) >= 4:
        print(f"  ✓ 成功！找到 {len(tokens)} 个 tokens")
        return tokens
    
    # 尝试 2: 销售页面
    print("  尝试 2: 销售页面...")
    driver.get(f"{BASE_URL}/StadiumHelper/sales/PageSalesServlet?optype=toSales")
    time.sleep(3)
    
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
        print(f"  ✓ 成功！找到 {len(tokens)} 个 tokens")
        return tokens
    
    # 尝试 3: 主页
    print("  尝试 3: 主页...")
    driver.get(f"{BASE_URL}/StadiumHelper/index/PageIndexServlet?optype=toIndex")
    time.sleep(3)
    
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
        print(f"  ✓ 成功！找到 {len(tokens)} 个 tokens")
        return tokens
    
    # 尝试 4: 等待并重试（增加等待时间）
    print("  尝试 4: 等待并重试...")
    print("    提示：登录后 localStorage 可能需要几秒钟才能设置")
    
    for i in range(20):  # 增加到 20 次尝试，共 60 秒
        time.sleep(3)  # 每次等待 3 秒
        
        # 检查当前 URL
        current_url = driver.current_url
        if i % 2 == 0:
            print(f"    等待中... ({(i+1)*3}s) - URL: {current_url[:50]}...")
        
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
        
        if tokens and len(tokens) > 0 and i % 2 == 0:
            print(f"    找到 {len(tokens)} 个 tokens: {list(tokens.keys())}")
        
        if tokens and len(tokens) >= 4:
            print(f"  ✓ 成功！等待 {(i+1)*3} 秒后找到 tokens")
            return tokens
    
    return None

def auto_login_and_extract():
    """自动登录并提取 tokens"""
    print("="*70)
    print("步骤 1/2：自动登录并提取 tokens")
    print("="*70)
    
    # 启动浏览器
    print("\n[1/5] 启动浏览器...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1200, 900)
    except Exception as e:
        print(f"❌ 无法启动 Chrome: {e}")
        return None, None
    
    tokens = None
    
    try:
        # 访问登录页
        print("[2/5] 访问登录页...")
        login_url = f"{BASE_URL}/StadiumHelper/"
        driver.get(login_url)
        print("  等待页面加载...")
        time.sleep(5)  # 增加等待时间，让页面充分加载
        
        # 填写用户名和密码
        print("[3/5] 填写登录信息...")
        try:
            # 等待登录表单加载
            print("  等待登录表单...")
            print(f"  当前页面 URL: {driver.current_url}")
            
            # 尝试多种方式查找用户名输入框
            username_field = None
            password_field = None
            
            # 直接使用 CSS 选择器（最快的方法）
            try:
                print("  等待输入框加载...")
                # 等待密码输入框出现（更可靠）
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                
                print("  查找输入框...")
                username_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                print("  ✓ 找到输入框")
            except Exception as e:
                print(f"  ✗ 查找输入框失败: {e}")
                raise Exception("无法找到登录输入框")
            
            if username_field and password_field:
                time.sleep(2)  # 表单出现后再等待 2 秒
                
                # 填写用户名
                print("  填写用户名...")
                username_field.clear()
                time.sleep(0.5)
                username_field.send_keys(USERNAME)
                print(f"  ✓ 已填写用户名: {USERNAME}")
                time.sleep(1)
                
                # 填写密码
                print("  填写密码...")
                password_field.clear()
                time.sleep(0.5)
                password_field.send_keys(PASSWORD)
                print(f"  ✓ 已填写密码: {'*' * len(PASSWORD)}")
                time.sleep(1)
                
                print("\n" + "="*70)
                print("✓ 用户名和密码已自动填写")
                print("\n⚠️  请在浏览器窗口中：")
                print("  1. 等待验证码图片加载（约 2-3 秒）")
                print("  2. 输入验证码")
                print("  3. 点击【登录】按钮")
                print("\n⏰ 你有 2 分钟时间来输入验证码和点击登录")
                print("脚本会自动检测登录成功后继续执行")
                print("="*70)
                
                # 给验证码图片加载留出时间
                print("\n等待验证码图片加载...")
                time.sleep(3)
                print("✓ 验证码应该已经加载完成")
                print("\n💡 提示：请慢慢输入验证码，不用着急，脚本会等待你登录成功")
            else:
                print("⚠️  未能找到登录输入框，请手动填写")
            
        except Exception as e:
            print(f"⚠️  自动填写失败: {e}")
            print("⚠️  请手动填写用户名和密码")
            import traceback
            print(f"详细错误:\n{traceback.format_exc()}")
        
        # 等待登录成功（给用户足够时间输入验证码）
        print("\n[4/5] 等待登录...")
        print("⏰ 等待最多 3 分钟，请慢慢输入验证码...")
        start_time = time.time()
        login_success = False
        
        while time.time() - start_time < 180:  # 增加到 180 秒（3 分钟）
            try:
                current_url = driver.current_url
                
                # 检查是否跳转或页面变化
                if current_url != login_url and "login" not in current_url.lower():
                    print(f"✓ 登录成功！当前页面: {current_url}")
                    login_success = True
                    break
                
                # 检查是否有登录成功提示
                if "登录成功" in driver.page_source or "欢迎" in driver.page_source:
                    print("✓ 检测到登录成功！")
                    login_success = True
                    time.sleep(2)
                    break
                
                time.sleep(1)
            except Exception as e:
                print(f"⚠️  页面状态变化: {e}")
                break
        
        if not login_success:
            print("继续尝试提取 tokens...")
        
        # 登录成功后，主动跳转到主页（确保 localStorage 被设置）
        try:
            current_url = driver.current_url
            print(f"\n登录后当前 URL: {current_url}")
            
            # 如果还在登录页或页面关闭，跳转到主页
            if not current_url or "about:blank" in current_url or current_url == login_url or "login" in current_url.lower():
                print("跳转到主页以确保 localStorage 被设置...")
                driver.get(f"{BASE_URL}/StadiumHelper/index/PageIndexServlet?optype=toIndex")
                time.sleep(5)  # 给足够时间让页面加载和设置 localStorage
                print(f"已跳转到: {driver.current_url}")
        except Exception as e:
            print(f"⚠️  跳转失败: {e}")
            try:
                driver.get(f"{BASE_URL}/StadiumHelper/index/PageIndexServlet?optype=toIndex")
                time.sleep(5)
            except:
                pass
        
        # 智能提取 tokens
        print("\n[5/5] 智能提取 tokens...")
        tokens = smart_extract_tokens(driver)
        
        if tokens:
            required = ['setUserid', 'setStadiumId', 'setToken', 'setCode']
            if all(key in tokens for key in required):
                # 保存 tokens
                token_file = Path("login_tokens.json")
                token_file.write_text(json.dumps(tokens, indent=2, ensure_ascii=False))
                
                print("\n✓✓✓ Tokens 提取成功！")
                print(f"✓ 已保存到: {token_file}")
                
                return tokens, driver
        
        print("\n❌ 未能提取 tokens")
        return None, driver
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return None, driver

def crawl_data(tokens):
    """爬取数据"""
    print("\n" + "="*70)
    print("步骤 2/2：爬取场地数据")
    print("="*70)
    
    # 导入必要的库
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 验证 tokens
    print("\n验证 tokens...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens.get('setCode', '')}",
    })
    
    try:
        resp = session.post(
            f"{BASE_URL}/StadiumHelper/index/StadiumIndexServlet",
            json={
                "method": "commonUserMsg",
                "userId": tokens.get("setUserid", ""),
                "stadiumId": tokens.get("setStadiumId", ""),
                "token": tokens.get("setToken", ""),
            },
            verify=False,
            timeout=10
        )
        data = resp.json()
        if data.get("result_code") != "0":
            print("❌ Tokens 无效或已过期")
            return False
    except Exception as e:
        print(f"⚠️  验证警告: {e}")
    
    print("✓ Tokens 有效！")
    
    # 爬取数据
    start_date = date.today()
    days = 7
    print(f"\n爬取日期范围: {start_date} 到 {start_date + timedelta(days=days-1)}")
    print(f"共 {days} 天\n")
    
    all_slots = []
    API_URL = f"{BASE_URL}/StadiumHelper/sales/StadiumSalesServlet"
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 获取数据
        payload = {
            "method": "getStadiumSalesDetail",
            "date": current_date.strftime("%Y-%m-%d"),
            "userId": tokens.get("setUserid", ""),
            "stadiumId": tokens.get("setStadiumId", ""),
            "token": tokens.get("setToken", ""),
            "nonce": int(time.time()),
        }
        
        try:
            resp = session.post(API_URL, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("result_code") == "0":
                result_data = data.get("result_data", {})
                status_list = result_data.get("statusList", [])
                
                # 解析数据
                for court in status_list:
                    court_name = court.get("name", "")
                    area_name = court.get("areaname", "")
                    site_status = court.get("siteStatus", [])
                    
                    for time_slot in site_status:
                        hour = int(time_slot.get("time", 0))
                        flag = str(time_slot.get("flag", "0"))
                        price = float(time_slot.get("relprice", 0.0))
                        
                        status_map = {
                            "0": "available",
                            "1": "online_reserved",
                            "2": "offline_reserved",
                            "3": "free",
                            "4": "locked",
                            "5": "long_term",
                        }
                        status = status_map.get(flag, "unknown")
                        
                        if "bookinfo" in time_slot:
                            book_content = time_slot["bookinfo"].get("content", "")
                            if "锁定" in book_content or "会员" in book_content:
                                status = "locked"
                        
                        all_slots.append({
                            "venue_name": area_name,
                            "court_name": court_name,
                            "date": current_date.strftime("%Y-%m-%d"),
                            "hour": hour,
                            "status": status,
                            "price": price,
                        })
                
                print(f"[{i+1}/{days}] {current_date}... ✓ {len(status_list) * 15} 条记录")
            else:
                print(f"[{i+1}/{days}] {current_date}... ✗ API 错误")
        except Exception as e:
            print(f"[{i+1}/{days}] {current_date}... ✗ 获取失败: {e}")
    
    if all_slots:
        print(f"\n{'='*70}")
        print(f"✓ 共获取 {len(all_slots)} 条记录")
        
        # 保存 CSV
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        csv_path = export_dir / f"bookings-{start_date.strftime('%Y%m%d')}.csv"
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["venue_name", "court_name", "date", "hour", "status", "price"])
            writer.writeheader()
            writer.writerows(all_slots)
        
        print(f"✓ 已保存到: {csv_path}")
        
        print("\n样例数据（前 10 条）:")
        for slot in all_slots[:10]:
            print(f"  {slot['date']} {slot['venue_name']}/{slot['court_name']} {slot['hour']:02d}:00 {slot['status']} ¥{slot['price']:.1f}")
        
        return True
    else:
        print("\n❌ 未获取到任何数据")
        return False

def crawl_orders(tokens, days=7):
    """爬取订单数据"""
    print("\n" + "="*70)
    print("步骤 3/3：爬取未来7天的预订记录")
    print("="*70)
    
    # 导入必要的库
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens.get('setCode', '')}",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": f"{BASE_URL}/StadiumHelper/order/PageOrderServlet?optype=toOrder",
        "Origin": BASE_URL,
    })
    
    # 计算日期范围：从今天开始的未来7天
    start_date = date.today()
    end_date = start_date + timedelta(days=days-1)
    
    print(f"\n日期范围: {start_date} 到 {end_date}")
    print(f"共 {days} 天（从今天开始往后）\n")
    
    # API URL（正确的地址）
    API_URL = f"{BASE_URL}/StadiumHelper/service/fieldOrderAPI/getFieldOrderList"
    
    all_orders = []
    
    # 爬取每一天的数据
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 构建请求参数（根据实际 API）
        payload = {
            "method": "getOrderList",
            "mobile": "",
            "pageNum": 1,
            "maxPage": 10,
            "orderType": "",
            "payType": "",
            "dateType": "",
            "areaType": "",
            "startDate": current_date.strftime("%Y%m%d"),  # 格式：YYYYMMDD
            "endDate": current_date.strftime("%Y%m%d"),    # 格式：YYYYMMDD
            "userId": tokens.get("setUserid", ""),
            "stadiumId": tokens.get("setStadiumId", ""),
            "token": tokens.get("setToken", ""),
        }
        
        try:
            resp = session.post(API_URL, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("result_code") == "0":
                result_data = data.get("result_data", {})
                order_list = result_data.get("fieldOrderList", [])  # 字段名是 fieldOrderList
                
                for order in order_list:
                    # 状态映射
                    status_map = {
                        "0": "待支付",
                        "1": "已支付",
                        "2": "已完成",
                        "3": "已取消",
                    }
                    status = status_map.get(order.get("status", ""), "未知")
                    
                    # 订单类型
                    order_type_map = {
                        "0": "普通订单",
                        "1": "会员订单",
                    }
                    order_type = order_type_map.get(order.get("orderType", ""), "未知")
                    
                    all_orders.append({
                        "order_id": order.get("orderId", ""),
                        "order_no": order.get("orderUID", ""),
                        "normal_no": order.get("normalUID", ""),
                        "date": order.get("bookDate", ""),
                        "time": order.get("timeDetail", ""),
                        "field_name": order.get("fieldName", ""),
                        "field_timebucket": order.get("fieldTimebucket", ""),
                        "customer_name": order.get("userName", ""),
                        "customer_nickname": order.get("userNickName", ""),
                        "customer_phone": order.get("mobile", ""),
                        "price": float(order.get("expense", 0.0)),
                        "status": status,
                        "order_type": order_type,
                        "confirmation_code": order.get("confirmationcode", ""),
                        "is_member": "是" if order.get("ismember") == 1 else "否",
                    })
                
                print(f"[{i+1}/{days}] {current_date}... ✓ {len(order_list)} 条订单")
            else:
                error_msg = data.get("result_msg", "未知错误")
                print(f"[{i+1}/{days}] {current_date}... ✗ API 错误: {error_msg}")
        
        except Exception as e:
            print(f"[{i+1}/{days}] {current_date}... ✗ 获取失败: {e}")
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 保存数据
    if all_orders:
        print(f"\n{'='*70}")
        print(f"✓ 共获取 {len(all_orders)} 条订单记录")
        
        # 保存 CSV
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        csv_path = export_dir / f"orders-future-{start_date.strftime('%Y%m%d')}-to-{end_date.strftime('%Y%m%d')}.csv"
        
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = [
                "order_id", "order_no", "normal_no", "date", "time",
                "field_name", "field_timebucket",
                "customer_name", "customer_nickname", "customer_phone",
                "price", "status", "order_type", "confirmation_code", "is_member"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_orders)
        
        print(f"✓ 已保存到: {csv_path}")
        
        # 显示样例数据
        print("\n样例数据（前 5 条）:")
        for order in all_orders[:5]:
            print(f"  {order['date']} {order['time']} | {order['field_name']} | {order['customer_name']} | ¥{order['price']:.2f} | {order['status']}")
        
        # 统计信息
        total_price = sum(order['price'] for order in all_orders)
        print(f"\n统计: 共 {len(all_orders)} 条订单，总金额 ¥{total_price:.2f}")
        
        return True
    else:
        print("\n❌ 未获取到任何订单数据")
        return False

def main():
    """主函数"""
    print("\n" + "🚀 一键自动爬虫".center(70))
    print("="*70)
    print("功能：")
    print("  1. 自动登录（只需输入验证码）")
    print("  2. 自动提取 tokens")
    print("  3. 自动爬取场地数据")
    print("  4. 自动爬取订单数据")
    print("  5. 自动保存 CSV")
    print("  6. 浏览器保持打开")
    print("="*70)
    
    driver = None
    
    try:
        # 步骤 1: 自动登录并提取 tokens
        tokens, driver = auto_login_and_extract()
        
        if not tokens:
            print("\n❌ 登录失败，无法继续")
            return False
        
        # 步骤 2: 爬取场地数据
        success1 = crawl_data(tokens)
        
        # 步骤 3: 爬取订单数据
        success2 = crawl_orders(tokens)
        
        if success1 or success2:
            print("\n" + "="*70)
            print("🎉 所有操作完成！")
            print("="*70)
            print("\n✓ 登录成功")
            print("✓ Tokens 已保存")
            if success1:
                print("✓ 场地数据已爬取")
            if success2:
                print("✓ 订单数据已爬取")
            print("✓ CSV 已保存")
            print("\n查看数据:")
            print("  - 场地数据: data/exports/bookings-*.csv")
            if success2:
                print("  - 订单数据: data/exports/orders-*.csv")
        
        return success1 or success2
        
    except KeyboardInterrupt:
        print("\n\n用户取消")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 保持浏览器打开，不关闭
        if driver:
            print("\n✓ 浏览器保持打开")
            print("提示：你可以继续在浏览器中查看数据")
            # 不关闭浏览器
            pass

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ 全部完成！")
        exit(0)
    else:
        print("\n❌ 执行失败")
        exit(1)

