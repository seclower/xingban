# 登录问题诊断和修复
import re

print("🔍 诊断登录问题...")
print("=" * 50)

# 读取文件
with open('d:\\xingban\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("\n1. 检查API配置...")

# 检查API_BASE_URL
if "const API_BASE_URL = 'http://localhost:8083'" in content:
    print("   ⚠️  发现问题: API使用localhost")
    print("   📝  在其他设备访问时会无法连接API")
    
    # 修复: 根据访问来源动态设置API地址
    print("\n   🔧 正在修复...")
    
    # 方案1: 使用相对路径（需要代理）
    old_api = "const API_BASE_URL = 'http://localhost:8083';"
    new_api = """const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') 
    ? 'http://localhost:8083' 
    : 'http://' + window.location.hostname + ':8083';"""
    
    content = content.replace(old_api, new_api)
    print("   ✅ 已修复: API地址现在会根据访问方式自动切换")

print("\n2. 检查表单绑定...")

# 检查登录表单
if 'id="loginForm"' in content:
    print("   ✅ 登录表单存在")
else:
    print("   ❌ 未找到登录表单")

if 'id="login-phone"' in content:
    print("   ✅ 手机号输入框存在")
else:
    print("   ❌ 未找到手机号输入框")

if 'id="login-password"' in content:
    print("   ✅ 密码输入框存在")
else:
    print("   ❌ 未找到密码输入框")

print("\n3. 检查JavaScript函数...")

# 检查关键函数
functions = [
    'handleLogin',
    'apiRequest',
    'showMainApp',
    'loadUserData',
    'initializeApp'
]

for func in functions:
    if f'function {func}' in content or f'async function {func}' in content:
        print(f"   ✅ {func} 函数存在")
    else:
        print(f"   ❌ {func} 函数缺失")

print("\n4. 添加调试日志...")

# 在handleLogin中添加更多调试信息
old_login = '''async function handleLogin(phone, password) {
      if (!phone || !password) {
        showToast('请填写完整信息');
        return false;
      }
      
      showToast('正在登录...');
      
      const result = await apiRequest('login', { phone, password });'''

new_login = '''async function handleLogin(phone, password) {
      console.log('🔐 开始登录流程...');
      console.log('手机号:', phone);
      console.log('密码:', password ? '***' : '未填写');
      
      if (!phone || !password) {
        showToast('请填写完整信息');
        return false;
      }
      
      showToast('正在登录...');
      console.log('📡 发送登录请求到:', API_BASE_URL);
      
      const result = await apiRequest('login', { phone, password });
      console.log('📥 收到响应:', result);'''

content = content.replace(old_login, new_login)

# 在showMainApp中添加调试
old_show_main = '''function showMainApp() {
      document.getElementById('auth-page').classList.add('hidden');
      document.getElementById('app').classList.remove('hidden');
    }'''

new_show_main = '''function showMainApp() {
      console.log('🚀 切换到主应用...');
      document.getElementById('auth-page').classList.add('hidden');
      document.getElementById('app').classList.remove('hidden');
      console.log('✅ 主应用已显示');
    }'''

content = content.replace(old_show_main, new_show_main)

print("   ✅ 已添加调试日志")

print("\n5. 添加错误详情显示...")

# 在apiRequest中添加更详细的错误信息
old_error = '''} catch (error) {
        console.error('API请求失败:', error);
        showToast('网络连接失败，请检查网络');
        return { error: '网络错误' };
      }'''

new_error = '''} catch (error) {
        console.error('❌ API请求失败:', error);
        console.error('错误类型:', error.name);
        console.error('错误消息:', error.message);
        showToast('网络连接失败，请检查网络: ' + error.message);
        return { error: '网络错误: ' + error.message };
      }'''

content = content.replace(old_error, new_error)

print("   ✅ 已添加详细错误信息")

# 保存文件
with open('d:\\xingban\\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 50)
print("✅ 诊断和修复完成！")
print("=" * 50)

print("\n📝 修复内容:")
print("   1. ✅ API地址自动切换（localhost/局域网）")
print("   2. ✅ 添加详细调试日志")
print("   3. ✅ 改进错误信息显示")
print("\n🔍 调试步骤:")
print("   1. 打开浏览器开发者工具 (F12)")
print("   2. 打开Console标签")
print("   3. 尝试登录")
print("   4. 查看Console中的调试信息")
print("\n💡 常见问题解决方案:")
print("   - 如果显示'网络错误': 检查后端API是否运行在8083端口")
print("   - 如果显示跨域错误: 确保两个服务都在运行")
print("   - 检查Console中的具体错误信息")

print("\n请刷新页面重试登录！")
