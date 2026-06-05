#!/bin/bash

# ============================================
# 星伴守护 - Heroku一键部署脚本
# ============================================

APP_NAME="xingban-guard-$(date +%Y%m%d)"

echo "============================================"
echo "  星伴守护 - Heroku一键部署"
echo "============================================"

# 1. 检查Heroku CLI
echo ""
echo "[1/5] 检查Heroku CLI..."
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI未安装"
    echo "请先安装: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi
echo "✅ Heroku CLI已安装"

# 2. 登录
echo ""
echo "[2/5] 登录Heroku..."
heroku login

# 3. 创建应用
echo ""
echo "[3/5] 创建应用..."
heroku create $APP_NAME

# 4. 配置环境变量
echo ""
echo "[4/5] 配置环境变量..."
heroku config:set DEEPSEEK_API_KEY=sk-3e2ae11bbc9a41398f0eac1b9ce7f063
heroku config:set SECRET_KEY=xingban-safety-guard-secret-key
heroku config:set FLASK_ENV=production

# 5. 部署
echo ""
echo "[5/5] 部署应用..."
git add .
git commit -m "Deploy to Heroku"
git push heroku master

echo ""
echo "============================================"
echo "  部署完成！"
echo "============================================"
echo ""
echo "访问地址: https://$APP_NAME.herokuapp.com"
echo ""
echo "管理面板: https://dashboard.heroku.com/apps/$APP_NAME"
echo ""
echo "测试账号: 13188393081 / 123456"
echo ""