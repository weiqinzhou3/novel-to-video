#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVD API完整测试脚本 - 异步版本

测试SVD API的完整异步任务流程：
1. 提交生成任务
2. 轮询任务状态
3. 等待任务完成
"""

import asyncio
import aiohttp
import json
import time

async def test_svd_complete():
    """测试SVD API的完整异步任务流程"""
    api_url = "http://192.168.50.112:8000"
    
    # 请求数据
    request_data = {
        "prompt": "A beautiful sunset over the ocean",
        "num_frames": 14
    }
    
    try:
        print(f"正在测试 {api_url} 的完整异步任务流程...")
        print(f"请求数据: {json.dumps(request_data, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            # 步骤1: 提交生成任务
            print("\n步骤1: 提交生成任务...")
            async with session.post(
                f"{api_url}/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                print(f"提交任务响应状态码: {response.status}")
                
                if response.status != 200:
                    text = await response.text()
                    print(f"提交任务失败: {text}")
                    return False
                
                try:
                    result = await response.json()
                    task_id = result.get('task_id')
                    if not task_id:
                        print("错误: 未获取到task_id")
                        return False
                    print(f"任务提交成功! Task ID: {task_id}")
                except json.JSONDecodeError as e:
                    text = await response.text()
                    print(f"JSON解析失败: {e}")
                    print(f"原始响应: {text}")
                    return False
            
            # 步骤2: 轮询任务状态
            print(f"\n步骤2: 轮询任务状态...")
            max_wait_time = 300  # 最大等待5分钟
            start_time = time.time()
            check_interval = 5  # 每5秒检查一次
            
            while time.time() - start_time < max_wait_time:
                try:
                    async with session.get(
                        f"{api_url}/status/{task_id}",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            status = status_data.get('status', 'unknown')
                            progress = status_data.get('progress', 0)
                            
                            print(f"任务状态: {status}, 进度: {progress}%")
                            
                            if status == 'completed':
                                output_file = status_data.get('output_file')
                                print(f"\n✓ 任务完成! 输出文件: {output_file}")
                                return True
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"\n✗ 任务失败: {error}")
                                return False
                            elif status in ['pending', 'processing']:
                                # 继续等待
                                await asyncio.sleep(check_interval)
                                continue
                            else:
                                print(f"\n未知状态: {status}")
                                await asyncio.sleep(check_interval)
                                continue
                        else:
                            print(f"状态查询失败: HTTP {status_response.status}")
                            await asyncio.sleep(check_interval)
                            continue
                            
                except Exception as e:
                    print(f"状态查询出错: {type(e).__name__}: {str(e)}")
                    await asyncio.sleep(check_interval)
                    continue
            
            print(f"\n✗ 任务超时 (等待了 {max_wait_time} 秒)")
            return False
            
    except Exception as e:
        print(f"测试失败: {type(e).__name__}: {str(e)}")
        return False

async def main():
    """主函数"""
    print("SVD API完整异步任务流程测试")
    print("=" * 50)
    
    success = await test_svd_complete()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ SVD API完整流程测试成功!")
    else:
        print("✗ SVD API完整流程测试失败!")

if __name__ == "__main__":
    asyncio.run(main())