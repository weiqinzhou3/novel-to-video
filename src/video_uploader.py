#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频上传模块

功能：
1. 上传视频到YouTube
2. 自动生成视频标题、描述和标签
3. 设置视频缩略图
4. 批量上传管理
5. 上传进度监控
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import requests
from PIL import Image, ImageDraw, ImageFont


class VideoUploader:
    """视频上传器类"""
    
    # YouTube API作用域
    YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    
    def __init__(self, config: Dict[str, Any]):
        """初始化视频上传器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.upload_config = config.get('upload', {})
        self.youtube_config = config.get('api_keys', {}).get('youtube', {})
        
        # YouTube服务
        self.youtube_service = None
        
        # 上传设置
        self.default_privacy = self.upload_config.get('default_privacy', 'private')
        self.default_category = self.upload_config.get('default_category', '24')  # Entertainment
        
        self.logger.info("视频上传器初始化完成")
    
    def _get_youtube_credentials(self) -> Credentials:
        """获取YouTube API凭证
        
        Returns:
            Google API凭证
        """
        creds = None
        token_file = self.youtube_config.get('token_file', 'token.json')
        credentials_file = self.youtube_config.get('credentials_file', 'credentials.json')
        
        # 检查是否存在已保存的凭证
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.YOUTUBE_UPLOAD_SCOPE)
        
        # 如果没有有效凭证，进行OAuth流程
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"刷新凭证失败: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"YouTube API凭证文件不存在: {credentials_file}\n"
                        "请从Google Cloud Console下载OAuth 2.0凭证文件"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.YOUTUBE_UPLOAD_SCOPE
                )
                creds = flow.run_local_server(port=0)
            
            # 保存凭证
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def _initialize_youtube_service(self):
        """初始化YouTube API服务"""
        try:
            if self.youtube_service is None:
                credentials = self._get_youtube_credentials()
                self.youtube_service = build(
                    self.YOUTUBE_API_SERVICE_NAME,
                    self.YOUTUBE_API_VERSION,
                    credentials=credentials
                )
                self.logger.info("YouTube API服务初始化完成")
        except Exception as e:
            self.logger.error(f"YouTube API服务初始化失败: {e}")
            raise
    
    def _generate_video_metadata(self, novel_title: str, chapter_info: str = None, 
                                keywords: List[str] = None) -> Dict[str, Any]:
        """生成视频元数据
        
        Args:
            novel_title: 小说标题
            chapter_info: 章节信息
            keywords: 关键词列表
            
        Returns:
            视频元数据字典
        """
        # 生成标题
        if chapter_info:
            title = f"【一口气看完】{novel_title} - {chapter_info}"
        else:
            title = f"【一口气看完】{novel_title}"
        
        # 限制标题长度
        if len(title) > 100:
            title = title[:97] + "..."
        
        # 生成描述
        description_parts = [
            f"📚 小说名称：{novel_title}",
            "",
            "🎬 本视频为AI自动生成的小说解说视频",
            "📖 完整还原小说精彩情节",
            "🎵 配音：AI语音合成",
            "🎨 画面：AI视频生成",
            "",
            "⚠️ 免责声明：",
            "本视频仅供娱乐和学习交流使用",
            "如有版权问题，请联系删除",
            "",
            "🔔 喜欢的话请点赞订阅支持！",
            "",
            "#小说解说 #AI视频 #一口气看完"
        ]
        
        if chapter_info:
            description_parts.insert(2, f"📑 章节：{chapter_info}")
        
        description = "\n".join(description_parts)
        
        # 生成标签
        default_tags = [
            "小说解说", "AI视频", "一口气看完", "小说推荐", 
            "网络小说", "故事解说", "书评", "文学"
        ]
        
        if keywords:
            tags = list(set(default_tags + keywords))
        else:
            tags = default_tags
        
        # 限制标签数量和长度
        tags = tags[:15]  # YouTube最多15个标签
        tags = [tag[:30] for tag in tags]  # 每个标签最多30字符
        
        return {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': self.default_category,
            'privacyStatus': self.default_privacy
        }
    
    def _create_thumbnail(self, novel_title: str, output_path: str) -> str:
        """创建视频缩略图
        
        Args:
            novel_title: 小说标题
            output_path: 输出路径
            
        Returns:
            缩略图文件路径
        """
        try:
            # 缩略图尺寸 (YouTube推荐1280x720)
            width, height = 1280, 720
            
            # 创建图像
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # 添加渐变背景
            for y in range(height):
                r = int(26 + (52 - 26) * y / height)
                g = int(26 + (73 - 26) * y / height)
                b = int(46 + (94 - 46) * y / height)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # 尝试加载字体
            try:
                # macOS系统字体
                title_font = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 80)
                subtitle_font = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 40)
            except:
                try:
                    # 备用字体
                    title_font = ImageFont.truetype('arial.ttf', 80)
                    subtitle_font = ImageFont.truetype('arial.ttf', 40)
                except:
                    # 默认字体
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
            
            # 添加主标题
            main_title = "【一口气看完】"
            title_bbox = draw.textbbox((0, 0), main_title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            title_y = height // 3
            
            # 添加标题阴影
            draw.text((title_x + 3, title_y + 3), main_title, font=title_font, fill='black')
            draw.text((title_x, title_y), main_title, font=title_font, fill='white')
            
            # 添加小说标题
            # 处理长标题换行
            max_chars_per_line = 20
            if len(novel_title) > max_chars_per_line:
                lines = []
                for i in range(0, len(novel_title), max_chars_per_line):
                    lines.append(novel_title[i:i + max_chars_per_line])
                novel_title_display = '\n'.join(lines[:2])  # 最多显示2行
            else:
                novel_title_display = novel_title
            
            subtitle_lines = novel_title_display.split('\n')
            subtitle_y = title_y + 120
            
            for line in subtitle_lines:
                subtitle_bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_x = (width - subtitle_width) // 2
                
                # 添加阴影
                draw.text((subtitle_x + 2, subtitle_y + 2), line, font=subtitle_font, fill='black')
                draw.text((subtitle_x, subtitle_y), line, font=subtitle_font, fill='#ffd700')
                
                subtitle_y += 60
            
            # 添加装饰元素
            # 左上角装饰
            draw.rectangle([50, 50, 200, 100], fill='#ff6b6b')
            draw.text((60, 60), "AI制作", font=subtitle_font, fill='white')
            
            # 右下角装饰
            draw.rectangle([width-200, height-100, width-50, height-50], fill='#4ecdc4')
            draw.text((width-190, height-90), "高清", font=subtitle_font, fill='white')
            
            # 保存缩略图
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, 'JPEG', quality=95)
            
            self.logger.info(f"缩略图创建完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"创建缩略图失败: {e}")
            return None
    
    def upload_to_youtube(self, video_path: str, novel_title: str, 
                         chapter_info: str = None, keywords: List[str] = None,
                         thumbnail_path: str = None) -> Dict[str, Any]:
        """上传视频到YouTube
        
        Args:
            video_path: 视频文件路径
            novel_title: 小说标题
            chapter_info: 章节信息
            keywords: 关键词列表
            thumbnail_path: 缩略图路径
            
        Returns:
            上传结果信息
        """
        try:
            self.logger.info(f"开始上传视频到YouTube: {video_path}")
            
            # 初始化YouTube服务
            self._initialize_youtube_service()
            
            # 验证视频文件
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size > 128 * 1024 * 1024 * 1024:  # 128GB限制
                raise ValueError("视频文件过大，超过YouTube限制")
            
            # 生成视频元数据
            metadata = self._generate_video_metadata(novel_title, chapter_info, keywords)
            
            # 准备上传请求
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': metadata['categoryId']
                },
                'status': {
                    'privacyStatus': metadata['privacyStatus']
                }
            }
            
            # 创建媒体上传对象
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            # 执行上传
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # 上传进度监控
            response = None
            error = None
            retry = 0
            
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        self.logger.info(f"上传进度: {progress}%")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # 可重试的错误
                        retry += 1
                        if retry > 5:
                            raise e
                        
                        wait_time = 2 ** retry
                        self.logger.warning(f"上传出错，{wait_time}秒后重试: {e}")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            if response is not None:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                self.logger.info(f"视频上传成功: {video_url}")
                
                # 上传缩略图
                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        self._upload_thumbnail(video_id, thumbnail_path)
                    except Exception as e:
                        self.logger.warning(f"缩略图上传失败: {e}")
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': metadata['title'],
                    'privacy_status': metadata['privacyStatus']
                }
            else:
                raise RuntimeError("上传失败，未收到响应")
                
        except Exception as e:
            self.logger.error(f"YouTube上传失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """上传视频缩略图
        
        Args:
            video_id: 视频ID
            thumbnail_path: 缩略图路径
        """
        try:
            self.youtube_service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            
            self.logger.info(f"缩略图上传成功: {video_id}")
            
        except Exception as e:
            self.logger.error(f"缩略图上传失败: {e}")
            raise
    
    def batch_upload(self, video_info_list: List[Dict[str, Any]], 
                    create_thumbnails: bool = True) -> List[Dict[str, Any]]:
        """批量上传视频
        
        Args:
            video_info_list: 视频信息列表
            create_thumbnails: 是否创建缩略图
            
        Returns:
            上传结果列表
        """
        results = []
        
        for i, video_info in enumerate(video_info_list):
            try:
                self.logger.info(f"批量上传进度: {i+1}/{len(video_info_list)}")
                
                video_path = video_info['video_path']
                novel_title = video_info['novel_title']
                chapter_info = video_info.get('chapter_info')
                keywords = video_info.get('keywords', [])
                
                # 创建缩略图
                thumbnail_path = None
                if create_thumbnails:
                    thumbnail_dir = os.path.join(os.path.dirname(video_path), 'thumbnails')
                    thumbnail_path = os.path.join(
                        thumbnail_dir, 
                        f"thumbnail_{i+1}.jpg"
                    )
                    self._create_thumbnail(novel_title, thumbnail_path)
                
                # 上传视频
                result = self.upload_to_youtube(
                    video_path, novel_title, chapter_info, keywords, thumbnail_path
                )
                
                result['index'] = i + 1
                results.append(result)
                
                # 避免API限制，添加延迟
                if i < len(video_info_list) - 1:
                    time.sleep(5)
                    
            except Exception as e:
                self.logger.error(f"批量上传第{i+1}个视频失败: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'index': i + 1
                })
        
        # 统计结果
        successful = sum(1 for r in results if r.get('success', False))
        self.logger.info(f"批量上传完成: {successful}/{len(video_info_list)} 成功")
        
        return results
    
    def update_video_info(self, video_id: str, title: str = None, 
                         description: str = None, tags: List[str] = None) -> bool:
        """更新视频信息
        
        Args:
            video_id: 视频ID
            title: 新标题
            description: 新描述
            tags: 新标签
            
        Returns:
            更新是否成功
        """
        try:
            self._initialize_youtube_service()
            
            # 获取当前视频信息
            response = self.youtube_service.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not response['items']:
                raise ValueError(f"视频不存在: {video_id}")
            
            snippet = response['items'][0]['snippet']
            
            # 更新信息
            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags
            
            # 提交更新
            self.youtube_service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            ).execute()
            
            self.logger.info(f"视频信息更新成功: {video_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"视频信息更新失败: {e}")
            return False
    
    def get_upload_quota(self) -> Dict[str, Any]:
        """获取上传配额信息
        
        Returns:
            配额信息
        """
        try:
            self._initialize_youtube_service()
            
            # YouTube API没有直接的配额查询接口
            # 这里返回一般的限制信息
            return {
                'daily_upload_limit': '6 videos or 12 hours',
                'file_size_limit': '128 GB',
                'video_length_limit': '12 hours',
                'api_quota_limit': '10,000 units per day'
            }
            
        except Exception as e:
            self.logger.error(f"获取配额信息失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    test_config = {
        'api_keys': {
            'youtube': {
                'credentials_file': 'credentials.json',
                'token_file': 'token.json'
            }
        },
        'upload': {
            'default_privacy': 'private',
            'default_category': '24'
        }
    }
    
    uploader = VideoUploader(test_config)
    
    # 创建测试缩略图
    thumbnail_path = uploader._create_thumbnail("测试小说", "test_thumbnail.jpg")
    print(f"测试缩略图创建: {thumbnail_path}")
    
    # 生成测试元数据
    metadata = uploader._generate_video_metadata("测试小说", "第一章", ["玄幻", "修仙"])
    print(f"测试元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")