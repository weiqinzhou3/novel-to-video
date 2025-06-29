# -*- coding: utf-8 -*-
"""
视频生成后端基类

定义所有视频生成后端的统一接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoGenerationTask:
    """视频生成任务数据类"""
    task_id: str
    prompt: str
    negative_prompt: Optional[str] = None
    duration: int = 4
    resolution: str = "1280x720"
    fps: int = 24
    style_prompt: Optional[str] = None
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 25
    input_image: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BackendCapabilities:
    """后端能力描述"""
    name: str
    supports_text_to_video: bool = True
    supports_image_to_video: bool = False
    supports_video_to_video: bool = False
    max_duration: int = 10
    supported_resolutions: List[str] = None
    supported_fps: List[int] = None
    cost_per_second: float = 0.0
    requires_gpu: bool = False
    is_local: bool = False

    def __post_init__(self):
        if self.supported_resolutions is None:
            self.supported_resolutions = ["1280x720", "1920x1080"]
        if self.supported_fps is None:
            self.supported_fps = [24, 30]


class BaseVideoBackend(ABC):
    """视频生成后端基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化后端
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._capabilities = self._get_capabilities()
        
    @property
    def capabilities(self) -> BackendCapabilities:
        """获取后端能力"""
        return self._capabilities
    
    @abstractmethod
    def _get_capabilities(self) -> BackendCapabilities:
        """获取后端能力描述"""
        pass
    
    @abstractmethod
    async def generate_video(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        生成视频
        
        Args:
            task: 视频生成任务
            
        Returns:
            更新后的任务对象
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> VideoGenerationTask:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        return {
            "status": "healthy",
            "backend": self.capabilities.name,
            "capabilities": self.capabilities.__dict__
        }
    
    def validate_task(self, task: VideoGenerationTask) -> bool:
        """
        验证任务参数
        
        Args:
            task: 视频生成任务
            
        Returns:
            是否有效
        """
        # 检查分辨率
        if task.resolution not in self.capabilities.supported_resolutions:
            raise ValueError(f"不支持的分辨率: {task.resolution}")
        
        # 检查帧率
        if task.fps not in self.capabilities.supported_fps:
            raise ValueError(f"不支持的帧率: {task.fps}")
        
        # 检查时长
        if task.duration > self.capabilities.max_duration:
            raise ValueError(f"时长超过限制: {task.duration}s > {self.capabilities.max_duration}s")
        
        return True
    
    def estimate_cost(self, task: VideoGenerationTask) -> float:
        """
        估算生成成本
        
        Args:
            task: 视频生成任务
            
        Returns:
            预估成本（美元）
        """
        return task.duration * self.capabilities.cost_per_second
    
    def _prepare_prompt(self, task: VideoGenerationTask) -> str:
        """
        准备完整的提示词
        
        Args:
            task: 视频生成任务
            
        Returns:
            完整提示词
        """
        prompt_parts = [task.prompt]
        
        if task.style_prompt:
            prompt_parts.append(task.style_prompt)
        
        return ", ".join(prompt_parts)