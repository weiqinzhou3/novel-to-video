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
from contextlib import asynccontextmanager
from huggingface_hub import login

# 导入配置管理器
from config_manager import config

# 设置环境变量
config.setup_environment()

# 配置日志
log_config = config.get_logging_config()
logging.basicConfig(
    level=getattr(logging, log_config.get('log_level', 'INFO').upper()),
    format=log_config.get('log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
    handlers=[
        logging.FileHandler(log_config.get('log_file', 'svd_server.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
pipeline = None
tasks = {}
storage_config = config.get_storage_config()
output_dir = Path(storage_config.get('output_dir', 'outputs'))
output_dir.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载模型
    await load_model()
    yield
    # 关闭时清理资源
    global pipeline
    if pipeline is not None:
        del pipeline
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("模型资源已清理")

app = FastAPI(
    title="SVD Video Generation API",
    description="Stable Video Diffusion 视频生成服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
from fastapi.middleware.cors import CORSMiddleware
security_config = config.get_security_config()
if security_config.get('enable_cors', True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.get('allowed_origins', ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

class VideoGenerationRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    num_frames: int = 25
    num_inference_steps: int = 25
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    fps: int = 8

class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

async def load_model():
    """加载SVD模型"""
    global pipeline
    try:
        # 获取模型配置
        model_config = config.get_model_config()
        model_name = model_config.get('name', 'stabilityai/stable-video-diffusion-img2vid-xt-1-1')
        
        logger.info(f"正在加载SVD模型: {model_name}")
        
        # 检查Hugging Face token
        hf_token = config.get_huggingface_token()
        if hf_token:
            try:
                login(token=hf_token)
                logger.info("Hugging Face认证成功")
            except Exception as e:
                logger.warning(f"Hugging Face认证失败: {e}")
        else:
            logger.warning("未找到Hugging Face token，可能无法访问受限模型")
            logger.info("请设置环境变量: set HUGGINGFACE_TOKEN=your_token_here")
            logger.info("或在命令行中运行: huggingface-cli login")
        
        # 设备配置
        device_config = model_config.get('device', 'auto')
        if device_config == 'auto':
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = device_config
        
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA不可用，将使用CPU运行（速度较慢）")
            device = "cpu"
        
        # 数据类型配置
        torch_dtype_config = model_config.get('torch_dtype', 'auto')
        if torch_dtype_config == 'auto':
            torch_dtype = torch.float16 if device == "cuda" else torch.float32
        elif torch_dtype_config == 'float16':
            torch_dtype = torch.float16
        elif torch_dtype_config == 'float32':
            torch_dtype = torch.float32
        else:
            torch_dtype = torch.float32
        
        logger.info(f"使用设备: {device}, 数据类型: {torch_dtype}")
        
        if device == "cuda":
            logger.info(f"使用GPU: {torch.cuda.get_device_name(0)}")
        
        # 构建模型参数
        model_kwargs = {
            "torch_dtype": torch_dtype,
            "token": hf_token if hf_token else True
        }
        
        # 变体配置
        variant = model_config.get('variant')
        if variant and device == "cuda":
            model_kwargs["variant"] = variant
        
        # 加载模型
        pipeline = StableVideoDiffusionPipeline.from_pretrained(
            model_name,
            **model_kwargs
        )
        pipeline = pipeline.to(device)
        
        # 内存优化配置
        if model_config.get('enable_cpu_offload', True) and device == "cuda":
            pipeline.enable_model_cpu_offload()
            logger.info("已启用模型CPU卸载")
        
        # VAE优化
        if model_config.get('enable_vae_slicing', True):
            try:
                if hasattr(pipeline, 'enable_vae_slicing'):
                    pipeline.enable_vae_slicing()
                    logger.info("VAE内存优化已启用")
                elif hasattr(pipeline, 'enable_vae_tiling'):
                    pipeline.enable_vae_tiling()
                    logger.info("VAE平铺优化已启用")
            except Exception as e:
                logger.warning(f"VAE优化启用失败，但不影响正常使用: {e}")
        
        # 注意力切片优化
        if model_config.get('enable_attention_slicing', True):
            try:
                if hasattr(pipeline, 'enable_attention_slicing'):
                    pipeline.enable_attention_slicing()
                    logger.info("注意力切片优化已启用")
            except Exception as e:
                logger.warning(f"注意力切片优化启用失败: {e}")
        
        logger.info("SVD模型加载完成")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        if "401" in str(e) or "access" in str(e).lower():
            logger.error("认证错误：请确保已正确设置Hugging Face访问令牌")
            logger.error("解决方案：")
            logger.error("1. 访问 https://huggingface.co/settings/tokens 创建访问令牌")
            logger.error("2. 设置环境变量: set HUGGINGFACE_TOKEN=your_token_here")
            logger.error("3. 或运行: huggingface-cli login")
            logger.error("4. 确保您的账户有权访问模型")
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

def resize_image(image: Image.Image, target_width: int = None, target_height: int = None) -> Image.Image:
    """调整图片尺寸"""
    gen_config = config.get_generation_config()
    if target_width is None:
        target_width = gen_config.get('default_width', 1024)
    if target_height is None:
        target_height = gen_config.get('default_height', 576)
    
    # 计算缩放比例
    width_ratio = target_width / image.width
    height_ratio = target_height / image.height
    scale_ratio = min(width_ratio, height_ratio)
    
    # 计算新尺寸
    new_width = int(image.width * scale_ratio)
    new_height = int(image.height * scale_ratio)
    
    # 调整图片大小
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 创建目标尺寸的画布
    canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))
    
    # 计算居中位置
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    
    # 将调整后的图片粘贴到画布中心
    canvas.paste(image, (x_offset, y_offset))
    
    return canvas

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

def find_available_port(start_port: int, fallback_ports: List[int]) -> int:
    """查找可用端口"""
    def is_port_available(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return True
        except OSError:
            return False
    
    # 首先尝试默认端口
    if is_port_available(start_port):
        return start_port
    
    # 尝试备用端口
    for port in fallback_ports:
        if is_port_available(port):
            logger.info(f"端口 {start_port} 被占用，切换到端口 {port}")
            return port
    
    # 如果所有配置的端口都被占用，尝试系统分配
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 0))
            port = s.getsockname()[1]
            logger.info(f"所有配置端口被占用，使用系统分配端口 {port}")
            return port
    except OSError:
        raise RuntimeError("无法找到可用端口")

if __name__ == "__main__":
    # 验证配置
    config_errors = config.validate_config()
    if config_errors:
        logger.error("配置验证失败:")
        for error in config_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # 启动时加载模型
    logger.info("正在启动SVD视频生成服务...")
    
    if not load_model():
        logger.error("模型加载失败，服务无法启动")
        sys.exit(1)
    
    # 获取服务器配置
    server_config = config.get_server_config()
    host = server_config.get('host', '0.0.0.0')
    default_port = server_config.get('port', 8000)
    fallback_ports = config.get_fallback_ports()
    log_level = server_config.get('log_level', 'info')
    access_log = server_config.get('access_log', True)
    
    # 查找可用端口
    try:
        port = find_available_port(default_port, fallback_ports)
        logger.info(f"服务将在 {host}:{port} 启动")
        
        # 启动服务器
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=access_log
        )
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)