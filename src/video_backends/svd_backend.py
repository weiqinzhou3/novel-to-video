# -*- coding: utf-8 -*-
"""
Stable Video Diffusion 后端

支持本地和远程SVD服务
"""

import asyncio
import aiohttp
import uuid
from typing import Dict, Any, Optional
from .base_backend import BaseVideoBackend, VideoGenerationTask, TaskStatus, BackendCapabilities


class SVDBackend(BaseVideoBackend):
    """Stable Video Diffusion 后端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.svd_config = config.get('svd', {})
        self.api_url = self.svd_config.get('api_url', 'http://localhost:8000')
        self.timeout = self.svd_config.get('timeout', 300)
        self.max_retries = self.svd_config.get('max_retries', 3)
        
        # 任务存储
        self._tasks = {}
        
        self.logger.info(f"SVD后端初始化完成，API地址: {self.api_url}")
    
    def _get_capabilities(self) -> BackendCapabilities:
        """获取SVD后端能力"""
        return BackendCapabilities(
            name="Stable Video Diffusion",
            supports_text_to_video=True,
            supports_image_to_video=True,
            supports_video_to_video=False,
            max_duration=8,
            supported_resolutions=["576x1024", "1024x576", "768x768"],
            supported_fps=[6, 12, 24],
            cost_per_second=0.0,  # 本地运行免费
            requires_gpu=True,
            is_local=True
        )
    
    def get_capabilities(self) -> BackendCapabilities:
        """获取后端能力（公共接口）"""
        return self._get_capabilities()
    
    async def generate_video(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        使用SVD生成视频
        
        Args:
            task: 视频生成任务
            
        Returns:
            更新后的任务对象
        """
        try:
            # 验证任务参数
            self.validate_task(task)
            
            # 准备请求数据
            request_data = {
                "prompt": self._prepare_prompt(task),
                "negative_prompt": task.negative_prompt or "",
                "num_frames": min(task.duration * task.fps, 25),  # SVD最大25帧
                "width": int(task.resolution.split('x')[0]),
                "height": int(task.resolution.split('x')[1]),
                "num_inference_steps": task.num_inference_steps,
                "guidance_scale": task.guidance_scale,
                "seed": task.seed or -1
            }
            
            # 发送生成请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.api_url}/generate",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        task.task_id = result.get('task_id', task.task_id)
                        task.status = TaskStatus.PROCESSING
                        
                        # 存储任务
                        self._tasks[task.task_id] = task
                        
                        self.logger.info(f"SVD视频生成任务已提交: {task.task_id}")
                        
                        # 等待生成完成
                        return await self._wait_for_completion(task)
                    else:
                        error_msg = await response.text()
                        raise Exception(f"SVD API错误: {response.status} - {error_msg}")
                        
        except Exception as e:
            self.logger.error(f"SVD视频生成失败: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return task
    
    async def _wait_for_completion(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        等待任务完成
        
        Args:
            task: 视频生成任务
            
        Returns:
            完成的任务对象
        """
        max_wait_time = 600  # 最大等待10分钟
        check_interval = 5   # 每5秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            try:
                updated_task = await self.get_task_status(task.task_id)
                
                if updated_task.status == TaskStatus.COMPLETED:
                    self.logger.info(f"SVD视频生成完成: {task.task_id}")
                    return updated_task
                elif updated_task.status == TaskStatus.FAILED:
                    self.logger.error(f"SVD视频生成失败: {updated_task.error_message}")
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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/status/{task_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 获取本地任务对象
                        task = self._tasks.get(task_id)
                        if not task:
                            # 创建新的任务对象
                            task = VideoGenerationTask(
                                task_id=task_id,
                                prompt="",  # 从API获取的状态可能不包含原始prompt
                            )
                        
                        # 更新状态
                        status_map = {
                            "pending": TaskStatus.PENDING,
                            "processing": TaskStatus.PROCESSING,
                            "completed": TaskStatus.COMPLETED,
                            "failed": TaskStatus.FAILED
                        }
                        
                        task.status = status_map.get(result.get('status'), TaskStatus.PENDING)
                        task.progress = result.get('progress', 0.0)
                        task.output_path = result.get('output_path')
                        task.error_message = result.get('error_message')
                        
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
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.api_url}/cancel/{task_id}") as response:
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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health") as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "healthy",
                            "backend": "SVD",
                            "api_url": self.api_url,
                            "gpu_info": result.get('gpu_info', {}),
                            "model_loaded": result.get('model_loaded', False),
                            "queue_size": result.get('queue_size', 0)
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "backend": "SVD",
                            "error": f"API返回状态码: {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "SVD",
                "error": str(e)
            }