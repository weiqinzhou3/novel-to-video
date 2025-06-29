#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多后端视频生成器测试脚本

用于测试新的多后端视频生成架构
"""

import asyncio
import json
import logging
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.video_generator import VideoGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_test_config():
    """加载测试配置"""
    config_paths = [
        'config/config.json',
        'config.json',
        'config/config.example.json'
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"成功加载配置文件: {config_path}")
                return config
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误 ({config_path}): {e}")
            continue
    
    print("错误: 找不到可用的配置文件")
    print("请确保以下文件之一存在:")
    for path in config_paths:
        print(f"  - {path}")
    return None

async def test_backend_status(generator):
    """测试后端状态"""
    print("\n=== 测试后端状态 ===")
    
    # 获取支持的后端
    backends = generator.get_supported_backends()
    print(f"支持的后端: {backends}")
    
    # 获取后端状态
    status = generator.get_backend_status()
    print("\n后端状态:")
    for name, info in status.items():
        enabled = "✓" if info.get('enabled', False) else "✗"
        priority = info.get('priority', 'N/A')
        print(f"  {enabled} {name} (优先级: {priority})")
    
    # 健康检查
    print("\n执行健康检查...")
    health = await generator.health_check()
    print(f"健康状态: {health.get('status', 'unknown')}")
    
    if health.get('backends'):
        print("各后端健康状态:")
        for name, backend_health in health['backends'].items():
            status_icon = "✓" if backend_health.get('healthy', False) else "✗"
            print(f"  {status_icon} {name}: {backend_health.get('status', 'unknown')}")

async def test_video_generation(generator):
    """测试视频生成"""
    print("\n=== 测试视频生成 ===")
    
    # 测试场景
    test_scenes = [
        {
            'description': '一个美丽的日出场景，阳光透过云层洒向大地',
            'duration': 3,
            'resolution': '1280x720',
            'fps': 24
        },
        {
            'description': '一只可爱的小猫在花园里玩耍',
            'duration': 4,
            'resolution': '1280x720',
            'fps': 24
        }
    ]
    
    print(f"准备生成 {len(test_scenes)} 个视频...")
    
    try:
        # 生成视频
        results = await generator.generate_videos(test_scenes)
        
        print("\n生成结果:")
        for i, result in enumerate(results):
            scene_num = i + 1
            if result['success']:
                print(f"  ✓ 场景 {scene_num}: 成功")
                print(f"    - 后端: {result.get('backend_used', 'unknown')}")
                print(f"    - 文件: {result.get('video_path', 'N/A')}")
                print(f"    - 时长: {result.get('duration', 'N/A')}s")
            else:
                print(f"  ✗ 场景 {scene_num}: 失败")
                print(f"    - 错误: {result.get('error', 'unknown')}")
        
        # 统计信息
        success_count = sum(1 for r in results if r['success'])
        print(f"\n总结: {success_count}/{len(results)} 个视频生成成功")
        
        return results
        
    except Exception as e:
        print(f"视频生成过程中出错: {e}")
        return []

async def test_task_management(generator):
    """测试任务管理"""
    print("\n=== 测试任务管理 ===")
    
    # 创建一个测试任务
    test_scene = {
        'description': '测试任务管理功能',
        'duration': 2,
        'resolution': '1280x720'
    }
    
    try:
        print("创建测试任务...")
        result = await generator.generate_single_video(test_scene)
        
        if result['success']:
            task_id = result.get('task_id')
            if task_id:
                print(f"任务创建成功，ID: {task_id}")
                
                # 查询任务状态
                status = await generator.get_task_status(task_id)
                if status:
                    print(f"任务状态: {status.get('status', 'unknown')}")
                    print(f"进度: {status.get('progress', 0)}%")
                else:
                    print("无法获取任务状态")
            else:
                print("任务ID不可用")
        else:
            print(f"任务创建失败: {result.get('error', 'unknown')}")
            
    except Exception as e:
        print(f"任务管理测试失败: {e}")

async def test_statistics(generator):
    """测试统计信息"""
    print("\n=== 测试统计信息 ===")
    
    try:
        stats = generator.get_statistics()
        print("生成统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"获取统计信息失败: {e}")

async def main():
    """主测试函数"""
    print("多后端视频生成器测试")
    print("=" * 50)
    
    # 加载配置
    config = load_test_config()
    if not config:
        return
    
    try:
        # 创建视频生成器
        generator = VideoGenerator(config)
        print("视频生成器初始化成功")
        
        # 运行测试
        await test_backend_status(generator)
        await test_video_generation(generator)
        await test_task_management(generator)
        await test_statistics(generator)
        
        print("\n=== 测试完成 ===")
        print("多后端架构测试成功完成！")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())