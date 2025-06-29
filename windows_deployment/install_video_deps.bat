@echo off
echo 正在安装视频处理依赖...
echo.

cd /d "%~dp0"

echo 激活虚拟环境...
call svd_env\Scripts\activate.bat

echo 安装 imageio 和 imageio-ffmpeg...
pip install imageio>=2.31.0 imageio-ffmpeg>=0.4.9

echo.
echo 验证安装...
python -c "import imageio; print('imageio version:', imageio.__version__); imageio.plugins.ffmpeg.get_exe(); print('ffmpeg 可用')"

echo.
echo 依赖安装完成！
pause