#!/usr/bin/env python3
"""
Sport8 场地操作 API 测试脚本
测试是否存在 lock/unlock API
"""

import json
import requests
from pathlib import Path

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://stadium.sports8.com.cn"

# 加载 token
TOKENS_FILE = Path("login_tokens.json")
if TOKENS_FILE.exists():
    TOKENS = json.loads(TOKENS_FILE.read_text())
    print(f"✅ 已加载 token: {TOKENS.get('setLoginname', 'unknown')}")
else:
    print("❌ 未找到 token 文件")
    exit(1)


def test_api(optype, extra_data=None):
    """测试 API 端点"""
    url = f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet"
    
    payload = {
        "optype": optype,
        "setToken": TOKENS.get("setToken", ""),
        "setStadiumId": TOKENS.get("setStadiumId", ""),
        "setUserid": TOKENS.get("setUserid", ""),
        "setCode": TOKENS.get("setCode", ""),
        "setCustId": TOKENS.get("setCustId", ""),
    }
    
    if extra_data:
        payload.update(extra_data)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/StadiumHelper/venue/PageStadiumServlet?optype=toStadium",
        "Authorization": f"Bearer {TOKENS.get('setCode', '')}",
    }
    
    try:
        resp = requests.post(url, data=payload, headers=headers, verify=False, timeout=30)
        print(f"\n📡 测试 optype={optype}")
        print(f"   URL: {url}")
        print(f"   Status: {resp.status_code}")
        
        try:
            data = resp.json()
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
            return data
        except:
            print(f"   Response (text): {resp.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   Error: {e}")
        return None


def main():
    print("=" * 70)
    print("🧪 Sport8 场地操作 API 测试")
    print("=" * 70)
    
    # 1. 测试已知可工作的 API
    print("\n📋 步骤 1: 测试查询 API (确认 token 有效)")
    result = test_api("getCourtTimeListByCourtId", {
        "court_id": "1",
        "stadium_id": TOKENS.get("setStadiumId", ""),
        "search_date": "2026-03-15",
    })
    
    if result and not result.get("error"):
        print("✅ Token 有效，查询 API 工作正常")
    else:
        print("❌ Token 可能已过期")
        return
    
    # 2. 测试可能的操作 API
    print("\n📋 步骤 2: 测试操作 API")
    
    # 测试锁定 API
    test_apis = [
        ("lockCourtTime", {"court_id": "1", "date": "2026-03-15", "hour": "21"}),
        ("unlockCourtTime", {"court_id": "1", "date": "2026-03-15", "hour": "21"}),
        ("reserveCourt", {"court_id": "1", "date": "2026-03-15", "hour": "21"}),
        ("cancelReservation", {"reservation_id": "test"}),
        ("lockTime", {"court_id": "1", "date": "2026-03-15", "hour": "21"}),
        ("unlockTime", {"court_id": "1", "date": "2026-03-15", "hour": "21"}),
    ]
    
    working_apis = []
    
    for optype, extra_data in test_apis:
        result = test_api(optype, extra_data)
        
        # 检查结果
        if result:
            error = result.get("error", "")
            msg = result.get("msg", "")
            
            # 如果返回 "未处理错误" 或特定错误码，说明 API 存在但参数不对
            if "未处理" in str(error) or "参数" in str(msg) or "不存在" in str(msg):
                print(f"   ⚠️  API 可能存在，但返回错误: {error or msg}")
                working_apis.append((optype, "partial"))
            elif result.get("code") == 0 or result.get("success"):
                print(f"   ✅ API 工作正常!")
                working_apis.append((optype, "working"))
            else:
                print(f"   ❌ API 不可用: {error or msg}")
        else:
            print(f"   ❌ 无响应或解析失败")
    
    # 3. 总结
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    if working_apis:
        print("\n可能可用的 API:")
        for api, status in working_apis:
            icon = "✅" if status == "working" else "⚠️"
            print(f"   {icon} {api}")
    else:
        print("\n❌ 未发现可用的操作 API")
        print("\n建议:")
        print("   1. 使用 Selenium 直接操作页面")
        print("   2. 检查 Sport8 管理后台是否有不同 API")
        print("   3. 联系 Sport8 技术支持获取 API 文档")


if __name__ == "__main__":
    main()
