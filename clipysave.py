"""
Video Downloader Library
A comprehensive library for downloading videos from YouTube, Instagram, and VK
Author: @thetemirbolatov
Version: 2.0.0
"""

import os
import sys
import json
import logging
import subprocess
import re
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Platform(Enum):
    """Supported platforms"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    VK = "vk"
    UNKNOWN = "unknown"

class VideoQuality(Enum):
    """Video quality presets"""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"
    AUDIO_ONLY = "audio_only"

@dataclass
class DownloadResult:
    """Result of a download operation"""
    success: bool
    platform: Platform
    url: str
    title: str = ""
    files: List[Path] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    download_time: float = 0.0
    total_size: int = 0

@dataclass
class VideoInfo:
    """Video information"""
    platform: Platform
    url: str
    title: str
    duration: Optional[int] = None
    uploader: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    formats: List[Dict[str, Any]] = field(default_factory=list)
    is_live: bool = False
    available_qualities: List[str] = field(default_factory=list)

class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else Path.home() / '.video_downloader' / 'config.json'
        self.config_dir = self.config_path.parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_config = {
            'download_path': str(Path.home() / 'Downloads' / 'VideoDownloader'),
            'temp_path': str(Path(tempfile.gettempdir()) / 'video_downloader'),
            'default_quality': 'highest',
            'youtube': {
                'cookies_file': None,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'embed_metadata': True,
                'embed_thumbnail': True,
                'subtitles': False,
                'subtitles_languages': ['en']
            },
            'instagram': {
                'cookies_file': None,
                'session_file': None,
                'username': None,
                'save_metadata': False,
                'download_videos': True,
                'download_video_thumbnails': False
            },
            'vk': {
                'cookies_file': None,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'referer': 'https://vk.com/',
                'max_quality': '1080p'
            },
            'proxy': None,
            'retries': 5,
            'timeout': 30,
            'rate_limit': None,  # in KB/s
            'concurrent_downloads': 1,
            'output_template': '%(title)s_%(resolution)s.%(ext)s'
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge with default config
                    merged = self.default_config.copy()
                    self._deep_update(merged, user_config)
                    return merged
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _deep_update(self, target: Dict, source: Dict):
        """Deep update dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save_config(self.config)

class CookieManager:
    """Manage cookies for different platforms"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cookies_dir = Path(config.config_dir) / 'cookies'
        self.cookies_dir.mkdir(exist_ok=True)
    
    def set_cookies(self, platform: Platform, cookies: Union[str, Dict, Path]):
        """
        Set cookies for a platform
        
        Args:
            platform: Platform to set cookies for
            cookies: Cookies as string, dict, or path to cookie file
        """
        cookie_file = self.cookies_dir / f"{platform.value}_cookies.txt"
        
        if isinstance(cookies, Path):
            shutil.copy(cookies, cookie_file)
        elif isinstance(cookies, dict):
            self._dict_to_netscape(cookies, cookie_file)
        elif isinstance(cookies, str):
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookies)
        
        # Update config
        self.config.set(f"{platform.value}.cookies_file", str(cookie_file))
        logger.info(f"Cookies set for {platform.value}")
    
    def _dict_to_netscape(self, cookies: Dict, output_file: Path):
        """Convert dict cookies to Netscape format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for domain, cookie_data in cookies.items():
                for name, value in cookie_data.items():
                    f.write(f"{domain}\tTRUE\t/\tFALSE\t0\t{name}\t{value}\n")
    
    def get_cookie_file(self, platform: Platform) -> Optional[Path]:
        """Get cookie file path for platform"""
        return self.config.get(f"{platform.value}.cookies_file")
    
    def clear_cookies(self, platform: Optional[Platform] = None):
        """Clear cookies for platform or all platforms"""
        if platform:
            cookie_file = self.get_cookie_file(platform)
            if cookie_file and Path(cookie_file).exists():
                Path(cookie_file).unlink()
            self.config.set(f"{platform.value}.cookies_file", None)
        else:
            for platform in Platform:
                self.clear_cookies(platform)

