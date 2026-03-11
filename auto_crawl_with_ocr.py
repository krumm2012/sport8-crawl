#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键自动爬虫 - 带自动验证码识别
功能：自动登录 + 自动识别验证码 + 自动爬取数据
"""

import os
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
    
    # 检查是否在 Docker 环境或需要 headless 模式
    headless_mode = os.getenv("HEADLESS", "false").lower() == "true" or os.path.exists("/.dockerenv")
    if headless_mode:
        print("  检测到 Docker 环境，使用 headless 模式...")
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    if not headless_mode:
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


def crawl_data(tokens, days: int = 7):
    """爬取场地数据（未来 days 天）"""
    print("\n" + "="*70)
    print("步骤 2/3：爬取场地数据")
    print("="*70)
    
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
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
            timeout=15,
        )
        data = resp.json()
        if data.get("result_code") != "0":
            print("❌ Tokens 无效或已过期")
            return False
    except Exception as exc:
        print(f"⚠️  Tokens 校验失败: {exc}")
    
    print("✓ Tokens 有效！")
    
    start_date = date.today()
    print(f"\n爬取日期范围: {start_date} 到 {start_date + timedelta(days=days-1)}")
    
    API_URL = f"{BASE_URL}/StadiumHelper/sales/StadiumSalesServlet"
    all_slots = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
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
            
            if data.get("result_code") != "0":
                print(f"[{i+1}/{days}] {current_date}... ✗ API 错误: {data.get('result_msg')}")
                continue
            
            status_list = data.get("result_data", {}).get("statusList", [])
            for court in status_list:
                court_name = court.get("name", "")
                area_name = court.get("areaname", "")
                site_status = court.get("siteStatus", [])
                
                for slot in site_status:
                    hour = int(slot.get("time", 0))
                    flag = str(slot.get("flag", "0"))
                    price = float(slot.get("relprice", 0.0))
                    
                    status_map = {
                        "0": "available",
                        "1": "online_reserved",
                        "2": "offline_reserved",
                        "3": "free",
                        "4": "locked",
                        "5": "long_term",
                    }
                    status = status_map.get(flag, "unknown")
                    
                    if "bookinfo" in slot:
                        book_content = slot["bookinfo"].get("content", "")
                        if any(keyword in book_content for keyword in ("锁定", "会员", "已约")):
                            status = "locked"
                    
                    all_slots.append({
                        "venue_name": area_name,
                        "court_name": court.get("name", ""),
                        "date": current_date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "status": status,
                        "price": price,
                    })
            
            print(f"[{i+1}/{days}] {current_date}... ✓ {len(status_list)} 组场地")
        except Exception as exc:
            print(f"[{i+1}/{days}] {current_date}... ✗ 获取失败: {exc}")
    
    if not all_slots:
        print("\n❌ 未获取到任何场地数据")
        return False
    
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    csv_path = export_dir / f"bookings-{start_date.strftime('%Y%m%d')}.csv"
    
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["venue_name", "court_name", "date", "hour", "status", "price"])
        writer.writeheader()
        writer.writerows(all_slots)
    
    print(f"\n✓ 共获取 {len(all_slots)} 条场地时段，已保存到: {csv_path}")
    return True


def crawl_orders(tokens, days: int = 7):
    """爬取订单数据（未来 days 天）"""
    print("\n" + "="*70)
    print("步骤 3/3：爬取未来7天的预订记录")
    print("="*70)
    
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens.get('setCode', '')}",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": f"{BASE_URL}/StadiumHelper/order/PageOrderServlet?optype=toOrder",
    })
    
    API_URL = f"{BASE_URL}/StadiumHelper/service/fieldOrderAPI/getFieldOrderList"
    start_date = date.today()
    end_date = start_date + timedelta(days=days-1)
    
    all_orders = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        payload = {
            "method": "getOrderList",
            "mobile": "",
            "pageNum": 1,
            "maxPage": 10,
            "orderType": "",
            "payType": "",
            "dateType": "",
            "areaType": "",
            "startDate": current_date.strftime("%Y%m%d"),
            "endDate": current_date.strftime("%Y%m%d"),
            "userId": tokens.get("setUserid", ""),
            "stadiumId": tokens.get("setStadiumId", ""),
            "token": tokens.get("setToken", ""),
        }
        
        try:
            resp = session.post(API_URL, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("result_code") != "0":
                print(f"[{i+1}/{days}] {current_date}... ✗ API 错误: {data.get('result_msg')}")
                continue
            
            order_list = data.get("result_data", {}).get("fieldOrderList", [])
            for order in order_list:
                status_map = {"0": "待支付", "1": "已支付", "2": "已完成", "3": "已取消"}
                order_type_map = {"0": "普通订单", "1": "会员订单"}
                
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
                    "status": status_map.get(order.get("status", ""), "未知"),
                    "order_type": order_type_map.get(order.get("orderType", ""), "未知"),
                    "confirmation_code": order.get("confirmationcode", ""),
                    "is_member": "是" if order.get("ismember") == 1 else "否",
                })
            
            print(f"[{i+1}/{days}] {current_date}... ✓ {len(order_list)} 条订单")
        except Exception as exc:
            print(f"[{i+1}/{days}] {current_date}... ✗ 获取失败: {exc}")
        
        time.sleep(0.5)
    
    if not all_orders:
        print("\n❌ 未获取到任何订单数据")
        return False
    
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    csv_path = export_dir / f"orders-future-{start_date.strftime('%Y%m%d')}-to-{end_date.strftime('%Y%m%d')}.csv"
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fp:
        fieldnames = [
            "order_id", "order_no", "normal_no", "date", "time",
            "field_name", "field_timebucket",
            "customer_name", "customer_nickname", "customer_phone",
            "price", "status", "order_type", "confirmation_code", "is_member",
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_orders)
    
    print(f"\n✓ 共获取 {len(all_orders)} 条订单记录，已保存到: {csv_path}")
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


