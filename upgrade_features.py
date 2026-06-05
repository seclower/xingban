# 功能升级脚本 - 让功能更贴近现实生活

import re

# 读取文件
with open('d:\\xingban\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ==================== 1. 升级AI聊天功能 - 添加真实场景回复 ====================

ai_upgrade = '''
  // ==================== 增强版AI聊天 - 更贴近现实 ====================
  function getSimpleAIResponse(message) {
    const msg = message.toLowerCase();
    
    // ==================== 真实生活场景 ====================
    
    // 日常问候
    if (msg.includes('早上好') || msg.includes('早安')) {
      const responses = [
        '早上好！☀️ 今天天气不错，记得出门带伞哦！',
        '早安！新的一天开始了，祝你今天心情愉快！',
        '早上好！记得吃早餐，保持好状态！',
        '早安朋友！今天也要元气满满哦！💪'
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    
    if (msg.includes('中午好') || msg.includes('午安')) {
      return '中午好！🍛 该吃午饭了，记得好好休息一下！';
    }
    
    if (msg.includes('晚上好') || msg.includes('晚安')) {
      const responses = [
        '晚上好！🌙 今天辛苦了，好好放松一下吧！',
        '晚安！早点休息，明天又是美好的一天！',
        '晚上好！记得护肤，保持美丽！💅'
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    
    if (msg.includes('吃饭') || msg.includes('饿了')) {
      const foods = ['火锅', '烧烤', '麻辣烫', '寿司', '披萨', '汉堡'];
      const food = foods[Math.floor(Math.random() * foods.length)];
      return `饿了就去吃点东西吧！推荐试试${food}，很好吃的！🍽️`;
    }
    
    if (msg.includes('喝水') || msg.includes('口渴')) {
      return '记得多喝水！💧 每天喝够8杯水对身体好哦！';
    }
    
    if (msg.includes('睡觉') || msg.includes('困了')) {
      return '困了就休息一下吧！😴 充足的睡眠很重要！';
    }
    
    if (msg.includes('加油') || msg.includes('努力')) {
      const responses = [
        '加油！你一定可以的！💪',
        '相信自己，你很棒！🌟',
        '坚持就是胜利！你已经很棒了！',
        '努力不会白费的，继续加油！🔥'
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // ==================== 真实安全场景 ====================
    
    if (msg.includes('一个人') && msg.includes('回家')) {
      return '一个人回家要注意安全！⚠️ 建议：\\n1) 走明亮人多的路线\\n2) 保持手机畅通\\n3) 告诉家人你的行程\\n4) 遇到可疑人员及时报警';
    }
    
    if (msg.includes('打车') || msg.includes('滴滴') || msg.includes('网约车')) {
      return '打车安全小贴士：\\n1) 使用正规打车平台\\n2) 核对车牌号和车型\\n3) 分享行程给亲友\\n4) 坐在后排更安全\\n5) 夜间尽量结伴出行';
    }
    
    if (msg.includes('地铁') || msg.includes('公交')) {
      return '公共交通安全：\\n1) 注意保管随身物品\\n2) 避免拥挤时露财\\n3) 遇到骚扰及时求助工作人员\\n4) 关注站台间隙';
    }
    
    if (msg.includes('外卖') || msg.includes('送餐')) {
      return '外卖安全提醒：\\n1) 核对订单信息\\n2) 尽量选择正规商家\\n3) 收货时检查包装是否完好\\n4) 不随意透露详细住址';
    }
    
    if (msg.includes('网购') || msg.includes('快递')) {
      return '网购安全：\\n1) 不点击可疑链接\\n2) 保护个人信息\\n3) 选择正规平台\\n4) 快递地址可填写驿站';
    }
    
    if (msg.includes('电话') && (msg.includes('诈骗') || msg.includes('骚扰'))) {
      return '防范电信诈骗：\\n1) 不透露验证码\\n2) 不轻信中奖信息\\n3) 公检法不会电话办案\\n4) 可疑来电挂掉后拨打96110';
    }
    
    // ==================== 真实情绪场景 ====================
    
    if (msg.includes('无聊') || msg.includes('没意思')) {
      const activities = ['看一部喜欢的电影', '听喜欢的音乐', '出门散散步', '和朋友聊聊天', '做点喜欢的美食'];
      const activity = activities[Math.floor(Math.random() * activities.length)];
      return `无聊吗？可以试试${activity}，让生活更有趣！🎨`;
    }
    
    if (msg.includes('压力') || msg.includes('累')) {
      return '压力大的时候要学会放松：\\n1) 深呼吸练习\\n2) 做一些喜欢的事情\\n3) 和朋友家人倾诉\\n4) 适当运动释放压力';
    }
    
    if (msg.includes('失恋') || msg.includes('分手')) {
      return '失恋确实很痛苦，但这不是终点！💔 时间会治愈一切，好好爱自己，未来会更好！';
    }
    
    if (msg.includes('考试') || msg.includes('学习')) {
      return '考试加油！📚 复习建议：\\n1) 制定学习计划\\n2) 重点突破薄弱环节\\n3) 保持充足睡眠\\n4) 相信自己的努力';
    }
    
    // ==================== 真实健康场景 ====================
    
    if (msg.includes('感冒') || msg.includes('发烧') || msg.includes('生病')) {
      return '生病了要好好照顾自己！🤒\\n1) 多喝温水\\n2) 注意休息\\n3) 按时吃药\\n4) 严重的话及时就医';
    }
    
    if (msg.includes('减肥') || msg.includes('健身')) {
      return '健身减肥小贴士：\\n1) 合理饮食比运动更重要\\n2) 循序渐进不要急\\n3) 结合有氧和力量训练\\n4) 保持良好心态';
    }
    
    if (msg.includes('皮肤') || msg.includes('护肤')) {
      return '护肤建议：\\n1) 每天清洁保湿\\n2) 坚持防晒\\n3) 多喝水保持水润\\n4) 选择适合自己的护肤品';
    }
    
    // ==================== 真实社交场景 ====================
    
    if (msg.includes('朋友') || msg.includes('闺蜜') || msg.includes('兄弟')) {
      return '朋友是人生的财富！👭 记得常联系，珍惜这份情谊！';
    }
    
    if (msg.includes('家人') || msg.includes('爸妈') || msg.includes('父母')) {
      return '家人永远是最支持你的人！👨👩👧👦 常回家看看，多陪陪他们！';
    }
    
    if (msg.includes('约会') || msg.includes('相亲')) {
      return '约会小贴士：\\n1) 提前做好准备\\n2) 保持礼貌和微笑\\n3) 多倾听对方\\n4) 自然就好，不要紧张！';
    }
    
    // ==================== 默认回复 ====================
    const defaultResponses = [
      '我在这里听你倾诉！💕 无论是什么都可以聊哦！',
      '嗯，我理解你的感受！😊 需要我帮你分析一下吗？',
      '谢谢你愿意和我分享！✨ 有什么需要帮助的随时说！',
      '生活总有起伏，但你不是一个人！🤗',
      '你的安全和快乐是我最关心的！💖',
      '今天过得怎么样？🌈 有没有什么有趣的事情？'
    ];
    
    return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
  }
'''

# 替换旧的AI聊天函数
pattern = r'function getSimpleAIResponse\(message\).*?^  \}'
match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
if match:
    content = content.replace(match.group(0), ai_upgrade.strip())
    print("✅ AI聊天功能已升级")

# ==================== 2. 升级社区互助 - 添加真实社区内容 ====================

community_upgrade = '''
  <!-- 社区互助页面 -->
  <div id="community" class="hidden p-4">
    <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-6 text-gradient">社区互助</h2>
    
    <!-- 发帖区域 -->
    <div class="bg-white dark:bg-dark rounded-2xl p-4 shadow-lg mb-6 premium-card">
      <textarea id="community-post-input" placeholder="分享你的安全经验、求助问题或生活感悟..." 
                class="w-full p-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-white resize-none outline-none focus:ring-2 focus:ring-primary transition-all"
                rows="3"></textarea>
      <div class="flex items-center justify-between mt-3">
        <select id="community-category-select" class="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm">
          <option value="经验分享">🌟 经验分享</option>
          <option value="求助咨询">🙋 求助咨询</option>
          <option value="安全提示">⚠️ 安全提示</option>
          <option value="生活感悟">💭 生活感悟</option>
          <option value="活动组织">🎉 活动组织</option>
        </select>
        <button onclick="submitCommunityPost()" class="px-6 py-2 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:opacity-90 transition-opacity font-medium gradient-btn ripple">
          <i class="fa-solid fa-paper-plane mr-1"></i>发布
        </button>
      </div>
    </div>
    
    <!-- 热门话题 -->
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">🔥 热门话题</h3>
      <div class="flex flex-wrap gap-2">
        <span class="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-300 rounded-full text-sm cursor-pointer hover:bg-red-200">夜间出行安全</span>
        <span class="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 rounded-full text-sm cursor-pointer hover:bg-blue-200">防诈骗技巧</span>
        <span class="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-300 rounded-full text-sm cursor-pointer hover:bg-green-200">心理健康</span>
        <span class="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300 rounded-full text-sm cursor-pointer hover:bg-purple-200">女性安全</span>
        <span class="px-3 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-300 rounded-full text-sm cursor-pointer hover:bg-orange-200">网络安全</span>
      </div>
    </div>
    
    <!-- 帖子列表 -->
    <div id="community-posts" class="space-y-4">
      <!-- 帖子1 -->
      <div class="bg-white dark:bg-dark rounded-2xl p-4 shadow-lg hover:shadow-xl transition-shadow premium-card">
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
            <span class="text-white font-bold">李</span>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold text-gray-800 dark:text-white">李明</span>
              <span class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 text-xs rounded">🌟 经验分享</span>
            </div>
            <h4 class="font-medium text-gray-800 dark:text-white mb-2">昨晚遇到跟踪，分享一下我的应对方法</h4>
            <p class="text-gray-600 dark:text-gray-300 text-sm">昨天加班到很晚，在地铁站遇到一个可疑男子一直跟着我。我当时很害怕，但还是保持冷静，做了这几件事...（详情）</p>
            <div class="flex items-center gap-4 text-sm text-gray-500 mt-3">
              <span><i class="fa-solid fa-thumbs-up text-red-500 mr-1"></i>23</span>
              <span><i class="fa-solid fa-message-circle text-blue-500 mr-1"></i>5</span>
              <span><i class="fa-solid fa-eye mr-1"></i>128</span>
              <span><i class="fa-solid fa-clock mr-1"></i>2小时前</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 帖子2 -->
      <div class="bg-white dark:bg-dark rounded-2xl p-4 shadow-lg hover:shadow-xl transition-shadow premium-card">
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-pink-400 to-pink-600 flex items-center justify-center">
            <span class="text-white font-bold">王</span>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold text-gray-800 dark:text-white">王芳</span>
              <span class="px-2 py-0.5 bg-orange-100 dark:bg-orange-900 text-orange-600 dark:text-orange-300 text-xs rounded">🙋 求助咨询</span>
            </div>
            <h4 class="font-medium text-gray-800 dark:text-white mb-2">求推荐女生防身工具</h4>
            <p class="text-gray-600 dark:text-gray-300 text-sm">最近经常加班晚归，想准备一些防身用品。大家有没有什么好的推荐？最好是方便携带的那种，谢谢！</p>
            <div class="flex items-center gap-4 text-sm text-gray-500 mt-3">
              <span><i class="fa-solid fa-thumbs-up text-red-500 mr-1"></i>45</span>
              <span><i class="fa-solid fa-message-circle text-blue-500 mr-1"></i>12</span>
              <span><i class="fa-solid fa-eye mr-1"></i>256</span>
              <span><i class="fa-solid fa-clock mr-1"></i>5小时前</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 帖子3 -->
      <div class="bg-white dark:bg-dark rounded-2xl p-4 shadow-lg hover:shadow-xl transition-shadow premium-card">
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
            <span class="text-white font-bold">张</span>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold text-gray-800 dark:text-white">张医生</span>
              <span class="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300 text-xs rounded">⚠️ 安全提示</span>
            </div>
            <h4 class="font-medium text-gray-800 dark:text-white mb-2">夏季高温安全提醒</h4>
            <p class="text-gray-600 dark:text-gray-300 text-sm">夏季高温天气，请注意防暑降温！特别是户外工作的朋友们，一定要做好防护措施...</p>
            <div class="flex items-center gap-4 text-sm text-gray-500 mt-3">
              <span><i class="fa-solid fa-thumbs-up text-red-500 mr-1"></i>89</span>
              <span><i class="fa-solid fa-message-circle text-blue-500 mr-1"></i>8</span>
              <span><i class="fa-solid fa-eye mr-1"></i>423</span>
              <span><i class="fa-solid fa-clock mr-1"></i>昨天</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
'''

# 替换旧的社区页面
content = content.replace('<!-- 社区互助页面 -->', community_upgrade)
print("✅ 社区互助功能已升级")

# ==================== 3. 升级SOS功能 - 添加真实紧急场景 ====================

sos_upgrade = '''
  <!-- SOS紧急求助功能 -->
  <div id="sos-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[70] hidden">
    <div class="bg-white dark:bg-gray-900 rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl text-center premium-modal">
      <div class="w-24 h-24 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse glow-effect">
        <span class="text-white text-4xl font-bold">SOS</span>
      </div>
      <h3 class="text-2xl font-bold text-gray-800 dark:text-white mb-4">紧急求助</h3>
      <p class="text-gray-600 dark:text-gray-300 mb-6">按住按钮3秒将发送求助信息给紧急联系人</p>
      
      <!-- 紧急状态显示 -->
      <div class="flex items-center justify-center gap-2 mb-6">
        <span class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
        <span class="text-sm text-gray-500">定位中...</span>
      </div>
      
      <div class="relative mb-6">
        <button id="sos-button" 
                class="w-32 h-32 bg-gradient-to-br from-red-500 to-red-600 rounded-full text-white font-bold text-xl shadow-lg mx-auto relative overflow-hidden gradient-btn"
                onmousedown="startSOSTimer()"
                onmouseup="cancelSOSTimer()"
                onmouseleave="cancelSOSTimer()"
                ontouchstart="startSOSTimer()"
                ontouchend="cancelSOSTimer()">
          <div id="sos-progress" class="absolute inset-0 bg-red-700 rounded-full" style="width: 0%; transition: width 0.1s;"></div>
          <span class="relative z-10">按住求助</span>
        </button>
      </div>
      
      <div class="grid grid-cols-3 gap-4 mb-6">
        <button onclick="quickCall('110')" class="p-4 bg-red-50 dark:bg-red-900/20 rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors">
          <i class="fa-solid fa-phone text-red-500 text-2xl mb-2"></i>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">报警</p>
          <p class="text-xs text-gray-500">110</p>
        </button>
        <button onclick="quickCall('120')" class="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors">
          <i class="fa-solid fa-ambulance text-orange-500 text-2xl mb-2"></i>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">急救</p>
          <p class="text-xs text-gray-500">120</p>
        </button>
        <button onclick="quickCall('119')" class="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors">
          <i class="fa-solid fa-fire-flame-curved text-yellow-500 text-2xl mb-2"></i>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">火警</p>
          <p class="text-xs text-gray-500">119</p>
        </button>
      </div>
      
      <!-- 快捷求助 -->
      <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-6">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">快捷求助</h4>
        <div class="grid grid-cols-2 gap-2">
          <button onclick="sendHelp('家庭暴力')" class="px-3 py-2 bg-purple-100 dark:bg-purple-900/20 text-purple-600 dark:text-purple-300 rounded-lg text-sm">
            🏠 家庭暴力
          </button>
          <button onclick="sendHelp('跟踪骚扰')" class="px-3 py-2 bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300 rounded-lg text-sm">
            👤 跟踪骚扰
          </button>
          <button onclick="sendHelp('交通事故')" class="px-3 py-2 bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-300 rounded-lg text-sm">
            🚗 交通事故
          </button>
          <button onclick="sendHelp('突发疾病')" class="px-3 py-2 bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-300 rounded-lg text-sm">
            💊 突发疾病
          </button>
        </div>
      </div>
      
      <button onclick="closeSOSModal()" class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
        取消
      </button>
    </div>
  </div>
'''

# 替换旧的SOS模态框
content = content.replace('<!-- SOS紧急求助功能 -->', sos_upgrade)
print("✅ SOS紧急求助功能已升级")

# ==================== 保存文件 ====================
with open('d:\\xingban\\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 功能升级完成！")
print("\n升级内容：")
print("🤖 AI聊天功能")
print("  - 添加了真实生活场景回复")
print("  - 日常问候、安全场景、情绪支持")
print("  - 更贴近现实生活")

print("\n👥 社区互助功能")
print("  - 添加了热门话题标签")
print("  - 更新了真实社区帖子内容")
print("  - 添加了浏览量显示")

print("\n🆘 SOS紧急求助")
print("  - 添加了定位状态显示")
print("  - 添加了快捷求助按钮")
print("  - 更真实的紧急场景")

print("\n文件已保存！")
