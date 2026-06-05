import http.server
import socketserver

PORT = 8082

handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(('127.0.0.1', PORT), handler) as httpd:
    print(f'Serving at http://127.0.0.1:{PORT}')
    httpd.serve_forever()