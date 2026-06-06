from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import logging
import requests
import json
import random
import time
from typing import Optional, Dict, Any, Tuple, List, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从环境变量读取配置
import os
from dotenv import load_dotenv

# 加载.env文件（仅开发环境）
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')

# 阿里云短信配置
ALIYUN_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID', '')
ALIYUN_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_ACCESS_KEY_SECRET', '')
ALIYUN_SMS_SIGN_NAME = os.environ.get('ALIYUN_SMS_SIGN_NAME', '星伴守护')
ALIYUN_SMS_TEMPLATE_CODE = os.environ.get('ALIYUN_SMS_TEMPLATE_CODE', 'SMS_155075006')

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 验证码存储
verification_codes = {}

# 阿里云短信发送函数
def send_sms_code(phone, code):
    """
    发送短信验证码
    生产环境使用阿里云，开发环境模拟发送
    """
    try:
        logger.info(f'[短信发送] 手机号: {phone}, 验证码: {code}')
        
        # 保存验证码（5分钟有效期）
        verification_codes[phone] = {
            'code': code,
            'expire_time': time.time() + 300
        }
        
        # 检查是否有阿里云配置
        if ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET and ALIYUN_ACCESS_KEY_ID != 'your_access_key_id':
            try:
                # 尝试导入阿里云SDK
                from aliyunsdkcore.client import AcsClient
                from aliyunsdkcore.request import CommonRequest
                
                client = AcsClient(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, 'cn-hangzhou')
                request = CommonRequest()
                request.set_accept_format('json')
                request.set_domain('dysmsapi.aliyuncs.com')
                request.set_version('2017-05-25')
                request.set_action_name('SendSms')
                request.add_query_param('PhoneNumbers', phone)
                request.add_query_param('SignName', ALIYUN_SMS_SIGN_NAME)
                request.add_query_param('TemplateCode', ALIYUN_SMS_TEMPLATE_CODE)
                request.add_query_param('TemplateParam', json.dumps({'code': code}))
                
                response = client.do_action(request)
                response_data = json.loads(str(response, encoding='utf-8'))
                
                if response_data.get('Code') == 'OK':
                    logger.info(f'[短信发送] 阿里云短信发送成功: {phone}')
                    return {'success': True, 'code': code, 'message': '验证码已发送'}
                else:
                    logger.warning(f'[短信发送] 阿里云短信发送失败: {response_data.get("Message")}')
                    # 阿里云失败时降级到模拟模式
                    return {'success': True, 'code': code, 'message': '验证码已发送（模拟）'}
                    
            except ImportError:
                logger.warning('[短信发送] 阿里云SDK未安装，使用模拟模式')
                return {'success': True, 'code': code, 'message': '验证码已发送（模拟）'}
            except Exception as e:
                logger.error(f'[短信发送] 阿里云短信发送异常: {e}')
                return {'success': True, 'code': code, 'message': '验证码已发送（模拟）'}
        else:
            logger.info('[短信发送] 使用模拟模式发送验证码')
            return {'success': True, 'code': code, 'message': '验证码已发送（模拟）'}
        
    except Exception as e:
        logger.error(f'短信发送失败: {e}')
        return {'success': False, 'message': '短信发送失败'}

# 验证验证码
def verify_code(phone, code):
    """验证短信验证码"""
    if phone not in verification_codes:
        return False, '验证码不存在'
    
    code_info = verification_codes[phone]
    
    # 检查是否过期
    if time.time() > code_info['expire_time']:
        del verification_codes[phone]
        return False, '验证码已过期'
    
    # 检查验证码
    if code_info['code'] != code:
        return False, '验证码错误'
    
    # 验证成功，删除验证码
    del verification_codes[phone]
    return True, '验证成功'

# 数据库连接
def get_db_connection():
    try:
        conn = sqlite3.connect('safety_guard.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f'Database connection error: {e}')
        raise

# 初始化数据库
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表（扩展会员和管理员字段）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        password TEXT NOT NULL,
        name TEXT DEFAULT '用户',
        nickname TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        avatar_id INTEGER DEFAULT 1,
        gender TEXT DEFAULT 'female',
        birthdate TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        safety_level INTEGER DEFAULT 1,
        membership TEXT DEFAULT '普通会员',
        membership_type TEXT DEFAULT 'free',
        membership_expire TEXT DEFAULT '',
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        wechat_openid TEXT UNIQUE,
        qq_openid TEXT UNIQUE,
        apple_id TEXT UNIQUE
    )''')
    
    # 创建会员订单表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        price REAL DEFAULT 0,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建管理日志表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        target_user_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )''')
    
    # 创建紧急联系人表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        relationship TEXT DEFAULT 'family',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建情绪日记表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        emotion TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建历史记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建SOS记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sos_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location TEXT,
        contacts_notified TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建AI聊天历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建支付订单表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_id TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        payment_type TEXT DEFAULT 'wechat',
        product_id TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        paid_at TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 添加测试用户
    cursor.execute('SELECT * FROM users WHERE phone = ?', ('13188393081',))
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
        INSERT INTO users (phone, password, name, nickname, membership_type, is_admin) VALUES (?, ?, ?, ?, ?, ?)
        ''', ('13188393081', hashed_password, '测试用户', '测试用户', 'pro', 1))
        
        # 添加测试联系人
        user_id = cursor.lastrowid
        cursor.execute('''
        INSERT INTO contacts (user_id, name, phone, relationship) VALUES (?, ?, ?, ?)
        ''', (user_id, '爸爸', '13800138123', 'family'))
        cursor.execute('''
        INSERT INTO contacts (user_id, name, phone, relationship) VALUES (?, ?, ?, ?)
        ''', (user_id, '妈妈', '13900139567', 'family'))
    
    # 添加管理员账户
    cursor.execute('SELECT * FROM users WHERE phone = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
        INSERT INTO users (phone, password, name, nickname, membership_type, is_admin) VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed_password, '管理员', '管理员', 'pro', 1))
    
    conn.commit()
    conn.close()

# JWT工具函数
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        logger.warning('Token expired')
        return None
    except jwt.InvalidTokenError:
        logger.warning('Invalid token')
        return None
    except Exception as e:
        logger.error(f'Token verification error: {e}')
        return None

# 登录
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 400
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': '密码错误'}), 400
    
    token = generate_token(user['id'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'avatar': user['avatar'],
            'bio': user['bio'],
            'safetyLevel': user['safety_level'],
            'membership': user['membership']
        }
    })

# 第三方登录 - 微信登录
@app.route('/api/auth/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录接口"""
    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({'message': '微信授权码不能为空'}), 400
    
    try:
        openid = None
        nickname = '微信用户'
        avatar = None
        
        # 检查是否配置了真实微信登录
        if WECHAT_APP_ID and WECHAT_APP_SECRET and WECHAT_APP_ID != 'your-wechat-app-id':
            try:
                import requests
                
                # 调用微信API获取session_key和openid
                url = 'https://api.weixin.qq.com/sns/jscode2session'
                params = {
                    'appid': WECHAT_APP_ID,
                    'secret': WECHAT_APP_SECRET,
                    'js_code': code,
                    'grant_type': 'authorization_code'
                }
                
                response = requests.get(url, params=params)
                result = response.json()
                
                if 'openid' in result:
                    openid = result['openid']
                    logger.info(f'[微信登录] 获取openid成功: {openid}')
                else:
                    logger.error(f'[微信登录] 获取openid失败: {result}')
                    return jsonify({'message': '微信授权失败'}), 400
                    
            except Exception as e:
                logger.error(f'[微信登录] 调用微信API失败: {e}')
                # 如果真实微信登录失败，使用模拟模式
                openid = 'wx_' + str(random.randint(1000000000, 9999999999))
        else:
            # 模拟模式生成唯一的openid
            openid = 'wx_' + str(random.randint(1000000000, 9999999999))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在该微信用户
        cursor.execute('SELECT * FROM users WHERE wechat_openid = ?', (openid,))
        user = cursor.fetchone()
        
        if user:
            # 已有用户，直接登录
            token = generate_token(user['id'])
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'phone': user['phone'] or '',
                    'name': user['name'] or nickname,
                    'avatar': user['avatar'],
                    'bio': user['bio'],
                    'safetyLevel': user['safety_level'],
                    'membership': user['membership'],
                    'need_bind_phone': not user['phone']  # 是否需要绑定手机号
                }
            })
        else:
            # 新用户，创建账号
            hashed_password = bcrypt.hashpw(openid[:10].encode('utf-8'), bcrypt.gensalt())
            # 使用None作为phone值避免唯一约束冲突
            cursor.execute('''
                INSERT INTO users (phone, name, password, avatar, bio, safety_level, membership, wechat_openid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (None, nickname, hashed_password, 1, '', 'high', 'free', openid))
            conn.commit()
            
            user_id = cursor.lastrowid
            token = generate_token(user_id)
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user_id,
                    'phone': '',
                    'name': nickname,
                    'avatar': 1,
                    'bio': '',
                    'safetyLevel': 'high',
                    'membership': 'free',
                    'need_bind_phone': True  # 新用户需要绑定手机号
                }
            })
            
    except Exception as e:
        logger.error(f'微信登录失败: {e}')
        return jsonify({'message': '微信登录失败'}), 500

