@echo off
echo SVD Service Restart Script
echo ========================
echo.

cd /d "%~dp0"

echo Step 1: Stopping any running SVD processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq SVD*" 2>nul
taskkill /f /im uvicorn.exe 2>nul
netstat -ano | findstr :7860 > temp_port_check.txt
if exist temp_port_check.txt (
    for /f "tokens=5" %%a in (temp_port_check.txt) do (
        echo Killing process using port 7860: %%a
        taskkill /f /pid %%a 2>nul
    )
    del temp_port_check.txt
)

echo Waiting 3 seconds for processes to terminate...
timeout /t 3 /nobreak >nul

echo.
echo Step 2: Checking if dependencies are installed...
call svd_env\Scripts\activate.bat
python -c "import imageio; imageio.plugins.ffmpeg.get_exe(); print('Dependencies OK')" 2>nul
if errorlevel 1 (
    echo WARNING: Video dependencies not found!
    echo Please run install_video_deps_en.bat first.
    echo.
    echo Do you want to install dependencies now? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        call install_video_deps_en.bat
        if errorlevel 1 (
            echo Failed to install dependencies. Exiting.
            pause
            exit /b 1
        )
    ) else (
        echo Skipping dependency installation.
        echo Service may not work properly without video dependencies.
    )
)

echo.
echo Step 3: Starting SVD service...
echo Service will start in a new window.
echo You can close this window after the service starts.
echo.

start "SVD Service" cmd /k "svd_env\Scripts\activate.bat && python svd_server.py"

echo.
echo Service startup initiated!
echo Check the new window for service status.
echo.
echo Waiting 5 seconds to verify startup...
timeout /t 5 /nobreak >nul

echo Testing service health...
curl -s http://localhost:7860/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: Service may not have started properly.
    echo Please check the service window for error messages.
) else (
    echo SUCCESS: Service is responding!
)

echo.
echo Press any key to exit...
pause >nul