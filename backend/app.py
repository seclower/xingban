from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 生产环境应使用环境变量

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
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT DEFAULT '用户',
        avatar TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        safety_level INTEGER DEFAULT 1,
        membership TEXT DEFAULT '普通会员',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # 添加测试用户
    cursor.execute('SELECT * FROM users WHERE phone = ?', ('12345678910',))
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
        INSERT INTO users (phone, password, name) VALUES (?, ?, ?)
        ''', ('12345678910', hashed_password, '测试用户'))
        
        # 添加测试联系人
        user_id = cursor.lastrowid
        cursor.execute('''
        INSERT INTO contacts (user_id, name, phone, relationship) VALUES (?, ?, ?, ?)
        ''', (user_id, '爸爸', '13800138123', 'family'))
        cursor.execute('''
        INSERT INTO contacts (user_id, name, phone, relationship) VALUES (?, ?, ?, ?)
        ''', (user_id, '妈妈', '13900139567', 'family'))
    
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

# 注册
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
    if cursor.fetchone():
        return jsonify({'message': '用户已存在'}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
    INSERT INTO users (phone, password) VALUES (?, ?)
    ''', (phone, hashed_password))
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

# AI聊天
@app.route('/api/emotion/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    
    # 更智能的AI回复逻辑
    if '安全' in message or '危险' in message or '求助' in message:
        responses = [
            "安全是最重要的，如果你遇到危险，请立即拨打紧急电话或通知紧急联系人。",
            "记住，在遇到危险时要保持冷静，优先确保自己的安全。",
            "建议你开启位置共享功能，让亲友知道你的位置。",
            "定期检查紧急联系人信息是个好习惯，确保在需要时能及时联系到他们。",
            "如果你感到不安全，可以尝试前往人多的地方或寻求周围人的帮助。"
        ]
    elif '心情' in message or '情绪' in message or '难过' in message or '开心' in message:
        responses = [
            "我理解你的感受，有什么我可以帮助你的吗？",
            "保持积极的心态对安全意识很重要，希望你心情好转。",
            "情绪状态会影响我们的判断力，建议你在情绪稳定时再做重要决定。",
            "如果你需要倾诉，我在这里倾听。",
            "记得照顾好自己的情绪，这对整体安全也很重要。"
        ]
    elif '演练' in message or '模拟' in message or '练习' in message:
        responses = [
            "定期进行安全演练是个好习惯，可以提高应急处理能力。",
            "建议你尝试不同的安全演练场景，如打车安全、独居防护等。",
            "演练可以帮助你在真正遇到危险时更快地做出反应。",
            "完成演练后，记得总结经验，不断提高自己的安全意识。",
            "安全演练不仅是技能的练习，也是心理的准备。"
        ]
    else:
        responses = [
            "我理解你的感受，有什么我可以帮助你的吗？",
            "安全是最重要的，如果你需要任何安全建议，随时告诉我。",
            "很高兴听到你的分享，保持积极的心态对安全意识很重要。",
            "记住，在遇到危险时要保持冷静，优先确保自己的安全。",
            "定期检查紧急联系人信息是个好习惯，确保在需要时能及时联系到他们。"
        ]
    
    import random
    random_response = random.choice(responses)
    
    return jsonify({'response': random_response})

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

# 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)