# 第三方登录 - QQ登录
@app.route('/api/auth/qq-login', methods=['POST'])
def qq_login():
    """QQ登录接口"""
    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({'message': 'QQ授权码不能为空'}), 400
    
    try:
        # 模拟QQ登录流程
        qq_openid = 'qq_' + str(random.randint(1000000000, 9999999999))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE qq_openid = ?', (qq_openid,))
        user = cursor.fetchone()
        
        if user:
            token = generate_token(user['id'])
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'phone': user['phone'] or '',
                    'name': user['name'] or 'QQ用户',
                    'avatar': user['avatar'],
                    'bio': user['bio'],
                    'safetyLevel': user['safety_level'],
                    'membership': user['membership']
                }
            })
        else:
            hashed_password = bcrypt.hashpw(qq_openid[:10].encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (phone, name, password, avatar, bio, safety_level, membership, qq_openid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (None, 'QQ用户', hashed_password, 2, '', 'high', 'free', qq_openid))
            conn.commit()
            
            user_id = cursor.lastrowid
            token = generate_token(user_id)
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user_id,
                    'phone': '',
                    'name': 'QQ用户',
                    'avatar': 2,
                    'bio': '',
                    'safetyLevel': 'high',
                    'membership': 'free'
                },
                'message': '首次登录，请完善个人信息'
            })
    except Exception as e:
        logger.error(f'QQ登录失败: {e}')
        return jsonify({'message': 'QQ登录失败'}), 500

# 第三方登录 - Apple登录
@app.route('/api/auth/apple-login', methods=['POST'])
def apple_login():
    """Apple登录接口"""
    data = request.json
    identity_token = data.get('identity_token')
    
    if not identity_token:
        return jsonify({'message': 'Apple身份令牌不能为空'}), 400
    
    try:
        # 模拟Apple登录流程
        apple_id = 'apple_' + str(random.randint(1000000000, 9999999999))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE apple_id = ?', (apple_id,))
        user = cursor.fetchone()
        
        if user:
            token = generate_token(user['id'])
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'phone': user['phone'] or '',
                    'name': user['name'] or 'Apple用户',
                    'avatar': user['avatar'],
                    'bio': user['bio'],
                    'safetyLevel': user['safety_level'],
                    'membership': user['membership']
                }
            })
        else:
            hashed_password = bcrypt.hashpw(apple_id[:10].encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (phone, name, password, avatar, bio, safety_level, membership, apple_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (None, 'Apple用户', hashed_password, 3, '', 'high', 'free', apple_id))
            conn.commit()
            
            user_id = cursor.lastrowid
            token = generate_token(user_id)
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user_id,
                    'phone': '',
                    'name': 'Apple用户',
                    'avatar': 3,
                    'bio': '',
                    'safetyLevel': 'high',
                    'membership': 'free'
                },
                'message': '首次登录，请完善个人信息'
            })
    except Exception as e:
        logger.error(f'Apple登录失败: {e}')
        return jsonify({'message': 'Apple登录失败'}), 500

