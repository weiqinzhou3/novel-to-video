@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo     SVD 视频生成服务启动脚本 (配置版)
echo ========================================
echo.

REM 检查Python环境
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✓ Python环境检查通过

REM 检查虚拟环境
echo.
echo [2/6] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo 警告: 虚拟环境不存在，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
) else (
    echo ✓ 虚拟环境已存在
)

REM 激活虚拟环境
echo.
echo [3/6] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)
echo ✓ 虚拟环境激活成功

REM 设置Hugging Face Token
echo.
echo [4/6] 配置Hugging Face Token...
if "%HUGGINGFACE_TOKEN%"=="" (
    echo 警告: 未设置HUGGINGFACE_TOKEN环境变量
    echo 请在系统环境变量中设置，或者运行以下命令:
    echo set HUGGINGFACE_TOKEN=your_token_here
    echo.
    echo 继续启动服务（可能无法访问受限模型）...
) else (
    echo ✓ Hugging Face Token已配置
)

REM 检查必要文件
echo.
echo [5/6] 检查必要文件...
set "missing_files="
if not exist "svd_server.py" set "missing_files=!missing_files! svd_server.py"
if not exist "config_manager.py" set "missing_files=!missing_files! config_manager.py"
if not exist "config.json" set "missing_files=!missing_files! config.json"

if not "!missing_files!"=="" (
    echo 错误: 缺少必要文件:!missing_files!
    pause
    exit /b 1
)
echo ✓ 必要文件检查通过

REM 启动服务
echo.
echo [6/6] 启动SVD视频生成服务...
echo ========================================
echo 服务启动中，请稍候...
echo 如需停止服务，请按 Ctrl+C
echo ========================================
echo.

python svd_server.py

REM 检查启动结果
if errorlevel 1 (
    echo.
    echo ========================================
    echo 服务启动失败！
    echo ========================================
    echo 可能的解决方案:
    echo 1. 检查Python依赖是否完整安装
    echo 2. 确认Hugging Face Token是否有效
    echo 3. 检查GPU驱动和CUDA是否正确安装
    echo 4. 查看上方错误信息进行排查
    echo ========================================
    pause
) else (
    echo.
    echo ========================================
    echo 服务已正常关闭
    echo ========================================
)

endlocal
pause