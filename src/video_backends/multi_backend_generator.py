# -*- coding: utf-8 -*-
"""
多后端视频生成器

统一管理多个视频生成后端，支持自动故障转移和负载均衡
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .base_backend import BaseVideoBackend, VideoGenerationTask, TaskStatus, BackendCapabilities
from .runway_backend import RunwayBackend
from .svd_backend import SVDBackend
from .pika_backend import PikaBackend
from .luma_backend import LumaBackend


class BackendPriority(Enum):
    """后端优先级"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3


@dataclass
class BackendConfig:
    """后端配置"""
    name: str
    backend_class: type
    priority: BackendPriority
    enabled: bool = True
    max_concurrent_tasks: int = 5
    health_check_interval: int = 60  # 秒


class MultiBackendVideoGenerator:
    """多后端视频生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 后端配置
        self.backend_configs = {
            'svd': BackendConfig(
                name='SVD',
                backend_class=SVDBackend,
                priority=BackendPriority.PRIMARY,
                enabled=config.get('video_generation', {}).get('backends', {}).get('svd', {}).get('enabled', True),
                max_concurrent_tasks=config.get('video_generation', {}).get('backends', {}).get('svd', {}).get('max_concurrent', 3)
            ),
            'pika': BackendConfig(
                name='Pika Labs',
                backend_class=PikaBackend,
                priority=BackendPriority.SECONDARY,
                enabled=config.get('video_generation', {}).get('backends', {}).get('pika', {}).get('enabled', True),
                max_concurrent_tasks=config.get('video_generation', {}).get('backends', {}).get('pika', {}).get('max_concurrent', 5)
            ),
            'luma': BackendConfig(
                name='Luma Dream Machine',
                backend_class=LumaBackend,
                priority=BackendPriority.SECONDARY,
                enabled=config.get('video_generation', {}).get('backends', {}).get('luma', {}).get('enabled', True),
                max_concurrent_tasks=config.get('video_generation', {}).get('backends', {}).get('luma', {}).get('max_concurrent', 5)
            ),
            'runway': BackendConfig(
                name='Runway',
                backend_class=RunwayBackend,
                priority=BackendPriority.FALLBACK,
                enabled=config.get('video_generation', {}).get('backends', {}).get('runway', {}).get('enabled', False),
                max_concurrent_tasks=config.get('video_generation', {}).get('backends', {}).get('runway', {}).get('max_concurrent', 3)
            )
        }
        
        # 初始化后端实例
        self.backends: Dict[str, BaseVideoBackend] = {}
        self.backend_health: Dict[str, bool] = {}
        self.backend_tasks: Dict[str, int] = {}  # 当前任务数
        
        # 配置选项
        video_config = config.get('video_generation', {})
        self.load_balancing_enabled = video_config.get('load_balancing', True)
        self.fallback_enabled = video_config.get('fallback_enabled', True)
        
        self._initialize_backends()
        
        # 启动健康检查
        self._health_check_task = None
        self._start_health_check()
    
    def _initialize_backends(self):
        """初始化所有启用的后端"""
        for backend_name, backend_config in self.backend_configs.items():
            if backend_config.enabled:
                try:
                    backend_instance = backend_config.backend_class(self.config)
                    self.backends[backend_name] = backend_instance
                    self.backend_health[backend_name] = True
                    self.backend_tasks[backend_name] = 0
                    self.logger.info(f"后端 {backend_config.name} 初始化成功")
                except Exception as e:
                    self.logger.error(f"后端 {backend_config.name} 初始化失败: {str(e)}")
                    self.backend_health[backend_name] = False
    
    def _start_health_check(self):
        """启动健康检查任务"""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._check_all_backends_health()
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"健康检查出错: {str(e)}")
                await asyncio.sleep(60)
    
    async def _check_all_backends_health(self):
        """检查所有后端健康状态"""
        for backend_name, backend in self.backends.items():
            try:
                health_info = await backend.health_check()
                is_healthy = health_info.get('status') == 'healthy'
                
                if self.backend_health[backend_name] != is_healthy:
                    self.logger.info(f"后端 {backend_name} 健康状态变更: {is_healthy}")
                    self.backend_health[backend_name] = is_healthy
                    
            except Exception as e:
                self.logger.warning(f"检查后端 {backend_name} 健康状态失败: {str(e)}")
                self.backend_health[backend_name] = False
    
    def get_available_backends(self) -> List[str]:
        """获取可用的后端列表，按优先级排序"""
        available = []
        
        # 按优先级排序
        sorted_backends = sorted(
            self.backend_configs.items(),
            key=lambda x: x[1].priority.value
        )
        
        for backend_name, config in sorted_backends:
            if (config.enabled and 
                backend_name in self.backends and 
                self.backend_health.get(backend_name, False) and
                self.backend_tasks.get(backend_name, 0) < config.max_concurrent_tasks):
                available.append(backend_name)
        
        return available
    
    def select_best_backend(self, task: VideoGenerationTask) -> Optional[str]:
        """选择最佳后端"""
        available_backends = self.get_available_backends()
        
        if not available_backends:
            return None
        
        # 根据任务需求选择后端
        for backend_name in available_backends:
            backend = self.backends[backend_name]
            capabilities = backend.get_capabilities()
            
            # 检查是否支持所需功能
            if task.input_image and not capabilities.supports_image_to_video:
                continue
            
            if task.duration > capabilities.max_duration:
                continue
            
            if task.resolution not in capabilities.supported_resolutions:
                # 尝试找到兼容的分辨率
                compatible_resolution = self._find_compatible_resolution(
                    task.resolution, capabilities.supported_resolutions
                )
                if not compatible_resolution:
                    continue
                task.resolution = compatible_resolution
            
            if task.fps not in capabilities.supported_fps:
                # 使用最接近的帧率
                task.fps = min(capabilities.supported_fps, key=lambda x: abs(x - task.fps))
            
            return backend_name
        
        return None
    
    def _find_compatible_resolution(self, requested: str, supported: List[str]) -> Optional[str]:
        """找到兼容的分辨率"""
        # 简单的分辨率映射
        resolution_map = {
            "1920x1080": ["1920x1080", "1280x720", "1024x576"],
            "1280x720": ["1280x720", "1024x576", "1920x1080"],
            "720x1280": ["720x1280", "576x1024"],
            "1024x1024": ["1024x1024", "768x768"]
        }
        
        candidates = resolution_map.get(requested, [requested])
        
        for candidate in candidates:
            if candidate in supported:
                return candidate
        
        # 如果没有找到，返回第一个支持的分辨率
        return supported[0] if supported else None
    
    async def generate_video(self, task: VideoGenerationTask) -> VideoGenerationTask:
        """
        生成视频，自动选择最佳后端
        
        Args:
            task: 视频生成任务
            
        Returns:
            完成的任务对象
        """
        # 选择后端
        backend_name = self.select_best_backend(task)
        
        if not backend_name:
            task.status = TaskStatus.FAILED
            task.error_message = "没有可用的后端"
            return task
        
        backend = self.backends[backend_name]
        
        try:
            # 增加任务计数
            self.backend_tasks[backend_name] += 1
            
            self.logger.info(f"使用后端 {backend_name} 生成视频: {task.task_id}")
            
            # 执行生成
            result = await backend.generate_video(task)
            
            # 记录后端信息
            result.backend_used = backend_name
            
            return result
            
        except Exception as e:
            self.logger.error(f"后端 {backend_name} 生成视频失败: {str(e)}")
            
            # 标记后端不健康
            self.backend_health[backend_name] = False
            
            # 尝试故障转移
            return await self._failover_generate(task, exclude_backends=[backend_name])
            
        finally:
            # 减少任务计数
            if backend_name in self.backend_tasks:
                self.backend_tasks[backend_name] = max(0, self.backend_tasks[backend_name] - 1)
    
    async def _failover_generate(self, task: VideoGenerationTask, exclude_backends: List[str]) -> VideoGenerationTask:
        """故障转移生成"""
        available_backends = [b for b in self.get_available_backends() if b not in exclude_backends]
        
        if not available_backends:
            task.status = TaskStatus.FAILED
            task.error_message = "所有后端都不可用"
            return task
        
        backend_name = available_backends[0]
        backend = self.backends[backend_name]
        
        try:
            self.backend_tasks[backend_name] += 1
            
            self.logger.info(f"故障转移到后端 {backend_name}: {task.task_id}")
            
            result = await backend.generate_video(task)
            result.backend_used = backend_name
            
            return result
            
        except Exception as e:
            self.logger.error(f"故障转移后端 {backend_name} 也失败: {str(e)}")
            
            # 继续尝试其他后端
            exclude_backends.append(backend_name)
            return await self._failover_generate(task, exclude_backends)
            
        finally:
            if backend_name in self.backend_tasks:
                self.backend_tasks[backend_name] = max(0, self.backend_tasks[backend_name] - 1)
    
    async def get_task_status(self, task_id: str, backend_name: Optional[str] = None) -> Optional[VideoGenerationTask]:
        """获取任务状态"""
        if backend_name and backend_name in self.backends:
            # 指定后端查询
            try:
                return await self.backends[backend_name].get_task_status(task_id)
            except Exception as e:
                self.logger.error(f"查询任务状态失败 ({backend_name}): {str(e)}")
                return None
        else:
            # 遍历所有后端查询
            for name, backend in self.backends.items():
                try:
                    task = await backend.get_task_status(task_id)
                    if task and task.status != TaskStatus.FAILED:
                        return task
                except Exception:
                    continue
            return None
    
    async def cancel_task(self, task_id: str, backend_name: Optional[str] = None) -> bool:
        """取消任务"""
        if backend_name and backend_name in self.backends:
            # 指定后端取消
            try:
                return await self.backends[backend_name].cancel_task(task_id)
            except Exception as e:
                self.logger.error(f"取消任务失败 ({backend_name}): {str(e)}")
                return False
        else:
            # 尝试所有后端
            success = False
            for name, backend in self.backends.items():
                try:
                    if await backend.cancel_task(task_id):
                        success = True
                except Exception:
                    continue
            return success
    
    def get_backend_status(self) -> Dict[str, Any]:
        """获取所有后端状态"""
        status = {}
        
        for backend_name, backend_config in self.backend_configs.items():
            backend_status = {
                "name": backend_config.name,
                "enabled": backend_config.enabled,
                "healthy": self.backend_health.get(backend_name, False),
                "current_tasks": self.backend_tasks.get(backend_name, 0),
                "max_tasks": backend_config.max_concurrent_tasks,
                "priority": backend_config.priority.name
            }
            
            if backend_name in self.backends:
                capabilities = self.backends[backend_name].get_capabilities()
                backend_status["capabilities"] = {
                    "max_duration": capabilities.max_duration,
                    "supported_resolutions": capabilities.supported_resolutions,
                    "supported_fps": capabilities.supported_fps,
                    "cost_per_second": capabilities.cost_per_second,
                    "is_local": capabilities.is_local
                }
            
            status[backend_name] = backend_status
        
        return status
    
    async def cleanup(self):
        """清理资源"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # 清理后端资源
        for backend in self.backends.values():
            if hasattr(backend, 'cleanup'):
                try:
                    await backend.cleanup()
                except Exception as e:
                    self.logger.warning(f"清理后端资源时出错: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        health_status = {
            "overall_status": "healthy",
            "backends": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        unhealthy_count = 0
        
        for backend_name, backend in self.backends.items():
            try:
                backend_health = await backend.health_check()
                health_status["backends"][backend_name] = backend_health
                
                if backend_health.get("status") != "healthy":
                    unhealthy_count += 1
                    
            except Exception as e:
                health_status["backends"][backend_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                unhealthy_count += 1
        
        # 如果所有后端都不健康，整体状态为不健康
        if unhealthy_count == len(self.backends):
            health_status["overall_status"] = "unhealthy"
        elif unhealthy_count > 0:
            health_status["overall_status"] = "degraded"
        
        return health_status
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = sum(self.backend_tasks.values())
        healthy_backends = sum(1 for healthy in self.backend_health.values() if healthy)
        
        return {
            "total_backends": len(self.backends),
            "healthy_backends": healthy_backends,
            "total_active_tasks": total_tasks,
            "backend_tasks": dict(self.backend_tasks),
            "backend_health": dict(self.backend_health),
            "load_balancing_enabled": self.load_balancing_enabled,
            "fallback_enabled": self.fallback_enabled
        }