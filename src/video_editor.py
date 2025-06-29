#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频编辑模块

功能：
1. 合成音频和视频片段
2. 添加字幕和特效
3. 视频剪辑和后处理
4. 生成不同格式的输出视频
5. 短视频拆分功能
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import cv2
import numpy as np
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, 
    TextClip, concatenate_videoclips, ColorClip
)
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.audio.fx import volumex


class VideoEditor:
    """视频编辑器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化视频编辑器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.video_config = config.get('video_editing', {})
        self.subtitle_config = config.get('subtitles', {})
        self.shorts_config = config.get('shorts', {})
        
        # 视频参数
        self.output_resolution = self.video_config.get('output_resolution', '1920x1080')
        self.output_fps = self.video_config.get('output_fps', 30)
        self.output_format = self.video_config.get('output_format', 'mp4')
        
        # 字幕样式
        self.subtitle_font = self.subtitle_config.get('font', 'Arial-Bold')
        self.subtitle_size = self.subtitle_config.get('font_size', 48)
        self.subtitle_color = self.subtitle_config.get('color', 'white')
        self.subtitle_stroke_color = self.subtitle_config.get('stroke_color', 'black')
        self.subtitle_stroke_width = self.subtitle_config.get('stroke_width', 2)
        
        self.logger.info("视频编辑器初始化完成")
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
        """
        try:
            with VideoFileClip(video_path) as clip:
                return clip.duration
        except Exception as e:
            self.logger.error(f"获取视频时长失败: {e}")
            return 0.0
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频时长（秒）
        """
        try:
            with AudioFileClip(audio_path) as clip:
                return clip.duration
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {e}")
            return 0.0
    
    def _adjust_video_duration(self, video_path: str, target_duration: float, 
                              output_path: str) -> str:
        """调整视频时长
        
        Args:
            video_path: 输入视频路径
            target_duration: 目标时长
            output_path: 输出视频路径
            
        Returns:
            调整后的视频路径
        """
        try:
            with VideoFileClip(video_path) as clip:
                current_duration = clip.duration
                
                if abs(current_duration - target_duration) < 0.1:
                    # 时长差异很小，直接返回原文件
                    return video_path
                
                if current_duration > target_duration:
                    # 视频过长，裁剪
                    adjusted_clip = clip.subclip(0, target_duration)
                else:
                    # 视频过短，循环或延长
                    if current_duration > 0:
                        loops_needed = int(target_duration / current_duration) + 1
                        extended_clip = concatenate_videoclips([clip] * loops_needed)
                        adjusted_clip = extended_clip.subclip(0, target_duration)
                    else:
                        # 创建黑色填充视频
                        adjusted_clip = ColorClip(
                            size=clip.size, 
                            color=(0, 0, 0), 
                            duration=target_duration
                        )
                
                adjusted_clip.write_videofile(
                    output_path,
                    fps=self.output_fps,
                    verbose=False,
                    logger=None
                )
                
                return output_path
                
        except Exception as e:
            self.logger.error(f"调整视频时长失败: {e}")
            raise
    
    def _create_subtitle_clip(self, text: str, start_time: float, 
                             duration: float, video_size: Tuple[int, int]) -> TextClip:
        """创建字幕片段
        
        Args:
            text: 字幕文本
            start_time: 开始时间
            duration: 持续时间
            video_size: 视频尺寸
            
        Returns:
            字幕片段
        """
        try:
            # 创建字幕
            subtitle = TextClip(
                text,
                fontsize=self.subtitle_size,
                font=self.subtitle_font,
                color=self.subtitle_color,
                stroke_color=self.subtitle_stroke_color,
                stroke_width=self.subtitle_stroke_width
            ).set_start(start_time).set_duration(duration)
            
            # 设置字幕位置（底部居中）
            subtitle = subtitle.set_position(('center', video_size[1] * 0.85))
            
            return subtitle
            
        except Exception as e:
            self.logger.error(f"创建字幕失败: {e}")
            raise
    
    def _parse_subtitle_data(self, subtitle_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析字幕数据
        
        Args:
            subtitle_data: 字幕数据列表
            
        Returns:
            解析后的字幕数据
        """
        parsed_subtitles = []
        
        for item in subtitle_data:
            if isinstance(item, dict):
                text = item.get('text', '')
                start_time = item.get('start_time', 0.0)
                end_time = item.get('end_time', 0.0)
                duration = end_time - start_time
                
                if text and duration > 0:
                    parsed_subtitles.append({
                        'text': text,
                        'start_time': start_time,
                        'duration': duration
                    })
        
        return parsed_subtitles
    
    def combine_audio_video(self, video_files: List[str], audio_file: str, 
                           subtitle_data: Optional[List[Dict[str, Any]]] = None,
                           output_path: str = "output/final_video.mp4") -> str:
        """合成音频和视频
        
        Args:
            video_files: 视频文件列表
            audio_file: 音频文件路径
            subtitle_data: 字幕数据
            output_path: 输出文件路径
            
        Returns:
            合成后的视频文件路径
        """
        try:
            self.logger.info(f"开始合成视频，视频片段数: {len(video_files)}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 获取音频时长
            audio_duration = self._get_audio_duration(audio_file)
            if audio_duration <= 0:
                raise ValueError("音频文件无效或时长为0")
            
            # 处理视频片段
            video_clips = []
            current_time = 0.0
            
            # 计算每个视频片段应该的时长
            segment_duration = audio_duration / len(video_files) if video_files else audio_duration
            
            temp_files = []  # 用于清理临时文件
            
            try:
                for i, video_file in enumerate(video_files):
                    if not os.path.exists(video_file):
                        self.logger.warning(f"视频文件不存在: {video_file}")
                        continue
                    
                    # 调整视频时长
                    temp_video_path = f"temp_adjusted_{i}.mp4"
                    temp_files.append(temp_video_path)
                    
                    adjusted_video = self._adjust_video_duration(
                        video_file, segment_duration, temp_video_path
                    )
                    
                    # 加载视频片段
                    clip = VideoFileClip(adjusted_video)
                    
                    # 设置开始时间
                    clip = clip.set_start(current_time)
                    current_time += segment_duration
                    
                    video_clips.append(clip)
                
                if not video_clips:
                    raise ValueError("没有有效的视频片段")
                
                # 合并视频片段
                final_video = concatenate_videoclips(video_clips, method="compose")
                
                # 调整视频总时长以匹配音频
                if final_video.duration > audio_duration:
                    final_video = final_video.subclip(0, audio_duration)
                elif final_video.duration < audio_duration:
                    # 如果视频短于音频，循环最后一帧
                    last_frame = final_video.to_ImageClip(t=final_video.duration-0.1)
                    extension = last_frame.set_duration(audio_duration - final_video.duration)
                    final_video = concatenate_videoclips([final_video, extension])
                
                # 添加音频
                audio_clip = AudioFileClip(audio_file)
                final_video = final_video.set_audio(audio_clip)
                
                # 添加字幕
                if subtitle_data and self.subtitle_config.get('enabled', True):
                    subtitle_clips = []
                    parsed_subtitles = self._parse_subtitle_data(subtitle_data)
                    
                    for subtitle in parsed_subtitles:
                        subtitle_clip = self._create_subtitle_clip(
                            subtitle['text'],
                            subtitle['start_time'],
                            subtitle['duration'],
                            final_video.size
                        )
                        subtitle_clips.append(subtitle_clip)
                    
                    if subtitle_clips:
                        final_video = CompositeVideoClip([final_video] + subtitle_clips)
                
                # 调整输出分辨率
                if self.output_resolution != 'original':
                    width, height = map(int, self.output_resolution.split('x'))
                    final_video = final_video.resize((width, height))
                
                # 输出最终视频
                final_video.write_videofile(
                    output_path,
                    fps=self.output_fps,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                self.logger.info(f"视频合成完成: {output_path}")
                return output_path
                
            finally:
                # 清理临时文件
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        self.logger.warning(f"清理临时文件失败: {temp_file}, {e}")
                
                # 关闭视频片段
                for clip in video_clips:
                    try:
                        clip.close()
                    except:
                        pass
                
                try:
                    final_video.close()
                    audio_clip.close()
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"视频合成失败: {e}")
            raise
    
    def create_shorts(self, input_video: str, output_dir: str = "output/shorts") -> List[str]:
        """将长视频拆分为短视频
        
        Args:
            input_video: 输入视频路径
            output_dir: 输出目录
            
        Returns:
            生成的短视频文件路径列表
        """
        try:
            self.logger.info(f"开始拆分短视频: {input_video}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 短视频配置
            segment_duration = self.shorts_config.get('segment_duration', 60)  # 60秒
            aspect_ratio = self.shorts_config.get('aspect_ratio', '9:16')  # 竖屏
            resolution = self.shorts_config.get('resolution', '1080x1920')
            
            with VideoFileClip(input_video) as video:
                total_duration = video.duration
                num_segments = int(total_duration / segment_duration) + 1
                
                short_videos = []
                
                for i in range(num_segments):
                    start_time = i * segment_duration
                    end_time = min((i + 1) * segment_duration, total_duration)
                    
                    if end_time - start_time < 10:  # 跳过太短的片段
                        continue
                    
                    # 提取片段
                    segment = video.subclip(start_time, end_time)
                    
                    # 调整为竖屏格式
                    if aspect_ratio == '9:16':
                        # 裁剪为竖屏
                        width, height = map(int, resolution.split('x'))
                        
                        # 计算裁剪区域（居中裁剪）
                        original_width, original_height = segment.size
                        target_ratio = width / height
                        original_ratio = original_width / original_height
                        
                        if original_ratio > target_ratio:
                            # 原视频更宽，需要裁剪宽度
                            new_width = int(original_height * target_ratio)
                            x_offset = (original_width - new_width) // 2
                            segment = segment.crop(x1=x_offset, x2=x_offset + new_width)
                        else:
                            # 原视频更高，需要裁剪高度
                            new_height = int(original_width / target_ratio)
                            y_offset = (original_height - new_height) // 2
                            segment = segment.crop(y1=y_offset, y2=y_offset + new_height)
                        
                        # 调整分辨率
                        segment = segment.resize((width, height))
                    
                    # 输出文件路径
                    output_path = os.path.join(output_dir, f"short_{i+1:03d}.mp4")
                    
                    # 写入文件
                    segment.write_videofile(
                        output_path,
                        fps=self.output_fps,
                        codec='libx264',
                        audio_codec='aac',
                        verbose=False,
                        logger=None
                    )
                    
                    short_videos.append(output_path)
                    self.logger.info(f"短视频片段生成: {output_path}")
                
                self.logger.info(f"短视频拆分完成，共生成{len(short_videos)}个片段")
                return short_videos
                
        except Exception as e:
            self.logger.error(f"短视频拆分失败: {e}")
            raise
    
    def add_intro_outro(self, video_path: str, intro_text: str = None, 
                       outro_text: str = None, output_path: str = None) -> str:
        """添加片头片尾
        
        Args:
            video_path: 输入视频路径
            intro_text: 片头文字
            outro_text: 片尾文字
            output_path: 输出路径
            
        Returns:
            处理后的视频路径
        """
        try:
            if output_path is None:
                output_path = video_path.replace('.mp4', '_with_intro_outro.mp4')
            
            clips = []
            
            with VideoFileClip(video_path) as main_video:
                # 添加片头
                if intro_text:
                    intro_duration = self.video_config.get('intro_duration', 3)
                    intro_clip = TextClip(
                        intro_text,
                        fontsize=self.subtitle_size * 1.5,
                        font=self.subtitle_font,
                        color=self.subtitle_color,
                        bg_color='black'
                    ).set_duration(intro_duration).set_position('center')
                    
                    # 调整片头尺寸
                    intro_clip = intro_clip.resize(main_video.size)
                    clips.append(intro_clip)
                
                # 主视频
                clips.append(main_video)
                
                # 添加片尾
                if outro_text:
                    outro_duration = self.video_config.get('outro_duration', 3)
                    outro_clip = TextClip(
                        outro_text,
                        fontsize=self.subtitle_size * 1.2,
                        font=self.subtitle_font,
                        color=self.subtitle_color,
                        bg_color='black'
                    ).set_duration(outro_duration).set_position('center')
                    
                    # 调整片尾尺寸
                    outro_clip = outro_clip.resize(main_video.size)
                    clips.append(outro_clip)
                
                # 合并所有片段
                final_video = concatenate_videoclips(clips)
                
                # 输出视频
                final_video.write_videofile(
                    output_path,
                    fps=self.output_fps,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                self.logger.info(f"片头片尾添加完成: {output_path}")
                return output_path
                
        except Exception as e:
            self.logger.error(f"添加片头片尾失败: {e}")
            raise
    
    def optimize_video(self, input_path: str, output_path: str = None, 
                      target_size_mb: int = None) -> str:
        """优化视频文件
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_size_mb: 目标文件大小（MB）
            
        Returns:
            优化后的视频路径
        """
        try:
            if output_path is None:
                output_path = input_path.replace('.mp4', '_optimized.mp4')
            
            # 获取视频信息
            with VideoFileClip(input_path) as video:
                duration = video.duration
                original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            
            # 计算目标比特率
            if target_size_mb:
                target_bitrate = int((target_size_mb * 8 * 1024) / duration)  # kbps
                target_bitrate = max(target_bitrate, 500)  # 最小500kbps
            else:
                target_bitrate = self.video_config.get('target_bitrate', 2000)
            
            # 使用ffmpeg优化
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',
                '-b:v', f'{target_bitrate}k',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                optimized_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.logger.info(
                    f"视频优化完成: {input_path} -> {output_path}, "
                    f"大小: {original_size_mb:.1f}MB -> {optimized_size_mb:.1f}MB"
                )
                return output_path
            else:
                raise RuntimeError(f"ffmpeg优化失败: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"视频优化失败: {e}")
            raise
    
    def validate_output(self, video_path: str) -> bool:
        """验证输出视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            验证是否通过
        """
        try:
            if not os.path.exists(video_path):
                self.logger.error(f"视频文件不存在: {video_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(video_path)
            if file_size < 1024 * 1024:  # 小于1MB
                self.logger.error(f"视频文件过小: {video_path}")
                return False
            
            # 检查视频可播放性
            with VideoFileClip(video_path) as video:
                if video.duration <= 0:
                    self.logger.error(f"视频时长无效: {video_path}")
                    return False
                
                if video.size[0] <= 0 or video.size[1] <= 0:
                    self.logger.error(f"视频尺寸无效: {video_path}")
                    return False
            
            self.logger.info(f"视频验证通过: {video_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"视频验证失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    test_config = {
        'video_editing': {
            'output_resolution': '1920x1080',
            'output_fps': 30,
            'output_format': 'mp4'
        },
        'subtitles': {
            'enabled': True,
            'font': 'Arial-Bold',
            'font_size': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2
        },
        'shorts': {
            'segment_duration': 60,
            'aspect_ratio': '9:16',
            'resolution': '1080x1920'
        }
    }
    
    editor = VideoEditor(test_config)
    print("视频编辑器测试初始化完成")