# 实现自动登录功能 - 直接登录测试账号

import re

print("🔧 正在实现自动登录功能...")
print("=" * 50)

# 读取文件
with open('d:\\xingban\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加自动登录逻辑
auto_login_code = '''
    // ==================== 自动登录功能 ====================
    const AUTO_LOGIN_PHONE = '13188393081';
    const AUTO_LOGIN_PASSWORD = '123456';
    
    async function autoLogin() {
      // 检查是否已登录
      if (currentUser) {
        console.log('✅ 已有登录状态，跳过自动登录');
        return;
      }
      
      // 检查本地存储
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        currentUser = JSON.parse(savedUser);
        console.log('✅ 从本地存储恢复登录状态');
        showMainApp();
        loadUserData();
        return;
      }
      
      // 自动登录测试账号
      console.log('🔐 自动登录测试账号...');
      
      try {
        const result = await apiRequest('login', {
          phone: AUTO_LOGIN_PHONE,
          password: AUTO_LOGIN_PASSWORD
        });
        
        if (result.success) {
          currentUser = result.user;
          localStorage.setItem('user', JSON.stringify(currentUser));
          showToast('自动登录成功！');
          showMainApp();
          loadUserData();
          console.log('✅ 自动登录成功:', currentUser);
        } else {
          console.log('⚠️  自动登录失败:', result.error);
          // 如果自动登录失败，显示登录页面
          document.getElementById('auth-page').classList.remove('hidden');
          document.getElementById('app').classList.add('hidden');
        }
      } catch (error) {
        console.log('⚠️  自动登录异常:', error.message);
        // 网络错误时显示登录页面
        document.getElementById('auth-page').classList.remove('hidden');
        document.getElementById('app').classList.add('hidden');
      }
    }
    
    // 在页面加载完成后自动登录
    document.addEventListener('DOMContentLoaded', () => {
      initializeApp();
      // 延迟1秒后自动登录（等待页面渲染完成）
      setTimeout(autoLogin, 1000);
    });
'''

# 找到初始化代码的位置并添加自动登录
content = content.replace(
    'document.addEventListener(\'DOMContentLoaded\', initializeApp);',
    auto_login_code
)

print("✅ 已添加自动登录逻辑")

# 保存文件
with open('d:\\xingban\\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# 同步到www目录
import shutil
shutil.copy('d:\\xingban\\index.html', 'd:\\xingban\\www\\index.html')
print("✅ 已同步到www目录")

print("\n" + "=" * 50)
print("🎉 自动登录功能已实现！")
print("=" * 50)

print("\n📝 修改内容:")
print("   1. ✅ 添加自动登录逻辑")
print("   2. ✅ 设置测试账号 (13188393081/123456)")
print("   3. ✅ 页面加载后自动登录")
print("   4. ✅ 同步到www目录")

print("\n🚀 现在打开页面会自动登录测试账号")
print("   访问地址: http://127.0.0.1:8082")
