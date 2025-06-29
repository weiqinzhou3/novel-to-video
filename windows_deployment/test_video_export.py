#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频导出功能
"""

import sys
import numpy as np
from pathlib import Path

def test_imageio_installation():
    """测试imageio安装状态"""
    try:
        import imageio
        print("✓ imageio 已安装")
        print(f"  版本: {imageio.__version__}")
        
        # 测试ffmpeg
        try:
            imageio.plugins.ffmpeg.get_exe()
            print("✓ ffmpeg 可用")
        except AttributeError as e:
            print(f"✗ ffmpeg 不可用: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ imageio 未安装: {e}")
        return False
    
    return True

def test_export_to_video():
    """测试export_to_video函数"""
    try:
        from diffusers.utils import export_to_video
        print("✓ export_to_video 导入成功")
        
        # 创建测试视频帧
        frames = []
        for i in range(10):
            # 创建简单的测试帧 (64x64 RGB)
            frame = np.random.rand(64, 64, 3).astype(np.float32)
            frames.append(frame)
        
        print(f"✓ 创建了 {len(frames)} 个测试帧")
        
        # 测试导出
        output_path = Path("test_output.mp4")
        if output_path.exists():
            output_path.unlink()
            
        try:
            result_path = export_to_video(frames, str(output_path), fps=8)
            print(f"✓ 视频导出成功: {result_path}")
            
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"✓ 文件已创建，大小: {file_size} bytes")
                # 清理测试文件
                output_path.unlink()
                return True
            else:
                print("✗ 文件未创建")
                return False
                
        except Exception as e:
            print(f"✗ 视频导出失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            return False
            
    except ImportError as e:
        print(f"✗ export_to_video 导入失败: {e}")
        return False

def main():
    print("=== 视频导出功能测试 ===")
    print(f"Python 版本: {sys.version}")
    print()
    
    # 测试imageio
    print("1. 测试 imageio 安装:")
    imageio_ok = test_imageio_installation()
    print()
    
    # 测试export_to_video
    print("2. 测试 export_to_video 函数:")
    export_ok = test_export_to_video()
    print()
    
    # 总结
    print("=== 测试结果 ===")
    if imageio_ok and export_ok:
        print("✓ 所有测试通过，视频导出功能正常")
        return 0
    else:
        print("✗ 测试失败，需要修复依赖问题")
        if not imageio_ok:
            print("  建议: pip install imageio imageio-ffmpeg")
        return 1

if __name__ == "__main__":
    sys.exit(main())