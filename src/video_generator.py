#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成模块

负责根据文本描述和音频生成视频内容
支持多种视频生成服务：SVD、Runway、Pika Labs、Luma Dream Machine等
"""

import os
import json
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional

from video_backends.multi_backend_generator import MultiBackendVideoGenerator
from video_backends.base_backend import VideoGenerationTask, TaskStatus


class VideoGenerator:
    """视频生成器 - 重构为多后端架构"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 视频生成配置
        video_config = config.get('video_generation', {})
        self.max_concurrent = config.get('performance', {}).get('max_concurrent_requests', 3)
        self.request_timeout = config.get('performance', {}).get('request_timeout', 300)
        
        # 初始化多后端生成器
        self.multi_backend = MultiBackendVideoGenerator(config)
        
        self.logger.info(f"视频生成器初始化完成，支持多后端架构")
        
        # 显示可用后端
        backend_status = self.multi_backend.get_backend_status()
        enabled_backends = [name for name, status in backend_status.items() if status['enabled']]
        self.logger.info(f"已启用的后端: {', '.join(enabled_backends)}")
    
    async def generate_videos(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量生成视频
        
        Args:
            scenes: 场景列表，每个场景包含描述、音频等信息
            
        Returns:
            生成结果列表
        """
        self.logger.info(f"开始批量生成 {len(scenes)} 个视频")
        
        # 创建任务
        tasks = []
        for i, scene in enumerate(scenes):
            task = VideoGenerationTask(
                task_id=str(uuid.uuid4()),
                prompt=scene.get('description', ''),
                duration=scene.get('duration', 5),
                resolution=scene.get('resolution', '1280x720'),
                fps=scene.get('fps', 24),
                guidance_scale=scene.get('guidance_scale', 7.5),
                num_inference_steps=scene.get('num_inference_steps', 25),
                seed=scene.get('seed'),
                negative_prompt=scene.get('negative_prompt'),
                input_image=scene.get('input_image')
            )
            tasks.append(task)
        
        # 并发生成
        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def generate_single(task):
            async with semaphore:
                return await self.multi_backend.generate_video(task)
        
        # 执行所有任务
        completed_tasks = await asyncio.gather(
            *[generate_single(task) for task in tasks],
            return_exceptions=True
        )
        
        # 处理结果
        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"场景 {i} 生成失败: {str(result)}")
                results.append({
                    'scene_index': i,
                    'success': False,
                    'error': str(result),
                    'video_path': None
                })
            else:
                success = result.status == TaskStatus.COMPLETED
                results.append({
                    'scene_index': i,
                    'success': success,
                    'error': result.error_message if not success else None,
                    'video_path': result.output_path if success else None,
                    'task_id': result.task_id,
                    'backend_used': getattr(result, 'backend_used', 'unknown'),
                    'duration': result.duration,
                    'resolution': result.resolution
                })
        
        success_count = sum(1 for r in results if r['success'])
        self.logger.info(f"批量生成完成: {success_count}/{len(scenes)} 成功")
        
        return results
    
    async def generate_single_video(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成单个视频
        
        Args:
            scene: 场景信息
            
        Returns:
            生成结果
        """
        try:
            # 创建任务
            task = VideoGenerationTask(
                task_id=str(uuid.uuid4()),
                prompt=scene.get('description', ''),
                duration=scene.get('duration', 5),
                resolution=scene.get('resolution', '1280x720'),
                fps=scene.get('fps', 24),
                guidance_scale=scene.get('guidance_scale', 7.5),
                num_inference_steps=scene.get('num_inference_steps', 25),
                seed=scene.get('seed'),
                negative_prompt=scene.get('negative_prompt'),
                input_image=scene.get('input_image')
            )
            
            # 生成视频
            result = await self.multi_backend.generate_video(task)
            
            success = result.status == TaskStatus.COMPLETED
            return {
                'success': success,
                'error': result.error_message if not success else None,
                'video_path': result.output_path if success else None,
                'task_id': result.task_id,
                'backend_used': getattr(result, 'backend_used', 'unknown'),
                'duration': result.duration,
                'resolution': result.resolution
            }
            
        except Exception as e:
            self.logger.error(f"生成视频时出错: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_path': None
            }
    
    async def get_task_status(self, task_id: str, backend_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            backend_name: 后端名称（可选）
            
        Returns:
            任务状态信息
        """
        try:
            task = await self.multi_backend.get_task_status(task_id, backend_name)
            if task:
                return {
                    'task_id': task.task_id,
                    'status': task.status.value,
                    'progress': task.progress,
                    'output_path': task.output_path,
                    'error_message': task.error_message,
                    'backend_used': getattr(task, 'backend_used', 'unknown')
                }
            return None
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {str(e)}")
            return None
    
    def get_backend_status(self) -> Dict[str, Any]:
        """
        获取所有后端状态
        
        Returns:
            后端状态信息
        """
        try:
            return self.multi_backend.get_backend_status()
        except Exception as e:
            self.logger.error(f"获取后端状态失败: {str(e)}")
            return {}
    
    async def cancel_task(self, task_id: str, backend_name: Optional[str] = None) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            backend_name: 后端名称（可选）
            
        Returns:
            是否成功取消
        """
        try:
            return await self.multi_backend.cancel_task(task_id, backend_name)
        except Exception as e:
            self.logger.error(f"取消任务失败: {str(e)}")
            return False
    
    def get_supported_backends(self) -> List[str]:
        """
        获取支持的后端列表
        
        Returns:
            后端名称列表
        """
        return list(self.multi_backend.backends.keys())
    
    def set_backend_priority(self, priorities: List[str]) -> bool:
        """
        设置后端优先级
        
        Args:
            priorities: 后端优先级列表
            
        Returns:
            是否设置成功
        """
        try:
            self.multi_backend.set_backend_priority(priorities)
            self.logger.info(f"后端优先级已更新: {priorities}")
            return True
        except Exception as e:
            self.logger.error(f"设置后端优先级失败: {str(e)}")
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
            
        Returns:
            清理的文件数量
        """
        try:
            return self.multi_backend.cleanup_temp_files(max_age_hours)
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {str(e)}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Returns:
            统计信息
        """
        try:
            return self.multi_backend.get_statistics()
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            return await self.multi_backend.health_check()
        except Exception as e:
            self.logger.error(f"健康检查失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    # 保留验证和工具方法
    
    def validate_video(self, video_path: str) -> bool:
        """验证视频文件
        
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
            if file_size < 1024:  # 小于1KB
                self.logger.error(f"视频文件过小: {video_path}, 大小: {file_size}字节")
                return False
            
            # 可以添加更多验证逻辑，如使用ffprobe检查视频格式
            
            self.logger.info(f"视频文件验证通过: {video_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"视频文件验证失败: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        try:
            import subprocess
            
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # 提取关键信息
                video_stream = None
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                if video_stream:
                    return {
                        'duration': float(info.get('format', {}).get('duration', 0)),
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                        'codec': video_stream.get('codec_name', ''),
                        'bitrate': int(info.get('format', {}).get('bit_rate', 0))
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    test_config = {
        'api_keys': {
            'runway': {
                'api_key': 'your-runway-api-key-here'
            },
            'pika_labs': {
                'api_key': 'your-pika-api-key-here'
            },
            'luma_dream_machine': {
                'api_key': 'your-luma-api-key-here'
            }
        },
        'video_generation': {
            'backends': {
                'svd': {
                    'enabled': True,
                    'priority': 1,
                    'endpoint': 'http://localhost:8000'
                },
                'runway': {
                    'enabled': True,
                    'priority': 2,
                    'model': 'gen4-turbo'
                },
                'pika_labs': {
                    'enabled': False,
                    'priority': 3
                },
                'luma_dream_machine': {
                    'enabled': False,
                    'priority': 4
                }
            },
            'default_backend': 'svd',
            'fallback_enabled': True,
            'resolution': '1280x720',
            'fps': 24,
            'duration': 5
        },
        'performance': {
            'max_concurrent_requests': 2,
            'request_timeout': 300
        }
    }
    
    async def test_generator():
        generator = VideoGenerator(test_config)
        
        test_scenes = [
            {
                'description': '一个古老的城堡在夕阳下显得格外神秘',
                'duration': 4,
                'resolution': '1280x720'
            }
        ]
        
        try:
            results = await generator.generate_videos(test_scenes)
            print(f"视频生成结果: {results}")
            
            # 检查后端状态
            status = generator.get_backend_status()
            print(f"后端状态: {status}")
            
        except Exception as e:
            print(f"视频生成失败: {e}")
    
    # 运行测试
    asyncio.run(test_generator())