#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块

功能：
1. 文件操作工具
2. 时间处理工具
3. 文本处理工具
4. 配置管理工具
5. 日志配置工具
"""

import json
import logging
import os
import re
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import yaml
from tqdm import tqdm


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> str:
        """确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            目录路径
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        cleaned = re.sub(illegal_chars, '_', filename)
        
        # 移除连续的下划线
        cleaned = re.sub(r'_+', '_', cleaned)
        
        # 移除首尾的下划线和空格
        cleaned = cleaned.strip('_ ')
        
        # 限制长度
        if len(cleaned) > 200:
            cleaned = cleaned[:200]
        
        return cleaned or 'untitled'
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化的文件大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def copy_file_with_progress(src: str, dst: str) -> bool:
        """带进度条的文件复制
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            复制是否成功
        """
        try:
            file_size = FileUtils.get_file_size(src)
            
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                with tqdm(total=file_size, unit='B', unit_scale=True, desc="复制文件") as pbar:
                    while True:
                        chunk = fsrc.read(64 * 1024)  # 64KB chunks
                        if not chunk:
                            break
                        fdst.write(chunk)
                        pbar.update(len(chunk))
            
            return True
            
        except Exception as e:
            logging.error(f"文件复制失败: {e}")
            return False
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str = None) -> str:
        """备份文件
        
        Args:
            file_path: 要备份的文件路径
            backup_dir: 备份目录
            
        Returns:
            备份文件路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(file_path), 'backup')
        
        FileUtils.ensure_dir(backup_dir)
        
        # 生成备份文件名
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制文件
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24):
        """清理临时文件
        
        Args:
            temp_dir: 临时文件目录
            max_age_hours: 最大保留时间（小时）
        """
        if not os.path.exists(temp_dir):
            return
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        logging.info(f"清理临时文件: {file_path}")
                except Exception as e:
                    logging.warning(f"清理文件失败: {file_path}, {e}")


class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时长
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时长字符串
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}小时{minutes}分{secs}秒"
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """解析时长字符串
        
        Args:
            duration_str: 时长字符串，如 "1h30m", "90s", "2:30"
            
        Returns:
            秒数
        """
        duration_str = duration_str.strip().lower()
        
        # 处理 "2:30" 格式
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 2:
                try:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    return minutes * 60 + seconds
                except ValueError:
                    pass
            elif len(parts) == 3:
                try:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                except ValueError:
                    pass
        
        # 处理 "1h30m45s" 格式
        total_seconds = 0
        
        # 小时
        hour_match = re.search(r'(\d+)h', duration_str)
        if hour_match:
            total_seconds += int(hour_match.group(1)) * 3600
        
        # 分钟
        minute_match = re.search(r'(\d+)m', duration_str)
        if minute_match:
            total_seconds += int(minute_match.group(1)) * 60
        
        # 秒
        second_match = re.search(r'(\d+)s', duration_str)
        if second_match:
            total_seconds += int(second_match.group(1))
        
        # 如果只有数字，假设是秒
        if total_seconds == 0:
            try:
                total_seconds = float(duration_str)
            except ValueError:
                total_seconds = 0
        
        return total_seconds
    
    @staticmethod
    def get_timestamp() -> str:
        """获取当前时间戳字符串
        
        Returns:
            时间戳字符串
        """
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    @staticmethod
    def estimate_completion_time(current_progress: float, total_progress: float, 
                               start_time: float) -> str:
        """估算完成时间
        
        Args:
            current_progress: 当前进度
            total_progress: 总进度
            start_time: 开始时间
            
        Returns:
            预计完成时间字符串
        """
        if current_progress <= 0:
            return "未知"
        
        elapsed_time = time.time() - start_time
        progress_ratio = current_progress / total_progress
        
        if progress_ratio <= 0:
            return "未知"
        
        estimated_total_time = elapsed_time / progress_ratio
        remaining_time = estimated_total_time - elapsed_time
        
        if remaining_time <= 0:
            return "即将完成"
        
        return TimeUtils.format_duration(remaining_time)


class TextUtils:
    """文本处理工具类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除首尾空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """截断文本
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（基于词频）
        # 在实际应用中可以使用更复杂的NLP方法
        
        # 移除标点符号和数字
        cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', ' ', text)
        
        # 分词（简单按空格分割）
        words = cleaned_text.split()
        
        # 过滤短词和常见词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前N个关键词
        return [word for word, freq in sorted_words[:max_keywords]]
    
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """分割句子
        
        Args:
            text: 文本内容
            
        Returns:
            句子列表
        """
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]', text)
        
        # 清理空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def count_words(text: str) -> int:
        """统计词数
        
        Args:
            text: 文本内容
            
        Returns:
            词数
        """
        # 中文按字符数计算，英文按单词数计算
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        return chinese_chars + english_words


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        self.config = yaml.safe_load(f)
                    else:
                        self.config = json.load(f)
            else:
                logging.warning(f"配置文件不存在: {self.config_path}")
                self.config = {}
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self.config = {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            FileUtils.ensure_dir(os.path.dirname(self.config_path))
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value):
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, new_config: Dict[str, Any]):
        """更新配置
        
        Args:
            new_config: 新配置字典
        """
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, new_config)


class LoggerSetup:
    """日志配置工具"""
    
    @staticmethod
    def setup_logger(name: str = None, log_file: str = None, 
                    level: str = 'INFO', format_str: str = None) -> logging.Logger:
        """设置日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径
            level: 日志级别
            format_str: 日志格式
            
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 默认格式
        if format_str is None:
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(format_str)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            FileUtils.ensure_dir(os.path.dirname(log_file))
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def setup_rotating_logger(name: str, log_file: str, max_bytes: int = 10*1024*1024, 
                            backup_count: int = 5, level: str = 'INFO') -> logging.Logger:
        """设置轮转日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径
            max_bytes: 最大文件大小
            backup_count: 备份文件数量
            level: 日志级别
            
        Returns:
            配置好的日志记录器
        """
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        if logger.handlers:
            return logger
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 轮转文件处理器
        FileUtils.ensure_dir(os.path.dirname(log_file))
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total_steps: int, description: str = "处理中"):
        """初始化进度跟踪器
        
        Args:
            total_steps: 总步数
            description: 描述
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.description = description
        self.pbar = tqdm(total=total_steps, desc=description)
    
    def update(self, step: int = 1, description: str = None):
        """更新进度
        
        Args:
            step: 步数增量
            description: 新描述
        """
        self.current_step += step
        self.pbar.update(step)
        
        if description:
            self.pbar.set_description(description)
    
    def set_progress(self, current: int, description: str = None):
        """设置当前进度
        
        Args:
            current: 当前进度
            description: 描述
        """
        diff = current - self.current_step
        if diff > 0:
            self.update(diff, description)
    
    def finish(self):
        """完成进度"""
        self.pbar.close()
        
        elapsed_time = time.time() - self.start_time
        logging.info(f"{self.description}完成，耗时: {TimeUtils.format_duration(elapsed_time)}")
    
    def get_eta(self) -> str:
        """获取预计剩余时间
        
        Returns:
            预计剩余时间字符串
        """
        return TimeUtils.estimate_completion_time(
            self.current_step, self.total_steps, self.start_time
        )


if __name__ == "__main__":
    # 测试代码
    
    # 测试文件工具
    print("文件大小:", FileUtils.format_file_size(1024*1024*1.5))
    print("清理文件名:", FileUtils.clean_filename("测试<文件>名称?.txt"))
    
    # 测试时间工具
    print("格式化时长:", TimeUtils.format_duration(3661))
    print("解析时长:", TimeUtils.parse_duration("1h30m"))
    
    # 测试文本工具
    test_text = "这是一个测试文本，包含了一些关键词。"
    print("关键词:", TextUtils.extract_keywords(test_text))
    print("词数:", TextUtils.count_words(test_text))
    
    # 测试配置管理器
    config_manager = ConfigManager("test_config.json")
    config_manager.set("test.key", "test_value")
    print("配置值:", config_manager.get("test.key"))
    
    # 测试日志设置
    logger = LoggerSetup.setup_logger("test_logger", "logs/test.log")
    logger.info("测试日志消息")
    
    print("工具模块测试完成")