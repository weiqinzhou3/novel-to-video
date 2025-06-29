@echo off
echo ========================================
echo     SVD Video Generation Service
echo ========================================
echo.

:: Detect Python command
set PYTHON_CMD=
echo Detecting Python command...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    echo Found python command
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python3
        echo Found python3 command
    ) else (
        py --version >nul 2>&1
        if %errorlevel% equ 0 (
            set PYTHON_CMD=py
            echo Found py command
        ) else (
            echo Error: Python not found, please install Python 3.8+
            pause
            exit /b 1
        )
    )
)

:: Check virtual environment
if exist "svd_env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call svd_env\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo Virtual environment activation failed
        pause
        exit /b 1
    )
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found, using system Python
)

:: Set Hugging Face Token
set HUGGINGFACE_TOKEN=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
echo Hugging Face Token set

:: Check Hugging Face authentication
echo.
echo Checking Hugging Face authentication status...
echo HUGGINGFACE_TOKEN environment variable is set
echo If you encounter authentication issues, please check if token is correct

:: Check required files
if not exist "svd_server.py" (
    echo Error: svd_server.py file not found
    pause
    exit /b 1
)

:: Create output directory
if not exist "outputs" (
    mkdir outputs
    echo Created output directory: outputs
)

:: Display service information
echo.
echo ========================================
echo           Service Information
echo ========================================
echo Local access: http://localhost:8000
echo Health check: http://localhost:8000/health
echo API docs: http://localhost:8000/docs
echo.
echo Network access:
echo   Check your IP address, then visit http://YOUR_IP:8000
echo   Or use: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop service
echo ========================================
echo.

:: Start service
echo Starting SVD service...
%PYTHON_CMD% svd_server.py

echo.
echo Service stopped.
pause