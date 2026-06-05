# 完整的后端API服务 - 验证码、登录注册、定位
import http.server
import socketserver
import json
import sqlite3
import random
import string
import time
import hashlib
from datetime import datetime
import os

PORT = 8083

# 数据库初始化
def init_db():
    conn = sqlite3.connect('safety_guard.db')
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
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

# 辅助函数
def generate_code(length=6):
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def clean_expired_codes():
    """清理过期验证码"""
    conn = sqlite3.connect('safety_guard.db')
    c = conn.cursor()
    c.execute("DELETE FROM verifications WHERE expires_at < datetime('now')")
    conn.commit()
    conn.close()

# API处理类
class APIHandler(http.server.BaseHTTPRequestHandler):
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            action = data.get('action')
            
            if action == 'send_code':
                self.handle_send_code(data)
            elif action == 'verify_code':
                self.handle_verify_code(data)
            elif action == 'register':
                self.handle_register(data)
            elif action == 'login':
                self.handle_login(data)
            elif action == 'save_location':
                self.handle_save_location(data)
            elif action == 'get_location_history':
                self.handle_get_location_history(data)
            elif action == 'send_sos':
                self.handle_send_sos(data)
            elif action == 'save_emergency_contact':
                self.handle_save_emergency_contact(data)
            elif action == 'get_emergency_contacts':
                self.handle_get_emergency_contacts(data)
            elif action == 'ai_chat':
                self.handle_ai_chat(data)
            else:
                self.send_json_response(400, {'error': '未知操作'})
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})
    
    def handle_send_code(self, data):
        """发送验证码"""
        phone = data.get('phone')
        code_type = data.get('type', 'register')  # register, login, reset
        
        if not phone or len(phone) != 11:
            self.send_json_response(400, {'error': '请输入正确的手机号'})
            return
        
        # 清理过期验证码
        clean_expired_codes()
        
        # 生成验证码
        code = generate_code()
        
        # 保存验证码
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        
        # 删除该手机号的旧验证码
        c.execute("DELETE FROM verifications WHERE phone = ? AND type = ?", (phone, code_type))
        
        # 插入新验证码（有效期5分钟）
        c.execute('''
            INSERT INTO verifications (phone, code, type, expires_at)
            VALUES (?, ?, ?, datetime('now', '+5 minutes'))
        ''', (phone, code, code_type))
        
        conn.commit()
        conn.close()
        
        # 模拟发送短信（实际项目中应接入短信网关）
        print(f"📱 验证码已发送: {phone} - {code}")
        
        # 模拟成功发送
        self.send_json_response(200, {
            'success': True,
            'message': '验证码已发送',
            'code': code,  # 开发环境下返回验证码
            'expires_in': 300
        })
    
    def handle_verify_code(self, data):
        """验证验证码"""
        phone = data.get('phone')
        code = data.get('code')
        code_type = data.get('type', 'register')
        
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        
        # 查询验证码
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
        
        # 检查是否过期
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        c.execute("SELECT datetime('now') > ?", (expires_at,))
        is_expired = c.fetchone()[0]
        conn.close()
        
        if is_expired:
            self.send_json_response(400, {'success': False, 'error': '验证码已过期'})
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
        
        # 验证验证码
        conn = sqlite3.connect('safety_guard.db')
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
            expires_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S.%f')
        except:
            expires_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_time:
            conn.close()
            self.send_json_response(400, {'error': '验证码已过期'})
            return
        
        # 创建用户
        try:
            c.execute('''
                INSERT INTO users (phone, password, nickname)
                VALUES (?, ?, ?)
            ''', (phone, hash_password(password), nickname))
            user_id = c.lastrowid
            conn.commit()
            
            # 删除已使用的验证码
            c.execute("DELETE FROM verifications WHERE phone = ? AND type = 'register'", (phone,))
            conn.commit()
            
            conn.close()
            
            self.send_json_response(200, {
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user_id,
                    'phone': phone,
                    'nickname': nickname
                }
            })
        except sqlite3.IntegrityError:
            conn.close()
            self.send_json_response(400, {'error': '该手机号已注册'})
    
    def handle_login(self, data):
        """用户登录"""
        phone = data.get('phone')
        password = data.get('password')
        code = data.get('code')
        
        if not phone or not password:
            self.send_json_response(400, {'error': '请填写完整信息'})
            return
        
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        
        # 查询用户
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
            'user': {
                'id': user_id,
                'phone': user_phone,
                'nickname': nickname
            }
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
        
        conn = sqlite3.connect('safety_guard.db')
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
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'address': address
            }
        })
    
    def handle_get_location_history(self, data):
        """获取位置历史"""
        user_id = data.get('user_id')
        
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        c.execute('''
            SELECT latitude, longitude, address, created_at
            FROM location_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        ''', (user_id,))
        
        locations = []
        for row in c.fetchall():
            locations.append({
                'latitude': row[0],
                'longitude': row[1],
                'address': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        self.send_json_response(200, {
            'success': True,
            'locations': locations
        })
    
    def handle_send_sos(self, data):
        """发送SOS求助"""
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        situation = data.get('situation', '紧急求助')
        
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO sos_records (user_id, latitude, longitude, address, situation)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, latitude, longitude, address, situation))
        sos_id = c.lastrowid
        
        # 获取紧急联系人
        c.execute('''
            SELECT name, phone FROM emergency_contacts WHERE user_id = ?
        ''', (user_id,))
        contacts = c.fetchall()
        
        conn.commit()
        conn.close()
        
        # 模拟发送求助信息给紧急联系人
        print(f"🆘 SOS求助已发送: 用户{user_id}")
        for name, phone in contacts:
            print(f"   通知 {name}: {phone}")
        
        self.send_json_response(200, {
            'success': True,
            'message': '求助信息已发送',
            'sos_id': sos_id,
            'contacts_notified': len(contacts)
        })
    
    def handle_save_emergency_contact(self, data):
        """保存紧急联系人"""
        user_id = data.get('user_id')
        name = data.get('name')
        phone = data.get('phone')
        relation = data.get('relation', '')
        
        if not all([user_id, name, phone]):
            self.send_json_response(400, {'error': '请填写完整信息'})
            return
        
        conn = sqlite3.connect('safety_guard.db')
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
            'contact': {
                'id': contact_id,
                'name': name,
                'phone': phone,
                'relation': relation
            }
        })
    
    def handle_get_emergency_contacts(self, data):
        """获取紧急联系人"""
        user_id = data.get('user_id')
        
        conn = sqlite3.connect('safety_guard.db')
        c = conn.cursor()
        c.execute('''
            SELECT id, name, phone, relation FROM emergency_contacts WHERE user_id = ?
        ''', (user_id,))
        
        contacts = []
        for row in c.fetchall():
            contacts.append({
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'relation': row[3]
            })
        
        conn.close()
        
        self.send_json_response(200, {
            'success': True,
            'contacts': contacts
        })
    
    def handle_ai_chat(self, data):
        """AI聊天"""
        message = data.get('message', '')
        user_id = data.get('user_id')
        
        # 这里可以接入真实的AI服务
        # 目前返回本地处理的回复
        response = self.get_local_ai_response(message)
        
        self.send_json_response(200, {
            'success': True,
            'response': response
        })
    
    def get_local_ai_response(self, message):
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
            return f'早上好！☀️ 新的一天开始了！今天也要元气满满哦！有什么我可以帮你的吗？'
        
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

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")

# 启动服务
init_db()

Handler = APIHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🚀 API服务器已启动: http://localhost:{PORT}")
    httpd.serve_forever()
