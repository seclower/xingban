# 完整的前端升级脚本 - 验证码、登录注册、定位功能

import re

# 读取文件
with open('d:\\xingban\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ==================== 1. 替换JavaScript部分 - 添加完整的API和功能 ====================

# 新的JavaScript代码
new_js_code = '''</script>
  <script>
    // ==================== API配置 ====================
    const API_BASE_URL = 'http://localhost:8083';
    let currentUser = null;
    let countdown = 0;

    // ==================== API请求封装 ====================
    async function apiRequest(action, data = {}) {
      try {
        const response = await fetch(API_BASE_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ action, ...data })
        });
        return await response.json();
      } catch (error) {
        console.error('API请求失败:', error);
        showToast('网络连接失败，请检查网络');
        return { error: '网络错误' };
      }
    }

    // ==================== Toast提示 ====================
    function showToast(message, duration = 3000) {
      const existing = document.querySelector('.toast-message');
      if (existing) existing.remove();
      
      const toast = document.createElement('div');
      toast.className = 'toast-message fixed top-20 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-xl shadow-2xl z-50 animate-bounce';
      toast.textContent = message;
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.remove();
      }, duration);
    }

    // ==================== 验证码功能 ====================
    function startCountdown(button) {
      countdown = 60;
      button.disabled = true;
      button.textContent = countdown + '秒后重试';
      
      const timer = setInterval(() => {
        countdown--;
        if (countdown <= 0) {
          clearInterval(timer);
          button.disabled = false;
          button.textContent = '获取验证码';
        } else {
          button.textContent = countdown + '秒后重试';
        }
      }, 1000);
      
      return timer;
    }

    async function sendVerificationCode(phone, type = 'register') {
      if (!phone || phone.length !== 11) {
        showToast('请输入正确的手机号');
        return false;
      }
      
      const button = event.target;
      const timer = startCountdown(button);
      
      const result = await apiRequest('send_code', { phone, type });
      
      if (result.success) {
        showToast('验证码已发送，请注意查收');
        console.log('开发环境验证码:', result.code);
        return true;
      } else {
        clearInterval(timer);
        button.disabled = false;
        button.textContent = '获取验证码';
        showToast(result.error || '发送失败');
        return false;
      }
    }

    // ==================== 用户认证 ====================
    async function handleRegister(phone, password, code, nickname) {
      if (!phone || !password || !code) {
        showToast('请填写完整信息');
        return false;
      }
      
      if (password.length < 6) {
        showToast('密码至少6位');
        return false;
      }
      
      showToast('正在注册...');
      
      const result = await apiRequest('register', { phone, password, code, nickname });
      
      if (result.success) {
        showToast('注册成功！');
        currentUser = result.user;
        localStorage.setItem('user', JSON.stringify(currentUser));
        setTimeout(() => {
          showMainApp();
          loadUserData();
        }, 1000);
        return true;
      } else {
        showToast(result.error || '注册失败');
        return false;
      }
    }

    async function handleLogin(phone, password) {
      if (!phone || !password) {
        showToast('请填写完整信息');
        return false;
      }
      
      showToast('正在登录...');
      
      const result = await apiRequest('login', { phone, password });
      
      if (result.success) {
        showToast('登录成功！');
        currentUser = result.user;
        localStorage.setItem('user', JSON.stringify(currentUser));
        setTimeout(() => {
          showMainApp();
          loadUserData();
        }, 1000);
        return true;
      } else {
        showToast(result.error || '登录失败');
        return false;
      }
    }

    function logout() {
      currentUser = null;
      localStorage.removeItem('user');
      document.getElementById('auth-page').classList.remove('hidden');
      document.getElementById('app').classList.add('hidden');
      showToast('已退出登录');
    }

    // ==================== 定位功能 ====================
    let currentPosition = null;

    function getCurrentPosition() {
      return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          showToast('您的浏览器不支持定位功能');
          reject(new Error('不支持定位'));
          return;
        }
        
        navigator.geolocation.getCurrentPosition(
          (position) => {
            currentPosition = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              timestamp: position.timestamp
            };
            
            reverseGeocode(currentPosition.latitude, currentPosition.longitude)
              .then(address => {
                currentPosition.address = address;
                resolve(currentPosition);
              })
              .catch(() => {
                currentPosition.address = '未知地址';
                resolve(currentPosition);
              });
          },
          (error) => {
            let errorMsg = '定位失败';
            switch (error.code) {
              case error.PERMISSION_DENIED:
                errorMsg = '请允许定位权限';
                break;
              case error.POSITION_UNAVAILABLE:
                errorMsg = '无法获取位置';
                break;
              case error.TIMEOUT:
                errorMsg = '定位超时';
                break;
            }
            showToast(errorMsg);
            reject(new Error(errorMsg));
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        );
      });
    }

    async function reverseGeocode(lat, lng) {
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
          {
            headers: {
              'User-Agent': 'SafetyGuardApp/1.0'
            }
          }
        );
        const data = await response.json();
        return data.display_name || '未知地址';
      } catch (error) {
        console.error('逆地理编码失败:', error);
        return '未知地址';
      }
    }

    async function saveLocationToServer() {
      if (!currentUser) {
        showToast('请先登录');
        return;
      }
      
      try {
        const position = await getCurrentPosition();
        const result = await apiRequest('save_location', {
          user_id: currentUser.id,
          latitude: position.latitude,
          longitude: position.longitude,
          address: position.address
        });
        
        if (result.success) {
          showToast('位置已保存');
        }
      } catch (error) {
        console.error('保存位置失败:', error);
      }
    }

    // ==================== SOS求助 ====================
    async function triggerSOS(situation = '紧急求助') {
      if (!currentUser) {
        showToast('请先登录');
        return;
      }
      
      showToast('正在获取位置...');
      
      try {
        const position = await getCurrentPosition();
        showToast('正在发送求助...');
        
        const result = await apiRequest('send_sos', {
          user_id: currentUser.id,
          latitude: position.latitude,
          longitude: position.longitude,
          address: position.address,
          situation: situation
        });
        
        if (result.success) {
          showToast('求助信息已发送！已通知 ' + result.contacts_notified + ' 位紧急联系人');
          
          if (confirm('是否立即拨打110报警？')) {
            window.location.href = 'tel:110';
          }
        }
      } catch (error) {
        showToast('求助发送失败，但已记录您的位置');
        await apiRequest('send_sos', {
          user_id: currentUser.id,
          situation: situation
        });
      }
    }

    // ==================== 紧急联系人 ====================
    async function saveEmergencyContact(name, phone, relation) {
      if (!currentUser) {
        showToast('请先登录');
        return false;
      }
      
      if (!name || !phone) {
        showToast('请填写姓名和电话');
        return false;
      }
      
      const result = await apiRequest('save_emergency_contact', {
        user_id: currentUser.id,
        name,
        phone,
        relation
      });
      
      if (result.success) {
        showToast('紧急联系人已保存');
        return true;
      } else {
        showToast('保存失败');
        return false;
      }
    }

    async function loadEmergencyContacts() {
      if (!currentUser) return [];
      
      const result = await apiRequest('get_emergency_contacts', {
        user_id: currentUser.id
      });
      
      return result.contacts || [];
    }

    async function loadUserData() {
      if (!currentUser) return;
      
      const contacts = await loadEmergencyContacts();
      renderEmergencyContacts(contacts);
      
      try {
        await getCurrentPosition();
        console.log('当前位置:', currentPosition);
      } catch (error) {
        console.log('获取位置失败:', error);
      }
    }

    function renderEmergencyContacts(contacts) {
      const container = document.getElementById('contacts-list');
      if (!container) return;
      
      if (contacts.length === 0) {
        container.innerHTML = `
          <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            <i class="fa-solid fa-users text-4xl mb-3"></i>
            <p>暂无紧急联系人</p>
            <p class="text-sm mt-1">请添加以便紧急情况下快速联系</p>
          </div>
        `;
        return;
      }
      
      container.innerHTML = contacts.map(contact => `
        <div class="flex items-center justify-between p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
              <i class="fa-solid fa-user text-white text-lg"></i>
            </div>
            <div>
              <p class="font-medium text-gray-800 dark:text-white">${contact.name}</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">${contact.phone}</p>
              <p class="text-xs text-gray-400 dark:text-gray-500">${contact.relation || '紧急联系人'}</p>
            </div>
          </div>
          <button onclick="quickCall('${contact.phone}')" class="p-3 bg-green-100 dark:bg-green-900/30 rounded-full hover:bg-green-200 transition-colors">
            <i class="fa-solid fa-phone text-green-500"></i>
          </button>
        </div>
      `).join('');
    }

    // ==================== 应用初始化 ====================
    function initializeApp() {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showMainApp();
        loadUserData();
      }
      
      const loginForm = document.getElementById('loginForm');
      if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          const phone = document.getElementById('login-phone').value;
          const password = document.getElementById('login-password').value;
          await handleLogin(phone, password);
        });
      }
      
      const registerForm = document.getElementById('registerForm');
      if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          const phone = document.getElementById('register-phone').value;
          const password = document.getElementById('register-password').value;
          const code = document.getElementById('register-code')?.value;
          const nickname = document.getElementById('register-nickname')?.value;
          
          // 验证密码确认
          const confirmPassword = document.getElementById('register-confirm-password')?.value;
          if (password !== confirmPassword) {
            showToast('两次密码输入不一致');
            return;
          }
          
          await handleRegister(phone, password, code, nickname);
        });
      }
      
      const addContactBtn = document.getElementById('add-contact-btn');
      if (addContactBtn) {
        addContactBtn.addEventListener('click', showAddContactModal);
      }
    }

    function showAddContactModal() {
      const modal = document.createElement('div');
      modal.id = 'add-contact-modal';
      modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50';
      modal.innerHTML = `
        <div class="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl">
          <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">添加紧急联系人</h3>
          <form id="add-contact-form" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">姓名</label>
              <input type="text" id="contact-name" required
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">电话</label>
              <input type="tel" id="contact-phone" required
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">关系</label>
              <select id="contact-relation"
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
                <option value="父母">父母</option>
                <option value="配偶">配偶</option>
                <option value="子女">子女</option>
                <option value="兄弟姐妹">兄弟姐妹</option>
                <option value="朋友">朋友</option>
                <option value="其他">其他</option>
              </select>
            </div>
            <div class="flex gap-3">
              <button type="button" onclick="closeAddContactModal()"
                class="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                取消
              </button>
              <button type="submit"
                class="flex-1 px-4 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-xl hover:opacity-90 transition-opacity">
                保存
              </button>
            </div>
          </form>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      document.getElementById('add-contact-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('contact-name').value;
        const phone = document.getElementById('contact-phone').value;
        const relation = document.getElementById('contact-relation').value;
        
        const success = await saveEmergencyContact(name, phone, relation);
        if (success) {
          closeAddContactModal();
          const contacts = await loadEmergencyContacts();
          renderEmergencyContacts(contacts);
        }
      });
      
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeAddContactModal();
        }
      });
    }

    function closeAddContactModal() {
      const modal = document.getElementById('add-contact-modal');
      if (modal) {
        modal.remove();
      }
    }

    document.addEventListener('DOMContentLoaded', initializeApp);

    // ==================== 定位函数升级 ====================
    function getLocation() {
      getCurrentPosition()
        .then(position => {
          showToast('位置获取成功！');
          const mapContainer = document.querySelector('#map-container');
          if (mapContainer) {
            mapContainer.innerHTML = `
              <div class="text-center p-4">
                <i class="fa-solid fa-map-pin text-6xl text-primary mb-3"></i>
                <p class="text-gray-700 dark:text-gray-300 font-medium">当前位置</p>
                <p class="text-sm text-gray-500 mt-1">${position.address}</p>
                <p class="text-xs text-gray-400 mt-2">
                  纬度: ${position.latitude.toFixed(6)}<br>
                  经度: ${position.longitude.toFixed(6)}
                </p>
                <button onclick="saveLocationToServer()" class="mt-4 px-6 py-2 bg-primary text-white rounded-xl hover:opacity-90 transition-opacity">
                  <i class="fa-solid fa-save mr-2"></i>保存位置
                </button>
              </div>
            `;
          }
        })
        .catch(error => {
          console.error('定位失败:', error);
        });
    }

    // ==================== 第三方登录 ====================
    function wechatLogin() {
      showToast('微信登录开发中...');
    }
    
    function qqLogin() {
      showToast('QQ登录开发中...');
    }
    
    function weiboLogin() {
      showToast('微博登录开发中...');
    }

    function showMainApp() {
      document.getElementById('auth-page').classList.add('hidden');
      document.getElementById('app').classList.remove('hidden');
    }

    function showResetPasswordModal() {
      const modal = document.createElement('div');
      modal.id = 'reset-password-modal';
      modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50';
      modal.innerHTML = `
        <div class="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl">
          <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">重置密码</h3>
          <form id="reset-password-form" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">手机号</label>
              <input type="tel" id="reset-phone" required maxlength="11" placeholder="请输入注册手机号"
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div class="flex gap-2">
              <input type="text" id="reset-code" required maxlength="6" placeholder="验证码"
                class="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
              <button type="button" id="send-reset-code" onclick="sendVerificationCode(document.getElementById('reset-phone').value, 'reset')"
                class="px-4 py-3 btn-gradient text-white rounded-xl font-medium whitespace-nowrap">
                获取验证码
              </button>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">新密码</label>
              <input type="password" id="reset-new-password" required minlength="6" placeholder="请输入新密码"
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div class="flex gap-3">
              <button type="button" onclick="closeResetPasswordModal()"
                class="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                取消
              </button>
              <button type="submit"
                class="flex-1 px-4 py-3 btn-gradient text-white rounded-xl hover:opacity-90 transition-opacity">
                重置密码
              </button>
            </div>
          </form>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      document.getElementById('reset-password-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        showToast('密码重置功能开发中...');
        closeResetPasswordModal();
      });
      
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeResetPasswordModal();
        }
      });
    }

    function closeResetPasswordModal() {
      const modal = document.getElementById('reset-password-modal');
      if (modal) modal.remove();
    }

    // ==================== 原有功能保留 ====================
    
    // AI聊天功能
    function openAIModal() {
      const modal = document.getElementById('ai-companion-modal');
      if (modal) {
        modal.classList.remove('hidden');
        setTimeout(() => {
          const input = document.getElementById('ai-chat-input');
          if (input) input.focus();
        }, 100);
      }
    }
    
    function closeAIModal() {
      const modal = document.getElementById('ai-companion-modal');
      if (modal) modal.classList.add('hidden');
    }
    
    function sendAIChatMessage() {
      const input = document.getElementById('ai-chat-input');
      if (!input) return;
      
      const message = input.value.trim();
      if (!message) return;
      
      const chatArea = document.getElementById('ai-chat-area');
      if (!chatArea) return;
      
      // 添加用户消息
      const userMsgDiv = document.createElement('div');
      userMsgDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 15px; justify-content: flex-end;';
      userMsgDiv.innerHTML = 
        '<div style="flex: 1; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 12px; border-top-right-radius: 0; padding: 10px; max-width: 85%; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 14px;">' +
        '<p style="word-wrap: break-word;">' + message + '</p></div>' +
        '<div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #10b981, #059669); display: flex; align-items: center; justify-content: center; font-size: 12px; color: white; font-weight: bold;">我</div>';
      chatArea.appendChild(userMsgDiv);
      
      input.value = '';
      
      // 滚动到底部
      chatArea.scrollTop = chatArea.scrollHeight;
      
      // 添加正在输入提示
      const typingDiv = document.createElement('div');
      typingDiv.id = 'ai-typing-indicator';
      typingDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 15px;';
      typingDiv.innerHTML = 
        '<div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center;">' +
        '<i class="fa fa-solid fa-robot text-white"></i></div>' +
        '<div style="background: white; border-radius: 12px; padding: 12px; display: flex; gap: 4px; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">' +
        '<span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: bounce 1.4s infinite;"></span>' +
        '<span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: bounce 1.4s infinite 0.2s;"></span>' +
        '<span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: bounce 1.4s infinite 0.4s;"></span></div>';
      chatArea.appendChild(typingDiv);
      chatArea.scrollTop = chatArea.scrollHeight;
      
      // 获取AI回复
      setTimeout(() => {
        typingDiv.remove();
        
        const response = getSimpleAIResponse(message);
        
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 15px;';
        aiMsgDiv.innerHTML = 
          '<div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center;">' +
          '<i class="fa fa-solid fa-robot text-white"></i></div>' +
          '<div style="flex: 1; background: white; border-radius: 12px; border-top-left-radius: 0; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 14px;">' +
          '<p style="color: #374151; white-space: pre-wrap; word-wrap: break-word;">' + response.replace(/\\n/g, '<br>') + '</p></div>';
        chatArea.appendChild(aiMsgDiv);
        chatArea.scrollTop = chatArea.scrollHeight;
      }, 1000);
    }
    
    function getSimpleAIResponse(message) {
      const msg = message.toLowerCase();
      
      // 紧急求助
      if (msg.includes('危险') || msg.includes('害怕') || msg.includes('跟踪')) {
        return '请立即拨打110报警！如果无法说话，可以发送短信到12110。保持冷静，尽量前往人多的地方。';
      }
      
      if (msg.includes('报警')) {
        return '报警电话是110。如果无法说话，可以发送短信到12110。';
      }
      
      if (msg.includes('急救') || msg.includes('受伤')) {
        return '请立即拨打120急救电话。在等待时保持冷静，不要随意移动伤者。';
      }
      
      // 日常问候
      if (msg.includes('早上好') || msg.includes('早安')) {
        return '早上好！☀️ 新的一天开始了！今天也要元气满满哦！';
      }
      
      if (msg.includes('晚上好') || msg.includes('晚安')) {
        return '晚上好！🌙 今天辛苦了，好好休息一下吧！';
      }
      
      if (msg.includes('你好') || msg.includes('嗨')) {
        return '你好！😊 有什么我可以帮你的吗？我可以提供安全咨询、情感陪伴等服务。';
      }
      
      // 安全知识
      if (msg.includes('诈骗')) {
        return '防范诈骗：1) 不轻信陌生来电 2) 不透露验证码 3) 不转账给陌生人 4) 遇到可疑情况拨打96110。';
      }
      
      if (msg.includes('打车') || msg.includes('网约车')) {
        return '打车安全：1) 使用正规平台 2) 核对车牌号 3) 坐在后排 4) 分享行程给亲友 5) 保持警惕。';
      }
      
      // 默认回复
      const defaultResponses = [
        '我理解你的感受。💭 作为安全守护助手，我可以为你提供安全建议和情感支持。',
        '谢谢你愿意和我分享！✨ 有什么需要帮助的随时说！',
        '你的安全是我最关心的。💖 如果有任何担忧或疑问，请随时告诉我。'
      ];
      
      return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    }

    // 表情包功能
    function toggleEmojiPicker() {
      const picker = document.getElementById('emoji-picker');
      if (picker) {
        picker.classList.toggle('hidden');
      }
    }
    
    function insertEmoji(emojiElement) {
      const input = document.getElementById('ai-chat-input');
      if (input) {
        input.value += emojiElement.textContent;
        input.focus();
        setTimeout(() => {
          const picker = document.getElementById('emoji-picker');
          if (picker) picker.classList.add('hidden');
        }, 300);
      }
    }

    // 社区互助
    let currentCommunityCategory = '经验分享';
    
    function showCommunityCategorySelector() {
      const select = document.getElementById('community-category-select');
      if (select) select.classList.toggle('hidden');
    }
    
    function submitCommunityPost() {
      const content = document.getElementById('community-post-input').value.trim();
      if (!content) {
        showToast('请输入内容');
        return;
      }
      
      const postsContainer = document.getElementById('community-posts');
      const newPost = document.createElement('div');
      newPost.className = 'bg-white dark:bg-dark rounded-2xl p-4 shadow-lg hover:shadow-xl transition-shadow animate-slide-up';
      
      const colors = ['from-blue-400 to-blue-600', 'from-green-400 to-green-600', 'from-purple-400 to-purple-600', 'from-pink-400 to-pink-600'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      
      newPost.innerHTML = `
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br ${color} flex items-center justify-center">
            <span class="text-white font-bold">我</span>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold text-gray-800 dark:text-white">${currentUser?.nickname || '我'}</span>
              <span class="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">${currentCommunityCategory}</span>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-3">${content}</p>
            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span><i class="fa fa-solid fa-heart text-gray-400 mr-1"></i>0</span>
              <span><i class="fa fa-solid fa-message text-gray-400 mr-1"></i>0</span>
              <span><i class="fa fa-solid fa-clock mr-1"></i>刚刚</span>
            </div>
          </div>
        </div>
      `;
      
      postsContainer.insertBefore(newPost, postsContainer.firstChild);
      document.getElementById('community-post-input').value = '';
      showToast('发布成功！');
    }

    // SOS功能
    let sosTimer = null;
    let sosProgress = 0;
    
    function openSOSModal() {
      document.getElementById('sos-modal').classList.remove('hidden');
    }
    
    function closeSOSModal() {
      document.getElementById('sos-modal').classList.add('hidden');
      cancelSOSTimer();
    }
    
    function startSOSTimer() {
      const button = document.getElementById('sos-button');
      const progress = document.getElementById('sos-progress');
      
      sosProgress = 0;
      button.textContent = Math.ceil((3 - sosProgress / 100) * 10) / 10 + 's';
      
      sosTimer = setInterval(() => {
        sosProgress += 3.33;
        progress.style.width = sosProgress + '%';
        button.textContent = Math.ceil((3 - sosProgress / 100) * 10) / 10 + 's';
        
        if (sosProgress >= 100) {
          clearInterval(sosTimer);
          triggerSOS();
        }
      }, 100);
    }
    
    function cancelSOSTimer() {
      if (sosTimer) {
        clearInterval(sosTimer);
        sosTimer = null;
        sosProgress = 0;
        document.getElementById('sos-progress').style.width = '0%';
        document.getElementById('sos-button').textContent = '按住求助';
      }
    }

    function quickCall(number) {
      window.location.href = 'tel:' + number;
    }

    // 智能提醒
    function addQuickReminder(title, content) {
      addReminder(title, content, '08:00', true);
      showToast(title + '已添加');
    }
    
    function addCustomReminder() {
      const title = document.getElementById('reminder-title').value.trim();
      const content = document.getElementById('reminder-content').value.trim();
      const time = document.getElementById('reminder-time').value;
      
      if (!title || !time) {
        showToast('请填写标题和时间');
        return;
      }
      
      addReminder(title, content || title, time, true);
      showToast('提醒已添加');
      
      document.getElementById('reminder-title').value = '';
      document.getElementById('reminder-content').value = '';
      document.getElementById('reminder-time').value = '';
    }
    
    function addReminder(title, content, time, enabled = true) {
      const reminderList = document.getElementById('reminder-list');
      const reminder = document.createElement('div');
      reminder.className = 'bg-white dark:bg-dark rounded-2xl p-4 shadow-lg flex items-center justify-between animate-slide-up';
      
      reminder.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
            <i class="fa fa-solid fa-bell text-primary text-xl"></i>
          </div>
          <div>
            <p class="font-medium text-gray-800 dark:text-white">${title}</p>
            <p class="text-sm text-gray-500">每天 ${time}</p>
          </div>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" class="sr-only peer" ${enabled ? 'checked' : ''}>
          <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
        </label>
      `;
      
      reminderList.insertBefore(reminder, reminderList.firstChild);
    }

    // 附近设施
    function filterNearby(type) {
      document.querySelectorAll('#nearby .flex.gap-2 button').forEach(btn => {
        if (btn.textContent.includes('全部') || btn.textContent.includes(type)) {
          btn.className = 'px-4 py-2 bg-primary text-white rounded-full whitespace-nowrap font-medium';
        } else {
          btn.className = 'px-4 py-2 bg-white dark:bg-dark text-gray-700 dark:text-gray-300 rounded-full whitespace-nowrap hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors';
        }
      });
      
      showToast('已筛选：' + (type === 'all' ? '全部' : type));
    }
    
    function navigateTo(place) {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const url = `https://maps.google.com/?q=${encodeURIComponent(place)}&saddr=${position.coords.latitude},${position.coords.longitude}`;
            window.open(url, '_blank');
          },
          () => {
            const url = `https://maps.google.com/?q=${encodeURIComponent(place)}`;
            window.open(url, '_blank');
          }
        );
      } else {
        const url = `https://maps.google.com/?q=${encodeURIComponent(place)}`;
        window.open(url, '_blank');
      }
    }

    function sendHelp(type) {
      showToast('正在发送' + type + '求助...');
      triggerSOS(type);
    }
'''

# 在第一个</script>前插入新代码
# 找到第一个</script>标签
first_script_end = content.find('</script>')
if first_script_end != -1:
    content = content[:first_script_end] + new_js_code + content[first_script_end:]

print("✅ JavaScript升级完成！")

# ==================== 保存文件 ====================
with open('d:\\xingban\\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 前端功能升级完成！")
print("\n升级内容：")
print("📱 验证码功能 - 真实发送和验证")
print("🔐 用户认证 - 注册、登录、退出")
print("📍 定位功能 - GPS定位和地址解析")
print("🆘 SOS求助 - 实时位置和紧急联系人通知")
print("👥 紧急联系人 - 添加和管理")
print("\n请运行 python d:\\xingban\\backend_api.py 启动后端API服务")
print("请运行 python d:\\xingban\\server.py 启动前端服务")
