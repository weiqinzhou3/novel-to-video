@echo off
set HUGGINGFACE_TOKEN=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
if exist "svd_env\Scripts\activate.bat" call svd_env\Scripts\activate.bat
echo Starting SVD service...
echo Local access: http://localhost:8000
echo Press Ctrl+C to stop
python svd_server.py
pause