# 发送验证码
@app.route('/api/auth/send-code', methods=['POST'])
def send_verification_code():
    """发送短信验证码"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'message': '手机号不能为空'}), 400
    
    # 检查是否频繁发送（60秒内）
    if phone in verification_codes:
        remaining = int(verification_codes[phone]['expire_time'] - time.time())
        if remaining > 240:
            return jsonify({'message': '请60秒后再试'}), 400
    
    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    
    # 发送短信
    result = send_sms_code(phone, code)
    
    if result['success']:
        return jsonify({
            'message': '验证码已发送',
            'debug_code': code  # 仅开发环境调试用
        })
    else:
        return jsonify({'message': result['message']}), 500

# 注册
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    code = data.get('code')
    nickname = data.get('nickname')
    avatar = data.get('avatar')
    gender = data.get('gender')
    birthdate = data.get('birthdate')
    
    # 验证验证码
    if not code:
        return jsonify({'message': '请填写验证码'}), 400
    
    is_valid, msg = verify_code(phone, code)
    if not is_valid:
        return jsonify({'message': msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
    if cursor.fetchone():
        return jsonify({'message': '用户已存在'}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
    INSERT INTO users (phone, password, name, avatar, gender, birthdate) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (phone, hashed_password, nickname or '用户', avatar or 0, gender, birthdate))
    user_id = cursor.lastrowid
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    token = generate_token(user_id)
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'avatar': user['avatar'],
            'bio': user['bio'],
            'safetyLevel': user['safety_level'],
            'membership': user['membership']
        }
    })

# 获取用户信息
@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'id': user['id'],
        'phone': user['phone'],
        'name': user['name'],
        'avatar': user['avatar'],
        'bio': user['bio'],
        'safetyLevel': user['safety_level'],
        'membership': user['membership']
    })

# 更新用户资料
@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    name = data.get('name')
    avatar = data.get('avatar')
    bio = data.get('bio')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
    if avatar:
        cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar, user_id))
    if bio:
        cursor.execute('UPDATE users SET bio = ? WHERE id = ?', (bio, user_id))
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': user['id'],
        'phone': user['phone'],
        'name': user['name'],
        'avatar': user['avatar'],
        'bio': user['bio'],
        'safetyLevel': user['safety_level'],
        'membership': user['membership']
    })

# 获取紧急联系人列表
@app.route('/api/safety/contacts', methods=['GET'])
def get_contacts():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE user_id = ?', (user_id,))
    contacts = cursor.fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': contact['id'],
        'name': contact['name'],
        'phone': contact['phone'],
        'relationship': contact['relationship'],
        'created_at': contact['created_at']
    } for contact in contacts])

# 添加紧急联系人
@app.route('/api/safety/contacts', methods=['POST'])
def add_contact():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    relationship = data.get('relationship', 'family')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO contacts (user_id, name, phone, relationship) VALUES (?, ?, ?, ?)
    ''', (user_id, name, phone, relationship))
    
    # 添加历史记录
    cursor.execute('''
    INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, 'contact', f'添加了紧急联系人 {name}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '添加成功'})

# 获取单个联系人
@app.route('/api/safety/contacts/<int:id>', methods=['GET'])
def get_contact(id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = ? AND user_id = ?', (id, user_id))
    contact = cursor.fetchone()
    
    conn.close()
    
    if not contact:
        return jsonify({'message': '联系人不存在'}), 404
    
    return jsonify({
        'id': contact['id'],
        'name': contact['name'],
        'phone': contact['phone'],
        'relationship': contact['relationship'],
        'created_at': contact['created_at']
    })

# 更新紧急联系人
@app.route('/api/safety/contacts/<int:id>', methods=['PUT'])
def update_contact(id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    relationship = data.get('relationship')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute('UPDATE contacts SET name = ? WHERE id = ? AND user_id = ?', (name, id, user_id))
    if phone:
        cursor.execute('UPDATE contacts SET phone = ? WHERE id = ? AND user_id = ?', (phone, id, user_id))
    if relationship:
        cursor.execute('UPDATE contacts SET relationship = ? WHERE id = ? AND user_id = ?', (relationship, id, user_id))
    
    # 添加历史记录
    cursor.execute('''
    INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, 'contact', f'更新了紧急联系人 {name}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '更新成功'})

# 删除紧急联系人
@app.route('/api/safety/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取联系人名称
    cursor.execute('SELECT name FROM contacts WHERE id = ? AND user_id = ?', (id, user_id))
    contact = cursor.fetchone()
    if not contact:
        return jsonify({'message': '联系人不存在'}), 400
    
    cursor.execute('DELETE FROM contacts WHERE id = ? AND user_id = ?', (id, user_id))
    
    # 添加历史记录
    cursor.execute('''
    INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, 'contact', f'删除了紧急联系人 {contact["name"]}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '删除成功'})

# 获取历史记录
@app.route('/api/safety/history', methods=['GET'])
def get_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    history = cursor.fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': item['id'],
        'type': item['type'],
        'content': item['content'],
        'created_at': item['created_at']
    } for item in history])

# 添加历史记录
@app.route('/api/safety/history', methods=['POST'])
def add_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    type = data.get('type')
    content = data.get('content')
    
    if not type or not content:
        return jsonify({'message': '类型和内容不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, type, content))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '添加成功'})

# 获取情绪日记列表
@app.route('/api/emotion/diary', methods=['GET'])
def get_diaries():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM diaries WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    diaries = cursor.fetchall()
    
    conn.close()
    
    diaries_list = []
    for diary in diaries:
        diaries_list.append({
            'id': diary['id'],
            'content': diary['content'],
            'emotion': diary['emotion'],
            'created_at': diary['created_at']
        })
    
    return jsonify(diaries_list)

# 获取聊天历史
@app.route('/api/emotion/chat-history', methods=['GET'])
def get_chat_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20', (user_id,))
    history = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': h['id'],
        'role': h['role'],
        'content': h['content'],
        'created_at': h['created_at']
    } for h in history])

# 清空聊天历史
@app.route('/api/emotion/chat-history', methods=['DELETE'])
def clear_chat_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '聊天历史已清空'})

# 获取聊天统计信息
@app.route('/api/emotion/chat-stats', methods=['GET'])
def get_chat_stats():
    """获取聊天统计信息"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取总消息数
    cursor.execute('SELECT COUNT(*) as count FROM chat_history WHERE user_id = ?', (user_id,))
    total_messages = cursor.fetchone()['count']
    
    # 获取用户消息数
    cursor.execute('SELECT COUNT(*) as count FROM chat_history WHERE user_id = ? AND role = ?', (user_id, 'user'))
    user_messages = cursor.fetchone()['count']
    
    # 获取AI消息数
    cursor.execute('SELECT COUNT(*) as count FROM chat_history WHERE user_id = ? AND role = ?', (user_id, 'assistant'))
    ai_messages = cursor.fetchone()['count']
    
    # 获取本周消息数
    cursor.execute('''
        SELECT COUNT(*) as count FROM chat_history 
        WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
    ''', (user_id,))
    weekly_messages = cursor.fetchone()['count']
    
    # 获取今日消息数
    cursor.execute('''
        SELECT COUNT(*) as count FROM chat_history 
        WHERE user_id = ? AND date(created_at) = date('now')
    ''', (user_id,))
    today_messages = cursor.fetchone()['count']
    
    # 获取最近的聊天日期
    cursor.execute('''
        SELECT date(created_at) as chat_date, COUNT(*) as count 
        FROM chat_history 
        WHERE user_id = ?
        GROUP BY date(created_at)
        ORDER BY chat_date DESC
        LIMIT 7
    ''', (user_id,))
    recent_dates = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'totalMessages': total_messages,
        'userMessages': user_messages,
        'aiMessages': ai_messages,
        'weeklyMessages': weekly_messages,
        'todayMessages': today_messages,
        'recentDates': recent_dates,
        'averagePerDay': round(weekly_messages / 7, 1) if weekly_messages > 0 else 0
    })

# 获取聊天话题分类
@app.route('/api/emotion/chat-topics', methods=['GET'])
def get_chat_topics():
    """获取聊天话题分类统计"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取最近30天的用户消息进行分析
    cursor.execute('''
        SELECT content FROM chat_history 
        WHERE user_id = ? AND role = 'user' AND created_at >= datetime('now', '-30 days')
        ORDER BY created_at DESC
    ''', (user_id,))
    
    messages = cursor.fetchall()
    conn.close()
    
    # 话题关键词分类
    topic_keywords = {
        '安全相关': ['安全', '危险', '报警', '求助', '跟踪', '陌生人', '夜晚', '打车', '独居'],
        '情感支持': ['难过', '伤心', '害怕', '担心', '焦虑', '孤独', '寂寞', '压力', '累'],
        '日常倾诉': ['今天', '事情', '发生', '工作', '学习', '朋友', '家人', '生活'],
        '紧急求助': ['紧急', 'SOS', '急救', '受伤', '生病', '火灾', '盗窃', '抢劫'],
        '健康养生': ['健康', '身体', '睡眠', '饮食', '运动', '心情', '放松']
    }
    
    topic_counts = {topic: 0 for topic in topic_keywords}
    topic_counts['其他'] = 0
    
    for msg in messages:
        content = msg['content']
        found = False
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topic_counts[topic] += 1
                found = True
                break
        if not found:
            topic_counts['其他'] += 1
    
    # 转换为列表格式
    topics = [
        {'name': topic, 'count': count, 'percentage': round(count / len(messages) * 100, 1) if messages else 0}
        for topic, count in topic_counts.items()
    ]
    
    # 按数量排序
    topics.sort(key=lambda x: x['count'], reverse=True)
    
    return jsonify({
        'topics': topics,
        'totalMessages': len(messages),
        'period': '30天'
    })

# 获取情绪分析
@app.route('/api/emotion/mood-analysis', methods=['GET'])
def get_mood_analysis():
    """获取用户情绪分析"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取最近30天的用户消息
    cursor.execute('''
        SELECT content FROM chat_history 
        WHERE user_id = ? AND role = 'user' AND created_at >= datetime('now', '-30 days')
        ORDER BY created_at DESC
    ''', (user_id,))
    
    messages = cursor.fetchall()
    
    # 情绪关键词分析
    mood_keywords = {
        '开心': ['开心', '高兴', '快乐', '棒', '谢谢', '好开心', '太好了', '完美', '幸福'],
        '平静': ['还好', '一般', '正常', '平静', '还好啦', '没什么', '还好吧'],
        '担忧': ['担心', '害怕', '担心', '焦虑', '紧张', '不安', '顾虑', '发愁'],
        '难过': ['难过', '伤心', '痛苦', '难受', '不爽', '郁闷', '沮丧', '失落'],
        '愤怒': ['生气', '愤怒', '讨厌', '气', '不爽', '恼火', '火大', '气愤']
    }
    
    mood_counts = {mood: 0 for mood in mood_keywords}
    
    for msg in messages:
        content = msg['content']
        for mood, keywords in mood_keywords.items():
            if any(keyword in content for keyword in keywords):
                mood_counts[mood] += 1
    
    # 计算主要情绪
    total_detected = sum(mood_counts.values())
    if total_detected > 0:
        main_mood = max(mood_counts, key=mood_counts.get)
    else:
        main_mood = '平静'
    
    conn.close()
    
    return jsonify({
        'mainMood': main_mood,
        'moodDistribution': mood_counts,
        'totalAnalyzed': total_detected,
        'period': '30天',
        'suggestions': _get_mood_suggestions(main_mood)
    })

