# 测试账号数据与生成APK操作说明

## 一、测试账号数据

### 1. 测试账号信息
- 手机号：12345678910
- 密码：123456

### 2. 已添加的模拟数据

#### 紧急联系人
- 家人：13800138001
- 朋友：13900139001
- 同事：13700137001

#### 情绪日记
1. **开心**：今天完成了安全演练，感觉很有收获。学习了打车安全和独居防护的知识，对自己的安全更有信心了。
2. **一般**：今天工作有点累，但安全指数保持良好。使用了位置共享功能，让家人知道我的位置，感觉更安全了。
3. **焦虑**：今天晚上要加班到很晚，有点担心回家的安全。已经设置了紧急联系人，开启了位置共享，希望一切顺利。
4. **开心**：今天和朋友一起参加了安全知识讲座，学到了很多实用的安全技巧。回家的路上使用了app的安全功能，感觉很安心。
5. **一般**：今天天气不好，下雨了。出门时使用了app的路线分析功能，选择了安全的路线，避免了积水和拥堵的区域。

#### 安全演练记录
- 打车安全模拟（已完成）
- 独居防护演练（已完成）
- 社交安全模拟（已完成）

#### 安全日志
- 安全提醒：本周有3次夜间独自出行记录，请注意选择明亮路线。
- 预警信息：检测到您最近进入了一个偏僻区域，建议开启实时位置共享。

## 二、生成APK操作说明

### 1. 所需工具

#### （1）前端构建工具
- Node.js（推荐v16+）
- npm或yarn
- Vite（用于构建前端代码）

#### （2）Android开发工具
- Android Studio（最新版本）
- JDK 11或更高版本
- Android SDK（API级别31+）

#### （3）WebView包装工具
- Capacitor（推荐）或Cordova

### 2. 生成APK的步骤

#### 步骤1：构建前端代码

1. **初始化前端项目**（如果尚未初始化）
   ```bash
   # 在d:\xingban目录下执行
   npm init -y
   ```

2. **安装Vite**
   ```bash
   npm install --save-dev vite
   ```

3. **创建vite.config.js文件**
   ```js
   // vite.config.js
   export default {
     base: './',
     build: {
       outDir: 'dist',
       assetsDir: 'assets'
     }
   }
   ```

4. **修改package.json**
   ```json
   {
     "scripts": {
       "build": "vite build"
     }
   }
   ```

5. **构建前端代码**
   ```bash
   npm run build
   ```
   构建完成后，会在`dist`目录生成优化后的前端代码。

#### 步骤2：使用Capacitor包装为Android应用

1. **安装Capacitor**
   ```bash
   npm install @capacitor/core @capacitor/cli
   ```

2. **初始化Capacitor**
   ```bash
   npx cap init
   ```
   按照提示填写应用名称和包名（如com.safetyapp.app）。

3. **安装Android平台**
   ```bash
   npx cap add android
   ```

4. **复制前端构建文件到Capacitor**
   ```bash
   npx cap sync
   ```

5. **打开Android Studio**
   ```bash
   npx cap open android
   ```

#### 步骤3：配置Android项目

1. **在Android Studio中打开项目**
   项目路径：`d:\xingban\android`

2. **配置权限**
   在`AndroidManifest.xml`中添加所需权限：
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
   <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
   <uses-permission android:name="android.permission.RECORD_AUDIO" />
   <uses-permission android:name="android.permission.SEND_SMS" />
   <uses-permission android:name="android.permission.CALL_PHONE" />
   ```

3. **配置WebView设置**
   在`MainActivity.java`中配置WebView，确保它能正确加载本地HTML文件。

#### 步骤4：生成APK

1. **构建APK**
   在Android Studio中，选择`Build` > `Build Bundle(s) / APK(s)` > `Build APK(s)`。

2. **查找生成的APK**
   生成的APK文件位于：`d:\xingban\android\app\build\outputs\apk\debug\app-debug.apk`

3. **测试APK**
   将APK安装到Android设备上进行测试。

### 3. 替代方案：使用WebView应用生成器

如果不想使用Capacitor，也可以使用在线WebView应用生成器，如：

- **AppYet**：https://www.appyet.com/
- **WebViewGold**：https://www.webviewgold.com/
- **AppsGeyser**：https://www.appsgeyser.com/

这些工具允许你上传前端代码，然后生成APK文件，操作更简单但功能可能有限。

### 4. 注意事项

1. **网络请求**：如果应用需要访问后端API，确保API地址是可公开访问的，或者在Android设备上使用相同的网络环境。

2. **权限配置**：确保在AndroidManifest.xml中添加了所有必要的权限，否则某些功能可能无法正常工作。

3. **WebView设置**：确保WebView启用了JavaScript和本地存储，否则应用可能无法正常运行。

4. **测试**：在生成最终APK之前，在Android设备上进行充分测试，确保所有功能都能正常工作。

5. **签名**：如果要发布到Google Play Store，需要对APK进行签名。

## 三、技术支持

如果在生成APK过程中遇到问题，可以参考以下资源：

- [Capacitor官方文档](https://capacitorjs.com/docs)
- [Android开发者文档](https://developer.android.com/docs)
- [Vite官方文档](https://vitejs.dev/docs)

或者联系专业的移动应用开发人员寻求帮助。