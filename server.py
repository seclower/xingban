#!/usr/bin/env python3
"""
星伴守护 - 统一服务器
整合前端服务和后端API，简化部署
"""
import http.server
import socketserver
import json
import sqlite3
import random
import string
import time
import hashlib
import threading
import os
from datetime import datetime
from urllib.parse import parse_qs, urlparse

# 配置
FRONTEND_PORT = 8084
API_PORT = 8085
DB_NAME = 'safety_guard.db'

# ==================== 数据库模块 ====================
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nickname TEXT,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 验证码表
    c.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    
    # 紧急联系人表
    c.execute('''
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            relation TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 位置记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS location_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 求助记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS sos_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL,
            longitude REAL,
            address TEXT,
            situation TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 心情日记表
    c.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            emotion TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

def generate_code(length=6):
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def clean_expired_codes():
    """清理过期验证码"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM verifications WHERE expires_at < datetime('now')")
    conn.commit()
    conn.close()

# ==================== AI回复模块 ====================
def get_local_ai_response(message):
    """本地AI回复"""
    msg = message.lower()
    
    # 紧急求助
    if any(keyword in msg for keyword in ['危险', '害怕', '跟踪', '报警']):
        return '请立即拨打110报警！如果无法说话，可以发送短信到12110。保持冷静，尽量前往人多的地方。'
    
    if any(keyword in msg for keyword in ['急救', '受伤', '生病']):
        return '请立即拨打120急救电话。在等待时：1) 保持冷静 2) 不要随意移动伤者 3) 准备好医保卡。'
    
    if any(keyword in msg for keyword in ['火警', '着火', '火灾']):
        return '请立即拨打119！逃生时：1) 用湿毛巾捂住口鼻 2) 不要乘坐电梯 3) 低姿势逃生。'
    
    # 日常问候
    if any(keyword in msg for keyword in ['早上好', '早安', '早呀']):
        return '早上好！☀️ 新的一天开始了！今天也要元气满满哦！有什么我可以帮你的吗？'
    
    if any(keyword in msg for keyword in ['晚上好', '晚安']):
        return '晚上好！🌙 今天辛苦了，好好休息一下吧！'
    
    if any(keyword in msg for keyword in ['你好', '您好', '嗨', 'hi', 'hello']):
        return '你好！😊 有什么我可以帮你的吗？我可以提供安全咨询、情感陪伴等服务。'
    
    # 安全知识
    if any(keyword in msg for keyword in ['诈骗', '被骗']):
        return '防范诈骗：1) 不轻信陌生来电 2) 不透露验证码 3) 不转账给陌生人 4) 遇到可疑情况拨打96110。'
    
    if any(keyword in msg for keyword in ['打车', '网约车', '滴滴']):
        return '打车安全：1) 使用正规平台 2) 核对车牌号 3) 坐在后排 4) 分享行程给亲友 5) 保持警惕。'
    
    if any(keyword in msg for keyword in ['一个人', '回家', '夜归']):
        return '夜间出行注意：1) 走明亮路线 2) 保持手机畅通 3) 告知家人行程 4) 随时观察周围环境。'
    
    # 情绪支持
    if any(keyword in msg for keyword in ['无聊', '没事做']):
        return '无聊的话可以：看看书📚、听听音乐🎵、出门散步🚶‍♀️、和朋友聊聊天💬，让生活更充实！'
    
    if any(keyword in msg for keyword in ['开心', '高兴', '快乐']):
        return '真替你高兴！😊 保持好心情很重要！有什么开心的事想分享吗？'
    
    if any(keyword in msg for keyword in ['难过', '伤心', '难过']):
        return '抱歉听到你难过。😢 每个人都会有低谷期，如果需要倾诉我随时在这里。'
    
    if any(keyword in msg for keyword in ['谢谢', '感谢']):
        return '不客气！😊 能帮到你我很开心！有任何问题随时来找我！'
    
    # 默认回复
    return '我理解你的感受。💭 作为安全守护助手，我可以为你提供安全建议和情感支持。有什么想问或想聊的吗？'

# ==================== API处理类 ====================
class APIHandler(http.server.BaseHTTPRequestHandler):
    """API请求处理器"""
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # 路由处理
        if path == '/api/health':
            self.send_json_response(200, {'status': 'ok', 'message': '服务正常运行'})
        elif path == '/api/contacts':
            self.handle_get_contacts(query)
        elif path == '/api/diaries':
            self.handle_get_diaries(query)
        elif path == '/api/location/history':
            self.handle_get_location_history(query)
        elif path == '/api/sos/history':
            self.handle_get_sos_history(query)
        else:
            self.send_json_response(404, {'error': '未找到接口'})
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data) if post_data else {}
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # 路由处理
            if path == '/api/send_code':
                self.handle_send_code(data)
            elif path == '/api/verify_code':
                self.handle_verify_code(data)
            elif path == '/api/register':
                self.handle_register(data)
            elif path == '/api/login':
                self.handle_login(data)
            elif path == '/api/location':
                self.handle_save_location(data)
            elif path == '/api/sos':
                self.handle_send_sos(data)
            elif path == '/api/contacts':
                self.handle_save_contact(data)
            elif path == '/api/diaries':
                self.handle_save_diary(data)
            elif path == '/api/emotion/chat':
                self.handle_ai_chat(data)
            else:
                self.send_json_response(400, {'error': '未知接口'})
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})
    
    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/emotion/chat-history':
            self.handle_clear_chat_history()
        elif path.startswith('/api/contacts/'):
            contact_id = path.split('/')[-1]
            self.handle_delete_contact(contact_id)
        elif path.startswith('/api/diaries/'):
            diary_id = path.split('/')[-1]
            self.handle_delete_diary(diary_id)
        else:
            self.send_json_response(404, {'error': '未找到接口'})
    
    # ==================== API处理方法 ====================
    def handle_send_code(self, data):
        """发送验证码"""
        phone = data.get('phone')
        code_type = data.get('type', 'register')
        
        if not phone or len(phone) != 11:
            self.send_json_response(400, {'error': '请输入正确的手机号'})
            return
        
        clean_expired_codes()
        code = generate_code()
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM verifications WHERE phone = ? AND type = ?", (phone, code_type))
        c.execute('''
            INSERT INTO verifications (phone, code, type, expires_at)
            VALUES (?, ?, ?, datetime('now', '+5 minutes'))
        ''', (phone, code, code_type))
        conn.commit()
        conn.close()
        
        print(f"📱 验证码已发送: {phone} - {code}")
        
        self.send_json_response(200, {
            'success': True,
            'message': '验证码已发送',
            'code': code,
            'expires_in': 300
        })
    
    def handle_verify_code(self, data):
        """验证验证码"""
        phone = data.get('phone')
        code = data.get('code')
        code_type = data.get('type', 'register')
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT code, expires_at FROM verifications
            WHERE phone = ? AND type = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (phone, code_type))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            self.send_json_response(400, {'success': False, 'error': '验证码已过期，请重新获取'})
            return
        
        saved_code, expires_at = result
        
        if saved_code != code:
            self.send_json_response(400, {'success': False, 'error': '验证码错误'})
            return
        
        self.send_json_response(200, {'success': True, 'message': '验证成功'})
    
    def handle_register(self, data):
        """用户注册"""
        phone = data.get('phone')
        password = data.get('password')
        code = data.get('code')
        nickname = data.get('nickname', f'用户{phone[-4:]}')
        
        if not phone or not password or not code:
            self.send_json_response(400, {'error': '请填写完整信息'})
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute('''
            SELECT code, expires_at FROM verifications
            WHERE phone = ? AND type = 'register'
            ORDER BY created_at DESC LIMIT 1
        ''', (phone,))
        
        result = c.fetchone()
        if not result or result[0] != code:
            conn.close()
            self.send_json_response(400, {'error': '验证码错误'})
            return
        
        try:
            c.execute('''
                INSERT INTO users (phone, password, nickname)
                VALUES (?, ?, ?)
            ''', (phone, hash_password(password), nickname))
            user_id = c.lastrowid
            c.execute("DELETE FROM verifications WHERE phone = ? AND type = 'register'", (phone,))
            conn.commit()
            conn.close()
            
            self.send_json_response(200, {
                'success': True,
                'message': '注册成功',
                'user': {'id': user_id, 'phone': phone, 'nickname': nickname}
            })
        except sqlite3.IntegrityError:
            conn.close()
            self.send_json_response(400, {'error': '该手机号已注册'})
    
    def handle_login(self, data):
        """用户登录"""
        phone = data.get('phone')
        password = data.get('password')
        
        if not phone or not password:
            self.send_json_response(400, {'error': '请填写完整信息'})
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, phone, password, nickname FROM users WHERE phone = ?', (phone,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            self.send_json_response(400, {'error': '用户不存在'})
            return
        
        user_id, user_phone, user_password, nickname = user
        
        if user_password != hash_password(password):
            self.send_json_response(400, {'error': '密码错误'})
            return
        
        self.send_json_response(200, {
            'success': True,
            'message': '登录成功',
            'user': {'id': user_id, 'phone': user_phone, 'nickname': nickname}
        })
    
    def handle_save_location(self, data):
        """保存位置"""
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        
        if not all([user_id, latitude, longitude]):
            self.send_json_response(400, {'error': '缺少必要参数'})
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO location_logs (user_id, latitude, longitude, address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, latitude, longitude, address))
        conn.commit()
        conn.close()
        
        self.send_json_response(200, {
            'success': True,
            'message': '位置已保存',
            'location': {'latitude': latitude, 'longitude': longitude, 'address': address}
        })
    
    def handle_get_location_history(self, query):
        """获取位置历史"""
        user_id = query.get('user_id', [None])[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT latitude, longitude, address, created_at
            FROM location_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        ''', (user_id,))
        
        locations = [{'latitude': r[0], 'longitude': r[1], 'address': r[2], 'created_at': r[3]} 
                     for r in c.fetchall()]
        conn.close()
        
        self.send_json_response(200, {'success': True, 'locations': locations})
    
    def handle_send_sos(self, data):
        """发送SOS求助"""
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        situation = data.get('situation', '紧急求助')
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO sos_records (user_id, latitude, longitude, address, situation)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, latitude, longitude, address, situation))
        sos_id = c.lastrowid
        
        c.execute('SELECT name, phone FROM emergency_contacts WHERE user_id = ?', (user_id,))
        contacts = c.fetchall()
        conn.commit()
        conn.close()
        
        print(f"🆘 SOS求助已发送: 用户{user_id}")
        for name, phone in contacts:
            print(f"   通知 {name}: {phone}")
        
        self.send_json_response(200, {
            'success': True,
            'message': '求助信息已发送',
            'sos_id': sos_id,
            'contacts_notified': len(contacts)
        })
    
    def handle_get_sos_history(self, query):
        """获取SOS历史"""
        user_id = query.get('user_id', [None])[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT id, latitude, longitude, address, situation, status, created_at
            FROM sos_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        records = [{'id': r[0], 'latitude': r[1], 'longitude': r[2], 'address': r[3], 
                   'situation': r[4], 'status': r[5], 'created_at': r[6]} 
                  for r in c.fetchall()]
        conn.close()
        
        self.send_json_response(200, {'success': True, 'records': records})
    
    def handle_save_contact(self, data):
        """保存紧急联系人"""
        user_id = data.get('user_id')
        name = data.get('name')
        phone = data.get('phone')
        relation = data.get('relation', '')
        
        if not all([user_id, name, phone]):
            self.send_json_response(400, {'error': '请填写完整信息'})
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO emergency_contacts (user_id, name, phone, relation)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, phone, relation))
        contact_id = c.lastrowid
        conn.commit()
        conn.close()
        
        self.send_json_response(200, {
            'success': True,
            'message': '紧急联系人已保存',
            'contact': {'id': contact_id, 'name': name, 'phone': phone, 'relation': relation}
        })
    
    def handle_get_contacts(self, query):
        """获取紧急联系人"""
        user_id = query.get('user_id', [None])[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, phone, relation FROM emergency_contacts WHERE user_id = ?', (user_id,))
        
        contacts = [{'id': r[0], 'name': r[1], 'phone': r[2], 'relation': r[3]} 
                    for r in c.fetchall()]
        conn.close()
        
        self.send_json_response(200, {'success': True, 'contacts': contacts})
    
    def handle_delete_contact(self, contact_id):
        """删除紧急联系人"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM emergency_contacts WHERE id = ?', (contact_id,))
        conn.commit()
        conn.close()
        
        self.send_json_response(200, {'success': True, 'message': '联系人已删除'})
    
    def handle_save_diary(self, data):
        """保存心情日记"""
        user_id = data.get('user_id')
        emotion = data.get('emotion', '')
        content = data.get('content', '')
        
        if not user_id:
            self.send_json_response(400, {'error': '缺少用户ID'})
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO diaries (user_id, emotion, content)
            VALUES (?, ?, ?)
        ''', (user_id, emotion, content))
        diary_id = c.lastrowid
        conn.commit()
        conn.close()
        
        self.send_json_response(200, {
            'success': True,
            'message': '日记已保存',
            'diary': {'id': diary_id, 'emotion': emotion, 'content': content}
        })
    
    def handle_get_diaries(self, query):
        """获取心情日记"""
        user_id = query.get('user_id', [None])[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT id, emotion, content, created_at
            FROM diaries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        diaries = [{'id': r[0], 'emotion': r[1], 'content': r[2], 'created_at': r[3]} 
                   for r in c.fetchall()]
        conn.close()
        
        self.send_json_response(200, {'success': True, 'diaries': diaries})
    
    def handle_delete_diary(self, diary_id):
        """删除心情日记"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM diaries WHERE id = ?', (diary_id,))
        conn.commit()
        conn.close()
        
        self.send_json_response(200, {'success': True, 'message': '日记已删除'})
    
    def handle_ai_chat(self, data):
        """AI聊天"""
        message = data.get('message', '')
        user_id = data.get('user_id')
        
        response = get_local_ai_response(message)
        
        self.send_json_response(200, {'success': True, 'response': response})
    
    def handle_clear_chat_history(self):
        """清空聊天历史"""
        self.send_json_response(200, {'success': True, 'message': '聊天历史已清空'})
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[API {datetime.now().strftime('%H:%M:%S')}] {args[0]}")

# ==================== 前端服务类 ====================
class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    """前端静态文件处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='www', **kwargs)
    
    def end_headers(self):
        # 添加不缓存头，确保更新后立即生效
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # CORS支持
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        print(f"[前端 {datetime.now().strftime('%H:%M:%S')}] {args[0]}")

# ==================== 启动服务 ====================
def run_api_server():
    """运行API服务器"""
    init_db()
    with socketserver.TCPServer(("127.0.0.1", API_PORT), APIHandler) as httpd:
        print(f"🚀 API服务器已启动: http://127.0.0.1:{API_PORT}")
        httpd.serve_forever()

def run_frontend_server():
    """运行前端服务器"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("127.0.0.1", FRONTEND_PORT), FrontendHandler) as httpd:
        print(f"🌐 前端服务器已启动: http://127.0.0.1:{FRONTEND_PORT}")
        httpd.serve_forever()

def main():
    """主入口"""
    print("\n" + "="*50)
    print("   星伴守护 - 安全守护APP服务")
    print("="*50 + "\n")
    
    # 启动API服务器（后台线程）
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # 等待API服务器启动
    time.sleep(1)
    
    # 启动前端服务器（主线程）
    print(f"\n📱 访问地址: http://127.0.0.1:{FRONTEND_PORT}")
    print("📋 测试账号: 13188393081 / 密码: 123456")
    print("\n按 Ctrl+C 停止服务...\n")
    
    try:
        run_frontend_server()
    except KeyboardInterrupt:
        print("\n\n服务已停止")

if __name__ == '__main__':
    main()