def _get_mood_suggestions(mood):
    """根据情绪提供建议"""
    suggestions = {
        '开心': [
            '继续保持好心情！😊',
            '可以将这份快乐分享给身边的人',
            '记录下让你开心的事情，以后可以回顾'
        ],
        '平静': [
            '保持平和的心态很重要 🌿',
            '可以尝试一些新的活动让生活更有趣',
            '记得适时放松，不要太紧绷'
        ],
        '担忧': [
            '不要一个人扛着，可以和我聊聊 💭',
            '把担心的事情写下来，逐一解决',
            '必要时记得寻求家人朋友或专业人士的帮助'
        ],
        '难过': [
            '难过的时候记得你不是一个人 🤗',
            '可以做一些让自己放松的事情',
            '如果持续很久，建议和心理咨询师聊聊'
        ],
        '愤怒': [
            '先深呼吸，冷静一下 🧘‍♀️',
            '可以换个环境，转移注意力',
            '把愤怒的原因写下来，有助于平复情绪'
        ]
    }
    return suggestions.get(mood, ['记得照顾好自己 💝'])

# AI聊天 - 增强版
@app.route('/api/emotion/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    
    # 从token获取用户ID
    token = request.headers.get('Authorization')
    user_id = None
    if token:
        user_id = verify_token(token)
    
    # 增强版星伴AI系统提示
    system_prompt = """你是"星伴"，一个专业、温暖、善解人意的女性安全助手。你的核心特质：

1. **温柔陪伴**：
   - 用温暖、亲切的语气和用户交流
   - 善于倾听，给予情感支持
   - 使用亲切的称呼和温馨的表情符号
   - 理解用户的情绪和感受

2. **安全守护**：
   - 拥有专业的安全知识
   - 时刻关注用户的安全状况
   - 敏锐识别危险信号
   - 提供实用、可操作的安全建议

3. **情感支持**：
   - 在用户焦虑、害怕时给予安慰
   - 在用户难过时给予陪伴
   - 在用户开心时一起分享快乐
   - 用共情的语言回应

4. **安全专业**：
   - 提供正确的安全知识
   - 不传播错误信息
   - 紧急情况给出明确指导
   - 引导用户寻求专业帮助

5. **对话风格**：
   - 使用自然、口语化的表达
   - 适当使用温馨的表情符号
   - 保持积极向上的态度
   - 关注对话的连贯性
   - 记得之前的对话内容

你的回答要：
✅ 温暖亲切，有共情
✅ 专业可靠，信息准确
✅ 简洁明了，易于理解
✅ 积极向上，给予希望
✅ 记得对话上下文

请时刻记住，你是"星伴"，一个守护用户安全、陪伴用户心灵的温暖助手！"""
    
    try:
        # 准备消息列表
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # 如果有用户ID，获取历史对话作为上下文（最近10条）
        if user_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY created_at ASC LIMIT 10', (user_id,))
            history = cursor.fetchall()
            
            # 添加历史消息
            for h in history:
                messages.append({'role': h['role'], 'content': h['content']})
            
            conn.close()
        
        # 添加当前消息
        messages.append({'role': 'user', 'content': message})
        
        # 调用DeepSeek API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.8,
            'max_tokens': 800
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # 保存到历史记录（如果有用户ID）
            if user_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', 
                              (user_id, 'user', message))
                cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', 
                              (user_id, 'assistant', ai_response))
                conn.commit()
                conn.close()
            
            return jsonify({'response': ai_response})
        else:
            logger.error(f'DeepSeek API error: {response.status_code}')
            raise Exception('API调用失败')
            
    except Exception as e:
        logger.error(f'AI chat error: {e}')
        # 如果API调用失败，使用更丰富的预设回复
        import random
        responses = [
            "亲爱的，我理解你的感受 💛 无论发生什么，我都会在这里陪伴你。有什么想和我说的吗？",
            "安全永远是第一位的哦 🛡️ 如果你需要任何安全建议，随时和我说，我会尽力帮助你！",
            "很高兴听到你的分享 🌟 保持积极的心态对安全意识真的很重要呢！",
            "记住哦，遇到危险时一定要保持冷静，优先确保自己的安全 🙏 有需要随时找我！",
            "定期检查紧急联系人信息是个好习惯呢 ✅ 确保在需要时能及时联系到他们，这让我很安心！",
            "你今天过得怎么样呀？😊 如果有什么不开心的，可以和我说说，我会认真听的！",
            "感觉你好像有点担心... 别害怕，有我在呢 💪 需要什么帮助吗？",
            "抱抱你 🤗 无论遇到什么困难，我们一起面对，好吗？"
        ]
        
        fallback_response = random.choice(responses)
        
        # 保存到历史记录（如果有用户ID）
        if user_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', 
                          (user_id, 'user', message))
            cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', 
                          (user_id, 'assistant', fallback_response))
            conn.commit()
            conn.close()
        
        return jsonify({'response': fallback_response})

# 安全场景分析
@app.route('/api/safety/analyze', methods=['POST'])
def analyze_safety():
    data = request.json
    scenario = data.get('scenario', '')
    
    import random
    
    # 根据场景内容生成分析结果
    if '夜晚' in scenario or '晚上' in scenario or '深夜' in scenario:
        analysis = {
            "scenario": "用户描述的场景涉及夜间出行或活动",
            "risks": ["夜间能见度低，容易成为犯罪分子的目标", "可能遇到醉酒人员或不良分子", "紧急情况下求助困难"],
            "suggestions": ["尽量避免独自夜间出行", "选择明亮、人多的路线", "开启位置共享功能", "随身携带防身工具"],
            "precautions": ["提前规划好行程", "告知亲友你的行踪", "保持手机电量充足", "学会基本的自我防卫技巧"]
        }
    elif '打车' in scenario or '网约车' in scenario or '滴滴' in scenario:
        analysis = {
            "scenario": "用户描述的场景涉及打车出行",
            "risks": ["可能遇到不良司机", "行车路线可能偏离", "车内安全隐患"],
            "suggestions": ["使用正规平台打车", "上车前拍照记录车牌", "共享行程给亲友", "坐在后排位置"],
            "precautions": ["核对司机信息与平台一致", "开启行程录音功能", "保持车窗开启", "了解紧急求助方式"]
        }
    elif '独居' in scenario or '一个人' in scenario:
        analysis = {
            "scenario": "用户描述的场景涉及独居生活",
            "risks": ["陌生人敲门风险", "突发状况无人知晓", "居家安全隐患"],
            "suggestions": ["安装智能门锁和监控", "不要轻易给陌生人开门", "设置紧急联系人", "定期与亲友联系"],
            "precautions": ["检查门窗安全性", "了解小区安保措施", "学会使用安防设备", "制定应急预案"]
        }
    elif '旅行' in scenario or '出差' in scenario or '旅游' in scenario:
        analysis = {
            "scenario": "用户描述的场景涉及旅行出行",
            "risks": ["陌生环境安全隐患", "财物丢失风险", "交通意外风险"],
            "suggestions": ["提前了解目的地安全情况", "保管好个人财物", "购买旅行保险", "随身携带重要证件复印件"],
            "precautions": ["告知亲友行程安排", "保存当地紧急联系方式", "了解当地习俗和法规", "保持通讯畅通"]
        }
    else:
        # 默认分析结果
        analysis = {
            "scenario": "用户描述了一个安全场景",
            "risks": ["可能存在未明确的安全隐患", "需要根据具体情况评估风险", "建议保持警惕"],
            "suggestions": ["提高安全意识", "注意周围环境", "保持通讯畅通", "必要时寻求帮助"],
            "precautions": ["定期检查安全设备", "学习安全知识", "制定应急预案", "定期演练"]
        }
    
    # 格式化输出
    result = f"1. 场景分析：{analysis['scenario']}\n\n"
    result += "2. 潜在风险：\n"
    for i, risk in enumerate(analysis['risks'], 1):
        result += f"   {i}. {risk}\n"
    result += "\n3. 安全建议：\n"
    for i, suggestion in enumerate(analysis['suggestions'], 1):
        result += f"   {i}. {suggestion}\n"
    result += "\n4. 预防措施：\n"
    for i, precaution in enumerate(analysis['precautions'], 1):
        result += f"   {i}. {precaution}\n"
    
    return jsonify({'result': result})

