#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理使用示例
演示如何使用配置管理器进行各种配置操作
"""

from config_manager import ConfigManager
import json

def main():
    """配置管理示例"""
    print("=" * 50)
    print("SVD 服务配置管理示例")
    print("=" * 50)
    
    # 创建配置管理器实例
    config = ConfigManager("config.json")
    
    print("\n1. 基本配置读取:")
    print("-" * 30)
    
    # 读取服务器配置
    server_config = config.get_server_config()
    print(f"服务器主机: {server_config.get('host')}")
    print(f"服务器端口: {server_config.get('port')}")
    print(f"备用端口: {config.get_fallback_ports()}")
    
    # 读取模型配置
    model_config = config.get_model_config()
    print(f"模型名称: {model_config.get('name')}")
    print(f"设备配置: {model_config.get('device')}")
    print(f"数据类型: {model_config.get('torch_dtype')}")
    
    print("\n2. 生成参数配置:")
    print("-" * 30)
    
    # 读取生成配置
    gen_config = config.get_generation_config()
    print(f"默认帧数: {gen_config.get('default_num_frames')}")
    print(f"最大帧数: {gen_config.get('max_num_frames')}")
    print(f"默认分辨率: {gen_config.get('default_width')}x{gen_config.get('default_height')}")
    print(f"默认推理步数: {gen_config.get('default_num_inference_steps')}")
    print(f"默认引导强度: {gen_config.get('default_guidance_scale')}")
    print(f"帧率: {gen_config.get('fps')}")
    
    print("\n3. 存储和性能配置:")
    print("-" * 30)
    
    # 读取存储配置
    storage_config = config.get_storage_config()
    print(f"输出目录: {storage_config.get('output_dir')}")
    print(f"最大存储空间: {storage_config.get('max_storage_gb')} GB")
    print(f"自动清理: {storage_config.get('auto_cleanup')}")
    print(f"清理周期: {storage_config.get('cleanup_after_days')} 天")
    
    # 读取性能配置
    perf_config = config.get('performance', {})
    print(f"最大并发任务: {perf_config.get('max_concurrent_tasks')}")
    print(f"任务超时: {perf_config.get('task_timeout_minutes')} 分钟")
    
    print("\n4. 安全和监控配置:")
    print("-" * 30)
    
    # 读取安全配置
    security_config = config.get_security_config()
    print(f"启用CORS: {security_config.get('enable_cors')}")
    print(f"允许的源: {security_config.get('allowed_origins')}")
    print(f"最大文件大小: {security_config.get('max_file_size_mb')} MB")
    print(f"速率限制: {security_config.get('rate_limit_per_minute')} 次/分钟")
    
    # 读取监控配置
    monitoring_config = config.get_monitoring_config()
    print(f"启用健康检查: {monitoring_config.get('enable_health_check')}")
    print(f"性能监控: {monitoring_config.get('log_performance_metrics')}")
    print(f"GPU监控: {monitoring_config.get('enable_gpu_monitoring')}")
    
    print("\n5. Hugging Face配置:")
    print("-" * 30)
    
    # 读取Hugging Face配置
    hf_config = config.get_huggingface_config()
    print(f"Token环境变量: {hf_config.get('token_env_var')}")
    print(f"自动登录: {hf_config.get('auto_login')}")
    print(f"缓存目录环境变量: {hf_config.get('cache_dir_env_var')}")
    print(f"禁用符号链接警告: {hf_config.get('disable_symlinks_warning')}")
    
    # 获取实际的token值
    token = config.get_huggingface_token()
    if token:
        print(f"当前Token: {token[:10]}...{token[-10:] if len(token) > 20 else token[10:]}")
    else:
        print("当前Token: 未设置")
    
    print("\n6. 配置验证:")
    print("-" * 30)
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("✅ 配置验证通过")
    
    print("\n7. 动态配置修改示例:")
    print("-" * 30)
    
    # 修改配置示例（不保存到文件）
    original_port = config.get('server.port')
    print(f"原始端口: {original_port}")
    
    # 临时修改端口
    config.set('server.port', 8080)
    print(f"修改后端口: {config.get('server.port')}")
    
    # 恢复原始端口
    config.set('server.port', original_port)
    print(f"恢复后端口: {config.get('server.port')}")
    
    print("\n8. 环境设置:")
    print("-" * 30)
    
    # 设置环境变量
    print("正在设置环境变量...")
    config.setup_environment()
    print("✅ 环境变量设置完成")
    
    print("\n" + "=" * 50)
    print("配置管理示例完成")
    print("=" * 50)

def show_config_structure():
    """显示完整的配置结构"""
    config = ConfigManager("config.json")
    
    print("\n完整配置结构:")
    print("=" * 50)
    print(json.dumps(config._config, indent=2, ensure_ascii=False))

def create_custom_config():
    """创建自定义配置示例"""
    print("\n创建自定义配置示例:")
    print("=" * 50)
    
    # 创建新的配置管理器
    custom_config = ConfigManager("custom_config.json")
    
    # 设置自定义配置
    custom_config.set('server.port', 9000)
    custom_config.set('model.device', 'cpu')
    custom_config.set('generation.default_num_frames', 15)
    custom_config.set('storage.output_dir', 'custom_outputs')
    
    # 保存配置
    custom_config.save_config()
    print("✅ 自定义配置已保存到 custom_config.json")
    
    # 显示自定义配置
    print("\n自定义配置内容:")
    print(f"端口: {custom_config.get('server.port')}")
    print(f"设备: {custom_config.get('model.device')}")
    print(f"默认帧数: {custom_config.get('generation.default_num_frames')}")
    print(f"输出目录: {custom_config.get('storage.output_dir')}")

if __name__ == "__main__":
    try:
        main()
        
        # 可选：显示完整配置结构
        show_structure = input("\n是否显示完整配置结构？(y/N): ").lower().strip()
        if show_structure == 'y':
            show_config_structure()
        
        # 可选：创建自定义配置
        create_custom = input("\n是否创建自定义配置示例？(y/N): ").lower().strip()
        if create_custom == 'y':
            create_custom_config()
            
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()