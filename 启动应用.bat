@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   星伴守护 - 一键启动
echo ========================================
echo.

:: 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.x
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

:: 启动统一服务器
echo.
echo 正在启动星伴守护服务...
echo.
start "星伴守护服务" python server.py

:: 等待3秒
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo   🎉 服务已启动！
echo ========================================
echo.
echo 📱 访问地址：
echo    本地访问: http://127.0.0.1:8082
echo.
echo 📋 测试账号：
echo    手机号: 13188393081
echo    密码:   123456
echo.
echo 按任意键打开浏览器...
pause > nul

:: 打开浏览器
start http://127.0.0.1:8082

echo.
echo ✅ 浏览器已打开！
echo.
pause