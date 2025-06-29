#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stable Video Diffusion API 服务器
用于在Windows上部署SVD视频生成服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
import uuid
import asyncio
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime
import logging
from pathlib import Path
import aiofiles
import uvicorn
from PIL import Image
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('svd_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SVD Video Generation API",
    description="Stable Video Diffusion 视频生成服务",
    version="1.0.0"
)

# 全局变量
pipeline = None
tasks = {}
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    num_frames: int = 25
    width: int = 1024
    height: int = 576
    num_inference_steps: int = 25
    guidance_scale: float = 7.5
    seed: int = -1
    input_image: Optional[str] = None  # base64编码的图像或图像URL

class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

@app.on_event("startup")
async def load_model():
    """启动时加载SVD模型"""
    global pipeline
    try:
        logger.info("正在加载SVD模型...")
        
        # 检查GPU可用性
        if not torch.cuda.is_available():
            logger.warning("CUDA不可用，将使用CPU运行（速度较慢）")
            device = "cpu"
            torch_dtype = torch.float32
        else:
            device = "cuda"
            torch_dtype = torch.float16
            logger.info(f"使用GPU: {torch.cuda.get_device_name(0)}")
        
        # 加载模型
        pipeline = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
            torch_dtype=torch_dtype,
            variant="fp16" if device == "cuda" else None
        )
        pipeline = pipeline.to(device)
        
        # 启用内存优化
        if device == "cuda":
            pipeline.enable_model_cpu_offload()
            pipeline.enable_vae_slicing()
        
        logger.info("SVD模型加载完成")
        
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        pipeline = None

@app.get("/health")
async def health_check():
    """健康检查接口"""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_count": torch.cuda.device_count(),
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory // 1024**3,
            "gpu_memory_allocated": torch.cuda.memory_allocated(0) // 1024**3,
            "gpu_memory_cached": torch.cuda.memory_reserved(0) // 1024**3
        }
    
    processing_tasks = len([t for t in tasks.values() if t["status"] == "processing"])
    
    return {
        "status": "healthy" if pipeline is not None else "unhealthy",
        "model_loaded": pipeline is not None,
        "gpu_info": gpu_info,
        "queue_size": processing_tasks,
        "total_tasks": len(tasks),
        "server_time": datetime.now().isoformat()
    }

@app.post("/generate")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    """生成视频接口"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    # 验证参数
    if request.num_frames > 25:
        request.num_frames = 25
    if request.num_frames < 1:
        request.num_frames = 1
        
    if request.num_inference_steps > 50:
        request.num_inference_steps = 50
    if request.num_inference_steps < 1:
        request.num_inference_steps = 1
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    # 添加后台任务
    background_tasks.add_task(process_generation, task_id, request)
    
    logger.info(f"新的视频生成任务: {task_id}")
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        output_path=task.get("output_path"),
        error_message=task.get("error_message"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )

@app.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if tasks[task_id]["status"] in ["pending", "processing"]:
        tasks[task_id]["status"] = "cancelled"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        logger.info(f"任务已取消: {task_id}")
        return {"message": "任务已取消"}
    else:
        return {"message": "任务无法取消"}

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    """下载生成的视频"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task["status"] != "completed" or "output_path" not in task:
        raise HTTPException(status_code=400, detail="视频尚未生成完成")
    
    output_path = task["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"{task_id}.mp4"
    )

@app.get("/tasks")
async def list_tasks(limit: int = 50, status: Optional[str] = None):
    """列出任务"""
    filtered_tasks = tasks
    if status:
        filtered_tasks = {k: v for k, v in tasks.items() if v["status"] == status}
    
    # 按创建时间排序，最新的在前
    sorted_tasks = sorted(
        filtered_tasks.items(),
        key=lambda x: x[1]["created_at"],
        reverse=True
    )[:limit]
    
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task_data["status"],
                "progress": task_data["progress"],
                "created_at": task_data["created_at"],
                "completed_at": task_data.get("completed_at")
            }
            for task_id, task_data in sorted_tasks
        ],
        "total": len(filtered_tasks)
    }

async def process_generation(task_id: str, request: GenerationRequest):
    """处理视频生成任务"""
    try:
        logger.info(f"开始处理任务: {task_id}")
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 0.1
        
        # 准备输入图像
        if request.input_image:
            # 如果提供了输入图像，使用它
            if request.input_image.startswith("http"):
                # URL图像
                image = load_image(request.input_image)
            else:
                # 假设是base64编码的图像
                import base64
                from io import BytesIO
                image_data = base64.b64decode(request.input_image)
                image = Image.open(BytesIO(image_data))
        else:
            # 如果没有输入图像，创建一个基于prompt的简单图像
            # 这里可以集成文本到图像的模型，暂时创建一个占位图像
            image = Image.new('RGB', (request.width, request.height), color='black')
        
        # 调整图像尺寸
        image = image.resize((request.width, request.height))
        tasks[task_id]["progress"] = 0.3
        
        # 设置随机种子
        if request.seed != -1:
            torch.manual_seed(request.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(request.seed)
        
        logger.info(f"开始生成视频，帧数: {request.num_frames}")
        tasks[task_id]["progress"] = 0.5
        
        # 生成视频帧
        frames = pipeline(
            image,
            height=request.height,
            width=request.width,
            num_frames=request.num_frames,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
        ).frames[0]
        
        tasks[task_id]["progress"] = 0.8
        
        # 保存视频
        output_path = output_dir / f"{task_id}.mp4"
        export_to_video(frames, str(output_path), fps=8)
        
        # 更新任务状态
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 1.0
        tasks[task_id]["output_path"] = str(output_path)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"任务完成: {task_id}, 输出: {output_path}")
        
    except Exception as e:
        logger.error(f"任务失败: {task_id}, 错误: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error_message"] = str(e)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )