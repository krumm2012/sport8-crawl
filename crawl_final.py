#!/usr/bin/env python3
"""
Sport8 场地预订爬虫 - 最终版本
使用浏览器手动登录后的 tokens
"""
import json
import requests
from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Any
import time

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://stadium.sports8.com.cn"
API_URL = f"{BASE_URL}/StadiumHelper/sales/StadiumSalesServlet"

def load_tokens() -> Dict[str, str]:
    """从文件加载 tokens"""
    token_file = Path("login_tokens.json")
    
    if not token_file.exists():
        print("❌ 未找到 login_tokens.json 文件")
        print("\n请先提取最新的 tokens！")
        show_token_extraction_guide()
        exit(1)
    
    try:
        tokens = json.loads(token_file.read_text())
        return tokens
    except Exception as e:
        print(f"❌ 无法读取 tokens 文件: {e}")
        exit(1)

def show_token_extraction_guide():
    """显示 token 提取指南"""
    print("\n" + "="*70)
    print("如何提取最新的 tokens")
    print("="*70)
    print("\n1. 在浏览器中登录 stadium.sports8.com.cn")
    print("2. 按 F12 打开开发者工具 → Application 标签")
    print("3. 左侧找到 Local Storage → https://stadium.sports8.com.cn")
    print("4. 复制以下字段的值：")
    print("   - setCode")
    print("   - setCustId")
    print("   - setDeviceFlag")
    print("   - setLoginname")
    print("   - setMobile")
    print("   - setStadiumId")
    print("   - setToken")
    print("   - setUserid")
    print("\n5. 按照以下格式保存到 login_tokens.json：")
    print("""
{
  "setCode": "从浏览器复制的值",
  "setCustId": "从浏览器复制的值",
  "setDeviceFlag": "1",
  "setLoginname": "hehh",
  "setMobile": "从浏览器复制的值",
  "setStadiumId": "966",
  "setToken": "从浏览器复制的值",
  "setUserid": "从浏览器复制的值"
}
""")

def verify_tokens(tokens: Dict[str, str]) -> bool:
    """验证 tokens 是否有效"""
    print("\n验证 tokens...")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens.get('setCode', '')}",
        "Accept": "application/json, text/plain, */*",
    })
    
    payload = {
        "method": "getStadiumSalesDetail",
        "date": "",
        "userId": tokens.get("setUserid", ""),
        "stadiumId": tokens.get("setStadiumId", ""),
        "token": tokens.get("setToken", ""),
    }
    
    try:
        resp = session.post(API_URL, json=payload, verify=False, timeout=10)
        data = resp.json()
        
        if data.get("result_code") == "0":
            print("✓ Tokens 有效！")
            return True
        else:
            print(f"✗ Tokens 已失效：{data.get('result_msg')}")
            return False
    except Exception as e:
        print(f"✗ 验证失败：{e}")
        return False

def fetch_sales_detail(tokens: Dict[str, str], target_date: date) -> Dict[str, Any]:
    """获取指定日期的场地销售详情"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens.get('setCode', '')}",
        "Accept": "application/json, text/plain, */*",
    })
    
    payload = {
        "method": "getStadiumSalesDetail",
        "date": target_date.strftime("%Y-%m-%d"),
        "userId": tokens.get("setUserid", ""),
        "stadiumId": tokens.get("setStadiumId", ""),
        "token": tokens.get("setToken", ""),
    }
    
    try:
        resp = session.post(API_URL, json=payload, verify=False, timeout=30)
        data = resp.json()
        
        if data.get("result_code") == "0":
            return data
        else:
            print(f"  ✗ {target_date}: {data.get('result_msg')}")
            return {}
    except Exception as e:
        print(f"  ✗ {target_date}: {e}")
        return {}

def parse_sales_detail(data: Dict[str, Any], target_date: date) -> List[Dict[str, Any]]:
    """解析销售详情数据"""
    slots = []
    
    result_data = data.get("result_data", {})
    status_list = result_data.get("statusList", [])
    
    for court in status_list:
        court_name = court.get("name", "")
        area_name = court.get("areaname", "")
        site_status = court.get("siteStatus", [])
        
        for time_slot in site_status:
            hour = int(time_slot.get("time", 0))
            flag = time_slot.get("flag", "0")
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
            
            slots.append({
                "venue_name": area_name,
                "court_name": court_name,
                "date": target_date.strftime("%Y-%m-%d"),
                "hour": hour,
                "status": status,
                "price": price,
            })
    
    return slots

def save_to_csv(slots: List[Dict[str, Any]], filename: str):
    """保存到 CSV 文件"""
    import csv
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / filename
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        if not slots:
            return csv_path
        
        writer = csv.DictWriter(f, fieldnames=slots[0].keys())
        writer.writeheader()
        writer.writerows(slots)
    
    return csv_path

def main():
    print("="*70)
    print("Sport8 场地预订爬虫")
    print("="*70)
    
    # 加载 tokens
    tokens = load_tokens()
    print(f"\n✓ 已加载 tokens (userId: {tokens.get('setUserid')})")
    
    # 验证 tokens
    if not verify_tokens(tokens):
        print("\n❌ Tokens 已过期，请重新提取！")
        show_token_extraction_guide()
        return
    
    # 设置爬取范围
    start_date = date.today()
    days = 7
    
    print(f"\n爬取日期范围: {start_date} 到 {start_date + timedelta(days=days-1)}")
    print(f"共 {days} 天\n")
    
    # 爬取数据
    all_slots = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        print(f"[{i+1}/{days}] {current_date}...", end=" ")
        
        data = fetch_sales_detail(tokens, current_date)
        
        if data:
            slots = parse_sales_detail(data, current_date)
            all_slots.extend(slots)
            print(f"✓ {len(slots)} 条记录")
        else:
            print("✗ 失败")
        
        time.sleep(0.5)  # 避免请求过快
    
    # 保存结果
    if all_slots:
        print(f"\n{'='*70}")
        print(f"✓ 共获取 {len(all_slots)} 条记录")
        
        csv_name = f"bookings-{start_date.strftime('%Y%m%d')}.csv"
        csv_path = save_to_csv(all_slots, csv_name)
        print(f"✓ 已保存到: {csv_path.resolve()}")
        
        # 显示样例
        print(f"\n样例数据（前 10 条）:")
        for slot in all_slots[:10]:
            print(f"  {slot['date']} {slot['venue_name']}/{slot['court_name']} "
                  f"{slot['hour']:02d}:00 {slot['status']} ¥{slot['price']}")
    else:
        print("\n❌ 未获取到任何数据")
        print("可能的原因:")
        print("  1. tokens 在爬取过程中过期了")
        print("  2. 网络连接问题")
        print("  3. API 接口发生变化")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


