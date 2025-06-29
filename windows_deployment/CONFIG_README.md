# SVD 视频生成服务 - 配置管理系统

## 概述

本配置管理系统为 SVD 视频生成服务提供了集中化、结构化的配置管理功能。通过 JSON 配置文件和 Python 配置管理器，您可以轻松地调整服务的各种参数，而无需修改代码。

## 文件结构

```
windows_deployment/
├── config.json              # 主配置文件
├── config_manager.py        # 配置管理器模块
├── config_example.py        # 配置使用示例
├── svd_server.py            # 主服务文件（已集成配置管理）
├── start_service_config.bat # 配置化启动脚本
└── CONFIG_README.md         # 本文档
```

## 配置文件结构

### 1. 服务器配置 (`server`)

```json
{
  "server": {
    "host": "0.0.0.0",                    // 服务监听地址
    "port": 8000,                         // 默认端口
    "fallback_ports": [8001, 8002, 8003, 8004, 8005], // 备用端口
    "log_level": "info",                  // 日志级别
    "access_log": true,                   // 是否启用访问日志
    "workers": 1                          // 工作进程数
  }
}
```

### 2. 模型配置 (`model`)

```json
{
  "model": {
    "name": "stabilityai/stable-video-diffusion-img2vid-xt-1-1", // 模型名称
    "device": "auto",                     // 设备选择：auto/cuda/cpu
    "torch_dtype": "auto",               // 数据类型：auto/float16/float32
    "variant": "fp16",                    // 模型变体
    "enable_cpu_offload": true,          // 启用CPU卸载
    "enable_vae_slicing": true,          // 启用VAE切片优化
    "enable_attention_slicing": true     // 启用注意力切片优化
  }
}
```

### 3. 生成参数配置 (`generation`)

```json
{
  "generation": {
    "default_num_frames": 25,            // 默认生成帧数
    "max_num_frames": 25,                // 最大帧数限制
    "default_width": 1024,               // 默认宽度
    "default_height": 576,               // 默认高度
    "max_width": 1024,                   // 最大宽度限制
    "max_height": 576,                   // 最大高度限制
    "default_num_inference_steps": 25,   // 默认推理步数
    "max_num_inference_steps": 50,       // 最大推理步数
    "default_guidance_scale": 7.5,       // 默认引导强度
    "fps": 8                             // 视频帧率
  }
}
```

### 4. 存储配置 (`storage`)

```json
{
  "storage": {
    "output_dir": "outputs",             // 输出目录
    "max_storage_gb": 10,                // 最大存储空间(GB)
    "cleanup_after_days": 7,             // 自动清理周期(天)
    "auto_cleanup": true                 // 是否启用自动清理
  }
}
```

### 5. 性能配置 (`performance`)

```json
{
  "performance": {
    "max_concurrent_tasks": 2,           // 最大并发任务数
    "task_timeout_minutes": 30,          // 任务超时时间(分钟)
    "memory_cleanup_interval": 300       // 内存清理间隔(秒)
  }
}
```

### 6. 安全配置 (`security`)

```json
{
  "security": {
    "enable_cors": true,                 // 启用CORS
    "allowed_origins": ["*"],           // 允许的源
    "max_file_size_mb": 50,              // 最大文件大小(MB)
    "rate_limit_per_minute": 10          // 速率限制(次/分钟)
  }
}
```

### 7. 日志配置 (`logging`)

```json
{
  "logging": {
    "log_file": "svd_server.log",         // 日志文件名
    "max_log_size_mb": 100,              // 最大日志文件大小(MB)
    "backup_count": 5,                   // 日志备份数量
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s" // 日志格式
  }
}
```

### 8. Hugging Face 配置 (`huggingface`)

```json
{
  "huggingface": {
    "token_env_var": "HUGGINGFACE_TOKEN", // Token环境变量名
    "auto_login": true,                  // 自动登录
    "cache_dir_env_var": "HF_HOME",      // 缓存目录环境变量
    "disable_symlinks_warning": true     // 禁用符号链接警告
  }
}
```

