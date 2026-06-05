from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import bcrypt
import os
import json

app = Flask(__name__)
CORS(app)

# 密钥，实际生产环境应该使用环境变量
app.config['SECRET_KEY'] = 'your-secret-key'

# 模拟数据库
users = {}
contacts = {}
diaries = {}
safety_history = {}
game_records = {}

# 模拟数据
mock_users = {
    '13188393081': {
        'phone': '13188393081',
        'password': bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'name': '测试用户',
        'avatar': 'https://via.placeholder.com/150',
        'id': '1'
    }
}

mock_contacts = {
    '1': [
        {'id': '1', 'name': '张三', 'phone': '13800138001', 'relation': '家人'},
        {'id': '2', 'name': '李四', 'phone': '13900139001', 'relation': '朋友'},
        {'id': '3', 'name': '王五', 'phone': '13700137001', 'relation': '同事'}
    ]
}

mock_diaries = {
    '1': [
        {
            'id': '1',
            'emotion': '开心',
            'content': '今天完成了安全演练，感觉很有收获。',
            'timestamp': '2024-07-17 10:30:00'
        },
        {
            'id': '2',
            'emotion': '一般',
            'content': '今天工作有点累，但安全指数保持良好。',
            'timestamp': '2024-07-16 18:45:00'
        }
    ]
}

mock_safety_history = {
    '1': [
        {
            'id': '1',
            'type': 'emergency',
            'content': '拨打了110紧急求助',
            'timestamp': '2024-07-15 14:20:00'
        },
        {
            'id': '2',
            'type': 'simulation',
            'content': '完成了打车安全模拟',
            'timestamp': '2024-07-14 10:15:00'
        }
    ]
}

mock_game_records = {
    '1': [
        {
            'id': '1',
            'game_type': '安全知识问答',
            'score': 80,
            'timestamp': '2024-07-16 16:30:00'
        },
        {
            'id': '2',
            'game_type': '急救知识挑战',
            'score': 90,
            'timestamp': '2024-07-15 11:20:00'
        }
    ]
}

# 初始化模拟数据
users.update(mock_users)
contacts.update(mock_contacts)
diaries.update(mock_diaries)
safety_history.update(mock_safety_history)
game_records.update(mock_game_records)

# 生成JWT token
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# 验证JWT token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

# 登录API
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码不能为空'}), 400
    
    user = users.get(phone)
    if not user:
        return jsonify({'error': '用户不存在'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': '密码错误'}), 401
    
    token = generate_token(user['id'])
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'phone': user['phone'],
            'name': user['name'],
            'avatar': user['avatar']
        }
    })

# 注册API
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码不能为空'}), 400
    
    if phone in users:
        return jsonify({'error': '用户已存在'}), 400
    
    # 生成新用户
    user_id = str(len(users) + 1)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = {
        'phone': phone,
        'password': hashed_password,
        'name': '新用户',
        'avatar': 'https://via.placeholder.com/150',
        'id': user_id
    }
    
    users[phone] = new_user
    
    # 初始化用户数据
    contacts[user_id] = []
    diaries[user_id] = []
    safety_history[user_id] = []
    game_records[user_id] = []
    
    token = generate_token(user_id)
    return jsonify({
        'token': token,
        'user': {
            'id': user_id,
            'phone': phone,
            'name': '新用户',
            'avatar': 'https://via.placeholder.com/150'
        }
    })

# 获取用户信息
@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    # 查找用户
    for phone, user in users.items():
        if user['id'] == user_id:
            return jsonify({
                'id': user['id'],
                'phone': user['phone'],
                'name': user['name'],
                'avatar': user['avatar']
            })
    
    return jsonify({'error': '用户不存在'}), 404

