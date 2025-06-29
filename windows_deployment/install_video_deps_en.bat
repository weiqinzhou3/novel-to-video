@echo off
echo Installing video processing dependencies...
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call svd_env\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    echo Please make sure svd_env folder exists and is properly set up.
    pause
    exit /b 1
)

echo Installing imageio and imageio-ffmpeg...
pip install imageio>=2.31.0 imageio-ffmpeg>=0.4.9
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo Verifying installation...
python -c "import imageio; print('imageio version:', imageio.__version__); imageio.plugins.ffmpeg.get_exe(); print('ffmpeg available')"
if errorlevel 1 (
    echo WARNING: Verification failed. Dependencies may not be properly installed.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo You can now restart the SVD service.
echo.
echo Press any key to exit...
pause >nul