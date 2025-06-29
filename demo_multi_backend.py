#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多后端视频生成演示脚本

展示如何使用新的多后端架构生成视频
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

from video_generator import VideoGenerator
from video_backends.base_backend import VideoGenerationTask


def load_config():
    """加载配置文件"""
    config_paths = [
        'config/config.json',
        'config.json',
        'config/config.example.json'
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✓ 成功加载配置文件: {config_path}")
                return config
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"✗ 配置文件格式错误 ({config_path}): {e}")
            continue
    
    print("✗ 找不到可用的配置文件")
    return None


async def demo_backend_status(generator):
    """演示后端状态查询"""
    print("\n=== 后端状态 ===")
    
    # 获取支持的后端
    backends = generator.get_supported_backends()
    print(f"支持的后端: {', '.join(backends)}")
    
    # 获取后端状态
    status = generator.get_backend_status()
    for backend_name, backend_info in status.items():
        status_icon = "✓" if backend_info['healthy'] else "✗"
        print(f"  {status_icon} {backend_info['name']} (优先级: {backend_info['priority']})")
        if 'capabilities' in backend_info:
            caps = backend_info['capabilities']
            print(f"    - 最大时长: {caps['max_duration']}秒")
            print(f"    - 支持分辨率: {', '.join(caps['supported_resolutions'][:3])}...")
            print(f"    - 成本: ${caps['cost_per_second']}/秒")


async def demo_health_check(generator):
    """演示健康检查"""
    print("\n=== 健康检查 ===")
    
    try:
        health = await generator.health_check()
        print(f"整体状态: {health['overall_status']}")
        
        print("各后端健康状态:")
        for backend_name, backend_health in health['backends'].items():
            status_icon = "✓" if backend_health.get('status') == 'healthy' else "✗"
            print(f"  {status_icon} {backend_name}: {backend_health.get('status', 'unknown')}")
            if 'error' in backend_health:
                print(f"    错误: {backend_health['error']}")
    except Exception as e:
        print(f"健康检查失败: {e}")


async def demo_video_generation(generator):
    """演示视频生成"""
    print("\n=== 视频生成演示 ===")
    
    # 准备测试场景
    scenes = [
        {
            "prompt": "一只可爱的小猫在花园里玩耍，阳光明媚，画面温馨",
            "duration": 4,
            "resolution": "1280x720",
            "style_prompt": "卡通风格，色彩鲜艳"
        },
        {
            "prompt": "未来城市的夜景，霓虹灯闪烁，科技感十足",
            "duration": 3,
            "resolution": "1920x1080",
            "style_prompt": "科幻风格，蓝紫色调"
        }
    ]
    
    print(f"准备生成 {len(scenes)} 个视频...")
    
    try:
        # 批量生成视频
        results = await generator.generate_videos(scenes)
        
        print("\n生成结果:")
        success_count = 0
        for i, result in enumerate(results, 1):
            if result and result.get('status') == 'completed':
                print(f"  ✓ 场景 {i}: 成功")
                print(f"    - 输出路径: {result.get('output_path', 'N/A')}")
                print(f"    - 使用后端: {result.get('backend', 'N/A')}")
                success_count += 1
            else:
                print(f"  ✗ 场景 {i}: 失败")
                if result and 'error' in result:
                    print(f"    - 错误: {result['error']}")
        
        print(f"\n总结: {success_count}/{len(scenes)} 个视频生成成功")
        
    except Exception as e:
        print(f"视频生成过程中出错: {e}")


async def demo_statistics(generator):
    """演示统计信息"""
    print("\n=== 统计信息 ===")
    
    try:
        stats = generator.get_statistics()
        print("系统统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"获取统计信息失败: {e}")


async def main():
    """主函数"""
    print("多后端视频生成系统演示")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置文件，退出演示")
        return
    
    try:
        # 初始化视频生成器
        print("\n初始化视频生成器...")
        generator = VideoGenerator(config)
        print("✓ 视频生成器初始化成功")
        
        # 演示各项功能
        await demo_backend_status(generator)
        await demo_health_check(generator)
        await demo_video_generation(generator)
        await demo_statistics(generator)
        
        print("\n=== 演示完成 ===")
        print("多后端架构演示成功完成！")
        print("\n注意: 由于没有实际的API密钥和服务，所有后端显示为不健康是正常的。")
        print("在实际使用中，请配置正确的API密钥并确保服务可用。")
        
    except Exception as e:
        print(f"演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())