#!/usr/bin/env python3
"""
星伴守护 - 前端服务器
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='www', static_url_path='')
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': '服务正常运行'})

try:
    from backend.app import *
    
    for rule in backend_app.url_map.iter_rules():
        if rule.rule != '/static/<filename>':
            view_func = backend_app.view_functions[rule.endpoint]
            app.add_url_rule(rule.rule, endpoint=rule.endpoint + '_backend', view_func=view_func, methods=rule.methods)
    
    print("✅ 后端API路由注册成功")
except Exception as e:
    print(f"警告：无法导入后端API: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path == '' or not os.path.exists(os.path.join('www', path)):
        return send_from_directory('www', 'index.html')
    return send_from_directory('www', path)

def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8084))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
