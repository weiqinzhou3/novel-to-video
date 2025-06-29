# -*- coding: utf-8 -*-
"""
配置管理模块
用于加载和管理SVD服务的配置
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"配置文件已加载: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._config = self._get_default_config()
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self.get('server', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.get('model', {})
    
    def get_generation_config(self) -> Dict[str, Any]:
        """获取生成配置"""
        return self.get('generation', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get('storage', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get('security', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_huggingface_config(self) -> Dict[str, Any]:
        """获取Hugging Face配置"""
        return self.get('huggingface', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get('monitoring', {})
    
    def get_fallback_ports(self) -> List[int]:
        """获取备用端口列表"""
        return self.get('server.fallback_ports', [8001, 8002, 8003, 8004, 8005])
    
    def get_huggingface_token(self) -> Optional[str]:
        """获取Hugging Face token"""
        token_env_var = self.get('huggingface.token_env_var', 'HUGGINGFACE_TOKEN')
        return os.getenv(token_env_var)
    
    def setup_environment(self) -> None:
        """设置环境变量"""
        # 设置Hugging Face缓存目录
        cache_dir_env = self.get('huggingface.cache_dir_env_var', 'HF_HOME')
        if cache_dir_env and not os.getenv(cache_dir_env):
            cache_dir = self.get('storage.cache_dir')
            if cache_dir:
                os.environ[cache_dir_env] = str(cache_dir)
        
        # 禁用符号链接警告
        if self.get('huggingface.disable_symlinks_warning', True):
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    
    def validate_config(self) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 验证服务器配置
        server_config = self.get_server_config()
        if not isinstance(server_config.get('port'), int) or server_config.get('port') <= 0:
            errors.append("服务器端口必须是正整数")
        
        # 验证模型配置
        model_config = self.get_model_config()
        if not model_config.get('name'):
            errors.append("模型名称不能为空")
        
        # 验证生成配置
        gen_config = self.get_generation_config()
        max_frames = gen_config.get('max_num_frames', 25)
        if not isinstance(max_frames, int) or max_frames <= 0:
            errors.append("最大帧数必须是正整数")
        
        return errors
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "fallback_ports": [8001, 8002, 8003, 8004, 8005],
                "log_level": "info",
                "access_log": True,
                "workers": 1
            },
            "model": {
                "name": "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
                "device": "auto",
                "torch_dtype": "auto",
                "variant": "fp16",
                "enable_cpu_offload": True,
                "enable_vae_slicing": True,
                "enable_attention_slicing": True
            },
            "generation": {
                "default_num_frames": 25,
                "max_num_frames": 25,
                "default_width": 1024,
                "default_height": 576,
                "max_width": 1024,
                "max_height": 576,
                "default_num_inference_steps": 25,
                "max_num_inference_steps": 50,
                "default_guidance_scale": 7.5,
                "fps": 8
            },
            "storage": {
                "output_dir": "outputs",
                "max_storage_gb": 10,
                "cleanup_after_days": 7,
                "auto_cleanup": True
            },
            "performance": {
                "max_concurrent_tasks": 2,
                "task_timeout_minutes": 30,
                "memory_cleanup_interval": 300
            },
            "security": {
                "enable_cors": True,
                "allowed_origins": ["*"],
                "max_file_size_mb": 50,
                "rate_limit_per_minute": 10
            },
            "logging": {
                "log_file": "svd_server.log",
                "max_log_size_mb": 100,
                "backup_count": 5,
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "huggingface": {
                "token_env_var": "HUGGINGFACE_TOKEN",
                "auto_login": True,
                "cache_dir_env_var": "HF_HOME",
                "disable_symlinks_warning": True
            },
            "monitoring": {
                "enable_health_check": True,
                "health_check_interval_seconds": 30,
                "log_performance_metrics": True,
                "enable_gpu_monitoring": True
            }
        }

# 全局配置实例
config = ConfigManager()