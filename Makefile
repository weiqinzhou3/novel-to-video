# 小说自动视频制作工具 - Makefile
# 提供常用的项目管理命令

.PHONY: help install test clean run setup dev lint format check-deps backup

# 默认目标
help:
	@echo "小说自动视频制作工具 - 可用命令:"
	@echo ""
	@echo "安装和设置:"
	@echo "  make install     - 安装项目依赖"
	@echo "  make setup       - 初始化项目环境"
	@echo "  make dev         - 安装开发依赖"
	@echo ""
	@echo "测试和检查:"
	@echo "  make test        - 运行测试"
	@echo "  make test-quick  - 运行快速测试"
	@echo "  make check-deps  - 检查依赖"
	@echo "  make lint        - 代码检查"
	@echo "  make format      - 代码格式化"
	@echo ""
	@echo "运行:"
	@echo "  make run         - 交互式运行"
	@echo "  make run-example - 运行示例"
	@echo "  make run-quick   - 快速模式运行示例"
	@echo ""
	@echo "维护:"
	@echo "  make clean       - 清理临时文件"
	@echo "  make backup      - 备份项目"
	@echo "  make update      - 更新依赖"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - 构建Docker镜像"
	@echo "  make docker-run   - 运行Docker容器"

# 安装依赖
install:
	@echo "📦 安装Python依赖..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

# 初始化项目环境
setup:
	@echo "🔧 初始化项目环境..."
	python setup.py
	@echo "✅ 项目环境初始化完成"

# 安装开发依赖
dev:
	@echo "🛠️  安装开发依赖..."
	pip install black flake8 pytest pytest-cov mypy
	@echo "✅ 开发依赖安装完成"

# 运行测试
test:
	@echo "🧪 运行完整测试..."
	python test.py --full

# 运行快速测试
test-quick:
	@echo "⚡ 运行快速测试..."
	python test.py --quick

# 检查依赖
check-deps:
	@echo "🔍 检查依赖状态..."
	pip list --outdated
	pip check

# 代码检查
lint:
	@echo "🔍 运行代码检查..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ main.py run.py test.py setup.py --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "⚠️  flake8未安装，跳过代码检查"; \
	fi

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	@if command -v black >/dev/null 2>&1; then \
		black src/ main.py run.py test.py setup.py --line-length=100; \
	else \
		echo "⚠️  black未安装，跳过代码格式化"; \
	fi

# 交互式运行
run:
	@echo "🚀 启动交互式模式..."
	python run.py --interactive

# 运行示例
run-example:
	@echo "📚 运行示例小说..."
	@if [ -f "data/novels/example.txt" ]; then \
		python run.py -i data/novels/example.txt -p standard; \
	else \
		echo "❌ 示例文件不存在，请先运行 make setup"; \
	fi

