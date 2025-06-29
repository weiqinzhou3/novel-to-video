# 多后端视频生成架构

## 概述

本项目已成功重构为多后端架构，支持同时使用多个视频生成服务，包括：
- **SVD (Stable Video Diffusion)** - 本地部署服务
- **Runway ML** - 商业视频生成服务
- **Pika Labs** - AI视频生成平台
- **Luma Dream Machine** - 高质量视频生成服务

## 架构特性

### 🚀 核心功能
- **多后端支持**: 同时管理多个视频生成服务
- **智能负载均衡**: 基于优先级和负载的任务分配
- **自动故障转移**: 当主要后端不可用时自动切换
- **健康监控**: 实时监控各后端服务状态
- **统一接口**: 提供一致的API接口，屏蔽底层差异

### 🔧 技术特性
- **异步处理**: 全异步架构，支持高并发
- **配置驱动**: 通过配置文件灵活管理后端
- **扩展性**: 易于添加新的视频生成后端
- **监控统计**: 详细的使用统计和性能监控

## 文件结构

```
src/video_backends/
├── base_backend.py              # 后端基类和数据结构
├── multi_backend_generator.py   # 多后端管理器
├── svd_backend.py              # SVD后端实现
├── runway_backend.py           # Runway后端实现
├── pika_backend.py             # Pika Labs后端实现
└── luma_backend.py             # Luma后端实现

src/
└── video_generator.py          # 视频生成器主类

config/
└── config.json                 # 配置文件

# 测试和演示
test_multi_backend.py           # 多后端测试脚本
demo_multi_backend.py           # 功能演示脚本
```

## 配置说明

### 后端配置

在 `config/config.json` 中配置各个后端：

```json
{
  "video_generation": {
    "load_balancing": true,
    "fallback_enabled": true,
    "backends": {
      "svd": {
        "enabled": true,
        "priority": 1,
        "max_concurrent_tasks": 2,
        "base_url": "http://localhost:8000",
        "timeout": 300
      },
      "runway": {
        "enabled": true,
        "priority": 2,
        "max_concurrent_tasks": 3,
        "api_key": "your_runway_api_key",
        "timeout": 600
      },
      "pika": {
        "enabled": true,
        "priority": 3,
        "max_concurrent_tasks": 2,
        "api_key": "your_pika_api_key",
        "timeout": 300
      },
      "luma": {
        "enabled": true,
        "priority": 4,
        "max_concurrent_tasks": 2,
        "api_key": "your_luma_api_key",
        "timeout": 300
      }
    }
  }
}
```

### 配置参数说明

- `enabled`: 是否启用该后端
- `priority`: 优先级（数字越小优先级越高）
- `max_concurrent_tasks`: 最大并发任务数
- `api_key`: API密钥（如需要）
- `base_url`: 服务地址（本地服务）
- `timeout`: 请求超时时间（秒）

## 使用方法

### 基本使用

```python
import asyncio
from src.video_generator import VideoGenerator

async def generate_video():
    # 加载配置
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    # 初始化生成器
    generator = VideoGenerator(config)
    
    # 生成视频
    scenes = [{
        "prompt": "一只可爱的小猫在花园里玩耍",
        "duration": 4,
        "resolution": "1280x720"
    }]
    
    results = await generator.generate_videos(scenes)
    return results

# 运行
results = asyncio.run(generate_video())
```

### 高级功能

#### 1. 健康检查

```python
# 检查所有后端健康状态
health = await generator.health_check()
print(f"整体状态: {health['overall_status']}")
```

#### 2. 后端状态查询

```python
# 获取后端状态
status = generator.get_backend_status()
for backend_name, info in status.items():
    print(f"{backend_name}: {info['healthy']}")
```

#### 3. 统计信息

```python
# 获取使用统计
stats = generator.get_statistics()
print(f"健康后端数: {stats['healthy_backends']}")
print(f"活跃任务数: {stats['total_active_tasks']}")
```

## 运行测试

### 功能测试

```bash
# 运行多后端测试
python3 test_multi_backend.py
```

### 功能演示

```bash
# 运行演示脚本
python3 demo_multi_backend.py
```

## 后端实现指南

### 添加新后端

1. **继承基类**
   ```python
   from video_backends.base_backend import BaseVideoBackend
   
   class NewBackend(BaseVideoBackend):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
   ```

2. **实现必需方法**
   ```python
   async def generate_video(self, task: VideoGenerationTask) -> Dict[str, Any]:
       # 实现视频生成逻辑
       pass
   
   async def get_task_status(self, task_id: str) -> Dict[str, Any]:
       # 实现任务状态查询
       pass
   
   async def health_check(self) -> Dict[str, Any]:
       # 实现健康检查
       pass
   
   def get_capabilities(self) -> BackendCapabilities:
       # 返回后端能力
       pass
   ```

3. **注册到多后端管理器**
   在 `multi_backend_generator.py` 中添加新后端的初始化逻辑。

## 性能优化

### 负载均衡策略

- **优先级模式**: 优先使用高优先级后端
- **轮询模式**: 在可用后端间轮询分配
- **负载感知**: 考虑当前任务负载进行分配

### 并发控制

- 每个后端独立的并发限制
- 全局并发控制
- 任务队列管理

## 监控和日志

### 日志级别

- `INFO`: 正常操作日志
- `WARNING`: 警告信息（如后端不可用）
- `ERROR`: 错误信息（如任务失败）
- `DEBUG`: 详细调试信息

### 监控指标

- 后端健康状态
- 任务成功率
- 平均响应时间
- 并发任务数
- 错误率统计

## 故障排除

### 常见问题

1. **所有后端显示不健康**
   - 检查API密钥配置
   - 确认服务地址可访问
   - 查看网络连接

2. **任务创建失败**
   - 确认至少有一个后端健康
   - 检查并发限制设置
   - 查看错误日志

3. **性能问题**
   - 调整并发限制
   - 优化后端优先级
   - 启用负载均衡

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展计划

- [ ] 添加更多视频生成后端
- [ ] 实现智能路由算法
- [ ] 添加成本优化功能
- [ ] 支持批量处理优化
- [ ] 实现缓存机制
- [ ] 添加Web管理界面

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 实现新功能或修复
4. 添加测试用例
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。