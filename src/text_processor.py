#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理模块

功能：
1. 读取和预处理小说文本
2. 使用AI提取关键情节
3. 生成视频脚本和场景描述
4. 处理长文本的分章功能
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import openai
from tenacity import retry, stop_after_attempt, wait_exponential


class TextProcessor:
    """文本处理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文本处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化OpenAI客户端
        openai_config = config['api_keys']['openai']
        self.client = openai.OpenAI(
            api_key=openai_config['api_key'],
            base_url=openai_config.get('base_url')
        )
        
        self.model = openai_config.get('model', 'gpt-4')
        self.text_config = config['text_processing']
    
    def read_novel(self, file_path: str) -> str:
        """读取小说文件
        
        Args:
            file_path: 小说文件路径
            
        Returns:
            小说文本内容
        """
        try:
            # 自动检测文件编码
            import chardet
            
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            # 读取文件内容
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.info(f"成功读取小说文件: {file_path}, 编码: {encoding}, 长度: {len(content)}字符")
            return content
            
        except Exception as e:
            self.logger.error(f"读取小说文件失败: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符和格式标记
        text = re.sub(r'[\r\n\t]+', '\n', text)
        
        # 移除章节标记（可选）
        text = re.sub(r'^第[\d一二三四五六七八九十百千万]+[章节回].*$', '', text, flags=re.MULTILINE)
        
        # 移除作者注释
        text = re.sub(r'\([^)]*作者[^)]*\)', '', text)
        
        return text.strip()
    
    def split_into_chapters(self, text: str, max_length: int = 8000) -> List[str]:
        """将长文本分割成章节
        
        Args:
            text: 完整文本
            max_length: 每章最大长度
            
        Returns:
            章节列表
        """
        # 尝试按章节标记分割
        chapter_pattern = r'第[\d一二三四五六七八九十百千万]+[章节回]'
        chapters = re.split(chapter_pattern, text)
        
        # 如果没有明显的章节标记，按长度分割
        if len(chapters) <= 1:
            chapters = []
            current_chapter = ""
            
            sentences = re.split(r'[。！？]', text)
            
            for sentence in sentences:
                if len(current_chapter) + len(sentence) > max_length:
                    if current_chapter:
                        chapters.append(current_chapter.strip())
                        current_chapter = sentence
                else:
                    current_chapter += sentence + "。"
            
            if current_chapter:
                chapters.append(current_chapter.strip())
        
        # 过滤掉太短的章节
        chapters = [ch for ch in chapters if len(ch.strip()) > 100]
        
        self.logger.info(f"文本分割完成，共{len(chapters)}个章节")
        return chapters
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_key_scenes(self, text: str) -> Dict[str, Any]:
        """使用AI提取关键场景
        
        Args:
            text: 输入文本
            
        Returns:
            包含场景信息的字典
        """
        scene_count = self.text_config['scene_count']
        target_duration = self.text_config['target_duration_seconds']
        
        prompt = f"""
请分析以下小说内容，提取{scene_count}个最关键的场景，制作成视频解说脚本。

要求：
1. 每个场景包含：
   - 简洁的叙述文本（用于配音）
   - 详细的视觉描述（用于AI生成视频）
   - 情感基调（如：紧张、温馨、激烈等）

2. 总配音时长控制在{target_duration}秒内
3. 语言简洁生动，适合视频解说
4. 突出故事的核心冲突和转折点

请以JSON格式返回，结构如下：
{{
  "title": "故事标题",
  "summary": "整体故事概要",
  "total_duration": 预估总时长（秒）,
  "scenes": [
    {{
      "id": 1,
      "narration": "配音文本",
      "visual_description": "视觉场景描述",
      "mood": "情感基调",
      "duration": 预估时长（秒）
    }}
  ]
}}

小说内容：
{text[:4000]}...
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频脚本编写专家，擅长将文学作品改编成吸引人的视频内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON格式")
                    
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试修复常见问题
                content = content.replace('```json', '').replace('```', '')
                content = re.sub(r',[\s]*}', '}', content)
                content = re.sub(r',[\s]*]', ']', content)
                result = json.loads(content)
            
            self.logger.info(f"成功提取{len(result['scenes'])}个关键场景")
            return result
            
        except Exception as e:
            self.logger.error(f"AI场景提取失败: {e}")
            raise
    
    def generate_narration_script(self, scenes: List[Dict[str, Any]]) -> str:
        """生成完整的旁白脚本
        
        Args:
            scenes: 场景列表
            
        Returns:
            完整的旁白文本
        """
        narration_parts = []
        
        for i, scene in enumerate(scenes):
            # 添加场景转换提示
            if i > 0:
                narration_parts.append("\n[场景转换]\n")
            
            narration_parts.append(scene['narration'])
        
        full_narration = "".join(narration_parts)
        
        self.logger.info(f"生成旁白脚本，总长度: {len(full_narration)}字符")
        return full_narration
    
    def process(self, input_file: str, split_chapters: bool = False) -> Dict[str, Any]:
        """处理小说文件的主要方法
        
        Args:
            input_file: 输入文件路径
            split_chapters: 是否分章处理
            
        Returns:
            处理结果字典
        """
        self.logger.info(f"开始处理文本文件: {input_file}")
        
        # 读取小说内容
        raw_text = self.read_novel(input_file)
        
        # 预处理文本
        processed_text = self.preprocess_text(raw_text)
        
        # 如果需要分章处理
        if split_chapters and len(processed_text) > self.text_config['max_script_length']:
            chapters = self.split_into_chapters(processed_text)
            
            # 处理第一章作为示例
            if chapters:
                processed_text = chapters[0]
                self.logger.info(f"使用第一章进行处理，长度: {len(processed_text)}字符")
        
        # 提取关键场景
        script_data = self.extract_key_scenes(processed_text)
        
        # 生成完整旁白
        script_data['narration'] = self.generate_narration_script(script_data['scenes'])
        
        # 添加元数据
        script_data['source_file'] = input_file
        script_data['source_length'] = len(raw_text)
        script_data['processed_length'] = len(processed_text)
        
        # 保存脚本数据
        output_file = "temp/script_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"文本处理完成，脚本已保存到: {output_file}")
        return script_data
    
    def validate_script(self, script_data: Dict[str, Any]) -> bool:
        """验证脚本数据的完整性
        
        Args:
            script_data: 脚本数据
            
        Returns:
            验证是否通过
        """
        required_fields = ['title', 'scenes', 'narration']
        
        for field in required_fields:
            if field not in script_data:
                self.logger.error(f"脚本数据缺少必要字段: {field}")
                return False
        
        if not script_data['scenes']:
            self.logger.error("脚本数据中没有场景信息")
            return False
        
        for i, scene in enumerate(script_data['scenes']):
            scene_required = ['narration', 'visual_description']
            for field in scene_required:
                if field not in scene:
                    self.logger.error(f"场景{i+1}缺少必要字段: {field}")
                    return False
        
        self.logger.info("脚本数据验证通过")
        return True


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_config = {
            'api_keys': {
                'openai': {
                    'api_key': 'your-api-key-here',
                    'model': 'gpt-4'
                }
            },
            'text_processing': {
                'scene_count': 5,
                'target_duration_seconds': 180,
                'max_script_length': 2000
            }
        }
        
        processor = TextProcessor(test_config)
        result = processor.process(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))