# 小说自动视频制作工具 - Docker配置
# 基于Python 3.9的轻量级镜像

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p data/novels data/temp output logs cache && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 复制配置文件模板
RUN if [ ! -f config/config.json ] && [ -f config/config.example.json ]; then \
        cp config/config.example.json config/config.json; \
    fi

# 暴露端口（如果需要web界面）
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 设置入口点
ENTRYPOINT ["python"]

# 默认命令
CMD ["run.py", "--interactive"]

# 构建信息
LABEL maintainer="Novel to Video Tool" \
      version="1.0.0" \
      description="自动将小说转换为视频的工具" \
      org.opencontainers.image.source="https://github.com/your-repo/novel-to-video"