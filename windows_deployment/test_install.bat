@echo off
chcp 65001 >nul
echo ========================================
echo 测试install_and_run.bat脚本
echo ========================================
echo.

:: 检查脚本是否存在
if not exist "install_and_run.bat" (
    echo 错误: 未找到install_and_run.bat文件
    pause
    exit /b 1
)

echo 找到install_and_run.bat文件
echo.

:: 检查Python命令
echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ python命令可用
    python --version
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ python3命令可用
        python3 --version
    ) else (
        py --version >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✓ py命令可用
            py --version
        ) else (
            echo ✗ 未找到Python命令
            echo 请先安装Python 3.8+
            pause
            exit /b 1
        )
    )
)

echo.
echo 检查pip...
python -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ pip (python -m pip) 可用
) else (
    python3 -m pip --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ pip (python3 -m pip) 可用
    ) else (
        py -m pip --version >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✓ pip (py -m pip) 可用
        ) else (
            echo ✗ pip不可用
            pause
            exit /b 1
        )
    )
)

echo.
echo 检查requirements.txt文件...
if exist "requirements.txt" (
    echo ✓ 找到requirements.txt文件
) else (
    echo ⚠ 未找到requirements.txt文件
)

echo.
echo 检查svd_server.py文件...
if exist "svd_server.py" (
    echo ✓ 找到svd_server.py文件
) else (
    echo ⚠ 未找到svd_server.py文件
)

echo.
echo ========================================
echo 环境检查完成
echo ========================================
echo 现在可以运行install_and_run.bat脚本了
echo.
echo 按任意键退出...
pause >nul