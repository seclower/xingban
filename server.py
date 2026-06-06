#!/usr/bin/env python3
"""
星伴守护 - 前端服务器
支持Vercel无服务器部署
"""
import os
import sys

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入Flask
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

# 创建Flask应用实例（Vercel需要顶级app变量）
app = Flask(__name__, static_folder='www', static_url_path='')
CORS(app)

# 尝试导入后端API路由
try:
    from backend.app import *
    
    # 获取后端app的所有路由并注册到主应用
    # 遍历后端app的视图函数
    for rule in backend_app.url_map.iter_rules():
        # 获取视图函数
        view_func = backend_app.view_functions[rule.endpoint]
        # 添加到主应用
        app.add_url_rule(rule.rule, endpoint=rule.endpoint, view_func=view_func, methods=rule.methods)
    
    print("✅ 后端API路由注册成功")
except ImportError as e:
    print(f"警告：无法导入后端API: {e}")
    print("将使用简化模式运行")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """提供前端静态文件"""
    if path == '' or not os.path.exists(os.path.join('www', path)):
        return send_from_directory('www', 'index.html')
    return send_from_directory('www', path)

@app.route('/api/health')
def health():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': '服务正常运行'})

# Vercel无服务器函数入口
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8084))
    app.run(host='0.0.0.0', port=port, debug=False)