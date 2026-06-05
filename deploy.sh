#!/bin/bash

# ============================================
# 星伴守护 - 云端一键部署脚本
# ============================================

DOMAIN="your-domain.com"
PROJECT_DIR="/app/xingban"
GIT_REPO="your-git-repo-url"

echo "============================================"
echo "  星伴守护 - 云端部署脚本"
echo "============================================"

# 1. 更新系统
echo ""
echo "[1/6] 更新系统..."
apt update && apt upgrade -y

# 2. 安装依赖
echo ""
echo "[2/6] 安装依赖..."
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# 3. 创建项目目录
echo ""
echo "[3/6] 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 4. 克隆代码
echo ""
echo "[4/6] 克隆代码..."
git clone $GIT_REPO .

# 5. 安装Python依赖
echo ""
echo "[5/6] 安装Python依赖..."
pip3 install -r requirements.txt

# 6. 配置Nginx
echo ""
echo "[6/6] 配置Nginx..."
cat > /etc/nginx/sites-available/xingban << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/xingban /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 7. 配置SSL
echo ""
echo "[7/7] 配置SSL证书..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

echo ""
echo "============================================"
echo "  部署完成！"
echo "============================================"
echo ""
echo "访问地址: https://$DOMAIN"
echo ""
echo "下一步:"
echo "1. 创建systemd服务"
echo "2. 配置环境变量"
echo "3. 启动服务"
echo "4. 配置支付接口"
echo ""