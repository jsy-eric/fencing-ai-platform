import re
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import json

class YouTubeParser:
    def __init__(self):
        self.video_id_patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_url(self, url: str) -> Optional[Dict]:
        """解析YouTube链接"""
        if not url:
            return None
        
        # 清理URL
        url = url.strip()
        
        # 提取视频ID
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        
        # 获取视频信息
        video_info = self.get_video_info(video_id)
        if not video_info:
            # 如果无法获取详细信息，返回基本信息
            video_info = self._create_basic_video_info(video_id, url)
        
        return video_info
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        for pattern in self.video_id_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 尝试解析查询参数
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']:
                if parsed_url.netloc == 'youtu.be':
                    # youtu.be/VIDEO_ID 格式
                    return parsed_url.path[1:]  # 移除开头的斜杠
                elif parsed_url.path == '/watch':
                    # youtube.com/watch?v=VIDEO_ID 格式
                    query_params = parse_qs(parsed_url.query)
                    if 'v' in query_params:
                        return query_params['v'][0]
        except Exception:
            pass
        
        return None
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """获取视频详细信息"""
        try:
            # 尝试获取视频页面
            response = self.session.get(
                f'https://www.youtube.com/watch?v={video_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                # 尝试从页面中提取信息
                video_info = self._extract_from_page(response.text, video_id)
                if video_info:
                    return video_info
        except Exception as e:
            print(f"获取视频信息失败: {e}")
        
        return None
    
    def _extract_from_page(self, html_content: str, video_id: str) -> Optional[Dict]:
        """从HTML页面中提取视频信息"""
        try:
            # 查找包含视频信息的JSON数据
            # YouTube页面通常包含一个名为"ytInitialData"的脚本标签
            
            # 尝试提取ytInitialData
            yt_data_match = re.search(r'var ytInitialData = ({.*?});', html_content)
            if yt_data_match:
                yt_data = json.loads(yt_data_match.group(1))
                return self._parse_yt_data(yt_data, video_id)
            
            # 尝试提取其他格式的数据
            data_match = re.search(r'"videoDetails":\s*({[^}]+})', html_content)
            if data_match:
                # 这里可以进一步解析videoDetails
                pass
            
        except Exception as e:
            print(f"解析页面数据失败: {e}")
        
        return None
    
    def _parse_yt_data(self, yt_data: Dict, video_id: str) -> Optional[Dict]:
        """解析YouTube数据"""
        try:
            # 这个函数需要根据YouTube的实际数据结构来实现
            # 由于YouTube经常更改其数据结构，这里提供一个基本框架
            
            video_info = {
                "id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            }
            
            # 尝试提取标题
            title = self._extract_title_from_data(yt_data)
            if title:
                video_info["title"] = title
            
            # 尝试提取时长
            duration = self._extract_duration_from_data(yt_data)
            if duration:
                video_info["duration"] = duration
            
            # 尝试提取频道信息
            channel = self._extract_channel_from_data(yt_data)
            if channel:
                video_info["channel"] = channel
            
            return video_info
            
        except Exception as e:
            print(f"解析YouTube数据失败: {e}")
            return None
    
    def _extract_title_from_data(self, yt_data: Dict) -> Optional[str]:
        """从数据中提取标题"""
        try:
            # 尝试多个可能的路径来获取标题
            paths = [
                ["videoDetails", "title"],
                ["contents", "twoColumnWatchNextResults", "results", "results", "contents", 0, "videoPrimaryInfoRenderer", "title", "runs", 0, "text"],
                ["contents", "twoColumnWatchNextResults", "results", "results", "contents", 0, "videoPrimaryInfoRenderer", "title", "simpleText"]
            ]
            
            for path in paths:
                value = self._get_nested_value(yt_data, path)
                if value:
                    return value
            
        except Exception:
            pass
        
        return None
    
    def _extract_duration_from_data(self, yt_data: Dict) -> Optional[str]:
        """从数据中提取时长"""
        try:
            # 尝试获取时长信息
            paths = [
                ["videoDetails", "lengthSeconds"],
                ["contents", "twoColumnWatchNextResults", "results", "results", "contents", 0, "videoPrimaryInfoRenderer", "viewCount", "videoViewCountRenderer", "lengthText", "simpleText"]
            ]
            
            for path in paths:
                value = self._get_nested_value(yt_data, path)
                if value:
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, int):
                        return self._format_duration(value)
            
        except Exception:
            pass
        
        return None
    
    def _extract_channel_from_data(self, yt_data: Dict) -> Optional[str]:
        """从数据中提取频道信息"""
        try:
            paths = [
                ["videoDetails", "channelId"],
                ["contents", "twoColumnWatchNextResults", "results", "results", "contents", 0, "videoPrimaryInfoRenderer", "owner", "videoOwnerRenderer", "title", "runs", 0, "text"]
            ]
            
            for path in paths:
                value = self._get_nested_value(yt_data, path)
                if value:
                    return value
            
        except Exception:
            pass
        
        return None
    
    def _get_nested_value(self, data: Dict, path: list) -> any:
        """获取嵌套字典中的值"""
        try:
            current = data
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                    current = current[key]
                else:
                    return None
            return current
        except Exception:
            return None
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def _create_basic_video_info(self, video_id: str, original_url: str) -> Dict:
        """创建基本的视频信息"""
        return {
            "id": video_id,
            "url": original_url,
            "embed_url": self.get_embed_url(video_id),
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "title": f"YouTube视频 ({video_id})",
            "duration": "未知",
            "channel": "未知频道"
        }
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否为有效的YouTube链接"""
        if not url:
            return False
        
        video_id = self.extract_video_id(url)
        return video_id is not None
    
    def get_embed_url(self, video_id: str, autoplay: bool = False, start_time: int = 0, origin: str = None) -> str:
        """生成嵌入URL，使用更稳定的参数组合"""
        params = []
        
        # 基本播放参数
        if autoplay:
            params.append("autoplay=1")
        
        if start_time > 0:
            params.append(f"start={start_time}")
        
        # 使用最简化的参数组合，避免任何可能导致问题的参数
        params.extend([
            "rel=0",  # 不显示相关视频
            "modestbranding=1",  # 减少YouTube品牌显示
            "controls=1",  # 显示控制条
            "fs=1",  # 允许全屏
            "playsinline=1"  # 在移动设备上内联播放
        ])
        
        # 只有在提供origin时才添加这些参数
        if origin:
            params.extend([
                f"origin={origin}",
                f"widget_referrer={origin}"
            ])
        
        query_string = "&".join(params)
        return f"https://www.youtube.com/embed/{video_id}?{query_string}"
    
    def get_thumbnail_urls(self, video_id: str) -> Dict[str, str]:
        """获取不同质量的缩略图URL"""
        return {
            "default": f"https://img.youtube.com/vi/{video_id}/default.jpg",
            "medium": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            "high": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "standard": f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",
            "maxres": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        }
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """提取播放列表ID"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc in ['www.youtube.com', 'youtube.com']:
                query_params = parse_qs(parsed_url.query)
                if 'list' in query_params:
                    return query_params['list'][0]
        except Exception:
            pass
        
        return None
    
    def is_playlist_url(self, url: str) -> bool:
        """检查是否为播放列表URL"""
        return self.extract_playlist_id(url) is not None
    
    def get_video_id_from_embed(self, embed_url: str) -> Optional[str]:
        """从嵌入URL中提取视频ID"""
        return self.extract_video_id(embed_url)
    
    def create_share_url(self, video_id: str, start_time: int = 0) -> str:
        """创建分享URL"""
        if start_time > 0:
            return f"https://youtu.be/{video_id}?t={start_time}"
        else:
            return f"https://youtu.be/{video_id}"
    
    def get_video_info_summary(self, video_id: str) -> Dict:
        """获取视频信息摘要"""
        basic_info = self._create_basic_video_info(video_id, "")
        
        return {
            "video_id": video_id,
            "title": basic_info["title"],
            "embed_url": basic_info["embed_url"],
            "thumbnail": basic_info["thumbnail"],
            "share_url": self.create_share_url(video_id),
            "is_valid": True
        }