class ProgressTracker:
    """Track download progress"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.start_time = None
        self.downloaded_bytes = 0
        self.total_bytes = 0
    
    def update(self, downloaded: int, total: int, speed: Optional[float] = None):
        """Update progress"""
        self.downloaded_bytes = downloaded
        self.total_bytes = total
        
        if self.callback:
            percentage = (downloaded / total * 100) if total > 0 else 0
            self.callback({
                'downloaded': downloaded,
                'total': total,
                'percentage': percentage,
                'speed': speed
            })

class VideoDownloader:
    """
    Main downloader class for YouTube, Instagram, and VK
    """
    
    def __init__(self, config: Optional[Union[Dict, Config]] = None):
        """
        Initialize VideoDownloader
        
        Args:
            config: Configuration dictionary or Config object
        """
        if isinstance(config, Config):
            self.config = config
        else:
            self.config = Config()
            if config:
                self.config.config.update(config)
        
        self.cookie_manager = CookieManager(self.config)
        self._check_dependencies()
        
        # Create download directory
        self.download_path = Path(self.config.get('download_path'))
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Create temp directory
        self.temp_path = Path(self.config.get('temp_path'))
        self.temp_path.mkdir(parents=True, exist_ok=True)
    
    def _check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            import yt_dlp
        except ImportError:
            logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
            raise ImportError("yt-dlp is required")
        
        try:
            import instaloader
        except ImportError:
            logger.warning("instaloader not installed. Instagram downloads will not work.")
            logger.warning("Install with: pip install instaloader")
    
    def detect_platform(self, url: str) -> Platform:
        """Detect platform from URL"""
        url_lower = url.lower()
        
        youtube_patterns = [
            r'youtube\.com',
            r'youtu\.be',
            r'm\.youtube\.com',
            r'youtube\.com\/shorts\/',
            r'music\.youtube\.com'
        ]
        
        instagram_patterns = [
            r'instagram\.com\/p\/',
            r'instagram\.com\/reel\/',
            r'instagram\.com\/tv\/',
            r'instagr\.am'
        ]
        
        vk_patterns = [
            r'vk\.com\/video',
            r'vk\.com\/wall.*?z=video',
            r'm\.vk\.com\/video',
            r'vkvideo\.ru\/video',  # ƒÓ·‡‚ÎˇÂÏ ÌÓ‚˚È ‰ÓÏÂÌ
            r'vk\.ru\/video'         # ƒÓ·‡‚ÎˇÂÏ vk.ru
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url_lower):
                return Platform.YOUTUBE
        
        for pattern in instagram_patterns:
            if re.search(pattern, url_lower):
                return Platform.INSTAGRAM
        
        for pattern in vk_patterns:
            if re.search(pattern, url_lower):
                return Platform.VK
        
        return Platform.UNKNOWN
    
    def get_video_info(self, url: str) -> VideoInfo:
        """
        Get video information without downloading
        
        Args:
            url: Video URL
            
        Returns:
            VideoInfo object with video metadata
        """
        platform = self.detect_platform(url)
        
        if platform == Platform.YOUTUBE:
            return self._get_youtube_info(url)
        elif platform == Platform.INSTAGRAM:
            return self._get_instagram_info(url)
        elif platform == Platform.VK:
            return self._get_vk_info(url)
        else:
            raise ValueError(f"Unsupported platform: {url}")
    
    def _get_youtube_info(self, url: str) -> VideoInfo:
        """Get YouTube video info"""
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        cookie_file = self.cookie_manager.get_cookie_file(Platform.YOUTUBE)
        if cookie_file and Path(cookie_file).exists():
            ydl_opts['cookiefile'] = str(cookie_file)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                # Get available formats
                formats = []
                available_qualities = []
                
                if 'formats' in info:
                    for f in info['formats']:
                        format_info = {
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext'),
                            'resolution': f.get('resolution'),
                            'filesize': f.get('filesize'),
                            'vcodec': f.get('vcodec'),
                            'acodec': f.get('acodec')
                        }
                        formats.append(format_info)
                        
                        if f.get('height') and f.get('height') not in available_qualities:
                            available_qualities.append(f"{f.get('height')}p")
                
                return VideoInfo(
                    platform=Platform.YOUTUBE,
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration'),
                    uploader=info.get('uploader'),
                    views=info.get('view_count'),
                    likes=info.get('like_count'),
                    description=info.get('description'),
                    thumbnail=info.get('thumbnail'),
                    formats=formats,
                    is_live=info.get('is_live', False),
                    available_qualities=available_qualities
                )
            except Exception as e:
                logger.error(f"Error getting YouTube info: {e}")
                raise
    
    def _get_instagram_info(self, url: str) -> VideoInfo:
        """Get Instagram video/post info"""
        try:
            import instaloader
            
            L = instaloader.Instaloader()
            
            cookie_file = self.cookie_manager.get_cookie_file(Platform.INSTAGRAM)
            if cookie_file and Path(cookie_file).exists():
                # Load session from cookies
                L.load_session_from_file(username=None, filename=str(cookie_file))
            
            # Extract shortcode
            shortcode = self._extract_instagram_shortcode(url)
            if not shortcode:
                raise ValueError(f"Invalid Instagram URL: {url}")
            
            from instaloader import Post
            post = Post.from_shortcode(L.context, shortcode)
            
            # Get available qualities
            available_qualities = []
            if post.is_video:
                available_qualities = ['highest']
                if post.video_duration:
                    available_qualities.append('lowest')
            
            return VideoInfo(
                platform=Platform.INSTAGRAM,
                url=url,
                title=post.caption[:100] if post.caption else f"Instagram {shortcode}",
                uploader=post.owner_username,
                likes=post.likes,
                views=post.video_view_count if post.is_video else None,
                description=post.caption,
                thumbnail=post.url,
                is_live=False,
                available_qualities=available_qualities,
                formats=[{
                    'type': 'video' if post.is_video else 'image',
                    'count': post.mediacount,
                    'duration': post.video_duration if post.is_video else None
                }]
            )
        except Exception as e:
            logger.error(f"Error getting Instagram info: {e}")
            raise
    
    def _get_vk_info(self, url: str) -> VideoInfo:
        """Get VK video info"""
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        cookie_file = self.cookie_manager.get_cookie_file(Platform.VK)
        if cookie_file and Path(cookie_file).exists():
            ydl_opts['cookiefile'] = str(cookie_file)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                return VideoInfo(
                    platform=Platform.VK,
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration'),
                    uploader=info.get('uploader'),
                    views=info.get('view_count'),
                    formats=info.get('formats', []),
                    is_live=info.get('is_live', False)
                )
            except Exception as e:
                logger.error(f"Error getting VK info: {e}")
                raise
    
    def _extract_instagram_shortcode(self, url: str) -> Optional[str]:
        """Extract Instagram shortcode from URL"""
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                shortcode = match.group(1)
                return shortcode.split('?')[0]
        
        return None
    
    def download(
        self,
        url: str,
        quality: Union[str, VideoQuality] = VideoQuality.HIGHEST,
        output_path: Optional[Union[str, Path]] = None,
        filename_template: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> DownloadResult:
        """
        Download video from URL
        
        Args:
            url: Video URL
            quality: Video quality (lowest, low, medium, high, highest, audio_only)
            output_path: Custom output path (default: from config)
            filename_template: Custom filename template
            progress_callback: Callback function for progress updates
            **kwargs: Additional platform-specific options
            
        Returns:
            DownloadResult object
        """
        platform = self.detect_platform(url)
        start_time = datetime.now()
        
        if platform == Platform.YOUTUBE:
            result = self._download_youtube(url, quality, output_path, filename_template, progress_callback, **kwargs)
        elif platform == Platform.INSTAGRAM:
            result = self._download_instagram(url, quality, output_path, progress_callback, **kwargs)
        elif platform == Platform.VK:
            result = self._download_vk(url, quality, output_path, filename_template, progress_callback, **kwargs)
        else:
            result = DownloadResult(
                success=False,
                platform=Platform.UNKNOWN,
                url=url,
                error=f"Unsupported platform: {url}"
            )
        
        result.download_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate total size
        for file in result.files:
            if file.exists():
                result.total_size += file.stat().st_size
        
        return result
    
    def _download_youtube(
        self,
        url: str,
        quality: Union[str, VideoQuality],
        output_path: Optional[Union[str, Path]],
        filename_template: Optional[str],
        progress_callback: Optional[callable],
        **kwargs
    ) -> DownloadResult:
        """Download from YouTube"""
        import yt_dlp
        
        output_dir = Path(output_path) if output_path else self.download_path
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Map quality
        quality_map = {
            VideoQuality.LOWEST: 'worst',
            VideoQuality.LOW: 'worst[height<=360]',
            VideoQuality.MEDIUM: 'best[height<=720]',
            VideoQuality.HIGH: 'best[height<=1080]',
            VideoQuality.HIGHEST: 'bestvideo+bestaudio/best',
            VideoQuality.AUDIO_ONLY: 'bestaudio/best'
        }
        
        if isinstance(quality, VideoQuality):
            format_spec = quality_map.get(quality, 'bestvideo+bestaudio/best')
        else:
            format_spec = quality
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': str(output_dir / (filename_template or self.config.get('output_template', '%(title)s.%(ext)s'))),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._create_progress_hook(progress_callback)],
            'retries': self.config.get('retries', 5),
            'socket_timeout': self.config.get('timeout', 30),
        }
        
        # YouTube specific options
        youtube_config = self.config.get('youtube', {})
        ydl_opts.update({
            'merge_output_format': youtube_config.get('merge_output_format', 'mp4'),
            'writethumbnail': youtube_config.get('embed_thumbnail', True),
            'writeinfojson': False,
            'writesubtitles': youtube_config.get('subtitles', False),
            'subtitleslangs': youtube_config.get('subtitles_languages', ['en']),
            'embedsubs': youtube_config.get('subtitles', False),
        })
        
        cookie_file = self.cookie_manager.get_cookie_file(Platform.YOUTUBE)
        if cookie_file and Path(cookie_file).exists():
            ydl_opts['cookiefile'] = str(cookie_file)
        
        # Add proxy if configured
        if self.config.get('proxy'):
            ydl_opts['proxy'] = self.config.get('proxy')
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Find downloaded files
                downloaded_files = []
                template = ydl_opts['outtmpl']
                
                if info.get('requested_downloads'):
                    for download in info['requested_downloads']:
                        if 'filepath' in download:
                            downloaded_files.append(Path(download['filepath']))
                
                if not downloaded_files:
                    # Try to find files by pattern
                    pattern = template.replace('%(title)s', '*').replace('%(ext)s', '*')
                    downloaded_files = list(output_dir.glob(pattern))
                
                return DownloadResult(
                    success=True,
                    platform=Platform.YOUTUBE,
                    url=url,
                    title=info.get('title', 'Unknown'),
                    files=downloaded_files,
                    metadata={
                        'uploader': info.get('uploader'),
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count')
                    }
                )
        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return DownloadResult(
                success=False,
                platform=Platform.YOUTUBE,
                url=url,
                error=str(e)
            )
    
    def _download_instagram(
        self,
        url: str,
        quality: Union[str, VideoQuality],
        output_path: Optional[Union[str, Path]],
        progress_callback: Optional[callable],
        **kwargs
    ) -> DownloadResult:
        """Download from Instagram"""
        try:
            import instaloader
            from instaloader import Post
            
            output_dir = Path(output_path) if output_path else self.download_path
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Change to output directory temporarily
            original_dir = os.getcwd()
            os.chdir(output_dir)
            
            try:
                L = instaloader.Instaloader(
                    download_videos=True,
                    download_video_thumbnails=False,
                    download_geotags=False,
                    download_comments=False,
                    save_metadata=self.config.get('instagram.save_metadata', False),
                    compress_json=False,
                    post_metadata_txt_pattern='',
                    max_connection_attempts=self.config.get('retries', 3),
                    request_timeout=self.config.get('timeout', 30.0),
                    quiet=True
                )
                
                cookie_file = self.cookie_manager.get_cookie_file(Platform.INSTAGRAM)
                if cookie_file and Path(cookie_file).exists():
                    L.load_session_from_file(username=None, filename=str(cookie_file))
                
                shortcode = self._extract_instagram_shortcode(url)
                if not shortcode:
                    raise ValueError(f"Invalid Instagram URL: {url}")
                
                post = Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target='.')
                
                # Find downloaded files
                downloaded_files = []
                current_dir = Path(output_dir)
                
                # Look for video and image files
                video_files = list(current_dir.glob(f'*{shortcode}*.mp4')) + \
                             list(current_dir.glob(f'*{shortcode}*.mov'))
                image_files = list(current_dir.glob(f'*{shortcode}*.jpg')) + \
                             list(current_dir.glob(f'*{shortcode}*.png'))
                
                downloaded_files = video_files + image_files
                
                # Clean up metadata files
                for json_file in current_dir.glob(f'*{shortcode}*.json'):
                    json_file.unlink()
                for txt_file in current_dir.glob(f'*{shortcode}*.txt'):
                    txt_file.unlink()
                
                return DownloadResult(
                    success=True,
                    platform=Platform.INSTAGRAM,
                    url=url,
                    title=f"Instagram_{shortcode}",
                    files=downloaded_files,
                    metadata={
                        'uploader': post.owner_username,
                        'likes': post.likes,
                        'views': post.video_view_count if post.is_video else None,
                        'is_video': post.is_video,
                        'media_count': post.mediacount
                    }
                )
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return DownloadResult(
                success=False,
                platform=Platform.INSTAGRAM,
                url=url,
                error=str(e)
            )
    
    def _download_vk(
        self,
        url: str,
        quality: Union[str, VideoQuality],
        output_path: Optional[Union[str, Path]],
        filename_template: Optional[str],
        progress_callback: Optional[callable],
        **kwargs
    ) -> DownloadResult:
        """Download from VK"""
        import yt_dlp
        
        output_dir = Path(output_path) if output_path else self.download_path
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # VK specific options
        quality_map = {
            VideoQuality.LOWEST: 'worst',
            VideoQuality.LOW: 'worst[height<=360]',
            VideoQuality.MEDIUM: 'best[height<=480]',
            VideoQuality.HIGH: 'best[height<=720]',
            VideoQuality.HIGHEST: 'best[height<=1080]',
            VideoQuality.AUDIO_ONLY: 'bestaudio/best'
        }
        
        if isinstance(quality, VideoQuality):
            format_spec = quality_map.get(quality, 'best[height<=1080]')
        else:
            format_spec = quality
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': str(output_dir / (filename_template or self.config.get('output_template', '%(title)s.%(ext)s'))),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._create_progress_hook(progress_callback)],
            'retries': self.config.get('retries', 5),
            'socket_timeout': self.config.get('timeout', 30),
        }
        
        # VK specific headers
        vk_config = self.config.get('vk', {})
        ydl_opts.update({
            'user_agent': vk_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'referer': vk_config.get('referer', 'https://vk.com/'),
        })
        
        cookie_file = self.cookie_manager.get_cookie_file(Platform.VK)
        if cookie_file and Path(cookie_file).exists():
            ydl_opts['cookiefile'] = str(cookie_file)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                downloaded_files = []
                if info.get('requested_downloads'):
                    for download in info['requested_downloads']:
                        if 'filepath' in download:
                            downloaded_files.append(Path(download['filepath']))
                
                return DownloadResult(
                    success=True,
                    platform=Platform.VK,
                    url=url,
                    title=info.get('title', 'Unknown'),
                    files=downloaded_files,
                    metadata={
                        'uploader': info.get('uploader'),
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count')
                    }
                )
        except Exception as e:
            logger.error(f"VK download error: {e}")
            return DownloadResult(
                success=False,
                platform=Platform.VK,
                url=url,
                error=str(e)
            )
    
    def _create_progress_hook(self, callback: Optional[callable]):
        """Create progress hook for yt-dlp"""
        def hook(d):
            if d['status'] == 'downloading':
                if callback:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    speed = d.get('speed', 0)
                    
                    callback({
                        'downloaded': downloaded,
                        'total': total,
                        'percentage': (downloaded / total * 100) if total > 0 else 0,
                        'speed': speed,
                        'eta': d.get('eta'),
                        'filename': d.get('filename', '')
                    })
            elif d['status'] == 'finished':
                if callback:
                    callback({'status': 'finished', 'filename': d.get('filename', '')})
        
        return hook
    
    def download_multiple(
        self,
        urls: List[str],
        quality: Union[str, VideoQuality] = VideoQuality.HIGHEST,
        output_path: Optional[Union[str, Path]] = None,
        max_concurrent: int = 1,
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> List[DownloadResult]:
        """
        Download multiple videos
        
        Args:
            urls: List of video URLs
            quality: Video quality
            output_path: Custom output path
            max_concurrent: Maximum concurrent downloads
            progress_callback: Progress callback for each download
            **kwargs: Additional options
            
        Returns:
            List of DownloadResult objects
        """
        results = []
        
        if max_concurrent > 1 and self.config.get('concurrent_downloads', 1) > 1:
            # Implement concurrent downloads
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_url = {
                    executor.submit(
                        self.download, url, quality, output_path, None, progress_callback, **kwargs
                    ): url for url in urls
                }
                
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if progress_callback:
                            progress_callback({'url': url, 'result': result})
                    except Exception as e:
                        results.append(DownloadResult(
                            success=False,
                            platform=Platform.UNKNOWN,
                            url=url,
                            error=str(e)
                        ))
        else:
            # Sequential downloads
            for url in urls:
                result = self.download(url, quality, output_path, None, progress_callback, **kwargs)
                results.append(result)
                if progress_callback:
                    progress_callback({'url': url, 'result': result})
        
        return results
    
    def set_cookies(self, platform: Union[str, Platform], cookies: Union[str, Dict, Path]):
        """
        Set cookies for a platform
        
        Args:
            platform: Platform name ('youtube', 'instagram', 'vk')
            cookies: Cookies data
        """
        if isinstance(platform, str):
            platform = Platform(platform.lower())
        
        self.cookie_manager.set_cookies(platform, cookies)
    
    def set_instagram_session(self, username: str, password: Optional[str] = None, session_file: Optional[Path] = None):
        """
        Set Instagram session for authenticated downloads
        
        Args:
            username: Instagram username
            password: Instagram password (optional if session_file provided)
            session_file: Session file path
        """
        import instaloader
        
        L = instaloader.Instaloader()
        
        if session_file and Path(session_file).exists():
            L.load_session_from_file(username, filename=str(session_file))
            self.config.set('instagram.session_file', str(session_file))
        elif username and password:
            L.login(username, password)
            session_file = self.cookie_manager.cookies_dir / f"instagram_session_{username}"
            L.save_session_to_file(filename=str(session_file))
            self.config.set('instagram.session_file', str(session_file))
            self.config.set('instagram.username', username)
        else:
            raise ValueError("Either session_file or username and password required")
    
    def get_download_history(self, limit: int = 50) -> List[Dict]:
        """
        Get download history
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of download history entries
        """
        history_file = self.config.config_dir / 'download_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    return history[-limit:]
            except:
                return []
        return []
    
    def save_to_history(self, result: DownloadResult):
        """Save download result to history"""
        history_file = self.config.config_dir / 'download_history.json'
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'platform': result.platform.value,
            'url': result.url,
            'title': result.title,
            'files': [str(f) for f in result.files],
            'success': result.success,
            'error': result.error,
            'download_time': result.download_time,
            'total_size': result.total_size
        }
        
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(entry)
        
        # Keep only last 1000 entries
        if len(history) > 1000:
            history = history[-1000:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
            self.temp_path.mkdir(parents=True, exist_ok=True)
            logger.info("Temporary files cleaned up")

# CLI Interface
def main_cli():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Video Downloader for YouTube, Instagram, and VK')
    parser.add_argument('url', nargs='?', help='Video URL to download')
    parser.add_argument('-q', '--quality', default='highest', 
                       choices=['lowest', 'low', 'medium', 'high', 'highest', 'audio_only'],
                       help='Video quality')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('-c', '--config', help='Config file path')
    parser.add_argument('--info', action='store_true', help='Get video info only')
    parser.add_argument('--set-cookies', help='Set cookies file for platform')
    parser.add_argument('--platform', choices=['youtube', 'instagram', 'vk'], help='Platform for cookies')
    parser.add_argument('--batch', help='Batch file with URLs')
    parser.add_argument('--history', action='store_true', help='Show download history')
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = VideoDownloader(args.config if args.config else None)
    
    if args.history:
        history = downloader.get_download_history()
        print("\n=== Download History ===")
        for entry in history:
            status = "‚úÖ" if entry['success'] else "‚ùå"
            print(f"{status} {entry['timestamp']} - {entry['platform']}: {entry['title']}")
        return
    
    if args.set_cookies and args.platform:
        cookie_file = Path(args.set_cookies)
        if cookie_file.exists():
            downloader.set_cookies(args.platform, cookie_file)
            print(f"‚úÖ Cookies set for {args.platform}")
        else:
            print(f"‚ùå Cookie file not found: {cookie_file}")
        return
    
    if args.info and args.url:
        try:
            info = downloader.get_video_info(args.url)
            print(f"\n=== Video Info ===")
            print(f"Platform: {info.platform.value}")
            print(f"Title: {info.title}")
            if info.uploader:
                print(f"Uploader: {info.uploader}")
            if info.duration:
                minutes = info.duration // 60
                seconds = info.duration % 60
                print(f"Duration: {minutes}:{seconds:02d}")
            if info.views:
                print(f"Views: {info.views:,}")
            if info.likes:
                print(f"Likes: {info.likes:,}")
            if info.available_qualities:
                print(f"Available qualities: {', '.join(info.available_qualities)}")
        except Exception as e:
            print(f"‚ùå Error: {e}")
        return
    
    if args.batch:
        # Download from batch file
        try:
            with open(args.batch, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"\n=== Downloading {len(urls)} videos ===")
            
            def progress_callback(data):
                if 'percentage' in data:
                    print(f"\rProgress: {data['percentage']:.1f}%", end='', flush=True)
                elif 'url' in data and 'result' in data:
                    result = data['result']
                    status = "‚úÖ" if result.success else "‚ùå"
                    print(f"\n{status} {result.title or result.url}")
            
            results = downloader.download_multiple(
                urls,
                quality=args.quality,
                output_path=args.output,
                progress_callback=progress_callback
            )
            
            # Summary
            successful = sum(1 for r in results if r.success)
            print(f"\n=== Summary ===")
            print(f"Total: {len(results)}")
            print(f"Successful: {successful}")
            print(f"Failed: {len(results) - successful}")
            
        except Exception as e:
            print(f"‚ùå Error: {e}")
    
    elif args.url:
        # Download single video
        try:
            print(f"\n=== Downloading ===")
            print(f"URL: {args.url}")
            
            def progress_callback(data):
                if 'percentage' in data:
                    print(f"\rProgress: {data['percentage']:.1f}% - {data.get('speed', 0)/1024:.1f} KB/s", end='', flush=True)
                elif 'status' in data and data['status'] == 'finished':
                    print(f"\n‚úÖ Download finished: {Path(data['filename']).name}")
            
            result = downloader.download(
                args.url,
                quality=args.quality,
                output_path=args.output,
                progress_callback=progress_callback
            )
            
            if result.success:
                print(f"\n‚úÖ Success!")
                for file in result.files:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"üìÅ {file.name} ({size_mb:.1f} MB)")
                print(f"‚è±Ô∏è  Time: {result.download_time:.1f} seconds")
            else:
                print(f"\n‚ùå Failed: {result.error}")
                
        except KeyboardInterrupt:
            print("\n\n‚ùå Download cancelled")
        except Exception as e:
            print(f"‚ùå Error: {e}")
    
    else:
        parser.print_help()

# Example usage and documentation
if __name__ == "__main__":
    # If run as script, use CLI
    main_cli()
else:
    # If imported as module, provide documentation
    __doc__ = """
    Video Downloader Library
    
    Examples:
        from video_downloader import VideoDownloader, VideoQuality
        
        # Basic usage
        downloader = VideoDownloader()
        result = downloader.download('https://youtube.com/watch?v=...', quality=VideoQuality.HIGH)
        
        # Get video info
        info = downloader.get_video_info('https://youtube.com/watch?v=...')
        print(info.title)
        
        # Set cookies for authenticated downloads
        downloader.set_cookies('youtube', 'path/to/cookies.txt')
        
        # Download multiple videos
        urls = ['url1', 'url2', 'url3']
        results = downloader.download_multiple(urls, max_concurrent=3)
        
        # Custom configuration
        config = {
            'download_path': '/my/downloads',
            'youtube': {
                'embed_metadata': True
            }
        }
        downloader = VideoDownloader(config)
        
        # Instagram with authentication
        downloader.set_instagram_session(username='user', password='pass')
        
        # Progress tracking
        def progress(data):
            print(f"Downloaded: {data['percentage']:.1f}%")
        
        result = downloader.download(url, progress_callback=progress)
    """