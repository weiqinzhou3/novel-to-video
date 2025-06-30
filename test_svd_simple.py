#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的SVD API测试
"""

import asyncio
import aiohttp
import json

async def test_svd_simple():
    """简单测试SVD API - 只测试任务提交"""
    api_url = "http://192.168.50.112:8000"
    
    # 最简单的请求数据
    request_data = {
        "prompt": "A beautiful sunset",
        "num_frames": 14
    }
    
    try:
        print(f"正在测试 {api_url}/generate...")
        print(f"请求数据: {json.dumps(request_data, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status == 200:
                    try:
                        result = await response.json()
                        task_id = result.get('task_id')
                        print(f"成功! 任务ID: {task_id}")
                        print("注意: 这只是任务提交测试，实际视频生成需要时间")
                        print(f"可以通过 {api_url}/status/{task_id} 查询任务状态")
                        return result
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        print(f"JSON解析失败: {e}")
                        print(f"原始响应: {text}")
                else:
                    text = await response.text()
                    print(f"错误状态码: {response.status}")
                    print(f"错误响应: {text}")
                    
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {str(e)}")
        
    return None

if __name__ == "__main__":
    result = asyncio.run(test_svd_simple())
    if result:
        print("\n✓ SVD API测试成功")
    else:
        print("\n✗ SVD API测试失败")