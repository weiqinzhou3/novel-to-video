# SVD视频生成服务 - Windows部署指南

本指南将帮助您在Windows系统上部署Stable Video Diffusion (SVD)视频生成服务，以供Mac或其他设备通过网络访问。

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 或更高版本
- **内存**: 8GB RAM (推荐16GB+)
- **存储**: 20GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **GPU**: NVIDIA RTX 3060 或更高 (8GB+ VRAM)
- **内存**: 32GB RAM
- **存储**: SSD 50GB+ 可用空间
- **CUDA**: 11.8 或 12.1

## 📁 文件说明

```
windows_deployment/
├── svd_server.py          # SVD API服务器主程序
├── requirements.txt       # Python依赖包列表
├── config.json           # 服务配置文件
├── install_and_run.bat   # 自动安装和启动脚本
├── start_service.bat     # 启动服务脚本
├── test_service.py       # 服务测试脚本
├── setup_firewall.bat    # 防火墙配置脚本
├── remove_firewall.bat   # 删除防火墙规则脚本
└── README.md             # 本说明文档
```

## 🚀 快速开始

### 方法一：一键安装（推荐）

1. **下载所有文件**到Windows机器的一个文件夹中

2. **右键点击** `install_and_run.bat`，选择 **"以管理员身份运行"**

3. **按照提示操作**：
   - 脚本会自动检测Python环境
   - 创建虚拟环境（推荐选择Y）
   - 自动安装所有依赖
   - 询问是否立即启动服务

4. **配置防火墙**（可选）：
   - 右键点击 `setup_firewall.bat`，选择 **"以管理员身份运行"**
   - 这将允许其他设备访问您的服务

### 方法二：手动安装

1. **安装Python**（如果尚未安装）：
   ```bash
   # 下载并安装Python 3.8+
   # https://www.python.org/downloads/
   ```

2. **创建虚拟环境**：
   ```bash
   python -m venv svd_env
   svd_env\Scripts\activate
   ```

3. **安装依赖**：
   ```bash
   # 升级pip
   python -m pip install --upgrade pip
   
   # 安装PyTorch (GPU版本)
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   
   # 或安装CPU版本
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   
   # 安装其他依赖
   pip install -r requirements.txt
   ```

4. **启动服务**：
   ```bash
   python svd_server.py
   ```

## 🔧 配置说明

### 服务配置 (config.json)

您可以修改 `config.json` 文件来自定义服务行为：

```json
{
  "server": {
    "host": "0.0.0.0",     # 监听所有网络接口
    "port": 8000,          # 服务端口
    "workers": 1           # 工作进程数
  },
  "model": {
    "device": "auto",      # auto/cpu/cuda
    "enable_cpu_offload": true  # 内存优化
  },
  "generation": {
    "max_num_frames": 25,  # 最大帧数
    "max_width": 1024,     # 最大宽度
    "max_height": 576      # 最大高度
  }
}
```

### 网络配置

1. **获取Windows机器IP地址**：
   ```bash
   ipconfig
   ```
   查找 "IPv4 地址" 行

2. **配置防火墙**：
   - 运行 `setup_firewall.bat`（需要管理员权限）
   - 或手动在Windows防火墙中允许端口8000

3. **路由器配置**（如果需要外网访问）：
   - 在路由器中设置端口转发：8000 → Windows机器IP:8000

## 🖥️ 使用方法

### 启动服务

```bash
# 方法1：使用批处理脚本
start_service.bat

# 方法2：直接运行Python
python svd_server.py
```

### 访问服务

- **本地访问**: http://localhost:8000
- **网络访问**: http://[Windows机器IP]:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### API使用示例

#### 1. 健康检查
```bash
curl http://localhost:8000/health
```

#### 2. 生成视频
```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "A beautiful sunset over mountains",
       "num_frames": 14,
       "width": 1024,
       "height": 576
     }'
```

#### 3. 查询任务状态
```bash
curl http://localhost:8000/status/{task_id}
```

#### 4. 下载视频
```bash
curl -O http://localhost:8000/download/{task_id}
```

## 🧪 测试服务

运行测试脚本验证服务是否正常工作：

```bash
python test_service.py
```

测试包括：
- ✅ 健康检查
- ✅ API文档访问
- ✅ 任务管理
- ✅ 视频生成（完整流程）

## 📱 Mac端配置

在您的Mac项目中，更新 `config.json` 文件：

```json
{
  "video_generation": {
    "multi_backend": {
      "svd": {
        "endpoint": "http://[Windows机器IP]:8000",
        "enabled": true,
        "priority": 1,
        "max_concurrent": 2,
        "timeout": 300,
        "retry_attempts": 3
      }
    }
  }
}
```

## 🔍 监控和日志

### 日志文件
- **服务日志**: `svd_server.log`
- **输出视频**: `outputs/` 目录

### 监控命令
```bash
# 查看实时日志
tail -f svd_server.log

# 检查GPU使用情况
nvidia-smi

# 查看进程状态
tasklist | findstr python
```

## ⚡ 性能优化

### GPU优化
1. **安装CUDA工具包**：
   - 下载：https://developer.nvidia.com/cuda-downloads
   - 推荐版本：CUDA 11.8 或 12.1

2. **启用内存优化**：
   ```json
   {
     "model": {
       "enable_cpu_offload": true,
       "enable_vae_slicing": true,
       "enable_attention_slicing": true
     }
   }
   ```

### 系统优化
1. **关闭不必要的程序**
2. **设置高性能电源模式**
3. **确保足够的虚拟内存**
4. **使用SSD存储**

## 🛠️ 故障排除

### 常见问题

#### 1. 模型下载失败
```bash
# 手动下载模型
huggingface-cli download stabilityai/stable-video-diffusion-img2vid-xt-1-1
```

#### 2. CUDA内存不足
- 减少 `max_concurrent_tasks`
- 启用 `enable_cpu_offload`
- 降低分辨率或帧数

#### 3. 网络访问失败
- 检查防火墙设置
- 确认IP地址正确
- 测试端口连通性：`telnet [IP] 8000`

#### 4. 服务启动失败
- 检查Python版本：`python --version`
- 验证依赖安装：`pip list`
- 查看错误日志：`svd_server.log`

### 调试命令
```bash
# 检查端口占用
netstat -an | findstr 8000

# 测试网络连接
ping [Windows机器IP]
telnet [Windows机器IP] 8000

# 查看GPU状态
nvidia-smi

# 检查Python环境
python -c "import torch; print(torch.cuda.is_available())"
```

## 🔒 安全建议

1. **网络安全**：
   - 仅在可信网络中使用
   - 考虑使用VPN连接
   - 定期更新防火墙规则

2. **访问控制**：
   - 限制访问IP范围
   - 使用强密码（如果添加认证）
   - 监控访问日志

3. **数据安全**：
   - 定期清理输出文件
   - 备份重要配置
   - 避免处理敏感内容

## 📞 技术支持

如果遇到问题，请：

1. **查看日志文件** `svd_server.log`
2. **运行测试脚本** `test_service.py`
3. **检查系统要求**是否满足
4. **参考故障排除**章节

## 📝 更新日志

- **v1.0.0**: 初始版本
  - 基础SVD视频生成功能
  - 完整的API接口
  - Windows部署支持
  - 自动化安装脚本

---

**注意**: 首次运行时，系统会自动下载约7GB的模型文件，请确保网络连接稳定且有足够的存储空间。