"""
Configuration file for video face extraction pipeline
"""
import os
from pathlib import Path

# ==========================================
# Environment Variables (can be overridden)
# ==========================================

# Default to script location if not set
_script_dir = os.path.dirname(os.path.abspath(__file__))
_default_project_root = os.path.abspath(_script_dir)

# Project directory (where Python scripts live)
PROJECT_DIR = _default_project_root

# Static web code directory (HTML/CSS/JS)
WEB_STATIC_DIR = os.path.join(PROJECT_DIR, 'web')
# Runtime web data directory (face_data.json + thumbnails)
WEB_DATA_DIR = os.path.join(WEB_STATIC_DIR, 'face_data')

# Video directory (all date directories under web/data)
VIDEO_DIR = os.path.join(WEB_STATIC_DIR, 'data')

# FFmpeg paths
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', r'ffmpeg.exe')
FFPROBE_PATH = os.environ.get('FFPROBE_PATH', r'ffprobe.exe')

# ==========================================
# FFmpeg Configuration
# ==========================================

FFMPEG_CONFIG = {
    'ffmpeg_path': FFMPEG_PATH,
    'ffprobe_path': FFPROBE_PATH,
    'output_dir': 'thumbnails',
    'quality': 90,
    'default_size': (640, 480)
}

# ==========================================
# InsightFace / Face Detection Configuration
# ==========================================
# USE_GPU: 1/true/yes = GPU, 0/false/no = CPU，不设则默认 True
USE_GPU = os.environ.get('USE_GPU', '1').strip().lower() in ('1', 'true', 'yes')

FACE_DETECTION_CONFIG = {
    'use_gpu': USE_GPU,
    'model_name': 'buffalo_l',
    'confidence_threshold': 0.7,  # Higher = stricter detection
    'min_face_size': (60, 60)
}

# ==========================================
# Clustering Configuration
# ==========================================

CLUSTERING_CONFIG = {
    # DBSCAN clustering parameters
    'dbscan': {
        'eps': 0.45,           # Cosine distance threshold (higher = more aggressive matching, lower = stricter)
        'min_samples': 2,      # Minimum samples in a cluster
        'metric': 'cosine'      # Distance metric
    },

    # Agglomerative clustering parameters (alternative)
    'agglomerative': {
        'distance_threshold': 0.5,  # Higher = more aggressive matching
        'linkage': 'average'
    },

    # Default method
    'default_method': 'dbscan'
}

# ==========================================
# Quality Filter Configuration
# ==========================================

QUALITY_FILTER_CONFIG = {
    'min_face_size': (60, 60),
    'confidence_threshold': 0.6,
    'max_faces_per_frame': 5,
    'min_face_quality_score': 0.3  # Blur/sharpness threshold
}

# ==========================================
# Video Deduplication Configuration
# ==========================================

DEDUPLICATION_CONFIG = {
    'enabled': os.environ.get('DEDUPLICATION_ENABLED', '1').strip().lower() in ('1', 'true', 'yes'),
    # Enable/disable video deduplication
    'similarity_threshold': 0.90,    # Hamming similarity threshold (0-1)
    'sample_frames': 3,              # Frames to sample per video for fingerprinting
    'hash_size': 16,                # Perceptual hash size
    'remove_duplicates': False,       # Actually remove duplicate files
    'report_file': 'duplicate_report.txt',  # Report output file
    'temp_dir': 'temp_dedupe'       # Temporary directory for deduplication
}

# ==========================================
# Video Processing Configuration
# ==========================================

VIDEO_PROCESSING_CONFIG = {
    # Frame extraction
    'frames_per_video': 3,         # Backward-compatible base frame count
    'adaptive_sampling': {
        'enabled': True,
        'target_interval_seconds': 8.0,   # target spacing between sampled timestamps
        'min_frames': 3,                  # minimum sampled frames per video
        'max_frames': 7,                 # cap for very long videos
        'retry_if_no_face': True,         # retry when first pass detects no faces
        'retry_prime_frames': [3, 11, 29],  # prime-count retry stages， 11,17,29,37
        'retry_max_rounds': 3             # number of retry rounds to run
    },
    'skip_start_seconds': 1.0,     # Skip first N seconds
    'skip_end_seconds': 1.0,        # Skip last N seconds

    # Processing limits
    'max_videos': None,             # None = process all
    'parallel_workers': 1,           # Number of parallel workers (1 = sequential)

    # Resume from checkpoint
    'resume_from': None,            # Resume from specific checkpoint or video

    # Video deduplication (references DEDUPLICATION_CONFIG)
    'deduplication': DEDUPLICATION_CONFIG
}

# ==========================================
# Storage Configuration
# ==========================================

STORAGE_CONFIG = {
    'data_file': os.path.join(WEB_DATA_DIR, 'face_data.json'),
    'clustering_results_file': 'clustering_results.json',
    'auto_save': True,
    'backup_on_save': False
}

# ==========================================
# HTML Generation Configuration
# ==========================================

HTML_CONFIG = {
    'output_file': 'index.html',
    'template_file': 'templates/index.html.j2',
    'title': '视频人脸索引',

    # UI settings
    'items_per_page': 20,
    'show_face_count': True,
    'show_video_count': True,
    'show_date_range': True,

    # Thumbnail settings
    'thumbnail_size': (200, 200),
    'thumbnail_quality': 85,

    # CSS/JS
    'embed_css': True,
    'embed_js': True
}

# ==========================================
# Logging Configuration
# ==========================================

LOGGING_CONFIG = {
    'log_file': 'processing.log',
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# ==========================================
# Path Configuration
# ==========================================

PATH_CONFIG = {
    'project_root': PROJECT_DIR,
    'project_dir': PROJECT_DIR,
    'video_dir': VIDEO_DIR,
    'output_dir': WEB_DATA_DIR,
    'web_dir': WEB_DATA_DIR,
    'web_static_dir': WEB_STATIC_DIR,
    'data_file': os.path.join(WEB_DATA_DIR, 'face_data.json'),
    'thumbnails_dir': os.path.join(WEB_DATA_DIR, 'thumbnails')
}

# ==========================================
# Get combined configuration
# ==========================================

def get_config() -> dict:
    """
    Get all configuration as a single dictionary

    Returns:
        Combined configuration dictionary
    """
    return {
        'ffmpeg': FFMPEG_CONFIG,
        'face_detection': FACE_DETECTION_CONFIG,
        'clustering': CLUSTERING_CONFIG,
        'quality_filter': QUALITY_FILTER_CONFIG,
        'deduplication': DEDUPLICATION_CONFIG,
        'video_processing': VIDEO_PROCESSING_CONFIG,
        'storage': STORAGE_CONFIG,
        'html': HTML_CONFIG,
        'logging': LOGGING_CONFIG,
        'paths': PATH_CONFIG
    }
