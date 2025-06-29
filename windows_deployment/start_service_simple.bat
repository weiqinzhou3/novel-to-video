@echo off
chcp 65001 >nul
echo ========================================
echo     SVD 视频生成服务启动器
echo ========================================
echo.

:: 检测Python命令
set PYTHON_CMD=
echo 正在检测Python命令...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    echo 找到 python 命令
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    echo 找到 python3 命令
    goto :python_found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo 找到 py 命令
    goto :python_found
)

echo 错误: 未找到Python，请先安装Python 3.8+
pause
exit /b 1

:python_found
echo Python命令: %PYTHON_CMD%
echo.

:: 检查虚拟环境
if exist "svd_env\Scripts\activate.bat" (
    echo 正在激活虚拟环境...
    call svd_env\Scripts\activate.bat
    echo 虚拟环境已激活
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
)

:: 检查必要文件
if not exist "svd_server.py" (
    echo 错误: 未找到 svd_server.py 文件
    pause
    exit /b 1
)

:: 创建输出目录
if not exist "outputs" (
    mkdir outputs
    echo 创建输出目录: outputs
)

:: 显示服务信息
echo.
echo ========================================
echo           服务启动信息
echo ========================================
echo 本地访问: http://localhost:8000
echo 健康检查: http://localhost:8000/health
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

:: 启动服务
echo 正在启动 SVD 服务...
%PYTHON_CMD% svd_server.py

echo.
echo 服务已停止。
pause