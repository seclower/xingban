# 测试登录功能
import requests
import json

print("🧪 测试登录功能...")
print("=" * 50)

# 测试登录
print("\n1. 测试登录API...")
response = requests.post('http://localhost:8083', json={
    'action': 'login',
    'phone': '13188393081',
    'password': '123456'
})
result = response.json()
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(result, ensure_ascii=False)}")

if result.get('success'):
    print("\n✅ 登录API正常！")
    user = result.get('user', {})
    print(f"用户信息:")
    print(f"  - ID: {user.get('id')}")
    print(f"  - 手机号: {user.get('phone')}")
    print(f"  - 昵称: {user.get('nickname')}")
else:
    print(f"\n❌ 登录失败: {result.get('error')}")

# 测试验证码
print("\n2. 测试发送验证码...")
response = requests.post('http://localhost:8083', json={
    'action': 'send_code',
    'phone': '13188393081',
    'type': 'register'
})
result = response.json()
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(result, ensure_ascii=False)}")

if result.get('success'):
    print(f"\n✅ 验证码API正常！")
    print(f"验证码: {result.get('code')}")
else:
    print(f"\n❌ 验证码发送失败: {result.get('error')}")

print("\n" + "=" * 50)
print("测试完成！")
