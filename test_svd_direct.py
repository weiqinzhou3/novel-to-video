#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试SVD API
"""

import asyncio
import aiohttp
import json
import base64
from PIL import Image
from io import BytesIO

async def test_svd_generation():
    """测试SVD视频生成"""
    api_url = "http://192.168.50.112:8001"
    
    # 创建一个简单的测试图像
    image = Image.new('RGB', (1024, 576), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 准备请求数据
    request_data = {
        "prompt": "A beautiful sunset over the ocean",
        "negative_prompt": "",
        "num_frames": 25,
        "width": 1024,
        "height": 576,
        "num_inference_steps": 25,
        "guidance_scale": 7.5,
        "seed": 42,
        "input_image": image_base64
    }
    
    try:
        print(f"正在向 {api_url}/generate 发送请求...")
        print(f"请求参数: {json.dumps({k: v if k != 'input_image' else '[base64_image]' for k, v in request_data.items()}, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"生成任务已提交: {json.dumps(result, indent=2)}")
                    
                    task_id = result.get('task_id')
                    if task_id:
                        # 轮询任务状态
                        await poll_task_status(session, api_url, task_id)
                    
                else:
                    error_text = await response.text()
                    print(f"错误响应: {error_text}")
                    
    except Exception as e:
        print(f"请求失败: {e}")

async def poll_task_status(session, api_url, task_id):
    """轮询任务状态"""
    print(f"\n开始轮询任务状态: {task_id}")
    
    for i in range(60):  # 最多等待5分钟
        try:
            async with session.get(f"{api_url}/status/{task_id}") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"任务状态: {status.get('status')} - 进度: {status.get('progress', 0):.1%}")
                    
                    if status.get('status') == 'completed':
                        print(f"✓ 任务完成! 输出文件: {status.get('output_path')}")
                        return True
                    elif status.get('status') == 'failed':
                        print(f"✗ 任务失败: {status.get('error_message')}")
                        return False
                        
                else:
                    print(f"状态查询失败: {response.status}")
                    
        except Exception as e:
            print(f"状态查询错误: {e}")
            
        await asyncio.sleep(5)  # 等待5秒后再次查询
        
    print("任务超时")
    return False

if __name__ == "__main__":
    asyncio.run(test_svd_generation())