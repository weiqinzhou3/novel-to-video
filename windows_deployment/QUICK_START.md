# 🚀 SVD服务快速启动指南

## 📋 准备工作

1. **确保已安装Python 3.8+**
   - 下载：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **将所有文件复制到Windows机器**的一个文件夹中

## ⚡ 一键启动（推荐）

### 步骤1：安装和启动服务
1. 右键点击 `install_and_run.bat`
2. 选择 **"以管理员身份运行"**
3. 按提示操作：
   - 创建虚拟环境？输入 `Y` 回车
   - 立即启动服务？输入 `Y` 回车

### 步骤2：配置防火墙（可选）
1. 右键点击 `setup_firewall.bat`
2. 选择 **"以管理员身份运行"**
3. 输入 `Y` 确认添加防火墙规则

### 步骤3：测试服务
1. 打开新的命令提示符
2. 进入项目目录
3. 运行：`python test_service.py`

## 🌐 获取访问地址

### Windows机器上查看IP地址：
```cmd
ipconfig
```
找到 "IPv4 地址"，例如：`192.168.1.100`

### 访问地址：
- **本地**: http://localhost:8000
- **网络**: http://192.168.1.100:8000
- **API文档**: http://localhost:8000/docs

## 📱 Mac端配置

在Mac项目的 `config/config.json` 中添加：

```json
{
  "video_generation": {
    "multi_backend": {
      "svd": {
        "endpoint": "http://192.168.1.100:8000",
        "enabled": true,
        "priority": 1
      }
    }
  }
}
```

## 🔧 后续使用

### 启动服务（已安装后）：
双击 `start_service.bat`

### 停止服务：
在服务窗口按 `Ctrl+C`

### 删除防火墙规则：
右键运行 `remove_firewall.bat`

## ❗ 常见问题

**Q: 提示"需要管理员权限"？**
A: 右键选择"以管理员身份运行"

**Q: Mac无法连接到Windows服务？**
A: 检查防火墙是否已配置，IP地址是否正确

**Q: 服务启动失败？**
A: 检查Python是否正确安装，查看 `svd_server.log` 日志

**Q: 生成视频很慢？**
A: 正常现象，首次使用需下载模型，GPU版本会更快

## 📞 需要帮助？

查看完整文档：`README.md`

---

**提示**: 首次运行会下载约7GB的AI模型，请耐心等待！