# 更新用户信息
@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    data = request.get_json()
    name = data.get('name')
    avatar = data.get('avatar')
    
    # 更新用户信息
    for phone, user in users.items():
        if user['id'] == user_id:
            if name:
                user['name'] = name
            if avatar:
                user['avatar'] = avatar
            return jsonify({
                'id': user['id'],
                'phone': user['phone'],
                'name': user['name'],
                'avatar': user['avatar']
            })
    
    return jsonify({'error': '用户不存在'}), 404

# 获取联系人列表
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    user_contacts = contacts.get(user_id, [])
    return jsonify(user_contacts)

# 添加联系人
@app.route('/api/contacts', methods=['POST'])
def add_contact():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    relation = data.get('relation')
    
    if not name or not phone:
        return jsonify({'error': '姓名和电话不能为空'}), 400
    
    # 生成新联系人ID
    user_contacts = contacts.get(user_id, [])
    contact_id = str(len(user_contacts) + 1)
    
    new_contact = {
        'id': contact_id,
        'name': name,
        'phone': phone,
        'relation': relation
    }
    
    user_contacts.append(new_contact)
    contacts[user_id] = user_contacts
    
    return jsonify(new_contact)

# 删除联系人
@app.route('/api/contacts/<contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    user_contacts = contacts.get(user_id, [])
    updated_contacts = [contact for contact in user_contacts if contact['id'] != contact_id]
    
    if len(updated_contacts) == len(user_contacts):
        return jsonify({'error': '联系人不存在'}), 404
    
    contacts[user_id] = updated_contacts
    return jsonify({'message': '联系人删除成功'})

# 获取情绪日记列表
@app.route('/api/diaries', methods=['GET'])
def get_diaries():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    user_diaries = diaries.get(user_id, [])
    return jsonify(user_diaries)

# 添加情绪日记
@app.route('/api/diaries', methods=['POST'])
def add_diary():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    data = request.get_json()
    emotion = data.get('emotion')
    content = data.get('content')
    
    if not emotion or not content:
        return jsonify({'error': '情绪和内容不能为空'}), 400
    
    # 生成新日记ID
    user_diaries = diaries.get(user_id, [])
    diary_id = str(len(user_diaries) + 1)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_diary = {
        'id': diary_id,
        'emotion': emotion,
        'content': content,
        'timestamp': timestamp
    }
    
    user_diaries.append(new_diary)
    diaries[user_id] = user_diaries
    
    return jsonify(new_diary)

# 获取安全历史记录
@app.route('/api/safety/history', methods=['GET'])
def get_safety_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    user_history = safety_history.get(user_id, [])
    return jsonify(user_history)

# 添加安全历史记录
@app.route('/api/safety/history', methods=['POST'])
def add_safety_history():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    data = request.get_json()
    type = data.get('type')
    content = data.get('content')
    
    if not type or not content:
        return jsonify({'error': '类型和内容不能为空'}), 400
    
    # 生成新历史记录ID
    user_history = safety_history.get(user_id, [])
    history_id = str(len(user_history) + 1)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_history = {
        'id': history_id,
        'type': type,
        'content': content,
        'timestamp': timestamp
    }
    
    user_history.append(new_history)
    safety_history[user_id] = user_history
    
    return jsonify(new_history)

# 获取游戏记录
@app.route('/api/game/records', methods=['GET'])
def get_game_records():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    user_records = game_records.get(user_id, [])
    return jsonify(user_records)

# 添加游戏记录
@app.route('/api/game/records', methods=['POST'])
def add_game_record():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供token'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': '无效的token'}), 401
    
    data = request.get_json()
    game_type = data.get('game_type')
    score = data.get('score')
    
    if not game_type or score is None:
        return jsonify({'error': '游戏类型和分数不能为空'}), 400
    
    # 生成新游戏记录ID
    user_records = game_records.get(user_id, [])
    record_id = str(len(user_records) + 1)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_record = {
        'id': record_id,
        'game_type': game_type,
        'score': score,
        'timestamp': timestamp
    }
    
    user_records.append(new_record)
    game_records[user_id] = user_records
    
    return jsonify(new_record)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
