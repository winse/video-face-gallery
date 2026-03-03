# AGENTS.md - Coding Guidelines for Video Face Classification System

This file provides guidelines for AI agents working on this codebase.

## Environment Setup

```bash
# Activate conda environment
conda activate video

# Project root
cd E:\local\home\xwechat_files\winseliu_f4ec\msg\video\py

# FFmpeg path (Windows)
E:\local\ffmpeg\bin\ffmpeg.exe
E:\local\ffmpeg\bin\ffprobe.exe
```

## Build, Lint, Test Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_face_detector.py

# Run specific test
pytest tests/test_face_detector.py::TestFaceDetector::test_detect_faces

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Skip slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m "integration"

# GPU tests (require CUDA)
pytest -m "gpu"
```

## Code Style Guidelines

### Imports

```python
# Standard library first, alphabetical
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
from tqdm import tqdm

# Local imports (relative)
from module import Class
from .package import function
```

### Module Structure

```python
"""
Module docstring - brief description of what this module does
"""
import logging
from typing import ...

# Logger at module level (use underscore, not hyphen)
logger = logging.getLogger("video_face")

class ClassName:
    """Class docstring"""
    def __init__(self, param: str) -> None:
        """Init docstring"""
        ...

def function_name(param: int) -> bool:
    """Function docstring"""
    ...
```

### Type Hints

```python
# Use type hints for function signatures
def process_video(
    video_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:

# Generic types
from typing import TypeVar, Generic
T = TypeVar('T')

class Container(Generic[T]):
    def get(self) -> T:
        ...

# Union types (modern syntax)
def fetch_data() -> str | None:
    ...

# Literal types
from typing import Literal
def sort_videos(mode: Literal['asc', 'desc']) -> None:
    ...
```

### Naming Conventions

```python
# Classes: PascalCase
class FaceDetector:
    ...

# Functions/variables: snake_case
def extract_frames():
    video_count = 0

# Constants: UPPER_SCASE
MAX_FRAMES = 100
DEFAULT_THRESHOLD = 0.6

# Private methods: _prefix
class Pipeline:
    def _initialize_components(self) -> None:
        ...

# Private module variables: _prefix
_script_dir = os.path.dirname(__file__)

# Abbreviations: lowercase (not CAPS)
# AVOID: def getFPS(), use def get_fps()
# ACCEPTABLE: cv2, np (standard library conventions)
```

### Error Handling

```python
# Use specific exceptions
try:
    result = subprocess.run(cmd, capture_output=True, timeout=30)
except subprocess.TimeoutExpired:
    logger.error("Command timed out")
    return None

# Avoid bare except
try:
    ...
except Exception as e:
    logger.error(f"Failed to process: {e}")
    return default_value

# Use logger, not print()
logger.info("Processing started")
logger.warning(f"Low confidence: {conf:.2f}")
logger.error(f"Failed: {e}")
```

### Configuration

```python
# Use config.py for all configurable parameters
# Group related configs with section comments

# ==========================================
# Video Processing Configuration
# ==========================================

VIDEO_CONFIG = {
    'max_videos': None,
    'parallel_workers': 1,
}

# Access via get_config()
from config import get_config
config = get_config()
threshold = config['face_detection']['confidence_threshold']
```

### Logging

```python
# Module logger
logger = logging.getLogger("video_face")

# Use format strings (lazy evaluation)
logger.debug("Processing video: %s", video_path)
logger.info("Faces detected: %d", face_count)
logger.warning("Low confidence: %.2f", conf)
logger.error("Failed to load: %s", e)

# Avoid f-strings in logging (evaluated even when disabled)
# BAD: logger.info(f"Value: {value}")
# GOOD: logger.info("Value: %s", value)
```

### Comments

```python
# Inline comments: 2 spaces before #
value = 100  # Maximum allowed

# Block comments: on own line, limited use
# Calculate frame position based on timestamp
frame_pos = int(timestamp * fps)

# Docstrings: Google-style
def extract_face(
    image: np.ndarray,
    bbox: List[int]
) -> Optional[np.ndarray]:
    """Extract face region from image based on bounding box.

    Args:
        image: Input image array
        bbox: Bounding box coordinates [x1, y1, x2, y2]

    Returns:
        Cropped face image or None if invalid
    """
    ...
```

### File Paths (Cross-Platform)

```python
# Use Path objects
from pathlib import Path
video_path = Path(r"E:\videos\video.mp4")

# Avoid hardcoded paths in code
# Use config or environment variables
VIDEO_DIR = Path(os.environ.get('VIDEO_DIR', 'videos'))

# Path operations
video_path.exists()
video_path.stat().st_size
video_path.parent / "subdir" / "file.txt"
```

### Data Serialization

```python
# Use orjson for JSON (faster, handles bytes)
import orjson
data = orjson.loads(f.read())
orjson.dumps(data)

# Regular json for simple cases
import json
with open('file.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### Testing Patterns

```python
# pytest fixtures in tests/conftest.py
@pytest.fixture
def sample_video(video_dir: Path) -> Path:
    videos = list(video_dir.glob("*.mp4"))
    return videos[0] if videos else None

# Test class pattern
class TestFaceDetector:
    def test_detect_single_face(self, sample_video: Path):
        detector = FaceDetector()
        faces = detector.detect(sample_video)
        assert len(faces) >= 1

# Mocking external dependencies
from unittest.mock import Mock, patch
```

## Key Technologies

- **Face Detection**: InsightFace (buffalo_l model)
- **Video Processing**: FFmpeg + OpenCV (cv2)
- **Clustering**: sklearn DBSCAN/Agglomerative
- **Data**: orjson for JSON, numpy arrays
- **Testing**: pytest with fixtures

## Common Workflows

```bash
# Process videos with face detection
python pipeline.py

# Generate HTML pages
python regenerate_html.py

# Run deduplication
python video_deduplicator.py --remove

# Debug clustering only
python debug_cluster.py
```

## Commit Message Style

Use conventional commits:
```
feat: add new face clustering algorithm
fix: handle empty video files
refactor: optimize frame extraction
docs: update README
config: adjust clustering thresholds
```

## Project Structure

```
py/
├── pipeline.py           # Main processing pipeline
├── config.py             # Configuration parameters
├── video_deduplicator.py # Video deduplication
├── regenerate_html.py     # HTML generation
├── face_detector.py      # InsightFace wrapper
├── face_clusterer.py     # Clustering logic
├── face_storage.py       # Data persistence
├── frame_extractor.py    # FFmpeg wrapper
├── utils.py              # Utility functions
├── tests/                # Pytest tests
├── 2026-02/             # Video directory
└── thumbnails/           # Output thumbnails
```
