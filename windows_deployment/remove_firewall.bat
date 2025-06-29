@echo off
chcp 65001
echo ========================================
echo 删除SVD服务防火墙规则
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 需要管理员权限来删除防火墙规则
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 检测到管理员权限，继续删除...
echo.

:: 显示现有规则
echo 查找SVD服务相关的防火墙规则...
netsh advfirewall firewall show rule name="SVD Video Service - Inbound" >nul 2>&1
if %errorlevel% equ 0 (
    echo 找到入站规则
) else (
    echo 未找到入站规则
)

netsh advfirewall firewall show rule name="SVD Video Service - Outbound" >nul 2>&1
if %errorlevel% equ 0 (
    echo 找到出站规则
) else (
    echo 未找到出站规则
)

echo.

:: 询问用户确认
echo 是否确认删除SVD服务的防火墙规则？[Y/n]
set /p confirm=
if /i "%confirm%"=="n" (
    echo 操作已取消
    pause
    exit /b 0
)

:: 删除入站规则
echo 删除入站规则...
netsh advfirewall firewall delete rule name="SVD Video Service - Inbound"
if %errorlevel% equ 0 (
    echo ✅ 入站规则删除成功
) else (
    echo ⚠️ 入站规则删除失败或不存在
)

:: 删除出站规则
echo 删除出站规则...
netsh advfirewall firewall delete rule name="SVD Video Service - Outbound"
if %errorlevel% equ 0 (
    echo ✅ 出站规则删除成功
) else (
    echo ⚠️ 出站规则删除失败或不存在
)

echo.
echo ========================================
echo 删除完成
echo ========================================
echo SVD服务的防火墙规则已删除
echo 现在外部设备将无法访问SVD服务
echo.
echo 如需重新配置，请运行: setup_firewall.bat
echo.
pause