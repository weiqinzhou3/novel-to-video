@echo off
chcp 936 >nul
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
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python3
        echo 找到 python3 命令
    ) else (
        py --version >nul 2>&1
        if %errorlevel% equ 0 (
            set PYTHON_CMD=py
            echo 找到 py 命令
        ) else (
            echo 错误: 未找到Python，请先安装Python 3.8+
            pause
            exit /b 1
        )
    )
)

:: 检查虚拟环境
if exist "svd_env\Scripts\activate.bat" (
    echo 正在激活虚拟环境...
    call svd_env\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo 虚拟环境激活失败
        pause
        exit /b 1
    )
    echo 虚拟环境已激活
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
)

:: 设置Hugging Face Token
set HUGGINGFACE_TOKEN=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
echo 已设置 Hugging Face Token

:: 检查Hugging Face认证
echo.
echo 正在检查 Hugging Face 认证状态...
echo 已设置 HUGGINGFACE_TOKEN 环境变量
echo 如果遇到认证问题，请检查 token 是否正确

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
echo 网络访问地址:
echo   请查看您的IP地址，然后访问 http://您的IP:8000
echo   或使用: http://127.0.0.1:8000
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