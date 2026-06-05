@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   安全守护APP - 一键启动
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

:: 启动后端API服务
echo.
echo 正在启动后端API服务（端口8083）...
start "Backend API" python backend_api.py

:: 等待2秒
timeout /t 2 /nobreak > nul

:: 启动前端服务
echo 正在启动前端服务（端口8082）...
start "Frontend Server" python server.py

:: 等待2秒
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo   🎉 所有服务已启动！
echo ========================================
echo.
echo 📱 访问地址：
echo    本地访问: http://127.0.0.1:8082
echo    局域网:  http://10.153.67.65:8082
echo.
echo 📋 测试账号：
echo    手机号: 13188393081
echo    密码:   123456
echo.
echo 📄 详细文档: 功能完善总结.md
echo.
echo 按任意键打开浏览器...
pause > nul

:: 打开浏览器
start http://127.0.0.1:8082

echo.
echo ✅ 浏览器已打开！
echo.
pause