# 情绪日记分析
@app.route('/api/emotion/analyze-diary', methods=['POST'])
def analyze_diary():
    # 使用request.get_data()获取原始数据并解码
    raw_data = request.get_data().decode('utf-8')
    import json
    try:
        data = json.loads(raw_data)
    except:
        data = {}
    
    content = data.get('content', '')
    
    # 确保内容是字符串
    if not isinstance(content, str):
        content = str(content)
    
    # 调试信息
    logger.info(f"情绪分析内容: {content}")
    logger.info(f"内容类型: {type(content)}")
    
    # 根据日记内容进行情绪分析
    if any(keyword in content for keyword in ['难过', '伤心', '沮丧', '失落', '悲伤', '忧郁']):
        analysis = {
            "emotion": "低落",
            "level": 3,
            "suggestion": "建议你找朋友聊聊天，或者做一些能让自己开心的事情。如果情绪持续低落，可以考虑寻求专业心理咨询帮助。"
        }
    elif any(keyword in content for keyword in ['开心', '高兴', '快乐', '幸福', '愉快', '兴奋']):
        analysis = {
            "emotion": "愉快",
            "level": 1,
            "suggestion": "很高兴看到你心情不错！保持积极的心态对身心健康都很有益。"
        }
    elif any(keyword in content for keyword in ['焦虑', '担心', '紧张', '压力', '忧虑', '不安']):
        analysis = {
            "emotion": "焦虑",
            "level": 4,
            "suggestion": "建议你尝试一些放松技巧，如深呼吸、冥想或运动。如果压力过大，可以与信任的人分享你的感受。"
        }
    elif any(keyword in content for keyword in ['生气', '愤怒', '烦躁', '恼火', '恼怒']):
        analysis = {
            "emotion": "愤怒",
            "level": 4,
            "suggestion": "请冷静下来，深呼吸。愤怒时做出的决定往往不够理智。可以尝试暂时离开让你生气的环境。"
        }
    else:
        analysis = {
            "emotion": "平静",
            "level": 2,
            "suggestion": "你的情绪状态比较平稳，这是很好的状态。继续保持良好的生活习惯和心态。"
        }
    
    return jsonify(analysis)

# 情绪日记
@app.route('/api/emotion/diary', methods=['POST'])
def add_diary():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    content = data.get('content')
    emotion = data.get('emotion')
    
    if not content or not emotion:
        return jsonify({'message': '内容和情绪不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO diaries (user_id, content, emotion) VALUES (?, ?, ?)',
        (user_id, content, emotion)
    )
    
    # 添加历史记录
    cursor.execute('''
    INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, 'diary', f'记录了一条{emotion}的情绪日记'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '添加成功'})

# 获取安全建议
@app.route('/api/safety/suggestions', methods=['GET'])
def get_safety_suggestions():
    # 从请求头获取token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    # 验证token
    try:
        payload = jwt.decode(token, 'secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'token已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的token'}), 401
    
    # 根据用户ID获取个性化安全建议
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 生成个性化安全建议
    suggestions = [
        '建议开启位置共享功能，让亲友知道你的位置',
        '定期检查紧急联系人信息，确保在需要时能及时联系到他们',
        '注意出行安全，避免前往危险区域',
        '保持良好的网络安全习惯，不随意透露个人信息'
    ]
    
    # 根据用户的安全等级添加个性化建议
    if user['safety_level'] < 80:
        suggestions.append('建议增加紧急联系人数量，提高安全保障')
        suggestions.append('定期进行安全演练，提高应急处理能力')
    
    return jsonify({'suggestions': suggestions})

# 健康检查 - 供内部使用
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

# 健康检查 - 供 Render 监控使用
@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'healthy'}), 200

# ==================== 会员系统API ====================

# 会员权限装饰器
def require_membership(min_level='free'):
    """检查会员权限"""
    levels = {'free': 0, 'basic': 1, 'pro': 2}
    def decorator(f):
        def wrapped(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'message': '未授权', 'code': 401}), 401
            
            user_id = verify_token(token)
            if not user_id:
                return jsonify({'message': '无效的令牌', 'code': 401}), 401
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT membership_type FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return jsonify({'message': '用户不存在', 'code': 404}), 404
            
            user_level = levels.get(user['membership_type'], 0)
            required_level = levels.get(min_level, 0)
            
            if user_level < required_level:
                return jsonify({
                    'message': '需要升级会员才能使用此功能',
                    'code': 403,
                    'required': min_level,
                    'current': user['membership_type']
                }), 403
            
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

# 获取会员信息
@app.route('/api/membership/status', methods=['GET'])
def get_membership_status():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT membership_type, membership_expire, name, nickname FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 会员特权列表
    features = {
        'free': {
            'name': '免费版',
            'features': ['情绪日记(限3条/天)', '紧急求助', 'AI基础聊天', '1位紧急联系人', '安全知识库'],
            'limits': {'diaries': 3, 'chat': 10}
        },
        'safety': {
            'name': '安全守护版',
            'features': ['情绪日记无限', '一键紧急求助', 'AI智能取证与引导', '情景模拟无限', '安全报告', '3-5位紧急联系人'],
            'limits': {'diaries': -1, 'chat': -1}
        },
        'family': {
            'name': '家庭守护版',
            'features': ['包含6个家庭账号', '家庭安全监控面板', '老人/儿童简易模式', '家庭群组紧急通知', '专属客服支持', '所有安全守护版功能'],
            'limits': {'diaries': -1, 'chat': -1}
        }
    }
    
    membership_info = features.get(user['membership_type'], features['free'])
    
    return jsonify({
        'type': user['membership_type'],
        'expire': user['membership_expire'],
        'info': membership_info
    })

# 获取会员套餐列表
@app.route('/api/membership/packages', methods=['GET'])
def get_membership_packages():
    packages = [
        {
            'type': 'free',
            'name': '免费版',
            'price_month': 0,
            'price_year': 0,
            'duration': '永久',
            'features': ['情绪日记(限3条/天)', '紧急求助', 'AI基础聊天', '1位紧急联系人', '安全知识库'],
            'recommended': False,
            'max_contacts': 1
        },
        {
            'type': 'safety',
            'name': '安全守护版',
            'price_month': 9.9,
            'price_year': 89.9,
            'duration': '月',
            'features': ['情绪日记无限', '一键紧急求助', 'AI智能取证与引导', '情景模拟无限', '安全报告', '3-5位紧急联系人'],
            'recommended': True,
            'max_contacts': 5
        },
        {
            'type': 'family',
            'name': '家庭守护版',
            'price_month': 19.9,
            'price_year': 179.9,
            'duration': '月',
            'features': ['包含6个家庭账号', '家庭安全监控面板', '老人/儿童简易模式', '家庭群组紧急通知', '专属客服支持', '所有安全守护版功能'],
            'recommended': False,
            'max_contacts': 5,
            'max_family_members': 6
        }
    ]
    return jsonify(packages)

# 购买会员
@app.route('/api/membership/purchase', methods=['POST'])
def purchase_membership():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    membership_type = data.get('type')
    billing_cycle = data.get('cycle', 'month')  # month or year
    
    if membership_type not in ['safety', 'family']:
        return jsonify({'message': '无效的会员类型'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 计算到期时间
    from datetime import datetime, timedelta
    start_date = datetime.now().strftime('%Y-%m-%d')
    days = 365 if billing_cycle == 'year' else 30
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 确定价格
    if membership_type == 'safety':
        price = 89.9 if billing_cycle == 'year' else 9.9
    else:
        price = 179.9 if billing_cycle == 'year' else 19.9
    
    # 更新用户会员状态
    cursor.execute('''
        UPDATE users SET membership_type = ?, membership_expire = ?, membership = ? WHERE id = ?
    ''', (membership_type, end_date, f'{membership_type}会员', user_id))
    
    # 创建会员订单
    cursor.execute('''
        INSERT INTO memberships (user_id, type, price, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, membership_type, price, start_date, end_date, 'active'))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': '购买成功',
        'type': membership_type,
        'expire': end_date,
        'price': price
    })