# 快速模式运行示例
run-quick:
	@echo "⚡ 快速模式运行示例..."
	@if [ -f "data/novels/example.txt" ]; then \
		python run.py -i data/novels/example.txt -p quick; \
	else \
		echo "❌ 示例文件不存在，请先运行 make setup"; \
	fi

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage
	@if [ -d "data/temp" ]; then \
		rm -rf data/temp/*; \
		echo "🗑️  清理临时数据目录"; \
	fi
	@if [ -d "cache" ]; then \
		rm -rf cache/*; \
		echo "🗑️  清理缓存目录"; \
	fi
	@echo "✅ 清理完成"

# 备份项目
backup:
	@echo "💾 备份项目..."
	@BACKUP_NAME="novel-to-video-backup-$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	tar --exclude='output' --exclude='data/temp' --exclude='cache' --exclude='logs' \
	    --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' \
	    -czf "$$BACKUP_NAME" .; \
	echo "✅ 备份完成: $$BACKUP_NAME"

# 更新依赖
update:
	@echo "🔄 更新依赖..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	@echo "✅ 依赖更新完成"

# 构建Docker镜像
docker-build:
	@echo "🐳 构建Docker镜像..."
	@if [ -f "Dockerfile" ]; then \
		docker build -t novel-to-video .; \
	else \
		echo "❌ Dockerfile不存在"; \
	fi

# 运行Docker容器
docker-run:
	@echo "🐳 运行Docker容器..."
	@if docker images | grep -q novel-to-video; then \
		docker run -it --rm -v $$(pwd)/data:/app/data -v $$(pwd)/output:/app/output novel-to-video; \
	else \
		echo "❌ Docker镜像不存在，请先运行 make docker-build"; \
	fi

# 创建虚拟环境
venv:
	@echo "🐍 创建虚拟环境..."
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
		echo "✅ 虚拟环境创建完成"; \
		echo "💡 激活虚拟环境: source venv/bin/activate"; \
	else \
		echo "⚠️  虚拟环境已存在"; \
	fi

# 激活虚拟环境并安装依赖
venv-install: venv
	@echo "📦 在虚拟环境中安装依赖..."
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ 虚拟环境依赖安装完成"
	@echo "💡 激活虚拟环境: source venv/bin/activate"

# 生成需求文件
freeze:
	@echo "📋 生成当前依赖列表..."
	pip freeze > requirements-freeze.txt
	@echo "✅ 依赖列表已保存到 requirements-freeze.txt"

# 检查项目状态
status:
	@echo "📊 项目状态检查"
	@echo "=================="
	@echo "Python版本: $$(python --version)"
	@echo "Pip版本: $$(pip --version)"
	@echo "项目目录: $$(pwd)"
	@echo ""
	@echo "📁 目录结构:"
	@ls -la | grep "^d" | awk '{print "  " $$9}'
	@echo ""
	@echo "📄 配置文件:"
	@if [ -f "config/config.json" ]; then \
		echo "  ✅ config/config.json"; \
	else \
		echo "  ❌ config/config.json (缺失)"; \
	fi
	@if [ -f "requirements.txt" ]; then \
		echo "  ✅ requirements.txt"; \
	else \
		echo "  ❌ requirements.txt (缺失)"; \
	fi
	@echo ""
	@echo "📚 小说文件:"
	@if [ -d "data/novels" ]; then \
		NOVEL_COUNT=$$(find data/novels -name "*.txt" | wc -l); \
		echo "  📖 找到 $$NOVEL_COUNT 个小说文件"; \
	else \
		echo "  ❌ data/novels 目录不存在"; \
	fi

# 显示日志
logs:
	@echo "📋 最近的日志:"
	@if [ -d "logs" ]; then \
		ls -la logs/; \
		echo ""; \
		echo "💡 查看特定日志: tail -f logs/main.log"; \
	else \
		echo "❌ logs 目录不存在"; \
	fi

# 监控输出目录
watch-output:
	@echo "👀 监控输出目录变化..."
	@if command -v fswatch >/dev/null 2>&1; then \
		fswatch -o output/ | xargs -n1 -I{} echo "📁 输出目录有新文件生成"; \
	elif command -v inotifywait >/dev/null 2>&1; then \
		inotifywait -m -r -e create,modify output/; \
	else \
		echo "❌ 需要安装 fswatch (macOS) 或 inotify-tools (Linux)"; \
	fi

# 一键安装（完整流程）
install-all: venv-install setup dev
	@echo "🎉 完整安装流程完成！"
	@echo ""
	@echo "🚀 下一步:"
	@echo "  1. 激活虚拟环境: source venv/bin/activate"
	@echo "  2. 配置API密钥: 编辑 config/config.json"
	@echo "  3. 运行测试: make test-quick"
	@echo "  4. 开始使用: make run"

# 快速开始（新用户）
quickstart:
	@echo "🚀 快速开始向导"
	@echo "================="
	@echo "1️⃣  检查系统环境..."
	@make check-deps
	@echo ""
	@echo "2️⃣  安装依赖..."
	@make install
	@echo ""
	@echo "3️⃣  初始化项目..."
	@make setup
	@echo ""
	@echo "4️⃣  运行快速测试..."
	@make test-quick
	@echo ""
	@echo "🎉 快速开始完成！"
	@echo "💡 接下来请编辑 config/config.json 配置API密钥"
	@echo "💡 然后运行: make run"