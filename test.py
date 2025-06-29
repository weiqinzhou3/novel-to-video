#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说自动视频制作工具 - 测试脚本

功能：
1. 测试各个模块的基本功能
2. 验证API连接
3. 检查配置文件
4. 运行简单的端到端测试
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import LoggerSetup, ConfigManager, FileUtils


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.project_root = project_root
        self.logger = LoggerSetup.setup_logger("TestRunner", "logs/test.log")
        self.config_manager = ConfigManager("config/config.json")
        self.test_results = []
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试
        
        Args:
            test_name: 测试名称
            test_func: 测试函数
        """
        print(f"\n🧪 测试: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"✅ 通过 ({duration:.2f}s)")
                self.test_results.append({
                    "name": test_name,
                    "status": "PASS",
                    "duration": duration,
                    "error": None
                })
            else:
                print(f"❌ 失败 ({duration:.2f}s)")
                self.test_results.append({
                    "name": test_name,
                    "status": "FAIL",
                    "duration": duration,
                    "error": "测试返回False"
                })
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ 错误 ({duration:.2f}s): {e}")
            self.test_results.append({
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            })
    
    def test_imports(self) -> bool:
        """测试模块导入"""
        try:
            from src.text_processor import TextProcessor
            from src.audio_generator import AudioGenerator
            from src.video_generator import VideoGenerator
            from src.video_editor import VideoEditor
            from src.video_uploader import VideoUploader
            from main import NovelToVideoConverter
            
            print("  ✓ 所有模块导入成功")
            return True
            
        except ImportError as e:
            print(f"  ✗ 模块导入失败: {e}")
            return False
    
    def test_config_file(self) -> bool:
        """测试配置文件"""
        config_file = self.project_root / "config" / "config.json"
        
        if not config_file.exists():
            print("  ✗ 配置文件不存在")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查必需的配置项
            required_sections = ['openai', 'text_processing', 'audio_generation', 'video_generation']
            for section in required_sections:
                if section not in config:
                    print(f"  ✗ 缺少配置节: {section}")
                    return False
            
            print("  ✓ 配置文件格式正确")
            return True
            
        except json.JSONDecodeError as e:
            print(f"  ✗ 配置文件JSON格式错误: {e}")
            return False
    
    def test_directories(self) -> bool:
        """测试目录结构"""
        required_dirs = [
            "data/novels",
            "data/temp",
            "output/videos",
            "output/audio",
            "logs",
            "src"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            print(f"  ✗ 缺少目录: {', '.join(missing_dirs)}")
            return False
        
        print("  ✓ 目录结构完整")
        return True
    
    def test_dependencies(self) -> bool:
        """测试依赖包"""
        required_packages = [
            'openai',
            'requests',
            'tqdm',
            'pydub',
            'moviepy',
            'pillow',
            'numpy'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"  ✗ 缺少依赖包: {', '.join(missing_packages)}")
            return False
        
        print("  ✓ 所有依赖包已安装")
        return True
    
    def test_openai_connection(self) -> bool:
        """测试OpenAI连接"""
        api_key = self.config_manager.get('openai.api_key')
        
        if not api_key or api_key == 'your_openai_api_key_here':
            print("  ⚠️  OpenAI API密钥未配置")
            return False
        
        try:
            import openai
            
            # 设置API密钥
            client = openai.OpenAI(api_key=api_key)
            
            # 测试简单的API调用
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=5
            )
            
            print("  ✓ OpenAI API连接正常")
            return True
            
        except Exception as e:
            print(f"  ✗ OpenAI API连接失败: {e}")
            return False
    
    def test_text_processor(self) -> bool:
        """测试文本处理器"""
        try:
            from src.text_processor import TextProcessor
            
            processor = TextProcessor(self.config_manager.config)
            
            # 测试文本预处理
            test_text = "这是一个测试文本。\n\n包含多个段落。\n\n用于测试文本处理功能。"
            processed = processor.preprocess_text(test_text)
            
            if not processed:
                print("  ✗ 文本预处理返回空结果")
                return False
            
            # 测试章节分割
            chapters = processor.split_chapters(test_text)
            
            if not chapters:
                print("  ✗ 章节分割返回空结果")
                return False
            
            print("  ✓ 文本处理器功能正常")
            return True
            
        except Exception as e:
            print(f"  ✗ 文本处理器测试失败: {e}")
            return False
    
    def test_audio_generator(self) -> bool:
        """测试音频生成器"""
        try:
            from src.audio_generator import AudioGenerator
            
            generator = AudioGenerator(self.config_manager.config)
            
            # 检查TTS服务配置
            if not generator.openai_client:
                print("  ⚠️  OpenAI客户端未初始化")
                return False
            
            print("  ✓ 音频生成器初始化成功")
            return True
            
        except Exception as e:
            print(f"  ✗ 音频生成器测试失败: {e}")
            return False
    
    def test_video_editor(self) -> bool:
        """测试视频编辑器"""
        try:
            from src.video_editor import VideoEditor
            
            editor = VideoEditor(self.config_manager.config)
            
            # 测试基本功能
            test_duration = editor.parse_duration("1:30")
            if test_duration != 90:
                print(f"  ✗ 时长解析错误: 期望90，得到{test_duration}")
                return False
            
            print("  ✓ 视频编辑器功能正常")
            return True
            
        except Exception as e:
            print(f"  ✗ 视频编辑器测试失败: {e}")
            return False
    
    def test_utils(self) -> bool:
        """测试工具模块"""
        try:
            from src.utils import FileUtils, TimeUtils, TextUtils
            
            # 测试文件工具
            test_size = FileUtils.format_file_size(1024 * 1024)
            if "MB" not in test_size:
                print(f"  ✗ 文件大小格式化错误: {test_size}")
                return False
            
            # 测试时间工具
            test_time = TimeUtils.format_duration(3661)
            if "1小时" not in test_time:
                print(f"  ✗ 时间格式化错误: {test_time}")
                return False
            
            # 测试文本工具
            test_words = TextUtils.count_words("测试文本 test text")
            if test_words <= 0:
                print(f"  ✗ 词数统计错误: {test_words}")
                return False
            
            print("  ✓ 工具模块功能正常")
            return True
            
        except Exception as e:
            print(f"  ✗ 工具模块测试失败: {e}")
            return False
    
    def test_example_novel(self) -> bool:
        """测试示例小说文件"""
        example_file = self.project_root / "data" / "novels" / "example.txt"
        
        if not example_file.exists():
            print("  ✗ 示例小说文件不存在")
            return False
        
        try:
            with open(example_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) < 100:
                print("  ✗ 示例小说文件内容过短")
                return False
            
            print(f"  ✓ 示例小说文件正常 ({len(content)} 字符)")
            return True
            
        except Exception as e:
            print(f"  ✗ 读取示例小说文件失败: {e}")
            return False
    
    def test_ffmpeg(self) -> bool:
        """测试FFmpeg"""
        try:
            import subprocess
            
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("  ✓ FFmpeg可用")
                return True
            else:
                print("  ✗ FFmpeg不可用")
                return False
                
        except Exception as e:
            print(f"  ✗ FFmpeg测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("🧪 小说自动视频制作工具 - 测试套件")
        print("="*60)
        
        # 定义测试列表
        tests = [
            ("模块导入", self.test_imports),
            ("配置文件", self.test_config_file),
            ("目录结构", self.test_directories),
            ("依赖包", self.test_dependencies),
            ("OpenAI连接", self.test_openai_connection),
            ("文本处理器", self.test_text_processor),
            ("音频生成器", self.test_audio_generator),
            ("视频编辑器", self.test_video_editor),
            ("工具模块", self.test_utils),
            ("示例小说", self.test_example_novel),
            ("FFmpeg", self.test_ffmpeg)
        ]
        
        # 运行测试
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']])
        
        print("\n" + "="*60)
        print("📊 测试结果统计")
        print("="*60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 显示失败的测试
        failed_results = [r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']]
        if failed_results:
            print("\n❌ 失败的测试:")
            for result in failed_results:
                print(f"  - {result['name']}: {result['error']}")
        
        # 给出建议
        if failed_tests > 0:
            print("\n💡 建议:")
            if any('OpenAI' in r['name'] for r in failed_results):
                print("  - 请检查OpenAI API密钥配置")
            if any('依赖' in r['name'] for r in failed_results):
                print("  - 请运行: pip install -r requirements.txt")
            if any('FFmpeg' in r['name'] for r in failed_results):
                print("  - 请安装FFmpeg: https://ffmpeg.org/download.html")
            if any('目录' in r['name'] for r in failed_results):
                print("  - 请运行: python setup.py")
        else:
            print("\n🎉 所有测试通过！系统已准备就绪。")
            print("\n🚀 您可以开始使用:")
            print("  python run.py --interactive")
            print("  python main.py --input data/novels/example.txt")
        
        print("="*60)
        
        return failed_tests == 0
    
    def quick_test(self):
        """快速测试（仅测试关键功能）"""
        print("🚀 快速测试模式")
        print("-" * 30)
        
        quick_tests = [
            ("模块导入", self.test_imports),
            ("配置文件", self.test_config_file),
            ("依赖包", self.test_dependencies),
            ("目录结构", self.test_directories)
        ]
        
        for test_name, test_func in quick_tests:
            self.run_test(test_name, test_func)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        total = len(self.test_results)
        
        if passed == total:
            print("\n✅ 快速测试通过！基本功能正常。")
        else:
            print(f"\n❌ 快速测试失败！{total-passed}/{total} 项测试未通过。")
            print("建议运行完整测试: python test.py --full")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="小说自动视频制作工具 - 测试脚本")
    parser.add_argument("--full", action="store_true", help="运行完整测试")
    parser.add_argument("--quick", action="store_true", help="运行快速测试")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.quick:
        runner.quick_test()
    else:
        runner.run_all_tests()


if __name__ == "__main__":
    main()