# ==================== 单次付费功能 ====================

# 获取单次付费服务列表
@app.route('/api/one-time/list', methods=['GET'])
def get_one_time_services():
    services = [
        {
            'id': 'assessment',
            'name': '深度安全评估报告',
            'price': 29.9,
            'description': '基于你的使用历史数据，生成个性化的安全评估报告',
            'icon': 'fa-chart-line',
            'color': 'from-blue-500 to-indigo-600'
        },
        {
            'id': 'plan',
            'name': '专属应急方案定制',
            'price': 19.9,
            'description': '根据你的具体情况，定制个性化的应急安全方案',
            'icon': 'fa-lightbulb',
            'color': 'from-yellow-500 to-orange-600'
        },
        {
            'id': 'consult',
            'name': '1对1安全咨询',
            'price': 39.9,
            'description': '30分钟专业安全顾问1对1在线咨询服务',
            'icon': 'fa-user-tie',
            'color': 'from-purple-500 to-pink-600'
        }
    ]
    return jsonify(services)

# 购买单次付费服务
@app.route('/api/one-time/purchase', methods=['POST'])
def purchase_one_time_service():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    service_id = data.get('id')
    
    services = {
        'assessment': 29.9,
        'plan': 19.9,
        'consult': 39.9
    }
    
    if service_id not in services:
        return jsonify({'message': '无效的服务'}), 400
    
    # 记录购买
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (user_id, type, content) VALUES (?, ?, ?)
    ''', (user_id, 'service', f'购买了{service_id}服务'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': '购买成功',
        'service': service_id,
        'price': services[service_id]
    })

# ==================== 管理端API ====================

# 管理员权限检查装饰器
def require_admin():
    """检查管理员权限"""
    def decorator(f):
        def wrapped(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'message': '未授权', 'code': 401}), 401
            
            user_id = verify_token(token)
            if not user_id:
                return jsonify({'message': '无效的令牌', 'code': 401}), 401
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin, name FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if not user or user['is_admin'] != 1:
                return jsonify({'message': '需要管理员权限', 'code': 403}), 403
            
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

# 管理员登录
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username') or data.get('phone')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE (phone = ? OR name = ?) AND is_admin = 1', (username, username))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'message': '管理员账户不存在'}), 400
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': '密码错误'}), 400
    
    token = generate_token(user['id'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'nickname': user['nickname'],
            'is_admin': True
        }
    })

# 获取所有用户列表
@app.route('/api/admin/users', methods=['GET'])
@require_admin()
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取分页参数
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    # 搜索参数
    search = request.args.get('search', '')
    membership_filter = request.args.get('membership', '')
    
    query = 'SELECT * FROM users WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (phone LIKE ? OR name LIKE ? OR nickname LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if membership_filter:
        query += ' AND membership_type = ?'
        params.append(membership_filter)
    
    query += f' ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}'
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # 获取总数
    count_query = 'SELECT COUNT(*) as total FROM users WHERE 1=1'
    if search:
        count_query += ' AND (phone LIKE ? OR name LIKE ? OR nickname LIKE ?)'
    if membership_filter:
        count_query += ' AND membership_type = ?'
    
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    conn.close()
    
    users_list = [{
        'id': user['id'],
        'phone': user['phone'],
        'name': user['name'],
        'nickname': user['nickname'],
        'gender': user['gender'],
        'birthdate': user['birthdate'],
        'avatar_id': user['avatar_id'],
        'membership_type': user['membership_type'],
        'membership_expire': user['membership_expire'],
        'is_admin': user['is_admin'],
        'created_at': user['created_at']
    } for user in users]
    
    return jsonify({
        'users': users_list,
        'total': total,
        'page': page,
        'limit': limit
    })

# 获取单个用户详情
@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin()
def get_user_detail(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取用户基本信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'message': '用户不存在'}), 404
    
    # 获取紧急联系人
    cursor.execute('SELECT * FROM contacts WHERE user_id = ?', (user_id,))
    contacts = cursor.fetchall()
    
    # 获取情绪日记
    cursor.execute('SELECT * FROM diaries WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (user_id,))
    diaries = cursor.fetchall()
    
    # 获取历史记录
    cursor.execute('SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20', (user_id,))
    history = cursor.fetchall()
    
    # 获取SOS记录
    cursor.execute('SELECT * FROM sos_records WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (user_id,))
    sos_records = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'nickname': user['nickname'],
            'gender': user['gender'],
            'birthdate': user['birthdate'],
            'avatar_id': user['avatar_id'],
            'membership_type': user['membership_type'],
            'membership_expire': user['membership_expire'],
            'is_admin': user['is_admin'],
            'created_at': user['created_at']
        },
        'contacts': [{
            'id': c['id'],
            'name': c['name'],
            'phone': c['phone'],
            'relationship': c['relationship'],
            'created_at': c['created_at']
        } for c in contacts],
        'diaries': [{
            'id': d['id'],
            'content': d['content'],
            'emotion': d['emotion'],
            'created_at': d['created_at']
        } for d in diaries],
        'history': [{
            'id': h['id'],
            'type': h['type'],
            'content': h['content'],
            'created_at': h['created_at']
        } for h in history],
        'sos_records': [{
            'id': s['id'],
            'location': s['location'],
            'contacts_notified': s['contacts_notified'],
            'status': s['status'],
            'created_at': s['created_at']
        } for s in sos_records]
    })

# 获取统计数据
@app.route('/api/admin/stats', methods=['GET'])
@require_admin()
def get_admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户总数
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total']
    
    # 各类型会员数
    cursor.execute('SELECT membership_type, COUNT(*) as count FROM users GROUP BY membership_type')
    membership_stats = cursor.fetchall()
    
    # 今日新增用户
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = DATE('now')")
    today_new = cursor.fetchone()['count']
    
    # 情绪日记总数
    cursor.execute('SELECT COUNT(*) as total FROM diaries')
    total_diaries = cursor.fetchone()['total']
    
    # SOS记录总数
    cursor.execute('SELECT COUNT(*) as total FROM sos_records')
    total_sos = cursor.fetchone()['total']
    
    # 最近活跃用户（7天内有记录）
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM history 
        WHERE created_at >= DATE('now', '-7 days')
    """)
    active_users = cursor.fetchone()['count']
    
    conn.close()
    
    membership_dict = {'free': 0, 'basic': 0, 'pro': 0}
    for stat in membership_stats:
        membership_dict[stat['membership_type']] = stat['count']
    
    return jsonify({
        'total_users': total_users,
        'membership_stats': membership_dict,
        'today_new': today_new,
        'total_diaries': total_diaries,
        'total_sos': total_sos,
        'active_users': active_users
    })

# 更新用户会员状态
@app.route('/api/admin/users/<int:user_id>/membership', methods=['PUT'])
@require_admin()
def update_user_membership(user_id):
    data = request.json
    membership_type = data.get('type')
    expire_days = data.get('expire_days', 30)
    
    if membership_type not in ['free', 'basic', 'pro']:
        return jsonify({'message': '无效的会员类型'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime, timedelta
    if membership_type == 'free':
        expire_date = ''
    else:
        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        UPDATE users SET membership_type = ?, membership_expire = ?, membership = ? WHERE id = ?
    ''', (membership_type, expire_date, f'{membership_type}会员', user_id))
    
    # 记录管理日志
    admin_id = verify_token(request.headers.get('Authorization'))
    cursor.execute('''
        INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (?, ?, ?, ?)
    ''', (admin_id, 'update_membership', user_id, f'更新会员类型为{membership_type}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '更新成功'})

# 删除用户
@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin()
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否是管理员
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user and user['is_admin'] == 1:
        return jsonify({'message': '不能删除管理员账户'}), 400
    
    # 删除用户相关数据
    cursor.execute('DELETE FROM contacts WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM diaries WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM sos_records WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM memberships WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    # 记录管理日志
    admin_id = verify_token(request.headers.get('Authorization'))
    cursor.execute('''
        INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (?, ?, ?, ?)
    ''', (admin_id, 'delete_user', user_id, '删除用户'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '删除成功'})

# 获取管理日志
@app.route('/api/admin/logs', methods=['GET'])
@require_admin()
def get_admin_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    offset = (page - 1) * limit
    
    cursor.execute('''
        SELECT al.*, u.name as admin_name 
        FROM admin_logs al 
        LEFT JOIN users u ON al.admin_id = u.id 
        ORDER BY al.created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    logs = cursor.fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': log['id'],
        'admin_id': log['admin_id'],
        'admin_name': log['admin_name'],
        'action': log['action'],
        'target_user_id': log['target_user_id'],
        'details': log['details'],
        'created_at': log['created_at']
    } for log in logs])

# ==================== 支付相关接口 ====================

# 微信支付 - 创建订单
@app.route('/api/payment/wechat/create', methods=['POST'])
def create_wechat_payment():
    """创建微信支付订单"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    amount = data.get('amount')
    payment_type = data.get('type', 'membership')
    product_id = data.get('product_id', '')
    
    if not amount or amount <= 0:
        return jsonify({'message': '金额错误'}), 400
    
    # 创建订单
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_id = f"XG{int(time.time())}{random.randint(1000, 9999)}"
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO payment_orders (user_id, order_id, amount, payment_type, product_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, order_id, amount, payment_type, product_id, 'pending', created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f'[微信支付] 创建订单: {order_id}, 用户: {user_id}, 金额: {amount}')
    
    # 检查是否配置了真实微信支付
    if WECHAT_APP_ID and WECHAT_MCH_ID and WECHAT_API_KEY and WECHAT_APP_ID != 'your-wechat-app-id':
        try:
            # 真实微信支付 - 使用微信支付SDK
            from wechatpayv3 import WeChatPay, SignType
            
            wxp = WeChatPay(
                appid=WECHAT_APP_ID,
                mchid=WECHAT_MCH_ID,
                api_key=WECHAT_API_KEY,
                cert_path=WECHAT_CERT_PATH if WECHAT_CERT_PATH and WECHAT_CERT_PATH != '/path/to/your/apiclient_cert.p12' else None
            )
            
            # 创建统一下单
            result = wxp.order.create(
                description=f'星伴守护-{payment_type}',
                out_trade_no=order_id,
                amount={'total': int(amount * 100)},  # 转换为分
                notify_url=f'{API_BASE_URL}/api/payment/wechat/callback'
            )
            
            logger.info(f'[微信支付] 统一下单成功: {order_id}')
            
            return jsonify({
                'success': True,
                'order_id': order_id,
                'payment_type': 'wechat',
                'prepay_id': result.get('prepay_id'),
                'code_url': result.get('code_url'),  # 二维码链接
                'message': '支付订单创建成功'
            })
            
        except ImportError:
            logger.warning('[微信支付] 未安装wechatpayv3 SDK，使用模拟模式')
        except Exception as e:
            logger.error(f'[微信支付] 创建订单失败: {e}')
    
    # 模拟模式或配置未完成
    return jsonify({
        'success': True,
        'order_id': order_id,
        'payment_type': 'wechat',
        'message': '请配置微信支付后使用真实支付',
        'qrcode_data': f'weixin://wxpay/bizpayurl?pr=mock{order_id}'
    })

# 微信支付回调
@app.route('/api/payment/wechat/callback', methods=['POST'])
def wechat_payment_callback():
    """微信支付回调"""
    try:
        data = request.get_json()
        if not data:
            # 微信回调可能是XML格式
            from xml.etree import ElementTree
            xml_data = request.data
            root = ElementTree.fromstring(xml_data)
            data = {}
            for child in root:
                data[child.tag] = child.text
        
        order_id = data.get('out_trade_no')
        transaction_id = data.get('transaction_id')
        result_code = data.get('result_code')
        
        if not order_id:
            return '<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[订单号缺失]]></return_msg></xml>'
        
        if result_code == 'SUCCESS':
            # 支付成功
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM payment_orders WHERE order_id = ?', (order_id,))
            order = cursor.fetchone()
            
            if order and order['status'] == 'pending':
                paid_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    UPDATE payment_orders 
                    SET status = 'paid', paid_at = ?, transaction_id = ?
                    WHERE order_id = ?
                ''', (paid_at, transaction_id, order_id))
                
                # 如果是会员购买，更新用户会员状态
                if order['payment_type'] == 'membership':
                    membership_expire = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        UPDATE users 
                        SET membership = 'VIP会员', 
                            membership_type = 'paid', 
                            membership_expire = ?
                        WHERE id = ?
                    ''', (membership_expire, order['user_id']))
                
                conn.commit()
                logger.info(f'[微信支付] 支付成功: {order_id}')
            
            conn.close()
        
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'
    
    except Exception as e:
        logger.error(f'[微信支付] 回调处理失败: {e}')
        return '<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[处理失败]]></return_msg></xml>'

# 支付宝支付 - 创建订单
@app.route('/api/payment/alipay/create', methods=['POST'])
def create_alipay_payment():
    """创建支付宝支付订单"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    amount = data.get('amount')
    payment_type = data.get('type', 'membership')
    product_id = data.get('product_id', '')
    
    if not amount or amount <= 0:
        return jsonify({'message': '金额错误'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_id = f"XG{int(time.time())}{random.randint(1000, 9999)}"
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO payment_orders (user_id, order_id, amount, payment_type, product_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, order_id, amount, payment_type, product_id, 'pending', created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f'[支付宝支付] 创建订单: {order_id}, 用户: {user_id}, 金额: {amount}')
    
    # 检查是否配置了真实支付宝
    if ALIPAY_APP_ID and ALIPAY_PRIVATE_KEY and ALIPAY_APP_ID != 'your-alipay-app-id':
        try:
            # 真实支付宝支付
            from alipay import AliPay
            
            alipay = AliPay(
                appid=ALIPAY_APP_ID,
                app_notify_url=f'{API_BASE_URL}/api/payment/alipay/callback',
                app_private_key_string=ALIPAY_PRIVATE_KEY,
                alipay_public_key_string=ALIPAY_PUBLIC_KEY,
                sign_type='RSA2',
                debug=False
            )
            
            # 创建支付订单
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=order_id,
                total_amount=str(amount),
                subject=f'星伴守护-{payment_type}',
                return_url=f'{API_BASE_URL}/payment/success',
                notify_url=f'{API_BASE_URL}/api/payment/alipay/callback'
            )
            
            pay_url = f'{ALIPAY_GATEWAY}?{order_string}'
            
            logger.info(f'[支付宝支付] 创建订单成功: {order_id}')
            
            return jsonify({
                'success': True,
                'order_id': order_id,
                'payment_type': 'alipay',
                'pay_url': pay_url,
                'message': '支付订单创建成功'
            })
            
        except ImportError:
            logger.warning('[支付宝支付] 未安装alipay-sdk-python，使用模拟模式')
        except Exception as e:
            logger.error(f'[支付宝支付] 创建订单失败: {e}')
    
    # 模拟模式或配置未完成
    return jsonify({
        'success': True,
        'order_id': order_id,
        'payment_type': 'alipay',
        'message': '请配置支付宝支付后使用真实支付',
        'qrcode_data': f'alipay://platformapi/startapp?saId=10000007&qrcode=mock{order_id}'
    })

# 支付宝支付回调
@app.route('/api/payment/alipay/callback', methods=['POST'])
def alipay_payment_callback():
    """支付宝支付回调"""
    try:
        data = request.form.to_dict()
        
        if ALIPAY_APP_ID and ALIPAY_PRIVATE_KEY and ALIPAY_APP_ID != 'your-alipay-app-id':
            from alipay import AliPay
            
            alipay = AliPay(
                appid=ALIPAY_APP_ID,
                app_notify_url=f'{API_BASE_URL}/api/payment/alipay/callback',
                app_private_key_string=ALIPAY_PRIVATE_KEY,
                alipay_public_key_string=ALIPAY_PUBLIC_KEY,
                sign_type='RSA2',
                debug=False
            )
            
            # 验证签名
            sign = data.pop('sign', None)
            sign_type = data.pop('sign_type', None)
            
            if not alipay.verify(data, sign):
                logger.warning('[支付宝支付] 签名验证失败')
                return 'failure'
        else:
            # 开发环境跳过签名验证
            pass
        
        order_id = data.get('out_trade_no')
        trade_status = data.get('trade_status')
        transaction_id = data.get('trade_no')
        
        if trade_status == 'TRADE_SUCCESS' or trade_status == 'TRADE_FINISHED':
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM payment_orders WHERE order_id = ?', (order_id,))
            order = cursor.fetchone()
            
            if order and order['status'] == 'pending':
                paid_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    UPDATE payment_orders 
                    SET status = 'paid', paid_at = ?, transaction_id = ?
                    WHERE order_id = ?
                ''', (paid_at, transaction_id, order_id))
                
                if order['payment_type'] == 'membership':
                    membership_expire = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        UPDATE users 
                        SET membership = 'VIP会员', 
                            membership_type = 'paid', 
                            membership_expire = ?
                        WHERE id = ?
                    ''', (membership_expire, order['user_id']))
                
                conn.commit()
                logger.info(f'[支付宝支付] 支付成功: {order_id}')
            
            conn.close()
        
        return 'success'
    
    except Exception as e:
        logger.error(f'[支付宝支付] 回调处理失败: {e}')
        return 'failure'

# 查询支付订单状态
@app.route('/api/payment/query/<order_id>', methods=['GET'])
def query_payment_status(order_id):
    """查询支付订单状态"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM payment_orders WHERE order_id = ? AND user_id = ?', (order_id, user_id))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'message': '订单不存在'}), 404
    
    conn.close()
    
    return jsonify({
        'order_id': order['order_id'],
        'amount': order['amount'],
        'payment_type': order['payment_type'],
        'status': order['status'],
        'created_at': order['created_at'],
        'paid_at': order['paid_at']
    })

# 模拟支付回调（测试用）
@app.route('/api/payment/callback/mock', methods=['POST'])
def mock_payment_callback():
    """模拟支付回调"""
    data = request.json
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({'success': False, 'message': '订单号缺失'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM payment_orders WHERE order_id = ?', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'success': False, 'message': '订单不存在'}), 404
    
    # 更新订单状态
    paid_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE payment_orders 
        SET status = 'paid', paid_at = ?
        WHERE order_id = ?
    ''', (paid_at, order_id))
    
    # 如果是会员购买，更新用户会员状态
    if order['payment_type'] == 'membership':
        # 这里可以根据支付金额设置不同的会员等级和时长
        membership_expire = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE users 
            SET membership = 'VIP会员', 
                membership_type = 'paid', 
                membership_expire = ?
            WHERE id = ?
        ''', (membership_expire, order['user_id']))
        
        logger.info(f'[支付] 会员开通成功: 用户 {order["user_id"]}, 订单 {order_id}')
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '支付成功'})

# 获取支付订单列表
@app.route('/api/payment/orders', methods=['GET'])
def get_payment_orders():
    """获取用户支付订单列表"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM payment_orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (user_id, limit, offset))
    
    orders = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'order_id': o['order_id'],
        'amount': o['amount'],
        'payment_type': o['payment_type'],
        'product_id': o['product_id'],
        'status': o['status'],
        'created_at': o['created_at'],
        'paid_at': o['paid_at']
    } for o in orders])

# ==================== 会员管理接口 ====================

# 获取会员信息
@app.route('/api/membership/info', methods=['GET'])
def get_membership_info():
    """获取用户会员信息"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return jsonify({
        'membership': user['membership'],
        'membership_type': user['membership_type'],
        'membership_expire': user['membership_expire'],
        'is_vip': user['membership_type'] == 'paid'
    })

# 会员套餐列表
@app.route('/api/membership/plans', methods=['GET'])
def get_membership_plans():
    """获取会员套餐列表"""
    return jsonify([
        {
            'id': 'monthly',
            'name': '月度会员',
            'price': 29.9,
            'duration': 30,
            'description': '享受VIP专属服务',
            'features': [
                'AI智能陪伴无限畅聊',
                '安全防护功能升级',
                '优先客服支持'
            ]
        },
        {
            'id': 'quarterly',
            'name': '季度会员',
            'price': 79.9,
            'duration': 90,
            'description': '超值季度套餐',
            'features': [
                'AI智能陪伴无限畅聊',
                '安全防护功能升级',
                '优先客服支持',
                '额外会员权益'
            ]
        },
        {
            'id': 'yearly',
            'name': '年度会员',
            'price': 299.0,
            'duration': 365,
            'description': '性价比之王，一年无忧',
            'features': [
                'AI智能陪伴无限畅聊',
                '安全防护功能升级',
                '优先客服支持',
                '额外会员权益',
                '专属定制服务'
            ]
        }
    ])

# 微信登录 - 绑定手机号
@app.route('/api/auth/wechat/bind-phone', methods=['POST'])
def wechat_bind_phone():
    """微信登录后绑定手机号"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': '无效的令牌'}), 401
    
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({'message': '请填写手机号和验证码'}), 400
    
    # 验证验证码
    is_valid, msg = verify_code(phone, code)
    if not is_valid:
        return jsonify({'message': msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查手机号是否已被注册
    cursor.execute('SELECT id FROM users WHERE phone = ? AND id != ?', (phone, user_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': '该手机号已被注册'}), 400
    
    # 更新用户手机号
    cursor.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
    conn.commit()
    
    # 获取更新后的用户信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    logger.info(f'[微信绑定] 用户 {user_id} 绑定手机号成功: {phone}')
    
    return jsonify({
        'token': generate_token(user_id),
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'avatar': user['avatar'],
            'bio': user['bio'],
            'safetyLevel': user['safety_level'],
            'membership': user['membership']
        },
        'message': '手机号绑定成功'
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

# Gunicorn 入口
def create_app():
    init_db()
    return app