### 9. 监控配置 (`monitoring`)

```json
{
  "monitoring": {
    "enable_health_check": true,         // 启用健康检查
    "health_check_interval_seconds": 30, // 健康检查间隔(秒)
    "log_performance_metrics": true,     // 记录性能指标
    "enable_gpu_monitoring": true        // 启用GPU监控
  }
}
```

## 使用方法

### 1. 基本使用

```python
from config_manager import config

# 获取服务器配置
server_config = config.get_server_config()
port = server_config.get('port', 8000)

# 获取单个配置值
model_name = config.get('model.name')
max_frames = config.get('generation.max_num_frames', 25)
```

### 2. 动态修改配置

```python
# 修改配置值
config.set('server.port', 9000)
config.set('model.device', 'cpu')

# 保存配置到文件
config.save_config()
```

### 3. 配置验证

```python
# 验证配置有效性
errors = config.validate_config()
if errors:
    for error in errors:
        print(f"配置错误: {error}")
```

### 4. 环境设置

```python
# 自动设置环境变量
config.setup_environment()
```

## 启动服务

### 使用配置化启动脚本

```bash
# Windows
start_service_config.bat
```

### 直接启动

```bash
python svd_server.py
```

## 配置优化建议

### 1. 性能优化

**GPU 环境:**
```json
{
  "model": {
    "device": "cuda",
    "torch_dtype": "float16",
    "variant": "fp16",
    "enable_cpu_offload": true,
    "enable_vae_slicing": true,
    "enable_attention_slicing": true
  }
}
```

**CPU 环境:**
```json
{
  "model": {
    "device": "cpu",
    "torch_dtype": "float32",
    "enable_cpu_offload": false,
    "enable_vae_slicing": false,
    "enable_attention_slicing": false
  },
  "generation": {
    "default_num_frames": 15,
    "max_num_frames": 20
  }
}
```

### 2. 内存优化

```json
{
  "performance": {
    "max_concurrent_tasks": 1,
    "memory_cleanup_interval": 60
  },
  "generation": {
    "max_num_frames": 15,
    "max_num_inference_steps": 25
  }
}
```

### 3. 生产环境配置

```json
{
  "server": {
    "log_level": "warning",
    "access_log": false
  },
  "security": {
    "allowed_origins": ["https://yourdomain.com"],
    "rate_limit_per_minute": 5
  },
  "storage": {
    "auto_cleanup": true,
    "cleanup_after_days": 3
  }
}
```

## 故障排除

### 1. 端口被占用

配置系统会自动尝试备用端口：
```json
{
  "server": {
    "port": 8000,
    "fallback_ports": [8001, 8002, 8003, 8004, 8005]
  }
}
```

### 2. 内存不足

调整以下配置：
```json
{
  "model": {
    "enable_cpu_offload": true,
    "enable_vae_slicing": true
  },
  "performance": {
    "max_concurrent_tasks": 1
  },
  "generation": {
    "max_num_frames": 15
  }
}
```

### 3. 模型访问权限

确保正确设置 Hugging Face Token：
```bash
set HUGGINGFACE_TOKEN=your_token_here
```

## 配置示例

运行配置示例脚本：
```bash
python config_example.py
```

这将展示所有配置功能的使用方法。

## 注意事项

1. **配置文件编码**: 确保 `config.json` 使用 UTF-8 编码
2. **权限设置**: 确保服务有读写配置文件和输出目录的权限
3. **端口冲突**: 系统会自动处理端口冲突，但建议配置足够的备用端口
4. **内存管理**: 根据硬件配置调整并发任务数和内存优化选项
5. **安全考虑**: 生产环境中应限制 CORS 源和调整速率限制

## 更新日志

- **v1.0.0**: 初始版本，支持完整的配置管理功能
- 自动端口检测和切换
- 模型参数配置化
- 环境变量自动设置
- 配置验证和错误检查