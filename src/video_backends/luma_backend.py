# -*- coding: utf-8 -*-
"""
Luma Dream Machine 后端

支持Luma Dream Machine视频生成服务
"""

import asyncio
import aiohttp
import uuid
from typing import Dict, Any, Optional
from .base_backend import BaseVideoBackend, VideoGenerationTask, TaskStatus, BackendCapabilities


class LumaBackend(BaseVideoBackend):
    """Luma Dream Machine 后端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 从video_generation.backends.luma获取配置
        luma_config = config.get('video_generation', {}).get('backends', {}).get('luma', {})
        self.api_key = luma_config.get('api_key')
        self.base_url = luma_config.get('base_url', 'https://api.lumalabs.ai/dream-machine/v1')
        self.model = luma_config.get('model', 'dream-machine-v1')
        
        if not self.api_key or self.api_key == 'your-luma-api-key-here':
            self.logger.warning("Luma Dream Machine API密钥未配置")
        
        # 任务存储
        self._tasks = {}
        
        self.logger.info(f"Luma Dream Machine后端初始化完成，模型: {self.model}")
    
    def _get_capabilities(self) -> BackendCapabilities:
        """获取Luma Dream Machine后端能力"""
        return BackendCapabilities(
            name="Luma Dream Machine",
            supports_text_to_video=True,
            supports_image_to_video=True,
            supports_video_to_video=False,
            max_duration=5,
            supported_resolutions=["1024x576", "576x1024", "768x768"],
            supported_fps=[30],
            cost_per_second=0.30,  # 约$0.30/秒
            requires_gpu=False,
            is_local=False
        )
    
    def get_capabilities(self) -> BackendCapabilities:
        """获取后端能力（公共接口）"""
        return self._get_capabilities()
    
    async def generate_video(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        使用Luma Dream Machine生成视频
        
        Args:
            task: 视频生成任务
            
        Returns:
            更新后的任务对象
        """
        try:
            # 验证API密钥
            if not self.api_key or self.api_key == 'your-luma-api-key-here':
                raise Exception("Luma Dream Machine API密钥未配置")
            
            # 验证任务参数
            self.validate_task(task)
            
            # Luma特殊参数处理
            if task.duration > 5:
                self.logger.warning(f"Luma Dream Machine最大支持5秒视频，将调整为5秒")
                task.duration = 5
            
            # 准备请求数据
            request_data = {
                "prompt": self._prepare_prompt(task),
                "aspect_ratio": self._convert_resolution_to_aspect_ratio(task.resolution),
                "loop": False
            }
            
            # Luma不支持某些参数，只保留基本参数
            if task.seed:
                request_data["seed"] = task.seed
            
            # 发送生成请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generations",
                    json=request_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        task.task_id = result.get('id', task.task_id)
                        task.status = TaskStatus.PROCESSING
                        
                        # 存储任务
                        self._tasks[task.task_id] = task
                        
                        self.logger.info(f"Luma Dream Machine视频生成任务已提交: {task.task_id}")
                        
                        # 等待生成完成
                        return await self._wait_for_completion(task)
                    else:
                        error_msg = await response.text()
                        raise Exception(f"Luma Dream Machine API错误: {response.status} - {error_msg}")
                        
        except Exception as e:
            self.logger.error(f"Luma Dream Machine视频生成失败: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return task
    
    def _convert_resolution_to_aspect_ratio(self, resolution: str) -> str:
        """
        将分辨率转换为Luma Dream Machine的宽高比格式
        
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
            "768x768": "1:1",
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
        max_wait_time = 240  # 最大等待4分钟
        check_interval = 5   # 每5秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            try:
                updated_task = await self.get_task_status(task.task_id)
                
                if updated_task.status == TaskStatus.COMPLETED:
                    self.logger.info(f"Luma Dream Machine视频生成完成: {task.task_id}")
                    return updated_task
                elif updated_task.status == TaskStatus.FAILED:
                    self.logger.error(f"Luma Dream Machine视频生成失败: {updated_task.error_message}")
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
                    f"{self.base_url}/generations/{task_id}",
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
                            "queued": TaskStatus.PENDING,
                            "dreaming": TaskStatus.PROCESSING,
                            "completed": TaskStatus.COMPLETED,
                            "failed": TaskStatus.FAILED
                        }
                        
                        luma_status = result.get('state', 'queued')
                        task.status = status_map.get(luma_status, TaskStatus.PENDING)
                        
                        # 计算进度
                        if luma_status == 'completed':
                            task.progress = 100.0
                            # Luma返回的视频URL在assets中
                            assets = result.get('assets', {})
                            if 'video' in assets:
                                task.output_path = assets['video']
                        elif luma_status == 'dreaming':
                            # Luma不提供具体进度，估算
                            task.progress = 50.0
                        elif luma_status == 'failed':
                            task.error_message = result.get('failure_reason', '未知错误')
                        
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
            # Luma Dream Machine可能不支持取消任务
            # 这里只更新本地状态
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                return True
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
            if not self.api_key or self.api_key == 'your-luma-api-key-here':
                return {
                    "status": "unhealthy",
                    "backend": "Luma Dream Machine",
                    "error": "API密钥未配置"
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 尝试获取用户信息来验证API密钥
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/user",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "backend": "Luma Dream Machine",
                            "model": self.model,
                            "api_url": self.base_url
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "backend": "Luma Dream Machine",
                            "error": f"API返回状态码: {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "Luma Dream Machine",
                "error": str(e)
            }