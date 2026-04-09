#!/bin/bash
# 推送到 GitHub 脚本（需要手动执行）

echo "🚀 推送到 GitHub..."

# 配置（请替换为你的信息）
GITHUB_USERNAME="krumm2012"
GITHUB_TOKEN="${GITHUB_TOKEN}"  # 从环境变量读取
REPO_NAME="sport8-crawl"

# 检查 token 是否有效
echo "检查 GitHub Token..."
if ! curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -q '"login"'; then
    echo "❌ GitHub Token 无效或已过期"
    echo "请访问 https://github.com/settings/tokens 生成新的 token"
    exit 1
fi

echo "✅ Token 有效"

# 检查仓库是否存在
echo "检查仓库是否存在..."
if curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$GITHUB_USERNAME/$REPO_NAME" | grep -q '"id"'; then
    echo "✅ 仓库已存在"
else
    echo "创建新仓库..."
    curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/user/repos \
        -d "{\"name\":\"$REPO_NAME\",\"private\":false,\"description\":\"Sport8 场馆预订爬虫 - 异步高性能版\"}"
    echo "✅ 仓库创建完成"
fi

# 添加 GitHub 远程仓库
cd /Users/mxchip/Documents/sport8-crawl

# 删除旧的 github remote（如果存在）
git remote remove github 2>/dev/null || true

# 添加新的 remote
git remote add github "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo "推送分支到 GitHub..."
git push github feature/async-crawler --force

echo ""
echo "✅ 推送完成！"
echo "访问: https://github.com/$GITHUB_USERNAME/$REPO_NAME/pulls"
