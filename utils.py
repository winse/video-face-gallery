"""
Utility functions for video face extraction pipeline
"""
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Union, Dict, Any, List, Optional

# ==========================================
# Logging Configuration
# ==========================================

def setup_logging(log_file: Union[str, Path] = "processing.log", level: int = logging.INFO) -> logging.Logger:
    log_file = Path(log_file)
    logger = logging.getLogger("video_face")
    logger.setLevel(level)
    logger.handlers.clear()
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# ==========================================
# Path Utilities
# ==========================================

def ensure_dir(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_hash(filepath: Union[str, Path], algorithm: str = "md5") -> str:
    filepath = Path(filepath)
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# ==========================================
# Timestamp Utilities
# ==========================================

def format_timestamp(seconds: Union[float, int, None]) -> str:
    """Format video timestamp (robust against None)."""
    if seconds is None:
        return "00:00:00.000"
    try:
        seconds = float(seconds)
    except:
        return "00:00:00.000"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def parse_timestamp(timestamp: str) -> float:
    parts = timestamp.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        secs = float(parts[2])
        return hours * 3600 + minutes * 60 + secs
    raise ValueError(f"Invalid timestamp format: {timestamp}")

# ==========================================
# Date/Time Utilities
# ==========================================

def get_video_date_from_path(video_path: Union[str, Path]) -> str:
    path = Path(video_path)
    parent_name = path.parent.name
    try:
        datetime.strptime(parent_name, "%Y-%m")
        return parent_name
    except ValueError:
        return "unknown"

# ==========================================
# Image Utilities
# ==========================================

def resize_dimensions(width: int, height: int, max_size: int):
    if width <= max_size and height <= max_size:
        return width, height
    aspect = width / height if height != 0 else 1
    if width > height:
        new_w = max_size
        new_h = int(max_size / aspect)
    else:
        new_h = max_size
        new_w = int(max_size * aspect)
    return new_w, new_h

# ==========================================
# Progress Tracking
# ==========================================

class ProgressTracker:
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.description = description
        self.current = 0
        self.last_percent = -1
        self.logger = logging.getLogger("video_face")

    def update(self, increment: int = 1) -> None:
        self.current += increment
        percent = int((self.current / self.total) * 100) if self.total > 0 else 100
        if percent >= self.last_percent + 10:
            self.logger.info(f"{self.description}: {self.current}/{self.total} ({percent}%)")
            self.last_percent = percent

    def complete(self) -> None:
        self.current = self.total
        self.logger.info(f"{self.description}: Complete ({self.current}/{self.total})")
