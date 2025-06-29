@echo off
chcp 936
echo ========================================
echo           SVD Video Generation Service
echo ========================================
echo.

REM Set Hugging Face Token
set HUGGINGFACE_TOKEN=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
echo Hugging Face Token has been set
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        py --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo ERROR: Python not found!
            echo Please install Python 3.8+ from https://python.org
            pause
            exit /b 1
        ) else (
            set PYTHON_CMD=py
        )
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)
echo Python found: %PYTHON_CMD%
echo.

REM Activate virtual environment
echo Activating virtual environment...
if exist "svd_env\Scripts\activate.bat" (
    call svd_env\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found
    echo Please run install_and_run.bat first
)
echo.

REM Check if port 8000 is available
echo Checking port availability...
netstat -an | find ":8000 " >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8000 is already in use
    echo Trying to find available port...
    set PORT=8001
) else (
    echo Port 8000 is available
    set PORT=8000
)
echo Using port: %PORT%
echo.

REM Check required files
echo Checking required files...
if not exist "svd_server.py" (
    echo ERROR: svd_server.py not found!
    pause
    exit /b 1
)
echo Required files found
echo.

REM Create output directory
if not exist "outputs" mkdir outputs
echo Output directory ready
echo.

REM Display service information
echo ========================================
echo           Service Information
echo ========================================
echo Local access: http://localhost:%PORT%
echo Health check: http://localhost:%PORT%/health
echo API docs: http://localhost:%PORT%/docs
echo.
echo Network access:
echo   Check your IP address, then visit http://YOUR_IP:%PORT%
echo   Or use: http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop service
echo ========================================
echo.

REM Start the service with custom port
echo Starting SVD service on port %PORT%...
%PYTHON_CMD% -c "import uvicorn; from svd_server import app; uvicorn.run(app, host='0.0.0.0', port=%PORT%, log_level='info')"

echo.
echo Service stopped.
pause