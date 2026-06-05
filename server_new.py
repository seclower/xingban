#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8083

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加不缓存的头
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(('127.0.0.1', PORT), NoCacheHTTPRequestHandler) as httpd:
    print(f'Serving at http://127.0.0.1:{PORT} (无缓存)')
    print('请使用此新链接测试，避免浏览器缓存问题')
    httpd.serve_forever()
