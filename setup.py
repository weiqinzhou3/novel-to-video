#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说自动视频制作工具 - 安装脚本

功能：
1. 检查系统环境
2. 安装依赖包
3. 配置环境变量
4. 初始化项目结构
5. 验证安装
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

# 项目信息
PROJECT_NAME = "novel-to-video"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "小说自动视频制作工具"
AUTHOR = "AI Assistant"
PYTHON_REQUIRES = ">=3.8"

# 必需的系统工具
REQUIRED_TOOLS = {
    "ffmpeg": "视频处理工具",
    "git": "版本控制工具"
}

# 可选的系统工具
OPTIONAL_TOOLS = {
    "imagemagick": "图像处理工具",
    "youtube-dl": "视频下载工具"
}


class SetupManager:
    """安装管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
    
    def check_python_version(self) -> bool:
        """检查Python版本"""
        print("检查Python版本...")
        
        current_version = sys.version_info
        required_version = (3, 8)
        
        if current_version >= required_version:
            print(f"✓ Python版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
            return True
        else:
            error_msg = f"Python版本过低，需要 {required_version[0]}.{required_version[1]}+，当前版本: {current_version.major}.{current_version.minor}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
    
    def check_system_tools(self) -> bool:
        """检查系统工具"""
        print("\n检查系统工具...")
        
        all_good = True
        
        # 检查必需工具
        for tool, description in REQUIRED_TOOLS.items():
            if self._check_tool_installed(tool):
                print(f"✓ {tool}: {description}")
            else:
                error_msg = f"缺少必需工具: {tool} ({description})"
                self.errors.append(error_msg)
                print(f"✗ {error_msg}")
                all_good = False
        
        # 检查可选工具
        for tool, description in OPTIONAL_TOOLS.items():
            if self._check_tool_installed(tool):
                print(f"✓ {tool}: {description} (可选)")
            else:
                warning_msg = f"建议安装: {tool} ({description})"
                self.warnings.append(warning_msg)
                print(f"! {warning_msg}")
        
        return all_good
    
    def _check_tool_installed(self, tool: str) -> bool:
        """检查工具是否已安装"""
        try:
            subprocess.run([tool, "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def install_python_dependencies(self) -> bool:
        """安装Python依赖"""
        print("\n安装Python依赖...")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            error_msg = "requirements.txt文件不存在"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
        
        try:
            # 升级pip
            print("升级pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True)
            
            # 安装依赖
            print("安装项目依赖...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True)
            
            print("✓ Python依赖安装完成")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"安装Python依赖失败: {e}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
    
    def setup_project_structure(self) -> bool:
        """设置项目结构"""
        print("\n设置项目结构...")
        
        # 需要创建的目录
        directories = [
            "data/novels",
            "data/temp",
            "output/videos",
            "output/audio",
            "output/scripts",
            "output/shorts",
            "logs",
            "cache",
            "backup"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✓ 创建目录: {directory}")
            
            # 创建.gitignore文件
            self._create_gitignore()
            
            # 创建示例配置文件
            self._setup_config_files()
            
            print("✓ 项目结构设置完成")
            return True
            
        except Exception as e:
            error_msg = f"设置项目结构失败: {e}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
    
    def _create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
config/config.json
data/novels/*.txt
output/
logs/
cache/
backup/
data/temp/

# API Keys
.env
*.key
*.pem

# OS
.DS_Store
Thumbs.db

# Media files
*.mp4
*.mp3
*.wav
*.avi
*.mov
*.mkv
*.jpg
*.jpeg
*.png
*.gif
*.bmp
"""
        
        gitignore_path = self.project_root / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
    
    def _setup_config_files(self):
        """设置配置文件"""
        config_dir = self.project_root / "config"
        
        # 如果config.json不存在，从example复制
        config_file = config_dir / "config.json"
        example_file = config_dir / "config.example.json"
        
        if not config_file.exists() and example_file.exists():
            shutil.copy2(example_file, config_file)
            print("✓ 创建配置文件: config/config.json")
            print("  请编辑此文件，填入您的API密钥")
    
    def verify_installation(self) -> bool:
        """验证安装"""
        print("\n验证安装...")
        
        try:
            # 尝试导入主要模块
            sys.path.insert(0, str(self.project_root))
            
            from src.text_processor import TextProcessor
            from src.audio_generator import AudioGenerator
            from src.video_generator import VideoGenerator
            from src.video_editor import VideoEditor
            from src.video_uploader import VideoUploader
            from src.utils import FileUtils, TimeUtils, TextUtils
            
            print("✓ 所有模块导入成功")
            
            # 检查配置文件
            config_file = self.project_root / "config" / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 检查是否有API密钥配置
                api_keys_configured = False
                if config.get('openai', {}).get('api_key') and config['openai']['api_key'] != 'your_openai_api_key_here':
                    api_keys_configured = True
                    print("✓ OpenAI API密钥已配置")
                
                if not api_keys_configured:
                    warning_msg = "请在config/config.json中配置API密钥"
                    self.warnings.append(warning_msg)
                    print(f"! {warning_msg}")
            
            print("✓ 安装验证完成")
            return True
            
        except ImportError as e:
            error_msg = f"模块导入失败: {e}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
        except Exception as e:
            error_msg = f"验证安装失败: {e}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False
    
    def print_installation_guide(self):
        """打印安装指南"""
        print("\n" + "="*60)
        print("小说自动视频制作工具 - 安装指南")
        print("="*60)
        
        if sys.platform == "darwin":  # macOS
            print("\n在macOS上安装系统依赖:")
            print("1. 安装Homebrew (如果未安装):")
            print('   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            print("\n2. 安装FFmpeg:")
            print("   brew install ffmpeg")
            print("\n3. 安装ImageMagick (可选):")
            print("   brew install imagemagick")
            
        elif sys.platform.startswith("linux"):  # Linux
            print("\n在Ubuntu/Debian上安装系统依赖:")
            print("sudo apt update")
            print("sudo apt install ffmpeg imagemagick git")
            print("\n在CentOS/RHEL上安装系统依赖:")
            print("sudo yum install ffmpeg imagemagick git")
            
        elif sys.platform == "win32":  # Windows
            print("\n在Windows上安装系统依赖:")
            print("1. 下载并安装FFmpeg:")
            print("   https://ffmpeg.org/download.html")
            print("2. 下载并安装ImageMagick:")
            print("   https://imagemagick.org/script/download.php#windows")
            print("3. 确保工具已添加到PATH环境变量")
        
        print("\n配置API密钥:")
        print("1. 复制 config/config.example.json 到 config/config.json")
        print("2. 编辑 config/config.json，填入您的API密钥:")
        print("   - OpenAI API Key (必需)")
        print("   - Runway API Key (可选，用于视频生成)")
        print("   - ElevenLabs API Key (可选，用于语音合成)")
        print("   - YouTube API Key (可选，用于自动上传)")
        
        print("\n运行示例:")
        print("python main.py --input data/novels/example.txt --output output/videos/")
    
    def run_setup(self) -> bool:
        """运行完整安装流程"""
        print(f"开始安装 {PROJECT_NAME} v{PROJECT_VERSION}")
        print(f"描述: {PROJECT_DESCRIPTION}")
        print(f"作者: {AUTHOR}")
        print("="*60)
        
        success = True
        
        # 检查Python版本
        if not self.check_python_version():
            success = False
        
        # 检查系统工具
        if not self.check_system_tools():
            success = False
        
        # 如果基础检查失败，显示安装指南
        if not success:
            self.print_installation_guide()
            return False
        
        # 安装Python依赖
        if not self.install_python_dependencies():
            success = False
        
        # 设置项目结构
        if not self.setup_project_structure():
            success = False
        
        # 验证安装
        if not self.verify_installation():
            success = False
        
        # 打印结果
        print("\n" + "="*60)
        if success:
            print("✓ 安装完成!")
            
            if self.warnings:
                print("\n注意事项:")
                for warning in self.warnings:
                    print(f"  ! {warning}")
            
            print("\n下一步:")
            print("1. 编辑 config/config.json 配置API密钥")
            print("2. 将小说文件放入 data/novels/ 目录")
            print("3. 运行: python main.py --help 查看使用说明")
            print("4. 运行示例: python main.py --input data/novels/your_novel.txt")
            
        else:
            print("✗ 安装失败!")
            print("\n错误列表:")
            for error in self.errors:
                print(f"  ✗ {error}")
            
            self.print_installation_guide()
        
        print("="*60)
        return success


def main():
    """主函数"""
    setup_manager = SetupManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        setup_manager.print_installation_guide()
        return
    
    success = setup_manager.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()