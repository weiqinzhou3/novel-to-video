@echo off
chcp 65001 >nul
echo ========================================
echo     Hugging Face 认证设置助手
echo ========================================
echo.
echo 此脚本将帮助您设置 Hugging Face 访问令牌，以便访问受限模型。
echo.
echo 步骤 1: 获取访问令牌
echo ----------------------------------------
echo 1. 访问 https://huggingface.co/settings/tokens
echo 2. 登录您的 Hugging Face 账户
echo 3. 点击 "New token" 创建新令牌
echo 4. 选择 "Read" 权限
echo 5. 复制生成的令牌
echo.
echo 步骤 2: 申请模型访问权限
echo ----------------------------------------
echo 1. 访问 https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt-1-1
echo 2. 点击 "Request access" 申请访问权限
echo 3. 等待审批通过（通常几分钟到几小时）
echo.
echo 步骤 3: 设置令牌
echo ----------------------------------------
echo 请选择设置方式：
echo 1. 设置环境变量（推荐）
echo 2. 使用 huggingface-cli 登录
echo.
set /p choice="请输入选择 (1 或 2): "

if "%choice%"=="1" goto set_env_var
if "%choice%"=="2" goto cli_login
echo 无效选择，退出。
pause
exit /b 1

:set_env_var
echo.
set token=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
echo 使用预设令牌: %token%
echo.
set /p confirm="确认使用此令牌吗？(y/n): "
if /i not "%confirm%"=="y" (
    set /p token="请输入您的 Hugging Face 令牌: "
    if "%token%"=="" (
        echo 令牌不能为空！
        pause
        exit /b 1
    )
)

echo 正在设置环境变量...
setx HUGGINGFACE_TOKEN "%token%"
if %errorlevel% equ 0 (
    echo ✓ 环境变量设置成功！
    echo ✓ 请重新启动命令提示符或重新运行服务。
) else (
    echo ✗ 环境变量设置失败！
)
echo.
goto test_auth

:cli_login
echo.
echo 正在启动 huggingface-cli 登录...
echo 请在打开的窗口中输入您的令牌。
huggingface-cli login
if %errorlevel% equ 0 (
    echo ✓ 登录成功！
) else (
    echo ✗ 登录失败！请检查令牌是否正确。
)
echo.
goto test_auth

:test_auth
echo 步骤 4: 测试认证
echo ----------------------------------------
echo 正在测试认证...
python -c "from huggingface_hub import HfApi; api = HfApi(); print('✓ 认证成功！' if api.whoami() else '✗ 认证失败！')"
if %errorlevel% neq 0 (
    echo ✗ 测试失败！请检查：
    echo   1. 令牌是否正确
    echo   2. 是否有网络连接
    echo   3. 是否已安装 huggingface_hub
)
echo.
echo 设置完成！现在您可以运行 SVD 服务了。
echo.
pause