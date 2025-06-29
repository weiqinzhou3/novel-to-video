# -*- coding: utf-8 -*-
"""
Pika Labs 后端

支持Pika Labs视频生成服务
"""

import asyncio
import aiohttp
import uuid
from typing import Dict, Any, Optional
from .base_backend import BaseVideoBackend, VideoGenerationTask, TaskStatus, BackendCapabilities


class PikaBackend(BaseVideoBackend):
    """Pika Labs 后端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        pika_config = config.get('api_keys', {}).get('pika', {})
        self.api_key = pika_config.get('api_key')
        self.base_url = pika_config.get('base_url', 'https://api.pika.art/v1')
        self.model = pika_config.get('model', 'pika-1.0')
        
        if not self.api_key or self.api_key == 'your-pika-api-key-here':
            self.logger.warning("Pika Labs API密钥未配置")
        
        # 任务存储
        self._tasks = {}
        
        self.logger.info(f"Pika Labs后端初始化完成，模型: {self.model}")
    
    def _get_capabilities(self) -> BackendCapabilities:
        """获取Pika Labs后端能力"""
        return BackendCapabilities(
            name="Pika Labs",
            supports_text_to_video=True,
            supports_image_to_video=True,
            supports_video_to_video=False,
            max_duration=4,
            supported_resolutions=["1024x576", "576x1024", "1024x1024"],
            supported_fps=[24],
            cost_per_second=0.35,  # 约$0.35/秒
            requires_gpu=False,
            is_local=False
        )
    
    def get_capabilities(self) -> BackendCapabilities:
        """获取后端能力（公共接口）"""
        return self._get_capabilities()
    
    async def generate_video(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        使用Pika Labs生成视频
        
        Args:
            task: 视频生成任务
            
        Returns:
            更新后的任务对象
        """
        try:
            # 验证API密钥
            if not self.api_key or self.api_key == 'your-pika-api-key-here':
                raise Exception("Pika Labs API密钥未配置")
            
            # 验证任务参数
            self.validate_task(task)
            
            # Pika Labs特殊参数处理
            if task.duration > 4:
                self.logger.warning(f"Pika Labs最大支持4秒视频，将调整为4秒")
                task.duration = 4
            
            # 准备请求数据
            request_data = {
                "model": self.model,
                "prompt": self._prepare_prompt(task),
                "duration": task.duration,
                "aspect_ratio": self._convert_resolution_to_aspect_ratio(task.resolution),
                "fps": task.fps
            }
            
            if task.negative_prompt:
                request_data["negative_prompt"] = task.negative_prompt
            
            if task.guidance_scale != 7.5:
                request_data["guidance_scale"] = task.guidance_scale
            
            if task.seed:
                request_data["seed"] = task.seed
            
            # 发送生成请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generate",
                    json=request_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        task.task_id = result.get('id', task.task_id)
                        task.status = TaskStatus.PROCESSING
                        
                        # 存储任务
                        self._tasks[task.task_id] = task
                        
                        self.logger.info(f"Pika Labs视频生成任务已提交: {task.task_id}")
                        
                        # 等待生成完成
                        return await self._wait_for_completion(task)
                    else:
                        error_msg = await response.text()
                        raise Exception(f"Pika Labs API错误: {response.status} - {error_msg}")
                        
        except Exception as e:
            self.logger.error(f"Pika Labs视频生成失败: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return task
    
    def _convert_resolution_to_aspect_ratio(self, resolution: str) -> str:
        """
        将分辨率转换为Pika Labs的宽高比格式
        
        Args:
            resolution: 分辨率字符串，如"1920x1080"
            
        Returns:
            宽高比字符串
        """
        resolution_map = {
            "1920x1080": "16:9",
            "1280x720": "16:9",
            "1024x576": "16:9",
            "720x1280": "9:16",
            "576x1024": "9:16",
            "1024x1024": "1:1"
        }
        
        return resolution_map.get(resolution, "16:9")
    
    async def _wait_for_completion(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        等待任务完成
        
        Args:
            task: 视频生成任务
            
        Returns:
            完成的任务对象
        """
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 5   # 每5秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            try:
                updated_task = await self.get_task_status(task.task_id)
                
                if updated_task.status == TaskStatus.COMPLETED:
                    self.logger.info(f"Pika Labs视频生成完成: {task.task_id}")
                    return updated_task
                elif updated_task.status == TaskStatus.FAILED:
                    self.logger.error(f"Pika Labs视频生成失败: {updated_task.error_message}")
                    return updated_task
                
                # 更新进度
                task.progress = updated_task.progress
                
                await asyncio.sleep(check_interval)
                waited_time += check_interval
                
            except Exception as e:
                self.logger.warning(f"检查任务状态时出错: {str(e)}")
                await asyncio.sleep(check_interval)
                waited_time += check_interval
        
        # 超时
        task.status = TaskStatus.FAILED
        task.error_message = "任务超时"
        return task
    
    async def get_task_status(self, task_id: str) -> VideoGenerationTask:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/generate/{task_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 获取本地任务对象
                        task = self._tasks.get(task_id)
                        if not task:
                            # 创建新的任务对象
                            task = VideoGenerationTask(
                                task_id=task_id,
                                prompt=result.get('prompt', ''),
                            )
                        
                        # 更新状态
                        status_map = {
                            "pending": TaskStatus.PENDING,
                            "processing": TaskStatus.PROCESSING,
                            "completed": TaskStatus.COMPLETED,
                            "failed": TaskStatus.FAILED
                        }
                        
                        pika_status = result.get('status', 'pending')
                        task.status = status_map.get(pika_status, TaskStatus.PENDING)
                        
                        # 计算进度
                        if pika_status == 'completed':
                            task.progress = 100.0
                            task.output_path = result.get('video_url')
                        elif pika_status == 'processing':
                            task.progress = result.get('progress', 50.0)
                        elif pika_status == 'failed':
                            task.error_message = result.get('error', '未知错误')
                        
                        return task
                    else:
                        raise Exception(f"获取任务状态失败: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"获取任务状态时出错: {str(e)}")
            # 返回失败状态的任务
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                return task
            else:
                return VideoGenerationTask(
                    task_id=task_id,
                    prompt="",
                    status=TaskStatus.FAILED,
                    error_message=str(e)
                )
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/generate/{task_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        # 更新本地任务状态
                        if task_id in self._tasks:
                            self._tasks[task_id].status = TaskStatus.CANCELLED
                        return True
                    else:
                        return False
                        
        except Exception as e:
            self.logger.error(f"取消任务时出错: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            if not self.api_key or self.api_key == 'your-pika-api-key-here':
                return {
                    "status": "unhealthy",
                    "backend": "Pika Labs",
                    "error": "API密钥未配置"
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "backend": "Pika Labs",
                            "model": self.model,
                            "api_url": self.base_url
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "backend": "Pika Labs",
                            "error": f"API返回状态码: {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "Pika Labs",
                "error": str(e)
            }