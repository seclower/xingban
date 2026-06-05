# 星伴守护 - 快速开始指南

## 🚀 快速启动

### 方法一：一键启动（推荐）
双击运行 `启动全部服务.bat`，会自动启动：
- 前端服务：http://127.0.0.1:8082
- 后端服务：http://127.0.0.1:5000

### 方法二：单独启动
```bash
# 1. 启动后端
python backend/app.py

# 2. 新开终端，启动前端
python server.py
```

### 方法三：仅启动前端（使用模拟数据）
```bash
python server.py
```
前端会自动运行，但部分功能需要真实API。

## 📱 访问应用
打开浏览器访问：http://127.0.0.1:8082

## 🔐 测试账号
- 手机号：13188393081
- 密码：123456

## ⚙️ 配置说明

### 1. 环境变量配置
复制 `.env.example` 为 `.env` 并配置：

```bash
# 必需
SECRET_KEY=your-secret-key

# DeepSeek API（AI聊天功能）
DEEPSEEK_API_KEY=your-api-key

# 阿里云短信（可选）
ALIYUN_ACCESS_KEY_ID=your-key-id
ALIYUN_ACCESS_KEY_SECRET=your-secret
```

### 2. 获取 DeepSeek API Key
1. 访问 https://platform.deepseek.com
2. 注册账号并登录
3. 创建 API Key
4. 将 Key 填入 `.env` 文件

### 3. 阿里云短信配置（可选）
如需真实短信功能：
1. 开通阿里云短信服务
2. 申请签名和模板
3. 配置 AccessKey

## 📂 项目结构

```
xingban/
├── backend/
│   └── app.py              # Flask后端应用
├── www/
│   ├── index.html          # 前端主页面
│   ├── manifest.json       # PWA配置
│   └── service-worker.js   # 离线支持
├── server.py              # 前端服务器
├── requirements.txt        # Python依赖
├── .env.example          # 环境变量示例
├── .gitignore            # Git忽略配置
├── README.md             # 项目说明
├── 启动全部服务.bat       # 一键启动脚本
└── safety_guard.db       # SQLite数据库
```

## 🛠️ 技术栈

- **前端**：HTML5 + CSS3 + JavaScript + Tailwind CSS
- **后端**：Python + Flask
- **数据库**：SQLite
- **API**：DeepSeek AI

## 🔧 常见问题

### 1. 端口被占用
如果8082或5000端口被占用，修改：
- `server.py` 中的 `PORT = 8082`
- `backend/app.py` 中的 `app.run(port=5000)`

### 2. AI聊天不工作
检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确配置。

### 3. 数据库错误
删除 `safety_guard.db` 文件，重新启动服务会自动创建。

### 4. 依赖安装失败
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 🌐 云端部署

详见项目根目录的部署文档，或访问：
- [Heroku部署指南](./DEPLOY_HEROKU.md)
- [Railway部署指南](./DEPLOY_RAILWAY.md)

## 📞 支持

如遇问题，请检查：
1. Python版本（需要3.7+）
2. 所有依赖是否安装成功
3. 端口是否被占用
4. 环境变量是否配置正确

---

**保持警惕，守护安全** 🌟
