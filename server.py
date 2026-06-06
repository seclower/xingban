#!/usr/bin/env python3
"""
星伴守护 - 前端服务器
支持Vercel无服务器部署
"""
import os
import sys

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from flask import Flask, send_from_directory, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__, static_folder='www', static_url_path='')
    CORS(app)
    
    # 尝试导入后端API
    try:
        from app import *
        # 如果成功导入backend/app.py，注册后端路由
        app.register_blueprint(app)
    except ImportError as e:
        print(f"警告：无法导入后端API: {e}")
        print("将使用简化模式运行")
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path == '' or not os.path.exists(os.path.join('www', path)):
            return send_from_directory('www', 'index.html')
        return send_from_directory('www', path)
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'message': '服务正常运行'})
    
    # Vercel入口
    def handler(event, context):
        return app(event, context)
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 8084))
        app.run(host='0.0.0.0', port=port, debug=False)
        
except ImportError as e:
    # 如果没有Flask，使用简单的HTTP服务器
    import http.server
    import socketserver
    
    PORT = int(os.environ.get('PORT', 8084))
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory='www', **kwargs)
        
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务已启动: http://localhost:{PORT}")
        httpd.serve_forever()