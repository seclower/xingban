@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   星伴守护 - Heroku一键部署
echo ========================================
echo.

:: 检查Heroku CLI是否安装
heroku --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Heroku CLI未安装
    echo.
    echo 请先安装Heroku CLI:
    echo 下载地址: https://cli-assets.heroku.com/heroku-x64.exe
    echo 或使用命令: winget install Heroku.CLI
    pause
    exit /b 1
)
echo ✅ Heroku CLI已安装

:: 登录Heroku
echo.
echo 正在登录Heroku...
heroku login
if errorlevel 1 (
    echo ❌ 登录失败
    pause
    exit /b 1
)
echo ✅ 登录成功

:: 创建应用名称
set "APP_NAME=xingban-guard-%date:~0,4%%date:~5,2%%date:~8,2%"

:: 创建应用
echo.
echo 正在创建应用...
heroku create %APP_NAME%
if errorlevel 1 (
    echo ❌ 创建应用失败
    pause
    exit /b 1
)
echo ✅ 应用创建成功

:: 配置环境变量
echo.
echo 正在配置环境变量...
heroku config:set DEEPSEEK_API_KEY=sk-3e2ae11bbc9a41398f0eac1b9ce7f063
heroku config:set SECRET_KEY=xingban-safety-guard-2024-secret
heroku config:set FLASK_ENV=production
echo ✅ 环境变量配置完成

:: 部署应用
echo.
echo 正在部署应用...
git add .
git commit -m "Deploy to Heroku"
git push heroku master
if errorlevel 1 (
    echo ❌ 部署失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   部署完成！🎉
echo ========================================
echo.
echo 访问地址: https://%APP_NAME%.herokuapp.com
echo.
echo 管理面板: https://dashboard.heroku.com/apps/%APP_NAME%
echo.
echo 测试账号: 13188393081 / 123456
echo.
echo 提示:
echo   - Heroku免费额度: 550小时/月
echo   - 应用30分钟无访问会自动休眠
echo   - 需要保持在线可使用Heroku Scheduler
echo.
pause