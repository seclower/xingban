#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8084

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format%args}")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(('', PORT), NoCacheHTTPRequestHandler) as httpd:
    print(f'='*60)
    print(f'✅ 服务器启动成功！')
    print(f'='*60)
    print(f'📱 本地访问: http://127.0.0.1:{PORT}')
    print(f'🌐 网络访问: http://10.153.67.65:{PORT}')
    print(f'📝 测试页面: http://10.153.67.65:{PORT}/test_chat.html')
    print(f'='*60)
    print('按 Ctrl+C 停止服务器')
    print(f'='*60)
    httpd.serve_forever()
