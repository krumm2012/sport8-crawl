#!/bin/bash
# 获取 Token 测试脚本

echo "=================================="
echo "🔐 获取 Token 测试"
echo "=================================="
echo ""

API_URL="https://51alljoin.cn:8000/api/v1"
USERNAME="superadmin"
PASSWORD="admin123"

echo "📍 API 地址: $API_URL"
echo "👤 用户名: $USERNAME"
echo ""

echo "🚀 发送登录请求..."
echo ""

# 使用 curl 获取 token
RESPONSE=$(curl -s -k -X POST \
  -d "username=$USERNAME&password=$PASSWORD" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -w "\nHTTP_CODE:%{http_code}" \
  "$API_URL/auth/login" 2>&1)

echo "📥 原始响应:"
echo "$RESPONSE"
echo ""

# 提取 HTTP 状态码
HTTP_CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
echo "📊 HTTP 状态码: $HTTP_CODE"
echo ""

# 提取 JSON 部分（去掉 HTTP_CODE 行）
JSON_PART=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 登录成功!"
    echo ""
    echo "📋 解析后的响应:"
    echo "$JSON_PART" | python3 -m json.tool 2>/dev/null || echo "$JSON_PART"
    echo ""
    
    # 提取 token
    TOKEN=$(echo "$JSON_PART" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('access_token',''))" 2>/dev/null)
    
    if [ -n "$TOKEN" ]; then
        echo "🔑 Token: ${TOKEN:0:30}..."
        echo ""
        echo "💾 保存 Token 到 token.txt"
        echo "$TOKEN" > token.txt
        echo ""
        
        # 使用 token 测试查询
        echo "🚀 使用 Token 测试查询预约..."
        curl -s -k -H "Authorization: Bearer $TOKEN" \
          "$API_URL/bookings?skip=0&limit=3&venue_id=11" | \
          python3 -m json.tool 2>/dev/null | head -50
    fi
else
    echo "❌ 登录失败，HTTP 状态码: $HTTP_CODE"
fi

echo ""
echo "=================================="
echo "✅ 测试完成"
echo "=================================="
