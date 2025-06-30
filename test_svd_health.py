#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SVD后端健康检查
"""

import asyncio
import aiohttp
import json

async def test_svd_health():
    """测试SVD健康检查"""
    api_url = "http://192.168.50.112:8000"
    
    try:
        print(f"正在连接到: {api_url}/health")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/health", timeout=10) as response:
                print(f"状态码: {response.status}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    try:
                        result = await response.json()
                        print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    except Exception as e:
                        print(f"解析JSON失败: {e}")
                        text = await response.text()
                        print(f"原始响应: {text}")
                else:
                    text = await response.text()
                    print(f"错误响应: {text}")
                    
    except asyncio.TimeoutError:
        print("连接超时")
    except Exception as e:
        print(f"连接错误: {e}")
        
    return None

if __name__ == "__main__":
    result = asyncio.run(test_svd_health())
    if result:
        print("\n✓ SVD服务健康检查成功")
    else:
        print("\n✗ SVD服务健康检查失败")