# 部署指南

## 静态网页部署

### 方法一：GitHub Pages

1. **创建GitHub仓库**
   - 登录GitHub，创建一个新的仓库
   - 仓库名称可以是 `xingban-app` 或其他名称

2. **上传文件**
   - 将以下文件上传到仓库根目录：
     - `index.html`
     - `manifest.json`
     - `service-worker.js`

3. **启用GitHub Pages**
   - 进入仓库设置 → Pages
   - 选择 `main` 分支，点击 "Save"
   - 等待几分钟，GitHub Pages会生成一个URL，例如 `https://username.github.io/xingban-app`

### 方法二：Vercel

1. **登录Vercel**
   - 访问 https://vercel.com，使用GitHub账号登录

2. **导入项目**
   - 点击 "New Project"
   - 选择刚才创建的GitHub仓库
   - 点击 "Import"

3. **部署**
   - 保持默认设置，点击 "Deploy"
   - 部署完成后，Vercel会生成一个URL，例如 `https://xingban-app.vercel.app`

### 方法三：Netlify

1. **登录Netlify**
   - 访问 https://www.netlify.com，使用GitHub账号登录

2. **添加新站点**
   - 点击 "Add new site" → "Import an existing project"
   - 选择刚才创建的GitHub仓库

3. **部署**
   - 保持默认设置，点击 "Deploy site"
   - 部署完成后，Netlify会生成一个URL，例如 `https://xingban-app.netlify.app`

## APK打包方法

### 方法一：使用在线APK打包工具

1. **访问在线APK打包工具**
   - 推荐使用：https://apkbuilder.net/
   - 或：https://www.appypie.com/

2. **上传文件**
   - 上传 `index.html` 文件
   - 填写应用名称、图标等信息

3. **生成APK**
   - 点击 "Build APK" 或类似按钮
   - 等待生成完成，下载APK文件

### 方法二：使用PhoneGap Build

1. **访问PhoneGap Build**
   - 访问 https://build.phonegap.com/
   - 使用GitHub账号登录

2. **创建新应用**
   - 点击 "New App"
   - 选择 "GitHub" 并连接到刚才创建的仓库

3. **构建应用**
   - 点击 "Build" 按钮
   - 等待构建完成，下载APK文件

### 方法三：使用Cordova（本地）

1. **安装Cordova**
   ```bash
   npm install -g cordova
   ```

2. **创建Cordova项目**
   ```bash
   cordova create xingban-app
   cd xingban-app
   ```

3. **替换文件**
   - 将 `index.html`、`manifest.json` 和 `service-worker.js` 复制到 `www` 目录

4. **添加Android平台**
   ```bash
   cordova platform add android
   ```

5. **构建APK**
   ```bash
   cordova build android
   ```
   - 生成的APK文件位于 `platforms/android/app/build/outputs/apk/debug/app-debug.apk`

## 测试账号

- 手机号：12345678910
- 密码：123456

## 功能说明

- **登录注册**：支持测试账号登录和新用户注册
- **安全指数**：显示详细的安全指标和个性化安全建议
- **紧急求助**：一键求助功能，可联系紧急联系人
- **位置共享**：分享实时位置给亲友
- **AI陪伴**：智能聊天功能，提供安全建议和情感支持
- **情绪日记**：记录和管理情绪
- **安全演练**：多种场景的安全模拟
- **个人资料**：编辑头像、昵称等个人信息

## 注意事项

- 所有数据存储在本地浏览器的localStorage中，保证隐私安全
- 应用是完全静态的，不需要任何后端服务器
- 响应式设计，适配各种设备屏幕
- 支持离线使用（PWA功能）