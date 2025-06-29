@echo off
chcp 65001 >nul
echo ========================================
echo SVD视频生成服务 - Windows部署脚本
echo ========================================
echo.

:: 检查Python是否安装（支持python、python3和py命令）
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 尝试使用python3命令...
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo 尝试使用py命令...
        py --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo 错误: 未找到Python，请先安装Python 3.8+
            echo 下载地址: https://www.python.org/downloads/
            pause
            exit /b 1
        ) else (
            set PYTHON_CMD=py
            echo 使用py命令
        )
    ) else (
        set PYTHON_CMD=python3
        echo 使用python3命令
    )
)

echo 检测到Python版本:
%PYTHON_CMD% --version
echo.

:: 检查pip是否可用
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: pip不可用，请检查Python安装
    pause
    exit /b 1
)

:: 创建虚拟环境（推荐）
echo 是否创建虚拟环境？(推荐) [Y/n]
set /p create_venv=
if /i "%create_venv%"=="" set create_venv=Y
if /i "%create_venv%"=="Y" (
    echo 创建虚拟环境...
    %PYTHON_CMD% -m venv svd_env
    if %errorlevel% neq 0 (
        echo 警告: 虚拟环境创建失败，将使用系统Python
    ) else (
        echo 激活虚拟环境...
        call svd_env\Scripts\activate.bat
        if %errorlevel% neq 0 (
            echo 警告: 虚拟环境激活失败，将使用系统Python
        )
    )
)

:: 升级pip
echo 升级pip...
%PYTHON_CMD% -m pip install --upgrade pip

:: 安装PyTorch（根据系统选择CPU或GPU版本）
echo.
echo 检测CUDA支持...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到NVIDIA GPU，安装CUDA版本的PyTorch...
    %PYTHON_CMD% -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo 未检测到NVIDIA GPU，安装CPU版本的PyTorch...
    %PYTHON_CMD% -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

:: 安装其他依赖
echo.
echo 安装其他依赖包...
if exist "requirements.txt" (
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo 警告: 未找到requirements.txt文件
)

:: 创建输出目录
if not exist "outputs" mkdir outputs

:: 显示系统信息
echo.
echo ========================================
echo 系统信息
echo ========================================
%PYTHON_CMD% -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}' if torch.cuda.is_available() else 'GPU数量: 0')"
echo.

:: 询问是否立即启动服务
echo 是否立即启动SVD服务？[Y/n]
set /p start_service=
if /i "%start_service%"=="" set start_service=Y
if /i "%start_service%"=="Y" (
    if exist "svd_server.py" (
        echo.
        echo ========================================
        echo 启动SVD视频生成服务
        echo ========================================
        echo 服务地址: http://localhost:8000
        echo API文档: http://localhost:8000/docs
        echo 健康检查: http://localhost:8000/health
        echo.
        echo 按Ctrl+C停止服务
        echo.
        %PYTHON_CMD% svd_server.py
    ) else (
        echo 错误: 未找到svd_server.py文件
        echo 请确保在正确的目录中运行此脚本
    )
) else (
    echo.
    echo 安装完成！
    echo 要启动服务，请运行: %PYTHON_CMD% svd_server.py
    echo 或者运行: start_service.bat
)

echo.
echo 按任意键退出...
pause >nul