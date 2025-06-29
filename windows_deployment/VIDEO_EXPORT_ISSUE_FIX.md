# 视频导出问题修复指南

## 问题描述

用户反馈 `outputs` 文件夹为空，即使视频生成任务显示已完成。

## 问题原因

经过分析，问题的根本原因是缺少必要的视频处理依赖库：

1. **缺少 `imageio` 库** - 用于视频文件的读写操作
2. **缺少 `imageio-ffmpeg` 库** - 提供 FFmpeg 后端支持，用于视频编码

当 `export_to_video` 函数尝试保存视频时，由于缺少这些依赖，会抛出异常，导致视频文件无法正常创建。

## 解决方案

### 方法一：使用自动安装脚本（推荐）

1. 运行 `install_video_deps.bat` 脚本：
   ```bash
   install_video_deps.bat
   ```

### 方法二：手动安装

1. 激活虚拟环境：
   ```bash
   svd_env\Scripts\activate.bat
   ```

2. 安装依赖：
   ```bash
   pip install imageio>=2.31.0 imageio-ffmpeg>=0.4.9
   ```

3. 验证安装：
   ```bash
   python -c "import imageio; print('imageio version:', imageio.__version__); imageio.plugins.ffmpeg.get_exe(); print('ffmpeg 可用')"
   ```

### 方法三：重新安装完整依赖

```bash
svd_env\Scripts\activate.bat
pip install -r requirements.txt
```

## 验证修复

1. 安装依赖后，重启 SVD 服务
2. 提交新的视频生成任务
3. 检查 `outputs` 文件夹，应该能看到生成的 `.mp4` 文件

## 技术细节

### 修复内容

1. **更新了 `requirements.txt`**：
   - 添加了 `imageio>=2.31.0`
   - 添加了 `imageio-ffmpeg>=0.4.9`

2. **增强了错误处理**：
   - 在 `svd_server.py` 中添加了详细的视频保存日志
   - 添加了文件创建验证逻辑
   - 改进了异常处理和错误报告

3. **创建了测试脚本**：
   - `test_video_export.py` - 用于诊断视频导出功能

### 视频文件位置

- **存储目录**：`d:\novel-to-video\windows_deployment\outputs\`
- **文件命名**：`{task_id}.mp4`
- **配置来源**：`config.json` 中的 `storage.output_dir` 设置

### 常见问题

**Q: 为什么之前任务显示完成但没有文件？**
A: 因为缺少视频编码依赖，`export_to_video` 函数会抛出异常，但异常被捕获并记录为任务失败，但状态可能没有正确更新。

**Q: 安装依赖后需要重启服务吗？**
A: 是的，需要重启 SVD 服务以加载新安装的依赖库。

**Q: 如何检查依赖是否正确安装？**
A: 运行 `test_video_export.py` 脚本进行完整测试。

## 预防措施

1. 在部署时确保安装完整的 `requirements.txt`
2. 定期检查日志文件以发现潜在问题
3. 考虑添加健康检查端点来验证关键依赖