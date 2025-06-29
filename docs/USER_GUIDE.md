# 小说自动视频制作工具 - 用户指南

## 📖 目录

- [快速开始](#快速开始)
- [详细安装](#详细安装)
- [配置说明](#配置说明)
- [使用教程](#使用教程)
- [高级功能](#高级功能)
- [故障排除](#故障排除)
- [API参考](#api参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8+ (推荐 3.9+)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最少 4GB，推荐 8GB+
- **存储**: 至少 10GB 可用空间
- **网络**: 稳定的互联网连接（用于API调用）

### 2. 一键安装

```bash
# 克隆项目
git clone https://github.com/your-repo/novel-to-video.git
cd novel-to-video

# 快速安装
make quickstart
```

### 3. 配置API密钥

编辑 `config/config.json`：

```json
{
  "openai": {
    "api_key": "your-openai-api-key",
    "model": "gpt-4"
  },
  "elevenlabs": {
    "api_key": "your-elevenlabs-api-key"
  }
}
```

### 4. 运行示例

```bash
# 运行内置示例
make run-example

# 或使用自己的小说
python run.py -i "path/to/your/novel.txt"
```

## 🔧 详细安装

### 方式一：使用 Make（推荐）

```bash
# 查看所有可用命令
make help

# 创建虚拟环境并安装
make install-all

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化项目
python setup.py

# 4. 运行测试
python test.py --quick
```

### 方式三：使用 Docker

```bash
# 构建镜像
docker build -t novel-to-video .

# 运行容器
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config:/app/config \
  novel-to-video

# 或使用 Docker Compose
docker-compose up -d
```

## ⚙️ 配置说明

### 主配置文件 (`config/config.json`)

```json
{
  "openai": {
    "api_key": "sk-...",
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1",
    "timeout": 60,
    "max_retries": 3
  },
  "elevenlabs": {
    "api_key": "...",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.8,
      "style": 0.2,
      "use_speaker_boost": true
    }
  },
  "runway": {
    "api_key": "...",
    "model": "gen3a_turbo",
    "resolution": "1280x768",
    "duration": 10,
    "motion_bucket_id": 127
  },
  "text_processing": {
    "max_chapter_length": 3000,
    "scene_extraction_prompt": "提取关键场景...",
    "script_generation_prompt": "生成旁白脚本...",
    "language": "zh-CN"
  },
  "video_editing": {
    "output_resolution": "1920x1080",
    "fps": 30,
    "video_codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "5000k",
    "subtitle_font": "Arial",
    "subtitle_size": 24
  }
}
```

### 环境变量配置

创建 `.env` 文件：

```bash
# API密钥
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
RUNWAY_API_KEY=...
YOUTUBE_API_KEY=...

# 代理设置（如需要）
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080

# 调试模式
DEBUG=false
LOG_LEVEL=INFO

# 缓存设置
CACHE_ENABLED=true
CACHE_TTL=3600
```

## 📚 使用教程

### 基础使用

#### 1. 准备小说文件

将小说文件放在 `data/novels/` 目录下：

```
data/novels/
├── 重生之都市修仙.txt
├── 斗破苍穹.txt
└── 完美世界.txt
```

#### 2. 运行转换

```bash
# 交互式模式
python run.py --interactive

# 命令行模式
python run.py -i "data/novels/重生之都市修仙.txt" -p standard

# 批量处理
python run.py --batch "data/novels/" -p quick
```

#### 3. 查看输出

```
output/
├── 重生之都市修仙/
│   ├── full_video.mp4      # 完整视频
│   ├── shorts/             # 短视频片段
│   │   ├── part_001.mp4
│   │   ├── part_002.mp4
│   │   └── ...
│   ├── audio/              # 音频文件
│   ├── subtitles/          # 字幕文件
│   └── metadata.json       # 元数据
└── ...
```

### 高级使用

#### 1. 自定义配置

```python
# custom_config.py
from src.text_processor import TextProcessor
from src.audio_generator import AudioGenerator
from src.video_generator import VideoGenerator
from src.video_editor import VideoEditor

# 自定义文本处理
processor = TextProcessor(config)
processor.set_custom_prompt(
    scene_extraction="根据小说内容，提取5个最精彩的场景...",
    script_generation="为每个场景生成30秒的旁白脚本..."
)

# 自定义音频生成
audio_gen = AudioGenerator(config)
audio_gen.set_voice_settings(
    voice_id="custom_voice_id",
    stability=0.7,
    similarity_boost=0.9
)

# 自定义视频编辑
editor = VideoEditor(config)
editor.set_style(
    font_family="思源黑体",
    subtitle_position="bottom",
    transition_effect="fade"
)
```

#### 2. 批量处理脚本

```python
# batch_process.py
import os
from main import NovelToVideoConverter

def batch_convert(novels_dir, output_dir):
    converter = NovelToVideoConverter()
    
    for filename in os.listdir(novels_dir):
        if filename.endswith('.txt'):
            novel_path = os.path.join(novels_dir, filename)
            print(f"处理: {filename}")
            
            try:
                result = converter.convert(
                    input_file=novel_path,
                    output_dir=output_dir,
                    preset="standard"
                )
                print(f"✅ 完成: {result['output_path']}")
            except Exception as e:
                print(f"❌ 失败: {e}")

if __name__ == "__main__":
    batch_convert("data/novels", "output")
```

#### 3. API集成

```python
# api_example.py
from main import NovelToVideoConverter
import json

# 初始化转换器
converter = NovelToVideoConverter()

# 转换小说
result = converter.convert(
    input_file="data/novels/example.txt",
    output_dir="output",
    preset="premium",
    options={
        "generate_shorts": True,
        "upload_to_youtube": False,
        "add_background_music": True
    }
)

# 获取结果
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 🎯 高级功能

### 1. 短视频生成

```bash
# 生成短视频片段
python run.py -i "novel.txt" -p shorts --duration 60

# 自定义短视频参数
python run.py -i "novel.txt" --shorts-config '{
  "duration": 90,
  "aspect_ratio": "9:16",
  "segments": 5,
  "add_hooks": true
}'
```

### 2. 自定义模板

```python
# templates/custom_template.py
class CustomTemplate:
    def __init__(self):
        self.intro_duration = 5
        self.outro_duration = 3
        self.transition_style = "crossfade"
    
    def apply(self, video_editor):
        # 添加片头
        video_editor.add_intro(
            text="欢迎观看小说解说",
            duration=self.intro_duration
        )
        
        # 设置转场效果
        video_editor.set_transitions(self.transition_style)
        
        # 添加片尾
        video_editor.add_outro(
            text="感谢观看，请点赞订阅",
            duration=self.outro_duration
        )
```

### 3. 插件系统

```python
# plugins/background_music.py
class BackgroundMusicPlugin:
    def __init__(self, music_dir="assets/music"):
        self.music_dir = music_dir
    
    def process(self, video_path, audio_path):
        # 添加背景音乐
        background_music = self.select_music(audio_path)
        return self.mix_audio(audio_path, background_music)
    
    def select_music(self, audio_path):
        # 根据音频情感选择背景音乐
        emotion = self.analyze_emotion(audio_path)
        return f"{self.music_dir}/{emotion}.mp3"
```

### 4. 监控和日志

```python
# monitoring/logger.py
import logging
from datetime import datetime

class VideoLogger:
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/conversion.log'),
                logging.StreamHandler()
            ]
        )
    
    def log_conversion_start(self, novel_path):
        logging.info(f"开始转换: {novel_path}")
    
    def log_conversion_complete(self, output_path, duration):
        logging.info(f"转换完成: {output_path}, 耗时: {duration}秒")
```

## 🔧 故障排除

### 常见问题

#### 1. API密钥错误

```bash
# 检查API密钥
python -c "from src.utils import validate_api_keys; validate_api_keys()"

# 测试OpenAI连接
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

#### 2. 内存不足

```python
# 调整配置以减少内存使用
config = {
    "text_processing": {
        "max_chapter_length": 1500,  # 减少章节长度
        "batch_size": 1              # 减少批处理大小
    },
    "video_editing": {
        "output_resolution": "1280x720",  # 降低分辨率
        "fps": 24                         # 降低帧率
    }
}
```

#### 3. FFmpeg错误

```bash
# 检查FFmpeg安装
ffmpeg -version

# 重新安装FFmpeg
# macOS
brew install ffmpeg

# Ubuntu
sudo apt update && sudo apt install ffmpeg

# Windows
# 下载并安装 https://ffmpeg.org/download.html
```

#### 4. 网络连接问题

```python
# 设置代理
import os
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'https://proxy.example.com:8080'

# 或在配置文件中设置
config = {
    "network": {
        "proxy": {
            "http": "http://proxy.example.com:8080",
            "https": "https://proxy.example.com:8080"
        },
        "timeout": 120,
        "max_retries": 5
    }
}
```

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python run.py -i "novel.txt" --debug

# 保存中间文件
python run.py -i "novel.txt" --keep-temp

# 单步执行
python run.py -i "novel.txt" --step-by-step
```

### 性能优化

```python
# performance_config.py
config = {
    "performance": {
        "parallel_processing": True,
        "max_workers": 4,
        "cache_enabled": True,
        "gpu_acceleration": True,
        "memory_limit": "4GB"
    },
    "optimization": {
        "video_quality": "medium",
        "audio_quality": "high",
        "compression_level": 6
    }
}
```

## 📊 API参考

### 主要类

#### NovelToVideoConverter

```python
class NovelToVideoConverter:
    def __init__(self, config_path="config/config.json"):
        """初始化转换器"""
    
    def convert(self, input_file, output_dir, preset="standard", **options):
        """转换小说为视频
        
        Args:
            input_file (str): 小说文件路径
            output_dir (str): 输出目录
            preset (str): 预设配置 (quick/standard/premium/shorts)
            **options: 额外选项
        
        Returns:
            dict: 转换结果
        """
    
    def batch_convert(self, input_dir, output_dir, **options):
        """批量转换"""
```

#### TextProcessor

```python
class TextProcessor:
    def extract_scenes(self, text, max_scenes=5):
        """提取关键场景"""
    
    def generate_script(self, scenes):
        """生成旁白脚本"""
    
    def split_chapters(self, text, max_length=3000):
        """分割章节"""
```

#### AudioGenerator

```python
class AudioGenerator:
    def text_to_speech(self, text, voice_id=None):
        """文本转语音"""
    
    def process_audio(self, audio_path):
        """音频后处理"""
    
    def get_audio_duration(self, audio_path):
        """获取音频时长"""
```

#### VideoGenerator

```python
class VideoGenerator:
    def generate_video(self, prompt, duration=10):
        """生成视频片段"""
    
    def batch_generate(self, prompts):
        """批量生成视频"""
```

#### VideoEditor

```python
class VideoEditor:
    def compose_video(self, video_clips, audio_path, subtitle_path):
        """合成最终视频"""
    
    def add_subtitles(self, video_path, subtitle_data):
        """添加字幕"""
    
    def generate_shorts(self, video_path, duration=60, segments=5):
        """生成短视频"""
```

### 配置选项

```python
# 预设配置
PRESETS = {
    "quick": {
        "max_scenes": 3,
        "video_duration": 5,
        "resolution": "1280x720",
        "quality": "medium"
    },
    "standard": {
        "max_scenes": 5,
        "video_duration": 10,
        "resolution": "1920x1080",
        "quality": "high"
    },
    "premium": {
        "max_scenes": 8,
        "video_duration": 15,
        "resolution": "1920x1080",
        "quality": "ultra"
    },
    "shorts": {
        "max_scenes": 3,
        "video_duration": 8,
        "resolution": "1080x1920",
        "aspect_ratio": "9:16"
    }
}
```

## 💡 最佳实践

### 1. 小说准备

- **格式**: 使用UTF-8编码的TXT文件
- **长度**: 单章建议3000-5000字
- **结构**: 清晰的章节分割
- **内容**: 情节紧凑，画面感强

### 2. 配置优化

```python
# 针对不同类型小说的配置
CONFIG_TEMPLATES = {
    "都市修仙": {
        "scene_keywords": ["修炼", "战斗", "突破", "法术"],
        "voice_style": "激昂",
        "background_music": "epic"
    },
    "言情小说": {
        "scene_keywords": ["相遇", "告白", "误会", "和解"],
        "voice_style": "温柔",
        "background_music": "romantic"
    },
    "悬疑推理": {
        "scene_keywords": ["线索", "推理", "真相", "揭露"],
        "voice_style": "神秘",
        "background_music": "suspense"
    }
}
```

### 3. 性能优化

```python
# 缓存策略
CACHE_CONFIG = {
    "text_processing": {
        "enabled": True,
        "ttl": 3600,  # 1小时
        "max_size": "100MB"
    },
    "audio_generation": {
        "enabled": True,
        "ttl": 86400,  # 24小时
        "max_size": "500MB"
    },
    "video_generation": {
        "enabled": True,
        "ttl": 86400,  # 24小时
        "max_size": "1GB"
    }
}
```

### 4. 质量控制

```python
# 质量检查
QUALITY_CHECKS = {
    "text": {
        "min_length": 1000,
        "max_length": 10000,
        "encoding": "utf-8"
    },
    "audio": {
        "min_duration": 30,
        "max_duration": 600,
        "sample_rate": 44100,
        "format": "wav"
    },
    "video": {
        "min_duration": 60,
        "max_duration": 1800,
        "min_resolution": "720p",
        "fps": 30
    }
}
```

## ❓ 常见问题

### Q: 支持哪些小说格式？
A: 目前支持UTF-8编码的TXT文件。计划支持EPUB、PDF等格式。

### Q: 生成的视频质量如何？
A: 支持720p到4K的多种分辨率，可根据需求调整质量设置。

### Q: 是否支持多语言？
A: 目前主要支持中文，计划添加英文、日文等语言支持。

### Q: API调用费用如何？
A: 费用取决于使用的服务：
- OpenAI GPT-4: ~$0.03/1K tokens
- ElevenLabs TTS: ~$0.30/1K characters
- Runway视频生成: ~$0.05/second

### Q: 可以商用吗？
A: 请遵守各API服务商的使用条款，确保内容版权合规。

### Q: 如何提高生成速度？
A: 
1. 使用GPU加速
2. 启用缓存
3. 调整质量设置
4. 使用并行处理

### Q: 支持自定义声音吗？
A: 支持ElevenLabs的声音克隆功能，可以使用自定义声音。

### Q: 如何批量处理？
A: 使用 `--batch` 参数或编写批处理脚本。

---

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/your-repo/novel-to-video/issues)
- **文档**: [在线文档](https://your-docs-site.com)
- **社区**: [Discord群组](https://discord.gg/your-invite)
- **邮箱**: support@your-domain.com

---

*最后更新: 2024年12月*