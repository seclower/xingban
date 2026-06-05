# 修复脚本 - 解决测试发现的问题
import sqlite3
import os

def fix_database():
    """修复数据库问题"""
    
    db_path = 'd:\\xingban\\safety_guard.db'
    
    print("🔧 开始修复数据库...")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 检查users表结构
    print("\n1. 检查users表结构...")
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    print(f"当前列: {columns}")
    
    # 如果缺少nickname列，添加它
    if 'nickname' not in columns:
        print("添加nickname列...")
        c.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
        print("✅ nickname列已添加")
    else:
        print("✅ nickname列已存在")
    
    # 检查是否有用户数据
    print("\n2. 检查用户数据...")
    c.execute("SELECT * FROM users WHERE phone = '13188393081'")
    user = c.fetchone()
    
    if not user:
        print("创建测试用户...")
        from hashlib import sha256
        password_hash = sha256('123456'.encode()).hexdigest()
        c.execute('''
            INSERT INTO users (phone, password, nickname)
            VALUES (?, ?, ?)
        ''', ('13188393081', password_hash, '测试用户'))
        print("✅ 测试用户已创建")
    else:
        print("✅ 测试用户已存在")
        # 更新nickname
        c.execute("UPDATE users SET nickname = ? WHERE phone = ?", ('测试用户', '13188393081'))
        print("✅ 更新用户昵称")
    
    # 检查并修复验证码表
    print("\n3. 检查verifications表...")
    c.execute("PRAGMA table_info(verifications)")
    ver_columns = [col[1] for col in c.fetchall()]
    print(f"当前列: {ver_columns}")
    
    # 删除过期验证码
    c.execute("DELETE FROM verifications WHERE datetime(expires_at) < datetime('now')")
    deleted = c.rowcount
    if deleted > 0:
        print(f"✅ 删除了 {deleted} 条过期验证码")
    
    # 提交更改
    conn.commit()
    
    # 验证修复结果
    print("\n4. 验证修复结果...")
    c.execute("SELECT id, phone, nickname FROM users WHERE phone = '13188393081'")
    user = c.fetchone()
    if user:
        print(f"✅ 用户验证成功: ID={user[0]}, 手机号={user[1]}, 昵称={user[2]}")
    else:
        print("❌ 用户验证失败")
    
    c.execute("SELECT COUNT(*) FROM verifications WHERE phone = '13188393081' AND datetime(expires_at) >= datetime('now')")
    valid_codes = c.fetchone()[0]
    print(f"✅ 有效验证码数量: {valid_codes}")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 数据库修复完成！")
    print("=" * 50)

def fix_backend_api():
    """修复后端API逻辑"""
    
    print("\n🔧 开始修复后端API逻辑...")
    
    api_file = 'd:\\xingban\\backend_api.py'
    
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1: 确保expires_at时间比较正确
    old_code = '''if datetime.now() > datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S'):'''
    new_code = '''try:
            expires_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S.%f')
        except:
            expires_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_time:'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ 修复验证码过期检查逻辑")
    else:
        print("⚠️  未找到需要修复的代码")
    
    # 保存修复后的代码
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "=" * 50)
    print("🎉 后端API修复完成！")
    print("=" * 50)

if __name__ == '__main__':
    print("=" * 50)
    print("🔧 开始修复...")
    print("=" * 50)
    
    fix_database()
    fix_backend_api()
    
    print("\n" + "=" * 50)
    print("✅ 所有修复完成！")
    print("请重启后端API服务以应用更改")
    print("=" * 50)
