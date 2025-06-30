#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用requests库测试SVD API
"""

import requests
import json
import time

def test_svd_with_requests():
    """使用requests库测试SVD API"""
    api_url = "http://192.168.50.112:8000"
    
    # 请求数据
    request_data = {
        "prompt": "A beautiful sunset",
        "num_frames": 14
    }
    
    try:
        print(f"正在测试 {api_url}/generate...")
        print(f"请求数据: {json.dumps(request_data, indent=2)}")
        
        # 步骤1: 提交生成任务
        response = requests.post(
            f"{api_url}/generate",
            json=request_data,
            timeout=120
        )
        
        print(f"提交任务响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"提交任务失败: {response.text}")
            return None
        
        # 解析任务ID
        try:
            result = response.json()
            task_id = result.get('task_id')
            print(f"任务已提交，任务ID: {task_id}")
            
            if not task_id:
                print("未获取到任务ID")
                print(f"完整响应: {result}")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"原始响应: '{response.text}'")
            return None
        
        # 步骤2: 轮询任务状态
        print("\n开始轮询任务状态...")
        max_wait_time = 300  # 最大等待5分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"{api_url}/status/{task_id}",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                
                print(f"任务状态: {status}, 进度: {progress:.1%}")
                
                if status == 'completed':
                    output_path = status_data.get('output_path')
                    print(f"\n✓ 任务完成！输出文件: {output_path}")
                    return {
                        'task_id': task_id,
                        'status': status,
                        'output_path': output_path
                    }
                elif status == 'failed':
                    error_msg = status_data.get('error_message', '未知错误')
                    print(f"\n✗ 任务失败: {error_msg}")
                    return None
                elif status in ['cancelled']:
                    print(f"\n任务已取消")
                    return None
            else:
                print(f"查询状态失败: {status_response.status_code}")
                print(f"错误响应: {status_response.text}")
            
            # 等待5秒后再次查询
            time.sleep(5)
        
        print(f"\n任务超时（超过{max_wait_time}秒）")
        return None
                
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    result = test_svd_with_requests()
    if result:
        print("\n✓ SVD API完整流程测试成功")
        print(f"任务ID: {result['task_id']}")
        print(f"输出文件: {result['output_path']}")
    else:
        print("\n✗ SVD API完整流程测试失败")