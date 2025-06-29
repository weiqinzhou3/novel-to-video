# 小说自动视频制作工具

基于AI技术的小说转视频自动化工具，可将TXT小说文件自动制作成3-5分钟的解说视频，并可选拆分成短视频片段。

## 功能特点

- 🤖 **全自动化**：无需人工干预，一键生成视频
- 💰 **低成本**：单个视频成本约1美元
- ⚡ **高效率**：全流程耗时约4-10分钟
- 📱 **多格式**：支持横屏和竖屏短视频输出
- 🎨 **可定制**：支持字幕、配色和模板自定义

## 系统要求

- macOS/Windows/Linux
- Python ≥ 3.10
- Node.js ≥ 20
- FFmpeg

## 快速开始

### 1. 安装依赖

```bash
# 安装FFmpeg
# macOS
brew install ffmpeg
# Windows
choco install ffmpeg
# Ubuntu/Debian
sudo apt install ffmpeg

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install
```

### 2. 配置API密钥

复制配置文件并填入你的API密钥：

```bash
cp config/config.example.json config/config.json
```

编辑 `config/config.json`，填入以下API密钥：

- OpenAI API Key（用于GPT和TTS）
- Runway API Key（用于视频生成）
- ElevenLabs API Key（可选，用于高质量语音）
- YouTube Data API Key（可选，用于自动上传）

### 3. 运行示例

```bash
# 将小说文件放入input目录
cp your_novel.txt input/

# 运行自动化脚本
./make_video.sh input/your_novel.txt

# 或使用Python脚本
python main.py --input input/your_novel.txt --output output/
```

## 项目结构

```
novel-to-video/
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
├── package.json          # Node.js依赖
├── make_video.sh         # 一键执行脚本
├── main.py               # 主程序入口
├── config/
│   ├── config.example.json # 配置模板
│   └── config.json        # 实际配置（需创建）
├── src/
│   ├── text_processor.py  # 文本处理模块
│   ├── audio_generator.py # 音频生成模块
│   ├── video_generator.py # 视频生成模块
│   ├── video_editor.py    # 视频编辑模块
│   └── uploader.py        # 上传模块
├── templates/
│   ├── subtitle_styles/   # 字幕样式
│   └── video_templates/   # 视频模板
├── input/                 # 输入文件目录
├── output/                # 输出文件目录
└── temp/                  # 临时文件目录
```

## 使用流程

1. **文本处理**：AI提取小说关键情节，生成脚本
2. **音频生成**：将脚本转换为高质量配音
3. **视频生成**：根据情节生成对应的视觉画面
4. **视频编辑**：音画同步，添加字幕和特效
5. **格式输出**：生成横屏视频和竖屏短视频
6. **自动上传**：可选自动上传到各大平台

## 成本预估

| 服务 | 用途 | 成本（每视频） |
|------|------|----------------|
| OpenAI GPT | 文本摘要 | ~$0.25 |
| OpenAI TTS | 语音合成 | ~$0.15 |
| Runway Gen-4 | 视频生成 | ~$0.60 |
| **总计** | | **~$1.00** |

## 高级功能

### 批量处理

```bash
# 批量处理多个小说
python batch_process.py --input-dir novels/ --output-dir videos/
```

### 自定义模板

```bash
# 使用自定义视频模板
python main.py --template templates/my_template.json --input novel.txt
```

### 短视频拆分

```bash
# 自动拆分为TikTok/YouTube Shorts格式
python shorts_generator.py --input output/final_video.mp4
```

## 故障排除

### 常见问题

**Q: 提示"context_length_exceeded"错误**
A: 小说过长，请使用 `--split-chapters` 参数分章处理

**Q: 视频画面时长不够**
A: 在配置中增加 `video_loop_count` 或启用 `ken_burns_effect`

**Q: 音频质量不佳**
A: 建议使用ElevenLabs API或调整OpenAI TTS的voice参数

### 日志查看

```bash
# 查看详细日志
tail -f logs/video_generation.log
```

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 免责声明

请确保使用的小说内容符合版权法规，建议使用公版作品或原创内容。