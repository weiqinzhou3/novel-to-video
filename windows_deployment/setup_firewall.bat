@echo off
chcp 65001
echo ========================================
echo Windows防火墙配置脚本
echo 为SVD视频生成服务配置防火墙规则
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 需要管理员权限来配置防火墙
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 检测到管理员权限，继续配置...
echo.

:: 显示当前防火墙状态
echo 当前防火墙状态:
netsh advfirewall show allprofiles state
echo.

:: 询问用户是否继续
echo 即将为SVD服务(端口8000)添加防火墙规则
echo 是否继续？[Y/n]
set /p continue=
if /i "%continue%"=="n" (
    echo 操作已取消
    pause
    exit /b 0
)

:: 删除可能存在的旧规则
echo 清理旧的防火墙规则...
netsh advfirewall firewall delete rule name="SVD Video Service - Inbound" >nul 2>&1
netsh advfirewall firewall delete rule name="SVD Video Service - Outbound" >nul 2>&1

:: 添加入站规则
echo 添加入站规则(端口8000)...
netsh advfirewall firewall add rule name="SVD Video Service - Inbound" dir=in action=allow protocol=TCP localport=8000
if %errorlevel% equ 0 (
    echo ✅ 入站规则添加成功
) else (
    echo ❌ 入站规则添加失败
)

:: 添加出站规则
echo 添加出站规则(端口8000)...
netsh advfirewall firewall add rule name="SVD Video Service - Outbound" dir=out action=allow protocol=TCP localport=8000
if %errorlevel% equ 0 (
    echo ✅ 出站规则添加成功
) else (
    echo ❌ 出站规则添加失败
)

:: 显示添加的规则
echo.
echo 已添加的防火墙规则:
netsh advfirewall firewall show rule name="SVD Video Service - Inbound"
netsh advfirewall firewall show rule name="SVD Video Service - Outbound"

:: 获取本机IP地址
echo.
echo ========================================
echo 网络信息
echo ========================================
echo 本机IP地址:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    echo   %%a
)

echo.
echo ========================================
echo 配置完成
echo ========================================
echo 防火墙规则已配置完成！
echo.
echo 现在可以通过以下地址访问SVD服务:
echo   - 本地访问: http://localhost:8000
echo   - 网络访问: http://[本机IP]:8000
echo   - API文档: http://localhost:8000/docs
echo.
echo 注意事项:
echo 1. 确保路由器也允许端口8000的访问
echo 2. 如果仍无法访问，请检查第三方防火墙软件
echo 3. 企业网络可能需要额外的网络配置
echo.
echo 要删除这些规则，请运行: remove_firewall.bat
echo.
pause