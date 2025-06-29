#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说自动视频制作工具 - 主程序

功能：
1. 解析命令行参数
2. 加载配置文件
3. 协调各个模块完成视频制作流程
4. 错误处理和日志记录
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from src.text_processor import TextProcessor
from src.audio_generator import AudioGenerator
from src.video_generator import VideoGenerator
from src.video_editor import VideoEditor
from src.video_uploader import VideoUploader


class NovelToVideoConverter:
    """小说转视频转换器主类"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """初始化转换器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
        # 初始化各个模块
        self.text_processor = TextProcessor(self.config)
        self.audio_generator = AudioGenerator(self.config)
        self.video_generator = VideoGenerator(self.config)
        self.video_editor = VideoEditor(self.config)
        self.uploader = VideoUploader(self.config)
        
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：配置文件 {config_path} 不存在")
            print("请复制 config/config.example.json 为 config/config.json 并填入API密钥")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误：配置文件格式错误 - {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """设置日志系统"""
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'logs/video_generation.log')
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志格式
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_directories(self):
        """创建必要的目录"""
        directories = ['input', 'output', 'temp', 'logs']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    async def convert(self, input_file: str, output_dir: str = "output", 
                     template: str = None, split_chapters: bool = False) -> str:
        """执行小说转视频的完整流程
        
        Args:
            input_file: 输入的小说TXT文件路径
            output_dir: 输出目录
            template: 自定义模板文件路径
            split_chapters: 是否分章处理
            
        Returns:
            生成的视频文件路径
        """
        self.logger.info(f"开始处理小说文件: {input_file}")
        
        try:
            # 1. 文本处理 - 提取关键情节
            self.logger.info("步骤1: 文本处理中...")
            script_data = self.text_processor.process(
                input_file, 
                split_chapters=split_chapters
            )
            
            # 2. 音频生成 - 文本转语音
            self.logger.info("步骤2: 生成配音音频...")
            audio_file = self.audio_generator.generate(
                script_data['narration'],
                output_path=f"{output_dir}/audio.wav"
            )
            
            # 3. 视频生成 - 根据情节生成画面（异步）
            self.logger.info("步骤3: 生成视频画面...")
            video_results = await self.video_generator.generate_videos(
                script_data['scenes']
            )
            
            # 检查生成结果
            successful_clips = [r for r in video_results if r['success']]
            if not successful_clips:
                raise RuntimeError("所有视频生成都失败了")
            
            self.logger.info(f"成功生成 {len(successful_clips)}/{len(video_results)} 个视频片段")
            
            # 4. 视频编辑 - 音画同步和后期处理
            self.logger.info("步骤4: 视频编辑和合成...")
            final_video = self.video_editor.compose(
                audio_file=audio_file,
                video_clips=successful_clips,
                script_data=script_data,
                output_path=f"{output_dir}/final_video.mp4",
                template=template
            )
            
            self.logger.info(f"视频制作完成: {final_video}")
            return final_video
            
        except Exception as e:
            self.logger.error(f"视频制作失败: {str(e)}")
            raise
    
    async def generate_shorts(self, video_file: str, output_dir: str = "output/shorts") -> list:
        """生成短视频片段
        
        Args:
            video_file: 源视频文件路径
            output_dir: 短视频输出目录
            
        Returns:
            生成的短视频文件路径列表
        """
        self.logger.info(f"开始生成短视频片段: {video_file}")
        
        try:
            shorts = self.video_editor.create_shorts(
                video_file,
                output_dir=output_dir
            )
            
            self.logger.info(f"短视频生成完成，共{len(shorts)}个片段")
            return shorts
            
        except Exception as e:
            self.logger.error(f"短视频生成失败: {str(e)}")
            raise
    
    async def upload_video(self, video_file: str, metadata: Dict[str, Any] = None) -> Dict[str, str]:
        """上传视频到各平台
        
        Args:
            video_file: 视频文件路径
            metadata: 视频元数据（标题、描述、标签等）
            
        Returns:
            上传结果字典
        """
        self.logger.info(f"开始上传视频: {video_file}")
        
        try:
            upload_results = self.uploader.upload(
                video_file,
                metadata=metadata
            )
            
            self.logger.info("视频上传完成")
            return upload_results
            
        except Exception as e:
            self.logger.error(f"视频上传失败: {str(e)}")
            raise


async def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description="小说自动视频制作工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --input novel.txt
  python main.py --input novel.txt --output my_videos/ --template custom.json
  python main.py --input novel.txt --split-chapters --generate-shorts
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入的小说TXT文件路径'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='输出目录（默认: output）'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/config.json',
        help='配置文件路径（默认: config/config.json）'
    )
    
    parser.add_argument(
        '--template', '-t',
        help='自定义视频模板文件路径'
    )
    
    parser.add_argument(
        '--split-chapters',
        action='store_true',
        help='分章处理长篇小说'
    )
    
    parser.add_argument(
        '--generate-shorts',
        action='store_true',
        help='生成短视频片段'
    )
    
    parser.add_argument(
        '--upload',
        action='store_true',
        help='自动上传到配置的平台'
    )
    
    parser.add_argument(
        '--title',
        help='视频标题（用于上传）'
    )
    
    parser.add_argument(
        '--description',
        help='视频描述（用于上传）'
    )
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误：输入文件 {args.input} 不存在")
        sys.exit(1)
    
    try:
        # 初始化转换器
        converter = NovelToVideoConverter(args.config)
        
        # 执行视频制作
        video_file = await converter.convert(
            input_file=args.input,
            output_dir=args.output,
            template=args.template,
            split_chapters=args.split_chapters
        )
        
        print(f"✅ 视频制作完成: {video_file}")
        
        # 生成短视频（如果需要）
        if args.generate_shorts:
            shorts = await converter.generate_shorts(
                video_file,
                output_dir=f"{args.output}/shorts"
            )
            print(f"✅ 短视频生成完成，共{len(shorts)}个片段")
        
        # 上传视频（如果需要）
        if args.upload:
            metadata = {
                'title': args.title or f"小说解说视频 - {Path(args.input).stem}",
                'description': args.description or "AI自动生成的小说解说视频"
            }
            
            upload_results = await converter.upload_video(video_file, metadata)
            print("✅ 视频上传完成:")
            for platform, url in upload_results.items():
                print(f"  {platform}: {url}")
        
        print("\n🎉 所有任务完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
