#!/usr/bin/env python3
"""
星伴守护 - 内网穿透脚本
使用Python创建简单的反向代理，将外网请求转发到本地服务
"""

import http.server
import socketserver
import threading
import sys
import urllib.request
import urllib.parse

# 配置
LOCAL_HOST = '10.153.67.65'
LOCAL_PORT = 8084

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 代理请求到本地服务器
        try:
            url = f'http://{LOCAL_HOST}:{LOCAL_PORT}{self.path}'
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.headers.get('User-Agent', ''))
            
            response = urllib.request.urlopen(req, timeout=10)
            content = response.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"代理错误: {e}")
            self.send_error(500, '代理服务器错误')

    def log_message(self, format, *args):
        print(f"[代理] {args[0]}")

def start_proxy(port=8085):
    """启动代理服务器"""
    with socketserver.TCPServer(("", port), ProxyHandler) as httpd:
        print(f"代理服务器启动成功！")
        print(f"访问地址: http://localhost:{port}")
        print(f"或者: http://{LOCAL_HOST}:{port}")
        print(f"\n按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n代理服务器已停止")
            sys.exit(0)

if __name__ == "__main__":
    port = 8085
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print("=" * 50)
    print("星伴守护 - 本地代理服务")
    print("=" * 50)
    print(f"\n本地服务器: http://{LOCAL_HOST}:{LOCAL_PORT}")
    print(f"代理端口: {port}")
    print("\n如果手机无法直接访问10.153.67.65:8084")
    print("可以尝试访问这个地址")
    print("=" * 50)
    start_proxy(port)
