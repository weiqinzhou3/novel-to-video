#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说自动视频制作工具 - 快速启动脚本

功能：
1. 快速启动主程序
2. 提供常用的预设配置
3. 批量处理多个小说文件
4. 简化命令行操作
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import NovelToVideoConverter
from src.utils import FileUtils, LoggerSetup


class QuickLauncher:
    """快速启动器"""
    
    def __init__(self):
        self.project_root = project_root
        self.logger = LoggerSetup.setup_logger("QuickLauncher", "logs/launcher.log")
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取预设配置
        
        Returns:
            预设配置字典
        """
        return {
            "quick": {
                "name": "快速模式",
                "description": "快速生成视频，适合测试",
                "config": {
                    "video_generation": {
                        "enabled": False,  # 关闭AI视频生成，使用静态图片
                        "use_static_images": True
                    },
                    "audio_generation": {
                        "voice_model": "tts-1",  # 使用较快的TTS模型
                        "speed": 1.2
                    },
                    "video_editing": {
                        "add_subtitles": True,
                        "add_background_music": False,
                        "video_quality": "medium"
                    }
                }
            },
            "standard": {
                "name": "标准模式",
                "description": "平衡质量和速度",
                "config": {
                    "video_generation": {
                        "enabled": True,
                        "model": "runway",
                        "quality": "standard"
                    },
                    "audio_generation": {
                        "voice_model": "tts-1-hd",
                        "speed": 1.0
                    },
                    "video_editing": {
                        "add_subtitles": True,
                        "add_background_music": True,
                        "video_quality": "high"
                    }
                }
            },
            "premium": {
                "name": "高质量模式",
                "description": "最高质量输出，耗时较长",
                "config": {
                    "video_generation": {
                        "enabled": True,
                        "model": "runway",
                        "quality": "high",
                        "duration": 4
                    },
                    "audio_generation": {
                        "service": "elevenlabs",
                        "voice_model": "eleven_multilingual_v2",
                        "speed": 1.0
                    },
                    "video_editing": {
                        "add_subtitles": True,
                        "add_background_music": True,
                        "add_transitions": True,
                        "video_quality": "ultra"
                    }
                }
            },
            "shorts": {
                "name": "短视频模式",
                "description": "专门用于生成短视频",
                "config": {
                    "text_processing": {
                        "max_scenes": 3,
                        "scene_duration": 15
                    },
                    "video_generation": {
                        "enabled": True,
                        "aspect_ratio": "9:16"
                    },
                    "video_editing": {
                        "output_format": "vertical",
                        "max_duration": 60,
                        "add_captions": True,
                        "caption_style": "dynamic"
                    },
                    "shorts_generation": {
                        "enabled": True,
                        "segment_duration": 30,
                        "overlap_seconds": 2
                    }
                }
            }
        }
    
    def list_novels(self) -> List[str]:
        """列出可用的小说文件
        
        Returns:
            小说文件路径列表
        """
        novels_dir = self.project_root / "data" / "novels"
        if not novels_dir.exists():
            return []
        
        novel_files = []
        for file_path in novels_dir.glob("*.txt"):
            novel_files.append(str(file_path))
        
        return sorted(novel_files)
    
    def interactive_mode(self):
        """交互式模式"""
        print("="*60)
        print("小说自动视频制作工具 - 交互式启动")
        print("="*60)
        
        # 选择小说文件
        novels = self.list_novels()
        if not novels:
            print("❌ 在 data/novels/ 目录中没有找到小说文件")
            print("请将 .txt 格式的小说文件放入该目录")
            return
        
        print("\n📚 可用的小说文件:")
        for i, novel in enumerate(novels, 1):
            filename = Path(novel).name
            print(f"  {i}. {filename}")
        
        while True:
            try:
                choice = input("\n请选择小说文件 (输入序号): ").strip()
                novel_index = int(choice) - 1
                if 0 <= novel_index < len(novels):
                    selected_novel = novels[novel_index]
                    break
                else:
                    print("❌ 无效的选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效的数字")
        
        # 选择预设模式
        presets = self.get_presets()
        print("\n🎬 可用的生成模式:")
        preset_keys = list(presets.keys())
        for i, key in enumerate(preset_keys, 1):
            preset = presets[key]
            print(f"  {i}. {preset['name']} - {preset['description']}")
        
        while True:
            try:
                choice = input("\n请选择生成模式 (输入序号): ").strip()
                preset_index = int(choice) - 1
                if 0 <= preset_index < len(preset_keys):
                    selected_preset = preset_keys[preset_index]
                    break
                else:
                    print("❌ 无效的选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效的数字")
        
        # 选择输出目录
        default_output = self.project_root / "output" / "videos"
        output_dir = input(f"\n📁 输出目录 (默认: {default_output}): ").strip()
        if not output_dir:
            output_dir = str(default_output)
        
        # 确认设置
        print("\n" + "="*60)
        print("📋 生成设置确认:")
        print(f"  小说文件: {Path(selected_novel).name}")
        print(f"  生成模式: {presets[selected_preset]['name']}")
        print(f"  输出目录: {output_dir}")
        print("="*60)
        
        confirm = input("\n确认开始生成? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 已取消生成")
            return
        
        # 开始生成
        self.run_conversion(
            input_file=selected_novel,
            output_dir=output_dir,
            preset=selected_preset
        )
    
    def run_conversion(self, input_file: str, output_dir: str, preset: str = "standard", **kwargs):
        """运行转换
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            preset: 预设模式
            **kwargs: 其他参数
        """
        try:
            print(f"\n🚀 开始处理: {Path(input_file).name}")
            print(f"📁 输出目录: {output_dir}")
            print(f"⚙️  使用预设: {preset}")
            
            # 加载预设配置
            presets = self.get_presets()
            if preset in presets:
                preset_config = presets[preset]['config']
                print(f"✅ 已加载预设配置: {presets[preset]['name']}")
            else:
                preset_config = {}
                print(f"⚠️  未知预设 '{preset}'，使用默认配置")
            
            # 创建转换器
            converter = NovelToVideoConverter(
                config_path="config/config.json",
                **kwargs
            )
            
            # 应用预设配置
            if preset_config:
                converter.apply_preset_config(preset_config)
            
            # 执行转换
            result = converter.convert_novel(
                input_file=input_file,
                output_dir=output_dir
            )
            
            if result['success']:
                print("\n" + "="*60)
                print("🎉 视频生成完成!")
                print("="*60)
                print(f"📹 主视频: {result.get('main_video', 'N/A')}")
                if result.get('shorts'):
                    print(f"📱 短视频数量: {len(result['shorts'])}")
                print(f"⏱️  总耗时: {result.get('duration', 'N/A')}")
                print("="*60)
            else:
                print(f"\n❌ 生成失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.error(f"转换过程中发生错误: {e}")
            print(f"\n❌ 发生错误: {e}")
    
    def batch_process(self, novels_dir: str, output_dir: str, preset: str = "standard"):
        """批量处理
        
        Args:
            novels_dir: 小说目录
            output_dir: 输出目录
            preset: 预设模式
        """
        novels_path = Path(novels_dir)
        if not novels_path.exists():
            print(f"❌ 目录不存在: {novels_dir}")
            return
        
        # 获取所有txt文件
        txt_files = list(novels_path.glob("*.txt"))
        if not txt_files:
            print(f"❌ 在 {novels_dir} 中没有找到 .txt 文件")
            return
        
        print(f"📚 找到 {len(txt_files)} 个小说文件")
        print(f"🎬 使用预设: {preset}")
        print(f"📁 输出目录: {output_dir}")
        
        # 确认批量处理
        confirm = input("\n确认开始批量处理? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 已取消批量处理")
            return
        
        # 逐个处理
        success_count = 0
        for i, txt_file in enumerate(txt_files, 1):
            print(f"\n[{i}/{len(txt_files)}] 处理: {txt_file.name}")
            
            try:
                # 为每个文件创建单独的输出目录
                file_output_dir = Path(output_dir) / txt_file.stem
                
                self.run_conversion(
                    input_file=str(txt_file),
                    output_dir=str(file_output_dir),
                    preset=preset
                )
                
                success_count += 1
                print(f"✅ {txt_file.name} 处理完成")
                
            except Exception as e:
                self.logger.error(f"处理 {txt_file.name} 时发生错误: {e}")
                print(f"❌ {txt_file.name} 处理失败: {e}")
        
        print(f"\n📊 批量处理完成: {success_count}/{len(txt_files)} 成功")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="小说自动视频制作工具 - 快速启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run.py                                    # 交互式模式
  python run.py -i novel.txt                      # 快速转换
  python run.py -i novel.txt -p premium           # 使用高质量模式
  python run.py --batch data/novels/ -p quick     # 批量处理
  python run.py --list-presets                    # 列出所有预设
        """
    )
    
    parser.add_argument("-i", "--input", help="输入小说文件路径")
    parser.add_argument("-o", "--output", default="output/videos", help="输出目录 (默认: output/videos)")
    parser.add_argument("-p", "--preset", default="standard", help="预设模式 (默认: standard)")
    parser.add_argument("--batch", help="批量处理目录")
    parser.add_argument("--list-novels", action="store_true", help="列出可用的小说文件")
    parser.add_argument("--list-presets", action="store_true", help="列出所有预设模式")
    parser.add_argument("--interactive", action="store_true", help="交互式模式")
    
    args = parser.parse_args()
    
    launcher = QuickLauncher()
    
    # 列出小说文件
    if args.list_novels:
        novels = launcher.list_novels()
        if novels:
            print("📚 可用的小说文件:")
            for novel in novels:
                print(f"  {Path(novel).name}")
        else:
            print("❌ 没有找到小说文件")
        return
    
    # 列出预设模式
    if args.list_presets:
        presets = launcher.get_presets()
        print("🎬 可用的预设模式:")
        for key, preset in presets.items():
            print(f"  {key}: {preset['name']} - {preset['description']}")
        return
    
    # 批量处理
    if args.batch:
        launcher.batch_process(args.batch, args.output, args.preset)
        return
    
    # 单文件处理
    if args.input:
        if not os.path.exists(args.input):
            print(f"❌ 文件不存在: {args.input}")
            return
        
        launcher.run_conversion(
            input_file=args.input,
            output_dir=args.output,
            preset=args.preset
        )
        return
    
    # 交互式模式（默认）
    launcher.interactive_mode()


if __name__ == "__main__":
    main()