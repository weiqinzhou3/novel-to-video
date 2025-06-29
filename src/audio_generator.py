#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频生成模块

功能：
1. 文本转语音（TTS）
2. 支持多种TTS服务（OpenAI、ElevenLabs）
3. 音频后处理和优化
4. 音频格式转换
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import openai
import requests
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt, wait_exponential


class AudioGenerator:
    """音频生成器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化音频生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.audio_config = config['audio_generation']
        self.provider = self.audio_config.get('provider', 'openai')
        
        # 初始化对应的TTS服务
        if self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'elevenlabs':
            self._init_elevenlabs()
        else:
            raise ValueError(f"不支持的TTS服务提供商: {self.provider}")
    
    def _init_openai(self):
        """初始化OpenAI TTS服务"""
        openai_config = self.config['api_keys']['openai']
        self.openai_client = openai.OpenAI(
            api_key=openai_config['api_key'],
            base_url=openai_config.get('base_url')
        )
        
        self.tts_model = openai_config.get('tts_model', 'tts-1-hd')
        self.voice = openai_config.get('tts_voice', 'alloy')
        
        self.logger.info(f"OpenAI TTS初始化完成，模型: {self.tts_model}, 声音: {self.voice}")
    
    def _init_elevenlabs(self):
        """初始化ElevenLabs TTS服务"""
        elevenlabs_config = self.config['api_keys']['elevenlabs']
        self.elevenlabs_api_key = elevenlabs_config['api_key']
        self.elevenlabs_voice_id = elevenlabs_config.get('voice_id')
        self.elevenlabs_model = elevenlabs_config.get('model', 'eleven_multilingual_v2')
        
        self.logger.info(f"ElevenLabs TTS初始化完成，声音ID: {self.elevenlabs_voice_id}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _generate_openai_tts(self, text: str, output_path: str) -> str:
        """使用OpenAI TTS生成音频
        
        Args:
            text: 输入文本
            output_path: 输出文件路径
            
        Returns:
            生成的音频文件路径
        """
        try:
            response = self.openai_client.audio.speech.create(
                model=self.tts_model,
                voice=self.voice,
                input=text,
                response_format="mp3",
                speed=self.audio_config.get('speed', 1.0)
            )
            
            # 保存音频文件
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"OpenAI TTS生成完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"OpenAI TTS生成失败: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _generate_elevenlabs_tts(self, text: str, output_path: str) -> str:
        """使用ElevenLabs TTS生成音频
        
        Args:
            text: 输入文本
            output_path: 输出文件路径
            
        Returns:
            生成的音频文件路径
        """
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": self.elevenlabs_model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=300)
            response.raise_for_status()
            
            # 保存音频文件
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"ElevenLabs TTS生成完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"ElevenLabs TTS生成失败: {e}")
            raise
    
    def split_text_for_tts(self, text: str, max_length: int = 4000) -> list:
        """将长文本分割成适合TTS的片段
        
        Args:
            text: 输入文本
            max_length: 每段最大长度
            
        Returns:
            文本片段列表
        """
        if len(text) <= max_length:
            return [text]
        
        segments = []
        current_segment = ""
        
        # 按句子分割
        sentences = text.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_segment) + len(sentence) <= max_length:
                current_segment += sentence
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence
        
        if current_segment:
            segments.append(current_segment)
        
        self.logger.info(f"文本分割完成，共{len(segments)}个片段")
        return segments
    
    def generate_audio_segments(self, text_segments: list, output_dir: str) -> list:
        """生成多个音频片段
        
        Args:
            text_segments: 文本片段列表
            output_dir: 输出目录
            
        Returns:
            音频文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        audio_files = []
        
        for i, segment in enumerate(text_segments):
            output_file = os.path.join(output_dir, f"segment_{i+1:03d}.mp3")
            
            if self.provider == 'openai':
                self._generate_openai_tts(segment, output_file)
            elif self.provider == 'elevenlabs':
                self._generate_elevenlabs_tts(segment, output_file)
            
            audio_files.append(output_file)
        
        return audio_files
    
    def merge_audio_segments(self, audio_files: list, output_path: str) -> str:
        """合并多个音频片段
        
        Args:
            audio_files: 音频文件路径列表
            output_path: 输出文件路径
            
        Returns:
            合并后的音频文件路径
        """
        try:
            combined = AudioSegment.empty()
            
            for audio_file in audio_files:
                audio = AudioSegment.from_mp3(audio_file)
                combined += audio
                
                # 添加短暂停顿
                silence = AudioSegment.silent(duration=500)  # 0.5秒停顿
                combined += silence
            
            # 导出合并后的音频
            combined.export(output_path, format="wav")
            
            self.logger.info(f"音频合并完成: {output_path}, 总时长: {len(combined)/1000:.2f}秒")
            return output_path
            
        except Exception as e:
            self.logger.error(f"音频合并失败: {e}")
            raise
    
    def process_audio(self, audio_path: str, output_path: str = None) -> str:
        """音频后处理
        
        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            
        Returns:
            处理后的音频文件路径
        """
        if output_path is None:
            output_path = audio_path.replace('.mp3', '_processed.wav')
        
        try:
            # 加载音频
            audio = AudioSegment.from_file(audio_path)
            
            # 音量调整
            volume = self.audio_config.get('volume', 1.0)
            if volume != 1.0:
                audio = audio + (20 * (volume - 1))  # 转换为dB
            
            # 音频标准化
            audio = audio.normalize()
            
            # 设置采样率
            sample_rate = self.audio_config.get('sample_rate', 24000)
            audio = audio.set_frame_rate(sample_rate)
            
            # 设置为单声道（如果需要）
            audio = audio.set_channels(1)
            
            # 导出处理后的音频
            audio.export(output_path, format="wav")
            
            self.logger.info(f"音频后处理完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"音频后处理失败: {e}")
            raise
    
    def get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频时长（秒）
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # 转换为秒
            
            self.logger.info(f"音频时长: {duration:.2f}秒")
            return duration
            
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {e}")
            return 0.0
    
    def generate(self, text: str, output_path: str = "output/audio.wav") -> str:
        """生成音频的主要方法
        
        Args:
            text: 输入文本
            output_path: 输出文件路径
            
        Returns:
            生成的音频文件路径
        """
        self.logger.info(f"开始生成音频，文本长度: {len(text)}字符")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # 检查文本长度，如果太长则分段处理
            max_length = 4000 if self.provider == 'openai' else 2500
            
            if len(text) <= max_length:
                # 直接生成
                temp_file = output_path.replace('.wav', '_temp.mp3')
                
                if self.provider == 'openai':
                    self._generate_openai_tts(text, temp_file)
                elif self.provider == 'elevenlabs':
                    self._generate_elevenlabs_tts(text, temp_file)
                
                # 音频后处理
                final_path = self.process_audio(temp_file, output_path)
                
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
            else:
                # 分段处理
                text_segments = self.split_text_for_tts(text, max_length)
                
                # 生成音频片段
                temp_dir = "temp/audio_segments"
                audio_files = self.generate_audio_segments(text_segments, temp_dir)
                
                # 合并音频片段
                final_path = self.merge_audio_segments(audio_files, output_path)
                
                # 清理临时文件
                for audio_file in audio_files:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
            
            # 获取音频时长
            duration = self.get_audio_duration(final_path)
            
            self.logger.info(f"音频生成完成: {final_path}, 时长: {duration:.2f}秒")
            return final_path
            
        except Exception as e:
            self.logger.error(f"音频生成失败: {e}")
            raise
    
    def validate_audio(self, audio_path: str) -> bool:
        """验证音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            验证是否通过
        """
        try:
            if not os.path.exists(audio_path):
                self.logger.error(f"音频文件不存在: {audio_path}")
                return False
            
            # 尝试加载音频
            audio = AudioSegment.from_file(audio_path)
            
            # 检查音频时长
            duration = len(audio) / 1000.0
            if duration < 1.0:
                self.logger.error(f"音频时长过短: {duration:.2f}秒")
                return False
            
            # 检查音频格式
            if audio.frame_rate < 16000:
                self.logger.warning(f"音频采样率较低: {audio.frame_rate}Hz")
            
            self.logger.info(f"音频验证通过: {audio_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"音频验证失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    test_config = {
        'api_keys': {
            'openai': {
                'api_key': 'your-api-key-here',
                'tts_model': 'tts-1-hd',
                'tts_voice': 'alloy'
            }
        },
        'audio_generation': {
            'provider': 'openai',
            'sample_rate': 24000,
            'speed': 1.0,
            'volume': 1.0
        }
    }
    
    generator = AudioGenerator(test_config)
    
    test_text = "这是一个测试文本，用于验证音频生成功能是否正常工作。"
    output_file = "test_audio.wav"
    
    try:
        result = generator.generate(test_text, output_file)
        print(f"音频生成成功: {result}")
    except Exception as e:
        print(f"音频生成失败: {e}")