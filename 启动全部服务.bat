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
    echo [错误] 未找到Python，请先安装Python 3.x
    pause
    exit /b 1
)

echo [OK] Python环境检查通过

:: 启动后端服务
echo.
echo [启动中] 正在启动后端服务...
start "星伴守护-后端服务" python backend/app.py

:: 等待后端启动
echo [等待] 等待后端服务启动...
timeout /t 5 /nobreak > nul

:: 启动前端服务
echo [启动中] 正在启动前端服务...
start "星伴守护-前端服务" python server.py

:: 等待前端启动
echo [等待] 等待前端服务启动...
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo   启动成功！
echo ========================================
echo.
echo 访问地址：
echo   前端页面: http://127.0.0.1:8082
echo   后端API:  http://127.0.0.1:5000
echo.
echo 测试账号：
echo   手机号: 13188393081
echo   密码:   123456
echo.
echo 按任意键打开浏览器...
pause > nul

:: 打开浏览器
start http://127.0.0.1:8082

echo.
echo [完成] 服务已全部启动！
echo.
echo 提示：
echo   - 关闭此窗口不会停止服务
echo   - 如需停止服务，请关闭对应的命令行窗口
echo   - 或使用 Ctrl+C 在对应窗口中停止
echo.
pause