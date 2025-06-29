@echo off
chcp 65001
echo ========================================
echo 启动SVD视频生成服务
echo ========================================
echo.

:: 检查虚拟环境是否存在
if exist "svd_env\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call svd_env\Scripts\activate.bat
)

:: 检查服务文件是否存在
if not exist "svd_server.py" (
    echo 错误: 找不到svd_server.py文件
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

:: 创建输出目录
if not exist "outputs" mkdir outputs

:: 显示网络信息
echo 获取本机IP地址...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    goto :found_ip
)
:found_ip
set ip=%ip: =%

echo.
echo ========================================
echo 服务信息
echo ========================================
echo 本地访问: http://localhost:8000
echo 网络访问: http://%ip%:8000
echo API文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo 日志文件: svd_server.log
echo 输出目录: outputs\
echo ========================================
echo.
echo 正在启动服务...
echo 按Ctrl+C停止服务
echo.

:: 启动服务
python svd_server.py

echo.
echo 服务已停止
pause