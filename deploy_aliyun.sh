#!/bin/bash

# ============================================
# 星伴守护 - 阿里云服务器一键部署脚本
# ============================================

echo "============================================"
echo "  星伴守护 - 阿里云服务器部署"
echo "============================================"

# 1. 更新系统
echo ""
echo "[1/6] 更新系统..."
apt update && apt upgrade -y

# 2. 安装依赖
echo ""
echo "[2/6] 安装依赖..."
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl git

# 3. 安装Node.js
echo ""
echo "[3/6] 安装Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 4. 创建项目目录
echo ""
echo "[4/6] 创建项目目录..."
mkdir -p /app/xingban
cd /app/xingban

# 5. 克隆代码（需要先在GitHub设置deploy key或token）
echo ""
echo "[5/6] 请手动上传代码或配置Git访问..."
echo "方式1: git clone https://github.com/seclower/xingban.git /app/xingban"
echo "方式2: 使用scp从本地上传"

# 6. 配置服务
echo ""
echo "[6/6] 配置服务..."
cat > /etc/systemd/system/xingban.service << 'EOF'
[Unit]
Description=Xingban Safety Guard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app/xingban
ExecStart=/usr/bin/python3 server.py
Restart=always
Environment="DEEPSEEK_API_KEY=sk-3e2ae11bbc9a41398f0eac1b9ce7f063"
Environment="SECRET_KEY=xingban-safety-guard-2024-secret"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xingban
systemctl start xingban

echo ""
echo "============================================"
echo "  部署完成！"
echo "============================================"
echo ""
echo "访问地址: http://your-server-ip:8082"
echo "API地址:  http://your-server-ip:5000"
echo ""
echo "管理命令:"
echo "  systemctl status xingban  - 查看状态"
echo "  systemctl restart xingban  - 重启服务"
echo "  journalctl -u xingban -f  - 查看日志"
echo ""