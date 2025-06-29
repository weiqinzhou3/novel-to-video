#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVD服务测试脚本
用于测试Windows上部署的SVD视频生成服务
"""

import requests
import json
import time
import base64
from PIL import Image
from io import BytesIO
import os

# 服务配置
SERVER_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查接口"""
    print("\n=== 测试健康检查 ===")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务健康检查通过")
            print(f"状态: {data['status']}")
            print(f"模型已加载: {data['model_loaded']}")
            print(f"队列大小: {data['queue_size']}")
            print(f"总任务数: {data['total_tasks']}")
            if data.get('gpu_info'):
                gpu = data['gpu_info']
                print(f"GPU: {gpu.get('gpu_name', 'N/A')}")
                print(f"GPU内存: {gpu.get('gpu_memory_allocated', 0)}/{gpu.get('gpu_memory_total', 0)} GB")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def create_test_image():
    """创建测试图像"""
    # 创建一个简单的测试图像
    img = Image.new('RGB', (1024, 576), color='blue')
    
    # 添加一些简单的图形
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([200, 200, 824, 376], fill='white')
    draw.text((400, 280), "Test Image", fill='black')
    
    # 转换为base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_base64

def test_video_generation():
    """测试视频生成"""
    print("\n=== 测试视频生成 ===")
    
    # 准备测试图像
    print("准备测试图像...")
    test_image = create_test_image()
    
    # 生成请求
    request_data = {
        "prompt": "A beautiful landscape with moving clouds",
        "negative_prompt": "blurry, low quality",
        "num_frames": 14,  # 较少帧数以加快测试
        "width": 1024,
        "height": 576,
        "num_inference_steps": 20,  # 较少步数以加快测试
        "guidance_scale": 7.5,
        "seed": 42,
        "input_image": test_image
    }
    
    try:
        print("发送生成请求...")
        response = requests.post(
            f"{SERVER_URL}/generate",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data['task_id']
            print(f"✅ 任务创建成功: {task_id}")
            
            # 轮询任务状态
            print("等待任务完成...")
            max_wait_time = 600  # 最大等待10分钟
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                status_response = requests.get(f"{SERVER_URL}/status/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    progress = status_data['progress']
                    
                    print(f"\r状态: {status}, 进度: {progress:.1%}", end="", flush=True)
                    
                    if status == "completed":
                        print("\n✅ 视频生成完成!")
                        print(f"输出路径: {status_data.get('output_path')}")
                        
                        # 尝试下载视频
                        download_response = requests.get(f"{SERVER_URL}/download/{task_id}")
                        if download_response.status_code == 200:
                            with open(f"test_output_{task_id}.mp4", "wb") as f:
                                f.write(download_response.content)
                            print(f"✅ 视频已下载: test_output_{task_id}.mp4")
                        return True
                        
                    elif status == "failed":
                        print(f"\n❌ 任务失败: {status_data.get('error_message')}")
                        return False
                        
                    elif status == "cancelled":
                        print("\n⚠️ 任务被取消")
                        return False
                
                time.sleep(5)  # 每5秒检查一次
            
            print("\n⏰ 任务超时")
            return False
            
        else:
            print(f"❌ 生成请求失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 生成测试失败: {e}")
        return False

def test_task_management():
    """测试任务管理功能"""
    print("\n=== 测试任务管理 ===")
    
    try:
        # 获取任务列表
        response = requests.get(f"{SERVER_URL}/tasks?limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务列表获取成功，共 {data['total']} 个任务")
            
            for task in data['tasks'][:3]:  # 显示前3个任务
                print(f"  - {task['task_id'][:8]}... | {task['status']} | {task['created_at']}")
            
            return True
        else:
            print(f"❌ 任务列表获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 任务管理测试失败: {e}")
        return False

def test_api_documentation():
    """测试API文档访问"""
    print("\n=== 测试API文档 ===")
    
    try:
        response = requests.get(f"{SERVER_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
            print(f"文档地址: {SERVER_URL}/docs")
            return True
        else:
            print(f"❌ API文档访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API文档测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("========================================")
    print("SVD视频生成服务测试")
    print("========================================")
    print(f"测试服务器: {SERVER_URL}")
    
    # 运行所有测试
    tests = [
        ("健康检查", test_health_check),
        ("API文档", test_api_documentation),
        ("任务管理", test_task_management),
        ("视频生成", test_video_generation),  # 最后测试，因为耗时较长
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"开始测试: {test_name}")
        result = test_func()
        results.append((test_name, result))
        
        if not result:
            print(f"\n⚠️ {test_name}测试失败，跳过后续测试")
            break
    
    # 显示测试结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！SVD服务运行正常")
    else:
        print("\n⚠️ 部分测试失败，请检查服务状态")

if __name__ == "__main__":
    main()