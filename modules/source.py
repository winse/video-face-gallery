"""
Source Data Module
Handles video discovery, metadata extraction, and deduplication.
"""
import os
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from config import get_config
from utils import get_video_date_from_path
from engine.video_deduplicator import VideoDeduplicator

logger = logging.getLogger("video_face.source")

class VideoSource:
    def __init__(self, video_dir: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        paths = self.config.get('paths', {})
        self.video_dir = Path(video_dir or paths.get('video_dir', '.'))
        self.ffprobe_path = self.config['ffmpeg'].get('ffprobe_path', 'ffprobe')

    def scan(self) -> List[Path]:
        """Scan video directory recursively for MP4 files."""
        logger.info(f"Scanning videos in: {self.video_dir}")
        if not self.video_dir.exists():
            logger.warning("Video directory does not exist: %s", self.video_dir)
            return []
        videos = sorted(list(self.video_dir.rglob("*.mp4")))
        if not videos:
            logger.warning("No .mp4 files found under: %s", self.video_dir)
        logger.info(f"Found {len(videos)} videos")
        return videos

    def deduplicate(self, videos: List[Path]) -> List[Path]:
        """Remove duplicate videos using perceptual hashing."""
        dedup_config = self.config.get('deduplication', {})
        if not dedup_config.get('enabled', False):
            return videos

        ffmpeg_config = self.config['ffmpeg']
        deduplicator = VideoDeduplicator(
            ffmpeg_path=ffmpeg_config['ffmpeg_path'],
            similarity_threshold=dedup_config.get('similarity_threshold', 0.90),
            sample_frames=dedup_config.get('sample_frames', 3),
            hash_size=dedup_config.get('hash_size', 16),
            temp_dir=dedup_config.get('temp_dir', 'temp_dedupe')
        )
        
        unique_videos, _ = deduplicator.find_duplicates(videos)
        return unique_videos

    def get_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Extract metadata from a video file."""
        video_path = Path(video_path)
        default_meta = {
            'size': '?', 
            'v_create_date': '?', 
            'duration': '0:00',
            'video_name': video_path.name
        }

        if not video_path.exists():
            return default_meta

        try:
            stat = video_path.stat()
            size_bytes = stat.st_size
            
            # Formatted size
            size_str = self._format_size(size_bytes)
            
            # Duration and creation time via ffprobe
            duration, creation_time = self._probe_video(video_path)
            
            # Fallback for creation time
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            ctime = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            if not creation_time or creation_time == "?":
                creation_time = ctime

            return {
                'size': size_str,
                'v_create_date': creation_time,
                'duration': self._format_duration(duration),
                'mtime': mtime,
                'ctime': ctime,
                'video_name': video_path.name,
                'video_path': str(video_path)
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {video_path}: {e}")
            return default_meta

    def _probe_video(self, path: Path) -> Tuple[float, str]:
        """Run ffprobe to get duration and creation time."""
        duration = 0.0
        creation_time = "?"
        
        try:
            # Get duration
            cmd_dur = [
                self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', str(path)
            ]
            res_dur = subprocess.run(cmd_dur, capture_output=True, text=True, timeout=5)
            if res_dur.returncode == 0 and res_dur.stdout.strip():
                duration = float(res_dur.stdout.strip())
                
            # Get creation time
            cmd_time = [
                self.ffprobe_path, '-v', 'error', '-show_entries', 'format_tags=creation_time',
                '-of', 'default=noprint_wrappers=1:nokey=1', str(path)
            ]
            res_time = subprocess.run(cmd_time, capture_output=True, text=True, timeout=5)
            if res_time.returncode == 0 and res_time.stdout.strip():
                creation_time = res_time.stdout.strip().replace('T', ' ').replace('Z', '')
        except:
            pass
            
        return duration, creation_time

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        return f"{int(seconds // 60)}:{int(seconds % 60):02d}"
