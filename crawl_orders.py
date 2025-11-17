#!/usr/bin/env python3
"""
爬取未来7天的预订记录
URL: https://stadium.sports8.com.cn/StadiumHelper/order/PageOrderServlet?optype=toOrder
"""

import json
import csv
import requests
import urllib3
from datetime import date, timedelta
from pathlib import Path
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://stadium.sports8.com.cn"

def load_tokens():
    """加载 tokens"""
    token_file = Path("login_tokens.json")
    if not token_file.exists():
        print("❌ 未找到 login_tokens.json 文件")
        print("请先运行 python3 auto_crawl.py 登录并获取 tokens")
        return None
    
    try:
        with open(token_file, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        required = ['setUserid', 'setStadiumId', 'setToken', 'setCode']
        if not all(key in tokens for key in required):
            print(f"❌ Tokens 不完整，缺少: {[k for k in required if k not in tokens]}")
            return None
        
        return tokens
    except Exception as e:
        print(f"❌ 读取 tokens 失败: {e}")
        return None

def crawl_orders(tokens, days=7):
    """爬取订单数据"""
    print("\n" + "="*70)
    print("爬取未来7天的预订记录")
    print("="*70)
    
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
            
            if data.get("result_code") == "0":
                result_data = data.get("result_data", {})
                order_list = result_data.get("fieldOrderList", [])
                
                for order in order_list:
                    status_map = {"0": "待支付", "1": "已支付", "2": "已完成", "3": "已取消"}
                    status = status_map.get(order.get("status", ""), "未知")
                    
                    order_type_map = {"0": "普通订单", "1": "会员订单"}
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
        
        except requests.exceptions.Timeout:
            print(f"[{i+1}/{days}] {current_date}... ✗ 请求超时")
        except requests.exceptions.RequestException as e:
            print(f"[{i+1}/{days}] {current_date}... ✗ 请求失败: {e}")
        except Exception as e:
            print(f"[{i+1}/{days}] {current_date}... ✗ 解析失败: {e}")
        
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
        print("\n样例数据（前 10 条）:")
        print("-" * 70)
        for order in all_orders[:10]:
            print(f"  订单号: {order['order_no']}")
            print(f"  日期时间: {order['date']} {order['time']}")
            print(f"  场地: {order['venue_name']}/{order['court_name']}")
            print(f"  客户: {order['customer_name']} ({order['customer_phone']})")
            print(f"  金额: ¥{order['price']:.2f} | 状态: {order['status']} | 支付: {order['pay_type']}")
            print("-" * 70)
        
        # 统计信息
        print("\n统计信息:")
        total_price = sum(order['price'] for order in all_orders)
        print(f"  总订单数: {len(all_orders)}")
        print(f"  总金额: ¥{total_price:.2f}")
        
        # 按状态统计
        status_count = {}
        for order in all_orders:
            status = order['status']
            status_count[status] = status_count.get(status, 0) + 1
        
        print("\n  按状态统计:")
        for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
            print(f"    {status}: {count} 条")
        
        return True
    else:
        print("\n❌ 未获取到任何订单数据")
        return False

def main():
    """主函数"""
    print("\n" + "📋 订单数据爬取工具".center(70))
    print("="*70)
    
    # 加载 tokens
    print("\n[1/2] 加载 tokens...")
    tokens = load_tokens()
    if not tokens:
        return
    
    print("✓ Tokens 加载成功")
    print(f"  用户ID: {tokens.get('setUserid')}")
    print(f"  场馆ID: {tokens.get('setStadiumId')}")
    
    # 爬取订单数据
    print("\n[2/2] 爬取订单数据...")
    success = crawl_orders(tokens, days=7)
    
    if success:
        print("\n" + "="*70)
        print("✅ 订单数据爬取完成！")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ 订单数据爬取失败")
        print("="*70)

if __name__ == "__main__":
    main()

