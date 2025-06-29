@echo off
chcp 65001 >nul
echo ========================================
echo Python环境详细诊断
echo ========================================
echo.

echo 1. 检查python命令:
python --version 2>&1
echo 错误级别: %errorlevel%
echo.

echo 2. 检查python3命令:
python3 --version 2>&1
echo 错误级别: %errorlevel%
echo.

echo 3. 检查py命令:
py --version 2>&1
echo 错误级别: %errorlevel%
echo.

echo 4. 检查py -3命令:
py -3 --version 2>&1
echo 错误级别: %errorlevel%
echo.

echo 5. 检查where命令查找Python:
where python 2>nul
if %errorlevel% neq 0 echo 未找到python
echo.

echo 6. 检查where命令查找python3:
where python3 2>nul
if %errorlevel% neq 0 echo 未找到python3
echo.

echo 7. 检查where命令查找py:
where py 2>nul
if %errorlevel% neq 0 echo 未找到py
echo.

echo 8. 检查PATH环境变量中的Python路径:
echo %PATH% | findstr /i python
if %errorlevel% neq 0 echo PATH中未找到python相关路径
echo.

echo 9. 检查常见Python安装位置:
echo 检查 C:\Python*
dir C:\Python* /b 2>nul
if %errorlevel% neq 0 echo 未找到 C:\Python*
echo.

echo 检查用户目录下的Python:
dir "%USERPROFILE%\AppData\Local\Programs\Python" /b 2>nul
if %errorlevel% neq 0 echo 未找到用户目录下的Python
echo.

echo 检查Microsoft Store Python:
dir "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\python*" /b 2>nul
if %errorlevel% neq 0 echo 未找到Microsoft Store Python
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 按任意键退出...
pause >nul